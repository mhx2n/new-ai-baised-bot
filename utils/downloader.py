import asyncio
import yt_dlp
import os

os.makedirs("downloads", exist_ok=True)

async def download_media(url, download_type='video'):
    def sync_download():
        opts = {
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'quiet': True,
        }
        if download_type == 'audio':
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            opts.update({'format': 'best[ext=mp4]/best'})
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if download_type == 'audio':
                base, _ = os.path.splitext(filename)
                filename = base + ".mp3"
            return filename, info.get('title', 'Media File')

    return await asyncio.to_thread(sync_download)
