from yt_dlp import YoutubeDL


def download_raw_audio(keyword):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'extract_audio': True,  # Keeps original format
        'quiet': True
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch1:{keyword} sound effect"])