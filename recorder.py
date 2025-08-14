import os
import sys
import time
import socket
import shutil
import logging
import subprocess
from datetime import datetime, date
from pathlib import Path

# Third-party
try:
	from mss import mss  # For monitor enumeration
except ImportError:
	print("Missing dependency 'mss'. Run: pip install -r requirements.txt", file=sys.stderr)
	raise

# Windows-specific graceful shutdown handling
try:
	import win32api  # type: ignore
	import win32con  # type: ignore
	_HAS_WIN32 = True
except Exception:
	_HAS_WIN32 = False


# ---------- Configuration ----------
NETWORK_ROOTS = [
	r"\\Desktop-j82oa53\grabaciones",
	r"\\192.168.10.149\grabaciones",
]
LOCAL_ROOT = r"C:\\Users\\FELIPE REDES\\Desktop\\GRABACIONES"
FRAMERATE = 25  # FPS per monitor
CRF_QUALITY = 20  # Lower is better quality (18-23 typical). 20 ~ good
SEGMENT_SECONDS = 3600  # 1 hour segments for safety/reliability
VIDEO_CODEC = "libx264"
VIDEO_CONTAINER_EXT = ".mkv"  # MKV is robust if process is interrupted

# If True, also try to capture system audio to WAV via FFmpeg WASAPI (best-effort)
CAPTURE_AUDIO_WAV = True
AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 2

LOGLEVEL = "warning"  # ffmpeg loglevel


# ---------- Helpers ----------
def find_executable(names):
	"""Return the first found absolute path to an executable from a list of names or common paths."""
	candidates = []
	for name in names:
		found = shutil.which(name)
		if found:
			candidates.append(found)

	# Add common WinRAR paths specifically when searching for RAR/FFmpeg
	if not candidates:
		for path in [
			# FFmpeg typical installs
			r"C:\\ffmpeg\\bin\\ffmpeg.exe",
			r"C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
			r"C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe",
			# WinRAR typical installs
			r"C:\\Program Files\\WinRAR\\Rar.exe",
			r"C:\\Program Files (x86)\\WinRAR\\Rar.exe",
			r"C:\\Program Files\\WinRAR\\rar.exe",
		]:
			if os.path.isfile(path):
				candidates.append(path)

	return candidates[0] if candidates else None


def choose_base_root() -> Path:
	"""Try network roots in order, fallback to local root. Ensure existence and return the base path."""
	for net in NETWORK_ROOTS:
		try:
			p = Path(net)
			p.mkdir(parents=True, exist_ok=True)
			return p
		except Exception:
			continue
	local = Path(LOCAL_ROOT)
	local.mkdir(parents=True, exist_ok=True)
	return local


def ensure_output_dir_for_date(host_dir: Path, date_str: str) -> Path:
	"""Ensure and return the folder path `<host_dir>/<YYYY-MM-DD>`."""
	date_dir = host_dir / date_str
	date_dir.mkdir(parents=True, exist_ok=True)
	return date_dir


def enumerate_monitors():
	"""Return list of dicts with left, top, width, height for each physical monitor."""
	with mss() as sct:
		# sct.monitors[0] is the virtual bounding box of all monitors.
		monitors = sct.monitors[1:]  # skip index 0
		# Normalize dict to only needed keys
		result = []
		for m in monitors:
			result.append({
				"left": int(m.get("left", 0)),
				"top": int(m.get("top", 0)),
				"width": int(m.get("width", 0)),
				"height": int(m.get("height", 0)),
			})
		return result


def build_ffmpeg_video_cmd(ffmpeg_path: str, monitor_idx: int, region: dict, output_dir: Path) -> tuple[list[str], str]:
	"""Build FFmpeg command for recording one monitor to hourly MKV segments.
	Returns (cmd_list, output_pattern_path_str)."""
	left = region["left"]
	top = region["top"]
	width = region["width"]
	height = region["height"]

	output_pattern = output_dir / f"monitor{monitor_idx+1}_%Y-%m-%d_%H-%M-%S{VIDEO_CONTAINER_EXT}"

	cmd = [
		ffmpeg_path,
		"-loglevel", LOGLEVEL,
		"-y",
		# Video input from gdigrab (Windows)
		"-f", "gdigrab",
		"-framerate", str(FRAMERATE),
		"-offset_x", str(left),
		"-offset_y", str(top),
		"-video_size", f"{width}x{height}",
		"-draw_mouse", "1",
		"-i", "desktop",
		# Encoding
		"-c:v", VIDEO_CODEC,
		"-pix_fmt", "yuv420p",
		"-preset", "veryfast",
		"-crf", str(CRF_QUALITY),
		# Segment to hourly files
		"-f", "segment",
		"-segment_time", str(SEGMENT_SECONDS),
		"-reset_timestamps", "1",
		"-strftime", "1",
		str(output_pattern)
	]
	return cmd, str(output_pattern)


def build_ffmpeg_audio_cmd(ffmpeg_path: str, output_dir: Path) -> tuple[list[str], str]:
	"""Build FFmpeg command to record system audio (best-effort) to hourly WAV segments.
	Note: Requires FFmpeg with WASAPI support. If fails, audio is skipped."""
	output_pattern = output_dir / "audio_%Y-%m-%d_%H-%M-%S.wav"
	cmd = [
		ffmpeg_path,
		"-loglevel", LOGLEVEL,
		"-y",
		"-f", "wasapi",
		"-i", "default",
		"-ac", str(AUDIO_CHANNELS),
		"-ar", str(AUDIO_SAMPLE_RATE),
		"-acodec", "pcm_s16le",
		"-f", "segment",
		"-segment_time", str(SEGMENT_SECONDS),
		"-reset_timestamps", "1",
		"-strftime", "1",
		str(output_pattern)
	]
	return cmd, str(output_pattern)


def start_process(cmd: list[str]) -> subprocess.Popen:
	creationflags = 0
	startupinfo = None
	if os.name == "nt":
		# Hide the console windows for ffmpeg subprocesses
		creationflags = 0x08000000  # CREATE_NO_WINDOW
		startupinfo = None
	return subprocess.Popen(
		cmd,
		stdin=subprocess.PIPE,
		stdout=subprocess.DEVNULL,
		stderr=subprocess.DEVNULL,
		creationflags=creationflags,
		startupinfo=startupinfo,
		text=False,
	)


def stop_ffmpeg(proc: subprocess.Popen, timeout_sec: int = 15):
	if proc.poll() is not None:
		return
	try:
		# Send 'q' to request graceful stop
		if proc.stdin:
			proc.stdin.write(b"q")
			proc.stdin.flush()
		# Wait a little for clean finalize
		proc.wait(timeout=timeout_sec)
	except Exception:
		try:
			proc.kill()
		except Exception:
			pass


def setup_logging(host_dir: Path):
	log_path = host_dir / "recorder.log"
	# Reset existing handlers to allow reconfiguration if needed
	root = logging.getLogger()
	for h in list(root.handlers):
		root.removeHandler(h)
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s [%(levelname)s] %(message)s",
		handlers=[
			logging.FileHandler(log_path, encoding="utf-8"),
			logging.StreamHandler(sys.stdout),
		],
	)
	return log_path


def register_shutdown_handler(stop_event):
	"""Register Windows shutdown handler so we can stop and finalize files before power-off."""
	if not _HAS_WIN32:
		logging.warning("win32api not available; graceful shutdown on Windows may not trigger.")
		return

	CTRL_EVENTS = {
		0: "CTRL_C_EVENT",
		1: "CTRL_BREAK_EVENT",
		2: "CTRL_CLOSE_EVENT",
		5: "CTRL_LOGOFF_EVENT",
		6: "CTRL_SHUTDOWN_EVENT",
	}

	def handler(ctrl_type):
		name = CTRL_EVENTS.get(ctrl_type, str(ctrl_type))
		logging.info(f"Console control event: {name} -> initiating graceful shutdown.")
		stop_event.set()
		# Return True to indicate we handled it and need time
		return True

	win32api.SetConsoleCtrlHandler(handler, True)


def compress_day_folder(day_dir: Path) -> Path | None:
	"""Compress content of the given day folder into a RAR if possible, else ZIP.
	Return path to archive or None on failure."""
	rardll = find_executable(["rar", "Rar.exe", "rar.exe"])
	archive_basename = f"grabacion_{day_dir.name}.rar" if rardll else f"grabacion_{day_dir.name}.zip"
	archive_path = day_dir / archive_basename

	# Build file list to include (video/audio only)
	include_extensions = {".mkv", ".mp4", ".wav"}
	files = [p for p in day_dir.iterdir() if p.is_file() and p.suffix.lower() in include_extensions]
	if not files:
		logging.warning("No files to compress.")
		return None

	try:
		if rardll:
			# Use WinRAR to create archive with high compression, excluding base paths (-ep1)
			cmd = [
				rardll,
				"a",
				"-ep1",
				"-m5",
				str(archive_path),
			]
			# Add relative file names
			cmd += [str(p.name) for p in files]
			logging.info("Creating RAR archive...")
			subprocess.check_call(cmd, cwd=str(day_dir))
		else:
			# Fallback to ZIP
			import zipfile
			logging.info("Creating ZIP archive (WinRAR not found)...")
			with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
				for p in files:
					zf.write(p, arcname=p.name)

		# Delete original heavy files after successful archive
		deleted = 0
		for p in files:
			try:
				p.unlink()
				deleted += 1
			except Exception as e:
				logging.warning(f"Failed to delete {p}: {e}")
		logging.info(f"Compressed to {archive_path.name}. Deleted {deleted} original files.")
		return archive_path
	except Exception as e:
		logging.error(f"Compression failed: {e}")
		return None


def start_all_recordings(ffmpeg: str, monitors: list[dict], output_dir: Path):
	video_procs: list[subprocess.Popen] = []
	for idx, region in enumerate(monitors):
		cmd, pattern = build_ffmpeg_video_cmd(ffmpeg, idx, region, output_dir)
		proc = start_process(cmd)
		video_procs.append(proc)
		logging.info(f"Monitor {idx+1}: recording started -> {pattern}")

	audio_proc = None
	if CAPTURE_AUDIO_WAV:
		try:
			cmd_a, pattern_a = build_ffmpeg_audio_cmd(ffmpeg, output_dir)
			audio_proc = start_process(cmd_a)
			logging.info(f"Audio recording started -> {pattern_a}")
		except Exception as e:
			logging.warning(f"Audio capture not started: {e}")

	return video_procs, audio_proc


def stop_all_recordings(video_procs: list[subprocess.Popen], audio_proc: subprocess.Popen | None):
	for p in video_procs:
		stop_ffmpeg(p)
	if audio_proc:
		stop_ffmpeg(audio_proc)


def main():
	if os.name != "nt":
		print("This script must be run on Windows.", file=sys.stderr)
		return 1

	# Resolve host and output directories
	base_root = choose_base_root()
	hostname = socket.gethostname()
	host_dir = base_root / hostname
	host_dir.mkdir(parents=True, exist_ok=True)

	# Setup logging at host level (outside daily folders)
	log_path = setup_logging(host_dir)
	logging.info(f"Base root: {base_root}")
	logging.info(f"Host folder: {host_dir}")
	logging.info(f"Log file: {log_path}")

	ffmpeg = find_executable(["ffmpeg", "ffmpeg.exe"])
	if not ffmpeg:
		logging.error("FFmpeg not found. Install FFmpeg and ensure ffmpeg.exe is in PATH.")
		return 2

	monitors = enumerate_monitors()
	if not monitors:
		logging.error("No monitors detected. Exiting.")
		return 3

	logging.info(f"Detected {len(monitors)} monitor(s). Starting recording...")

	current_date = date.today()
	output_dir = ensure_output_dir_for_date(host_dir, current_date.strftime("%Y-%m-%d"))
	video_procs, audio_proc = start_all_recordings(ffmpeg, monitors, output_dir)

	# Register shutdown handler
	import threading
	stop_event = threading.Event()
	register_shutdown_handler(stop_event)

	# Main loop until shutdown, rotate daily
	try:
		while not stop_event.is_set():
			time.sleep(1)
			if date.today() != current_date:
				logging.info("Date changed. Rotating to new day folder...")
				stop_all_recordings(video_procs, audio_proc)
				compress_day_folder(output_dir)
				current_date = date.today()
				output_dir = ensure_output_dir_for_date(host_dir, current_date.strftime("%Y-%m-%d"))
				video_procs, audio_proc = start_all_recordings(ffmpeg, monitors, output_dir)
	except KeyboardInterrupt:
		logging.info("KeyboardInterrupt received. Stopping...")
		stop_event.set()

	# Stop all recordings gracefully
	logging.info("Stopping recordings...")
	stop_all_recordings(video_procs, audio_proc)

	# Compress results
	logging.info("Compressing day folder...")
	compress_day_folder(output_dir)

	logging.info("Done.")
	return 0


if __name__ == "__main__":
	sys.exit(main())