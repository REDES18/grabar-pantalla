# Grabador de todas las pantallas (Windows)

Este programa detecta cuántas pantallas hay conectadas, graba cada pantalla con FFmpeg en segmentos de 1 hora, guarda las grabaciones en la carpeta en red y, al finalizar (apagado o cierre), comprime el contenido del día en un archivo .rar (o .zip si WinRAR no está disponible) y elimina los archivos grandes para ahorrar espacio.

## Requisitos (en cada PC Windows)
- Python 3.10+
- FFmpeg instalado y `ffmpeg.exe` accesible en `PATH` (o en `C:\ffmpeg\bin\ffmpeg.exe`).
- (Opcional pero recomendado) WinRAR instalado para generar `.rar` (`C:\Program Files\WinRAR\Rar.exe`). Si no está, se genera `.zip`.
- `pip install -r requirements.txt`

## Dónde se guardan los archivos
- Intenta guardar en la carpeta de red: `\\\\Desktop-j82oa53\\grabaciones\\<HOSTNAME>\\YYYY-MM-DD\\`
- Si la carpeta de red no está accesible, guarda localmente en: `C:\\Users\\FELIPE REDES\\Desktop\\GRABACIONES\\<HOSTNAME>\\YYYY-MM-DD\\`

## Ejecución
```bash
python recorder.py
```
Se iniciará la grabación de todas las pantallas y (si es posible) del audio del sistema en WAV. Se crean archivos segmentados por hora para mayor robustez. Al apagarse Windows, la app cierra las grabaciones y comprime el día en `grabacion_YYYY-MM-DD.rar` (o `.zip`).

## Inicio automático al prender el PC
- Cree un acceso directo a `python.exe` con el argumento hacia el `recorder.py`, y colóquelo en:
  `shell:startup` (Carpeta de Inicio del usuario)
  Ejemplo destino del acceso directo:
  `"C:\\Path\\to\\Python\\python.exe" "C:\\Path\\to\\recorder.py"`

## Notas
- Vídeo: H.264 (CRF 20, 25 FPS) en MKV. Puede ajustar en el código `CRF_QUALITY`, `FRAMERATE`.
- Audio: Se intenta capturar con FFmpeg WASAPI (`-f wasapi -i default`) a WAV. Si no hay soporte, se omite el audio y se continúa.
- Compresión: Usa WinRAR si disponible (`rar a -m5`), de lo contrario ZIP.
- Si desea forzar sólo la ruta local o la de red, edite las constantes en `recorder.py`.
- Las grabaciones se segmentan por hora y luego se comprimen al final del día. Tras comprimir, se eliminan los archivos de vídeo/audio para ahorrar espacio (se mantiene el `.rar`/`.zip` y el `recorder.log`).