"""
Universal Video Downloader - Kivy GUI para Android
Soporta: YouTube, TikTok, Facebook, Instagram, Twitter
"""

import os
import sys
import subprocess
import threading
from pathlib import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.metrics import dp

import conf_management as cfg

# --- Constantes ---
APP_VERSION = "2.2.0"

# Importar yt-dlp
try:
    import yt_dlp
except ImportError:
    yt_dlp = None


# --- Auto-update ---
def _version_normalizada(v):
    return ".".join(str(int(x)) for x in v.split("."))


def verificar_actualizaciones():
    global yt_dlp
    if yt_dlp is None:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "yt-dlp", "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except:
            pass
        return

    try:
        import requests
        resp = requests.get(
            "https://pypi.org/pypi/yt-dlp/json",
            timeout=5
        )
        latest = _version_normalizada(resp.json()["info"]["version"])
        current = _version_normalizada(yt_dlp.version.__version__)
        if latest != current:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-U", "yt-dlp", "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
    except:
        pass


# --- Utilidades ---
def _tiene_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False


def obtener_ruta_descargas():
    if platform == "android":
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
        ruta = os.path.join(os.getenv("EXTERNAL_STORAGE", "/sdcard"), "Download", "UniversalDownloader")
    else:
        ruta = cfg.get_ruta_descargas()
    os.makedirs(ruta, exist_ok=True)
    for d in ["video", "audio"]:
        os.makedirs(os.path.join(ruta, d), exist_ok=True)
    return ruta


# --- Interfaz Kivy ---
class DownloadScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(10), padding=dp(15), **kwargs)
        self.ruta_descargas = obtener_ruta_descargas()
        self._build_ui()

    def _build_ui(self):
        # Titulo
        titulo = Label(
            text="[b]UNIVERSAL DOWNLOADER[/b]",
            markup=True,
            size_hint_y=0.1,
            font_size=dp(20)
        )
        self.add_widget(titulo)

        self.version_label = Label(
            text=f"Version {APP_VERSION} | YouTube, TikTok, FB, IG",
            size_hint_y=0.05,
            font_size=dp(12)
        )
        self.add_widget(self.version_label)

        # URL input
        self.add_widget(Label(text="URL del video:", size_hint_y=0.05, font_size=dp(14)))
        self.url_input = TextInput(
            hint_text="Pega el enlace aqui...",
            size_hint_y=0.08,
            multiline=False,
            font_size=dp(14)
        )
        self.add_widget(self.url_input)

        # Modo de descarga
        self.add_widget(Label(text="Modo:", size_hint_y=0.05, font_size=dp(14)))
        self.modo_spinner = Spinner(
            text="Video + Audio (mejor calidad)",
            values=[
                "Video + Audio (mejor calidad)",
                "Video (elegir formato)",
                "Solo Audio (MP3)"
            ],
            size_hint_y=0.07,
            font_size=dp(13)
        )
        self.add_widget(self.modo_spinner)

        # Boton descargar
        self.descargar_btn = Button(
            text="DESCARGAR",
            size_hint_y=0.1,
            font_size=dp(18),
            bold=True,
            background_color=(0.2, 0.6, 1, 1)
        )
        self.descargar_btn.bind(on_press=self.iniciar_descarga)
        self.add_widget(self.descargar_btn)

        # Progreso
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=0.04)
        self.add_widget(self.progress_bar)

        self.status_label = Label(
            text="Listo",
            size_hint_y=0.05,
            font_size=dp(13)
        )
        self.add_widget(self.status_label)

        # Info del video
        self.info_label = Label(
            text="",
            size_hint_y=0.2,
            font_size=dp(12),
            text_size=(Window.width - dp(30), None),
            halign="left",
            valign="top"
        )
        self.info_label.bind(width=lambda *x: setattr(self.info_label, "text_size", (self.info_label.width, None)))
        self.add_widget(self.info_label)

        # Version consola
        self.consola = ScrollView(size_hint_y=0.2, do_scroll_y=True)
        self.consola_label = Label(
            text="",
            font_size=dp(10),
            size_hint_y=None,
            text_size=(Window.width - dp(30), None),
            halign="left",
            valign="top"
        )
        self.consola_label.bind(width=lambda *x: setattr(self.consola_label, "text_size", (self.consola_label.width, None)))
        self.consola.add_widget(self.consola_label)
        self.add_widget(self.consola)

    def log(self, mensaje):
        actual = self.consola_label.text
        self.consola_label.text = (actual + "\n" + mensaje).strip()
        self.consola.scroll_y = 0

    def set_status(self, mensaje, color=(1, 1, 1, 1)):
        self.status_label.text = mensaje
        self.status_label.color = color

    def iniciar_descarga(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.set_status("Ingresa una URL", (1, 0, 0, 1))
            return

        self.descargar_btn.disabled = True
        self.progress_bar.value = 0
        self.info_label.text = ""
        self.consola_label.text = ""
        self.set_status("Iniciando...")

        modos = {
            "Video + Audio (mejor calidad)": "1",
            "Video (elegir formato)": "2",
            "Solo Audio (MP3)": "3"
        }
        modo = modos.get(self.modo_spinner.text, "1")

        thread = threading.Thread(target=self.descargar_thread, args=(url, modo))
        thread.start()

    def descargar_thread(self, url, modo):
        try:
            # Mostrar info
            try:
                with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                Clock.schedule_once(lambda dt: self._mostrar_info(info))
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: self.set_status(f"Error obteniendo info: {str(e)[:50]}", (1, 0, 0, 1)))

            if modo == "1":
                self._descargar_video(url)
            elif modo == "2":
                self._descargar_con_formato(url)
            elif modo == "3":
                self._descargar_audio(url)

        except Exception as e:
            Clock.schedule_once(lambda dt, e=e: self.set_status(f"Error: {str(e)[:60]}", (1, 0, 0, 1)))
        finally:
            Clock.schedule_once(lambda dt: self._finalizar())

    def _mostrar_info(self, info):
        txt = (
            f"Titulo: {info.get('title', '?')}\n"
            f"Autor: {info.get('uploader', '?')}\n"
            f"Duracion: {info.get('duration_string', info.get('duration', '?'))}"
        )
        self.info_label.text = txt

    def _descargar_video(self, url):
        self.log("Descargando video...")
        if _tiene_ffmpeg():
            formato = "bestvideo+bestaudio/best"
        else:
            self.log("Sin ffmpeg: usando formato progresivo")
            formato = "best"

        ydl_opts = {
            "outtmpl": os.path.join(self.ruta_descargas, "video", "%(title)s.%(ext)s"),
            "format": formato,
            "merge_output_format": "mp4",
            "progress_hooks": [self._hook_progreso],
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        Clock.schedule_once(lambda dt: self.set_status("Video descargado!", (0, 1, 0, 1)))

    def _descargar_audio(self, url):
        self.log("Descargando audio...")
        ydl_opts = {
            "outtmpl": os.path.join(self.ruta_descargas, "audio", "%(title)s.%(ext)s"),
            "format": "bestaudio/best",
            "progress_hooks": [self._hook_progreso],
            "quiet": True,
            "no_warnings": True,
        }
        if _tiene_ffmpeg():
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        else:
            self.log("Sin ffmpeg: audio en formato original")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        Clock.schedule_once(lambda dt: self.set_status("Audio descargado!", (0, 1, 0, 1)))

    def _descargar_con_formato(self, url):
        self.log("Descargando video (formato seleccionado)...")
        if _tiene_ffmpeg():
            formato = "bestvideo+bestaudio/best"
        else:
            formato = "best"

        ydl_opts = {
            "outtmpl": os.path.join(self.ruta_descargas, "video", "%(title)s.%(ext)s"),
            "format": formato,
            "merge_output_format": "mp4",
            "progress_hooks": [self._hook_progreso],
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        Clock.schedule_once(lambda dt: self.set_status("Video descargado!", (0, 1, 0, 1)))

    def _hook_progreso(self, d):
        if d["status"] == "downloading":
            try:
                p = float(d.get("_percent_str", "0%").strip().replace("%", ""))
                eta = d.get("_eta_str", "?")
                Clock.schedule_once(lambda dt: self._actualizar_progreso(p, eta))
            except:
                pass
        elif d["status"] == "finished":
            self.log("Descarga finalizada, procesando...")

    def _actualizar_progreso(self, porcentaje, eta):
        self.progress_bar.value = porcentaje
        self.set_status(f"Descargando... {int(porcentaje)}% | ETA: {eta}")

    def _finalizar(self):
        self.descargar_btn.disabled = False


class UniversalDownloaderApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Universal Downloader"
        self.icon = ""

    def build(self):
        # Ejecutar update en segundo plano
        threading.Thread(target=verificar_actualizaciones, daemon=True).start()
        return DownloadScreen()


if __name__ == "__main__":
    UniversalDownloaderApp().run()
