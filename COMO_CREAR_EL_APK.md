# Cómo compilar el APK para Android

Dado que estás usando Windows, el comando `buildozer` no funciona de forma nativa. Sin embargo, tienes 2 opciones súper fáciles para generar el APK:

## Opción 1: Usar GitHub Actions (Automático - ¡La más recomendada!)

He creado un archivo automático (`.github/workflows/build_apk.yml`) en tu proyecto.

1. Sube este proyecto a un repositorio en **GitHub**.
2. Ve a la pestaña **Actions** en tu repositorio de GitHub.
3. El sistema comenzará a compilar tu APK automáticamente en la nube de GitHub usando Linux.
4. Cuando termine (suele tardar unos 10-15 minutos), podrás descargar el archivo `.apk` directamente desde la misma pestaña **Actions** (en la sección de Artifacts).

## Opción 2: Usar Google Colab (Si no quieres usar GitHub)

Google Colab te presta una máquina Linux gratis donde puedes compilar tu app:

1. Ve a [Google Colab](https://colab.research.google.com/) y crea un nuevo cuaderno (New Notebook).
2. Comprime toda la carpeta de tu proyecto (`Python_youtube_video_downloader-master`) en un archivo `.zip` (ej. `app.zip`).
3. En Google Colab, haz clic en el icono de la carpeta a la izquierda y sube tu archivo `app.zip`.
4. Crea una celda de código y pega esto, luego ejecútalo:
   ```bash
   !pip install buildozer cython virtualenv
   !sudo apt-get install -y python3-pip build-essential git python3 python3-dev ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev libffi-dev openjdk-17-jdk unzip
   ```
5. Una vez que termine, crea otra celda y ejecuta:
   ```bash
   !unzip app.zip -d proyecto
   %cd proyecto
   !yes | buildozer android debug
   ```
6. Cuando el proceso finalice, encontrarás tu archivo APK listo para descargar dentro de la carpeta `proyecto/bin/` en la barra lateral izquierda de Colab.

---

### ¿Qué cambios le hice al código (`main.py`)?
- El antiguo método de intentar actualizar `yt-dlp` usando `pip install` desde adentro de Android **estaba roto** porque el entorno de Android está "congelado" y bloquea instalaciones de pip. 
- Ahora tu aplicación **descarga automáticamente el paquete oficial `.zipapp` de `yt-dlp` directamente desde GitHub** a la memoria interna de la app y lo carga "en caliente" (dinámicamente).
- Esto garantiza que **siempre** tendrás la versión más actual sin importar cuándo compilaste el APK, y evita que se pierda la funcionalidad de descarga si YouTube o TikTok cambian sus protocolos.
