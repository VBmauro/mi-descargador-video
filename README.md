# 📥 Universal Video Downloader "Never Die"

![Universal Downloader](https://img.shields.io/badge/Version-2.0-blue.svg) ![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg) ![Status](https://img.shields.io/badge/Status-Active-green.svg)

**Universal Video Downloader** es una herramienta potente y robusta diseñada para descargar videos y audio de miles de sitios web (YouTube, TikTok, Facebook, Instagram, Twitch, etc.) con una interfaz moderna y un sistema único de auto-reparación.

> **By Morris** 🔴

## ✨ Características Principales

*   **🚀 Sistema "Never Die" (Auto-Reparación)**:
    *   El programa detecta automáticamente si el motor de descargas (`yt-dlp`) está obsoleto.
    *   Descarga e instala parches automáticamente en segundo plano sin necesidad de volver a compilar el ejecutable.
    *   ¡Nunca deja de funcionar aunque YouTube cambie sus algoritmos!
*   **💻 Interfaz Moderna**: Construida con `CustomTkinter` para un modo oscuro elegante y profesional.
*   **🌍 Multi-Plataforma**: Soporta miles de sitios web gracias al motor `yt-dlp`.
*   **🎵 Video y Audio**: Elige entre descargar el video en máxima calidad o convertirlo y extraer solo el audio (MP3).
*   **📦 Portable**: Funciona como un script de Python o como un ejecutable (.exe) independiente.

## 🛠️ Instalación y Uso

### Opción 1: Usar el Ejecutable (Windows)
1.  Descarga el archivo `UniversalDownloader.exe` de la carpeta `dist`.
2.  Ejecútalo. ¡No requiere instalación!
3.  El programa creará automáticamente las carpetas necesarias para guardar tus descargas.

### Opción 2: Ejecutar desde el código fuente
1.  Clona este repositorio:
    ```bash
    git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
    cd Python_youtube_video_downloader-master
    ```
2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3.  Ejecuta la aplicación:
    ```bash
    python GuiPrincipal.py
    ```

## 📸 Capturas

*(Aquí puedes agregar capturas de pantalla de tu aplicación)*

## 🔧 Requisitos (Para desarrolladores)
*   Python 3.8+
*   FFmpeg (necesario para la conversión de audio y unión de video/audio, incluido automáticamente vía `imageio-ffmpeg`).

## 📝 Créditos

Desarrollado con ❤️ **By Morris**.

---
*Este proyecto es para fines educativos y de uso personal.*