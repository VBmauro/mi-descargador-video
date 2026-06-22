import customtkinter
import os
import threading
from pytubefix import YouTube
import subprocess
import imageio_ffmpeg
from moviepy import AudioFileClip, VideoFileClip
import config as cfg

# Set theme and color
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Professional YouTube Downloader")
        self.geometry("800x600")

        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="YT Downloader", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Download Video", command=self.show_single_download)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)

        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, text="Batch Download", command=self.show_batch_download)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)

        # Main Area
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # --- Single Download View ---
        self.single_view = customtkinter.CTkFrame(self.main_frame, fg_color="transparent")
        
        self.url_label = customtkinter.CTkLabel(self.single_view, text="YouTube URL:", font=customtkinter.CTkFont(size=14))
        self.url_label.pack(anchor="w", pady=(0, 5))
        
        self.url_entry = customtkinter.CTkEntry(self.single_view, width=500, placeholder_text="Paste link here...")
        self.url_entry.pack(anchor="w", pady=(0, 20))

        self.type_var = customtkinter.StringVar(value="video")
        self.radio_video = customtkinter.CTkRadioButton(self.single_view, text="Video + Audio (Best Quality)", variable=self.type_var, value="video")
        self.radio_video.pack(anchor="w", pady=5)
        self.radio_audio = customtkinter.CTkRadioButton(self.single_view, text="Audio Only (MP3)", variable=self.type_var, value="audio")
        self.radio_audio.pack(anchor="w", pady=5)

        self.download_btn = customtkinter.CTkButton(self.single_view, text="Start Download", command=self.start_download_thread, height=40)
        self.download_btn.pack(anchor="w", pady=20)

        self.status_label = customtkinter.CTkLabel(self.single_view, text="", text_color="gray")
        self.status_label.pack(anchor="w", pady=10)

        self.progress_bar = customtkinter.CTkProgressBar(self.single_view, width=500)
        self.progress_bar.set(0)
        self.progress_bar.pack(anchor="w", pady=10)
        
        self.open_folder_btn = customtkinter.CTkButton(self.single_view, text="Open Download Folder", command=self.open_download_folder, state="disabled", fg_color="gray")
        self.open_folder_btn.pack(anchor="w", pady=5)

        # Default View
        self.show_single_download()

    def open_download_folder(self):
        output_path = cfg.RUTA_DESCARGAS
        if os.path.exists(output_path):
            os.startfile(output_path)

    def show_single_download(self):
        self.single_view.pack(fill="both", expand=True)

    def show_batch_download(self):
        # Placeholder for future implementation
        self.single_view.pack_forget()

    def start_download_thread(self):
        url = self.url_entry.get()
        if not url:
            self.status_label.configure(text="Please enter a URL", text_color="red")
            return
        
        mode = self.type_var.get()
        self.download_btn.configure(state="disabled")
        self.open_folder_btn.configure(state="disabled", fg_color="gray")
        self.progress_bar.start()
        self.status_label.configure(text="Downloading...", text_color="white")
        
        thread = threading.Thread(target=self.download_task, args=(url, mode))
        thread.start()

    def download_task(self, url, mode):
        try:
            yt = YouTube(url, on_progress_callback=self.on_progress)
            output_path = cfg.RUTA_DESCARGAS
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            if mode == "video":
                stream = yt.streams.get_highest_resolution()
                stream.download(output_path=output_path)
                self.update_status(f"Video Downloaded Successfully!", "green")
                self.open_folder_btn.configure(state="normal", fg_color=["#3B8ED0", "#1F6AA5"])
            else:
                stream = yt.streams.get_audio_only()
                file_path = stream.download(output_path=output_path)
                new_file = file_path.replace(".mp4", ".mp3").replace(".webm", ".mp3").replace(".m4a", ".mp3")
                
                self.update_status(f"Converting to MP3...", "orange")
                
                # Robust Conversion using direct FFmpeg process
                try:
                    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                    
                    # Command: ffmpeg -y -i "input" -vn -ab 192k -ar 44100 "output.mp3"
                    # -y: overwrite
                    # -vn: no video
                    # -ab 192k: bitrate
                    # -ar 44100: sample rate
                    command = [
                        ffmpeg_exe, '-y',
                        '-i', file_path,
                        '-vn',
                        '-ab', '192k',
                        '-ar', '44100',
                        new_file
                    ]
                    
                    # Run conversion (hide window on Windows)
                    startupinfo = None
                    if os.name == 'nt':
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        
                    subprocess.run(command, check=True, startupinfo=startupinfo, capture_output=True)
                    
                    # Cleanup original file
                    try:
                        os.remove(file_path)
                    except: pass
                        
                    self.update_status(f"Audio Downloaded Successfully!", "green")
                    self.open_folder_btn.configure(state="normal", fg_color=["#3B8ED0", "#1F6AA5"])
                    
                except Exception as e:
                    self.update_status(f"Conversion Error: {str(e)}", "red")
                    print(f"Detailed error: {e}")

        except Exception as e:
            self.update_status(f"Error: {str(e)}", "red")
        finally:
            self.download_btn.configure(state="normal")
            self.progress_bar.stop()
            self.progress_bar.set(1)

    def on_progress(self, stream, chunk, bytes_remaining):
        # Optional: Calculate percentage for determinate progress bar
        pass

    def update_status(self, message, color):
        self.status_label.configure(text=message, text_color=color)

if __name__ == "__main__":
    app = App()
    app.mainloop()
