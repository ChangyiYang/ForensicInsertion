import yt_dlp
import os

def download_audio(query, amount=2):
    downloaded_sizes = []
    url = []

    def progress_hook(d):
        if d['status'] == 'finished':
            # Size is in bytes, convert to MB
            file_size_mb = d.get('total_bytes', d.get('total_bytes_estimate', 0)) / (1024 * 1024)
            downloaded_sizes.append(file_size_mb)
            url.append(d['info_dict']['webpage_url'])

    ydl_opts = {
        'format': 'bestaudio/best',
        'progress_hooks': [progress_hook],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False
    }

    os.makedirs("downloads", exist_ok=True)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch{amount}:{query} sound effect"])

    print(f"\n🔍 Total files downloaded: {len(downloaded_sizes)}")
    print(f"📊 Total size: {sum(downloaded_sizes):.2f} MB")

# Example usage
download_audio("pets")
