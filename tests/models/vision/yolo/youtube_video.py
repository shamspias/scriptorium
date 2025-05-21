from ultralytics import YOLO
import subprocess
import os


def download_youtube_video(url, output_file='temp_video.mp4'):
    command = [
        'yt-dlp',
        '-f', 'best[ext=mp4]',
        '-o', output_file,
        url
    ]
    subprocess.run(command, check=True)
    return output_file


def detect_from_video(video_path):
    model = YOLO('../../../../models/best.pt')
    model.predict(source=video_path, show=True, device='mps')


def delete_video(video_path):
    if os.path.exists(video_path):
        os.remove(video_path)
        print(f"Deleted: {video_path}")
    else:
        print("File not found.")


if __name__ == '__main__':
    youtube_url = input("Enter YouTube URL: ")
    video_file = download_youtube_video(youtube_url)
    detect_from_video(video_file)
    delete_video(video_file)
