import yt_dlp
import os
BASE_UPLOAD_DIR = "./to_upload"


def download_youtube(url, type='video'):
    try:
        if type == 'audios':
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': os.path.join(BASE_UPLOAD_DIR, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [],
                'extractaudio': False,
            }
        else:  # video
            ydl_opts = {
                'format': 'worst[ext=mp4]',  # Worst quality that's already in mp4 format
                'outtmpl': os.path.join(BASE_UPLOAD_DIR, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if type == 'audios':
                filename = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            print(f"Downloaded: {os.path.basename(filename)}")
            return filename

    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None
