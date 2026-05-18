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
            'no_warnings': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'extractor_retries': 3,
            'format': 'best[ext=mp4]/best' if download_type == 'video' else 'bestaudio/best'
        }
        
        # Spoofing as a real Windows 11 Chrome Browser to bypass blocks
        yt_dlp.utils.std_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                if download_type == 'audio' and not filename.endswith('.mp3'):
                    base, _ = os.path.splitext(filename)
                    new_filename = base + ".mp3"
                    os.rename(filename, new_filename)
                    filename = new_filename
                    
                return filename, info.get('title', 'Media')
        except Exception as e:
            # Clean up the error message for the user
            err_msg = str(e).split('\n')[0]
            raise Exception(err_msg)

    return await asyncio.to_thread(sync_download)
