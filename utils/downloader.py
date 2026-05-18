import asyncio
import yt_dlp
import os

os.makedirs("downloads", exist_ok=True)

async def download_media(url, download_type='video'):
    def sync_download():
        # একদম বেস্ট কম্প্যাটিবল ফরম্যাট যা FFmpeg ছাড়াই চলবে
        opts = {
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]/best' if download_type == 'video' else 'bestaudio/best'
        }
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # অডিও হলে জাস্ট এক্সটেনশন রিনেম করে দিবো, FFmpeg এর দরকার নেই
                if download_type == 'audio' and not filename.endswith('.mp3'):
                    base, _ = os.path.splitext(filename)
                    new_filename = base + ".mp3"
                    os.rename(filename, new_filename)
                    filename = new_filename
                    
                return filename, info.get('title', 'Extracted Media')
        except Exception as e:
            raise Exception(f"{str(e)}")

    return await asyncio.to_thread(sync_download)
