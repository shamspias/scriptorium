import os
import subprocess
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
from ultralytics import YOLO


class VideoDetectionApp:
    """A Tkinter GUI for real-time YOLOv8 video detection."""

    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("YOLOv8 Video Detection")
        self.master.geometry("800x800")
        self.master.minsize(800, 800)

        self.model_path: str | None = None
        self.video_path: str | None = None
        self.temp_file: str | None = None
        self.stop_requested = False

        # --- UI Elements ---
        tk.Label(master, text="1. Select YOLO Model (.pt):").pack(pady=(10, 0))
        tk.Button(master, text="Browse Model", command=self.select_model).pack(pady=(0, 10))

        tk.Label(master, text="2. Enter YouTube URL:").pack()
        self.url_entry = tk.Entry(master, width=60)
        self.url_entry.pack(pady=(0, 10))

        tk.Label(master, text="3. OR select a local video file:").pack()
        tk.Button(master, text="Browse Video", command=self.select_video).pack(pady=(0, 20))

        self.run_button = tk.Button(master, text="▶ Run Detection", command=self.run_detection)
        self.run_button.pack(pady=(0, 10))

        self.stop_button = tk.Button(master, text="🛑 Stop Detection", command=self.stop_detection)
        self.stop_button.pack(pady=(0, 10))

        tk.Button(master, text="❌ Exit", command=self.master.destroy).pack(pady=(0, 20))

    def select_model(self) -> None:
        """Open file dialog to choose a .pt model."""
        path = filedialog.askopenfilename(filetypes=[("YOLOv8 model (*.pt)", "*.pt")])
        if path:
            self.model_path = path
            print(f"Model selected: {path}")

    def select_video(self) -> None:
        """Open file dialog to choose a local video."""
        path = filedialog.askopenfilename(
            filetypes=[
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("MOV files", "*.mov"),
                ("All files", "*.*"),
            ]
        )
        if path:
            self.video_path = path
            print(f"Video selected: {path}")

    def download_youtube_video(self, url: str) -> str:
        """
        Use yt-dlp to download a YouTube URL to a temporary file.
        Returns the path to the downloaded file.
        """
        output = f"temp_{int(time.time())}.mp4"
        cmd = ["yt-dlp", "-f", "best[ext=mp4]", "-o", output, url]
        subprocess.run(cmd, check=True)
        return output

    def stop_detection(self) -> None:
        """Signal the detection loop to stop after the current frame."""
        self.stop_requested = True
        print("🛑 Stop requested; finishing current frame then exiting loop.")

    def run_detection(self) -> None:
        """Main detection routine, runs in the GUI thread to allow cv2.imshow."""
        if not self.model_path:
            messagebox.showwarning("No Model", "Please select a YOLOv8 model file first.")
            return

        url = self.url_entry.get().strip()
        video_source: str

        # Reset stop flag and disable Run button
        self.stop_requested = False
        self.run_button.config(state=tk.DISABLED)

        # Download if URL provided
        try:
            if url:
                print("📥 Downloading YouTube video...")
                self.temp_file = self.download_youtube_video(url)
                video_source = self.temp_file
            elif self.video_path:
                video_source = self.video_path
            else:
                raise ValueError("No video source provided.")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to get video:\n{exc}")
            self.run_button.config(state=tk.NORMAL)
            return

        # Open video capture
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            messagebox.showerror("Error", "Cannot open video source.")
            self.cleanup()
            return

        # Load model once
        model = YOLO(self.model_path)
        cv2.namedWindow("Detection", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Detection", 800, 600)

        # Frame-by-frame loop
        while cap.isOpened() and not self.stop_requested:
            ret, frame = cap.read()
            if not ret:
                break

            # Run inference on the frame
            results = model(frame)[0]  # first (and only) batch
            annotated = results.plot()

            # Display
            cv2.imshow("Detection", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            # Process any pending GUI events (so Stop button works)
            self.master.update()

        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        self.cleanup()
        print("✅ Detection finished.")
        self.run_button.config(state=tk.NORMAL)

    def cleanup(self) -> None:
        """Remove temp file if it exists."""
        if self.temp_file and os.path.exists(self.temp_file):
            os.remove(self.temp_file)
            print(f"🧹 Deleted temporary file: {self.temp_file}")
            self.temp_file = None


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDetectionApp(root)
    root.mainloop()
