# grabación completa

Aplicación para grabación de pantalla y audio, guardando archivos en carpetas por fecha y equipo.

## Uso rápido (Windows)

1. Instala ffmpeg y agrega su ruta a la variable de entorno `PATH` o define `FFMPEG` con la ruta completa al ejecutable.
2. Opcional: define `BASE_ROOT` para cambiar el destino (por defecto `\\\\Desktop-j82oa53\\grabaciones\\`).
3. Ejecuta:

```powershell
python recorder.py
```

Los archivos se guardarán en:
```
BASE_ROOT/COMPUTERNAME/YYYY-MM-DD/
  monitor1_YYYY-MM-DD_HH-MM-SS.mkv
  monitor2_YYYY-MM-DD_HH-MM-SS.mkv
  audio_YYYY-MM-DD_HH-MM-SS.wav
```

## Notas
- Evitamos patrones de fecha con `%Y` en los nombres que recibe ffmpeg; se formatean previamente con `strftime`.
- El log se escribe en `BASE_ROOT/COMPUTERNAME/recorder.log`.
- Si no tienes segundo monitor, comenta el bloque del segundo proceso o ajusta la fuente.