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

# --- Auto-update yt-dlp ---
yt_dlp = None

def get_ytdlp_path():
    from kivy.app import App
    app = App.get_running_app()
    if app:
        base_dir = app.user_data_dir
    else:
        base_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_dir, "yt-dlp.zipapp")

def load_ytdlp():
    global yt_dlp
    path = get_ytdlp_path()
    if os.path.exists(path):
        if path not in sys.path:
            sys.path.insert(0, path)
    try:
        import yt_dlp as ytdlp_module
        yt_dlp = ytdlp_module
        return True
    except ImportError:
        # Si falla aqui, el yt-dlp que espera la app no es importable desde esta
        # instalacion. Se reporta para diagnosticar en el log de la consola.
        print("[UDL] AVISO: no se puede importar yt_dlp. Reinstala la app.")
        return False

def verificar_actualizaciones():
    # IMPORTANTE: Este auto-update estaba DESCARGANDO el binario ejecutable de
    # GitHub (yt-dlp) y guardandolo como "yt-dlp.zipapp", corrompiendo el paquete
    # importable que se necesita con 'import yt_dlp'. Eso es lo que hizo que la
    # app dejara de funcionar "de un dia para otro". Se DESACTIVA la sobrescritura
    # automatica: yt-dlp viene instalado correctamente dentro del APK (requirements).
    global yt_dlp
    load_ytdlp()
    try:
        if yt_dlp:
            ver = getattr(getattr(yt_dlp, "version", None), "__version__", "?")
            print("[UDL] yt-dlp instalado:", ver)
    except Exception as e:
        print("Error leyendo version yt-dlp:", e)


# --- Utilidades ---
def _tiene_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False


# Clientes de YouTube a probar en orden (ninguno es universal en 2026:
# YouTube bloquea segun IP/sesion). El primero es el mas fiable sin JS runtime.
_YT_CLIENTS = ["android", "android_vr", "ios", "mweb", "tv", "web_safari", "web"]


def _es_youtube(url):
    u = (url or "").lower()
    return "youtube.com" in u or "youtu.be" in u


def _opts_yt(base_opts, cliente):
    """Agrega extractor_args con un player_client concreto para YouTube."""
    if not cliente:
        return base_opts
    opts = dict(base_opts)
    opts.setdefault("extractor_args", {})["youtube"] = {"player_client": [cliente]}
    return opts


class _SafeLogger:
    """Logger que evita que yt-dlp use stderr(stdout directamente en Android."""
    def __init__(self, log_func=None):
        self.log_func = log_func
    def debug(self, msg):
        pass
    def warning(self, msg):
        if self.log_func:
            self.log_func(msg)
    def error(self, msg):
        if self.log_func:
            self.log_func(msg)
        try:
            sys.stderr.write(f"[YTDLP] {msg}\n")
        except Exception:
            pass


def _descargar_con_retry(url, ydl_opts, log_func=None):
    """Descarga probando varios player_clients de YouTube en orden."""
    clientes = _YT_CLIENTS if _es_youtube(url) else [None]
    ultimo_err = None
    for cl in clientes:
        opts = _opts_yt(ydl_opts, cl)
        if log_func:
            log_func(f"Probando: {cl or 'cliente por defecto'}...")
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            ultimo_err = e
            continue
    if ultimo_err:
        raise ultimo_err
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
        global yt_dlp
        if yt_dlp is None:
            Clock.schedule_once(lambda dt: self.set_status("yt-dlp se esta descargando, intenta en unos segundos...", (1, 0.5, 0, 1)))
            Clock.schedule_once(lambda dt: self._finalizar())
            return

        try:
            # Mostrar info (con retry de clientes YouTube para no bloquearse)
            info = self._extraer_info_soporta_retry(url)
            Clock.schedule_once(lambda dt: self._mostrar_info(info))

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

    def _extraer_info_soporta_retry(self, url):
        """Extrae info probando varios player_clients en YouTube (2026)."""
        clientes = _YT_CLIENTS if _es_youtube(url) else [None]
        ultimo_err = None
        for cl in clientes:
            base = {
                "quiet": True,
                "no_warnings": True,
                "logger": _SafeLogger(),
                "socket_timeout": 30,
                "retries": 2,
            }
            if _es_youtube(url):
                base["extractor_args"] = {"youtube": {"player_client": [cl]}}
            try:
                with yt_dlp.YoutubeDL(base) as ydl:
                    return ydl.extract_info(url, download=False)
            except Exception as e:
                ultimo_err = e
                continue
        raise ultimo_err if ultimo_err else Exception("No se pudo obtener la info")

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
            "logger": _SafeLogger(lambda m: self.log(m)),
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 60,
            "retries": 3,
        }
        _descargar_con_retry(url, ydl_opts, lambda m: self.log(m))
        Clock.schedule_once(lambda dt: self.set_status("Video descargado!", (0, 1, 0, 1)))

    def _descargar_audio(self, url):
        self.log("Descargando audio...")
        ydl_opts = {
            "outtmpl": os.path.join(self.ruta_descargas, "audio", "%(title)s.%(ext)s"),
            "format": "bestaudio/best",
            "progress_hooks": [self._hook_progreso],
            "logger": _SafeLogger(lambda m: self.log(m)),
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 60,
            "retries": 3,
        }
        if _tiene_ffmpeg():
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        else:
            self.log("Sin ffmpeg: audio en formato original")

        _descargar_con_retry(url, ydl_opts, lambda m: self.log(m))
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
            "logger": _SafeLogger(lambda m: self.log(m)),
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 60,
            "retries": 3,
        }
        _descargar_con_retry(url, ydl_opts, lambda m: self.log(m))
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
