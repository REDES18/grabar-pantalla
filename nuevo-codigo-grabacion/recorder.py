#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from datetime import datetime

# Configuración de destino (ajusta BASE_ROOT si usas UNC)
BASE_ROOT = os.environ.get("BASE_ROOT", r"\\Desktop-j82oa53\grabaciones")
HOSTNAME = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "HOST"
HOST_DIR = os.path.join(BASE_ROOT, HOSTNAME)
DATE_DIR = os.path.join(HOST_DIR, datetime.now().strftime('%Y-%m-%d'))
LOG_FILE = os.path.join(HOST_DIR, 'recorder.log')

FFMPEG_PATH = os.environ.get("FFMPEG", "ffmpeg")  # o ruta completa a ffmpeg.exe


def ensure_dirs() -> None:
	os.makedirs(DATE_DIR, exist_ok=True)
	os.makedirs(HOST_DIR, exist_ok=True)


def timestamp() -> str:
	return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')


def build_paths():
	ts = timestamp()
	video1 = os.path.join(DATE_DIR, f"monitor1_{ts}.mkv")
	video2 = os.path.join(DATE_DIR, f"monitor2_{ts}.mkv")
	audio = os.path.join(DATE_DIR, f"audio_{ts}.wav")
	return video1, video2, audio


def open_log():
	os.makedirs(HOST_DIR, exist_ok=True)
	# Apertura en modo append, line-buffered
	return open(LOG_FILE, 'a', buffering=1, encoding='utf-8', errors='replace')


def start_ffmpeg_process(args, logf):
	return subprocess.Popen(args, stdout=logf, stderr=logf, shell=False)


def main():
	print(f"Base root: {BASE_ROOT}")
	print(f"Host folder: {HOST_DIR}")
	print(f"Log file: {LOG_FILE}")

	ensure_dirs()
	video1, video2, audio = build_paths()
	logf = open_log()

	print(f"Grabando monitor 1 -> {video1}")
	print(f"Grabando monitor 2 -> {video2}")
	print(f"Grabando audio -> {audio}")

	processes = []

	# Captura de pantalla en Windows con gdigrab. Ajusta a tu necesidad.
	try:
		p1 = start_ffmpeg_process([
			FFMPEG_PATH, "-y",
			"-f", "gdigrab", "-framerate", "30", "-i", "desktop",
			"-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
			video1
		], logf)
		processes.append(p1)
	except FileNotFoundError:
		print("No se encontró ffmpeg. Define la variable de entorno FFMPEG con la ruta completa.")
		return 1

	# Segundo monitor: si no tienes, comenta este bloque o cambia la fuente -i
	try:
		p2 = start_ffmpeg_process([
			FFMPEG_PATH, "-y",
			"-f", "gdigrab", "-framerate", "30", "-i", "desktop",
			"-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
			video2
		], logf)
		processes.append(p2)
	except Exception as exc:
		print(f"Advertencia: no se pudo iniciar grabación del segundo monitor: {exc}")

	# Audio (ejemplo con dshow en Windows; ajusta el nombre del dispositivo)
	try:
		p3 = start_ffmpeg_process([
			FFMPEG_PATH, "-y",
			"-f", "dshow", "-i", "audio=Microphone (Realtek Audio)",
			audio
		], logf)
		processes.append(p3)
	except Exception as exc:
		print(f"Advertencia: no se pudo iniciar grabación de audio: {exc}")

	# Espera a que finalicen (Ctrl+C para terminar)
	try:
		for p in processes:
			p.wait()
	except KeyboardInterrupt:
		print("Deteniendo grabaciones...")
		for p in processes:
			try:
				p.terminate()
			except Exception:
				pass
		for p in processes:
			try:
				p.wait(timeout=5)
			except Exception:
				pass
	finally:
		logf.close()

	return 0


if __name__ == "__main__":
	sys.exit(main())