import customtkinter
import os
import sys
import threading
import subprocess
import requests

# PRE-IMPORT UPDATE CHECK: If a newer yt-dlp wheel exists in AppData, use it.
try:
    app_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'UniversalDownloader', 'updates')
    if os.path.exists(app_data_dir):
        # Add to front of sys.path so it takes precedence
        sys.path.insert(0, app_data_dir)
        # Scan for .whl files in that directory
        for file in os.listdir(app_data_dir):
            if file.endswith('.whl'):
                 sys.path.insert(0, os.path.join(app_data_dir, file))
                 break
except:
    pass

import yt_dlp

import imageio_ffmpeg
import config as cfg
from tkinter import messagebox

# Set theme and color
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("Universal Video Downloader (YouTube, TikTok, FB, etc.)")
        self.geometry("800x600")

        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)


        # Sidebar
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Universal\nDownloader", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.signature_label = customtkinter.CTkLabel(self.sidebar_frame, text="By Morris", text_color="red", font=customtkinter.CTkFont(size=12, weight="bold"))
        self.signature_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Download Video", command=self.show_single_download)
        self.sidebar_button_1.grid(row=2, column=0, padx=20, pady=10)

        # Main Area
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # --- Single Download View ---
        self.single_view = customtkinter.CTkFrame(self.main_frame, fg_color="transparent")
        
        self.url_label = customtkinter.CTkLabel(self.single_view, text="Video URL (YouTube, TikTok, Facebook, etc.):", font=customtkinter.CTkFont(size=14))
        self.url_label.pack(anchor="w", pady=(0, 5))
        
        self.url_entry = customtkinter.CTkEntry(self.single_view, width=500, placeholder_text="Paste link here...")
        self.url_entry.pack(anchor="w", pady=(0, 20))

        self.type_var = customtkinter.StringVar(value="video")
        self.radio_video = customtkinter.CTkRadioButton(self.single_view, text="Best Video + Audio", variable=self.type_var, value="video")
        self.radio_video.pack(anchor="w", pady=5)
        self.radio_audio = customtkinter.CTkRadioButton(self.single_view, text="Audio Only (MP3)", variable=self.type_var, value="audio")
        self.radio_audio.pack(anchor="w", pady=5)

        self.download_btn = customtkinter.CTkButton(self.single_view, text="Start Download", command=self.start_download_thread, height=40)
        self.download_btn.pack(anchor="w", pady=20)

        self.status_label = customtkinter.CTkLabel(self.single_view, text="Ready", text_color="gray")
        self.status_label.pack(anchor="w", pady=10)

        self.progress_bar = customtkinter.CTkProgressBar(self.single_view, width=500)
        self.progress_bar.set(0)
        self.progress_bar.pack(anchor="w", pady=10)
        
        self.open_folder_btn = customtkinter.CTkButton(self.single_view, text="Open Download Folder", command=self.open_download_folder, state="disabled", fg_color="gray")
        self.open_folder_btn.pack(anchor="w", pady=5)

        # Default View
        self.show_single_download()
        
        # Start auto-update check after UI is ready
        self.after(500, self.start_update_thread)

    def start_update_thread(self):
        # Start update in background
        threading.Thread(target=self.perform_update, daemon=True).start()

    def perform_update(self):
        self.after(0, lambda: self.update_status("Checking for core updates...", "orange"))
        
        try:
            # Check if frozen (EXE mode)
            if getattr(sys, 'frozen', False):
                # EXE Update Logic: Download wheel to AppData
                try:
                    # 1. Get latest version info from PyPI
                    response = requests.get("https://pypi.org/pypi/yt-dlp/json", timeout=5)
                    data = response.json()
                    latest_version = data['info']['version']
                    
                    current_version = yt_dlp.version.__version__
                    
                    if latest_version != current_version:
                        self.after(0, lambda: self.update_status(f"Updating core to {latest_version}...", "orange"))
                        
                        # Find the wheel url
                        wheel_url = None
                        for url_info in data['urls']:
                            if url_info['packagetype'] == 'bdist_wheel':
                                wheel_url = url_info['url']
                                break
                        
                        if wheel_url:
                            # Define update path
                            app_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'UniversalDownloader', 'updates')
                            if not os.path.exists(app_data_dir):
                                os.makedirs(app_data_dir)
                            
                            # Clean old updates
                            for f in os.listdir(app_data_dir):
                                os.remove(os.path.join(app_data_dir, f))
                                
                            # Download new wheel
                            filename = wheel_url.split('/')[-1]
                            local_path = os.path.join(app_data_dir, filename)
                            
                            with requests.get(wheel_url, stream=True) as r:
                                r.raise_for_status()
                                with open(local_path, 'wb') as f:
                                    for chunk in r.iter_content(chunk_size=8192): 
                                        f.write(chunk)
                                        
                            self.after(0, lambda: self.update_status("Core updated! Restart required.", "green"))
                        else:
                             self.after(0, lambda: self.update_status("Update found but no wheel available.", "gray"))
                    else:
                        self.after(0, lambda: self.update_status("Core components are up to date.", "green"))

                except Exception as e:
                    print(f"EXE Update failed: {e}")
                    self.after(0, lambda: self.update_status("Update check failed (net)", "gray"))

            else:
                # Dev/Script Mode: Use Pip
                # Add --no-warn-script-location to avoid path warnings cluttering or confusing
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"], 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("yt-dlp updated successfully.")
                self.after(0, lambda: self.update_status("Core components updated. Ready.", "green"))

        except Exception as e:
            print(f"Could not update yt-dlp: {e}")
            self.after(0, lambda: self.update_status("Update check failed (continuing anyway)", "gray"))
        
        # Reset to Ready after a few seconds
        self.after(3000, lambda: self.update_status_if_idle("Ready"))

    def update_status_if_idle(self, message):
        # Helper to set status only if we aren't currently downloading
        # simplified check: if status is green or orange (updates), we can reset. 
        # But if downloading, status might be changing rapidly. 
        # For now, just setting it is fine as downloads will overwrite it anyway.
        if self.open_folder_btn.cget("state") == "disabled":
             # downloading is active, don't overwrite
             return
        self.update_status(message, "gray")

    def open_download_folder(self):
        output_path = cfg.RUTA_DESCARGAS
        if os.path.exists(output_path):
            os.startfile(output_path)

    def show_single_download(self):
        self.single_view.pack(fill="both", expand=True)

    def start_download_thread(self):
        url = self.url_entry.get()
        if not url:
            self.status_label.configure(text="Please enter a URL", text_color="red")
            return
        
        mode = self.type_var.get()
        self.download_btn.configure(state="disabled")
        self.open_folder_btn.configure(state="disabled", fg_color="gray")
        self.progress_bar.set(0)
        self.status_label.configure(text="Initializing...", text_color="white")
        
        thread = threading.Thread(target=self.download_task, args=(url, mode))
        thread.start()

    def download_task(self, url, mode):
        try:
            output_path = cfg.RUTA_DESCARGAS
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            
            # Get ffmpeg binary path from imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            
            ydl_opts = {
                'ffmpeg_location': ffmpeg_path,
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self.yt_dlp_progress_hook],
            }

            if mode == "video":
                # Best video + best audio
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            else:
                # Audio only, convert to mp3
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]

            self.update_status(f"Downloading from {self.get_domain(url)}...", "white")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.update_status("Download Complete!", "green")
            self.open_folder_btn.configure(state="normal", fg_color=["#3B8ED0", "#1F6AA5"])

        except Exception as e:
            self.update_status(f"Error: {str(e)}", "red")
            print(f"Error details: {e}")
        finally:
            self.download_btn.configure(state="normal")
            self.progress_bar.stop()

    def get_domain(self, url):
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return "URL"

    def yt_dlp_progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', '0%').replace('%','')
                self.progress_bar.set(float(p) / 100)
                self.update_status(f"Downloading... {d.get('_percent_str')} | ETA: {d.get('_eta_str')}", "white")
            except:
                pass
        elif d['status'] == 'finished':
            self.update_status("Processing/Converting...", "orange")

    def update_status(self, message, color):
        self.status_label.configure(text=message, text_color=color)

if __name__ == "__main__":
    app = App()
    app.mainloop()
