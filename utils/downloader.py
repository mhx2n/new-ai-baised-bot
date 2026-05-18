import aiohttp
import json

async def download_media(url, download_type='video'):
    # Cobalt API is the most advanced zero-error media downloader available
    api_url = "https://co.wuk.sh/api/json"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    data = {
        "url": url,
        "isAudioOnly": True if download_type == 'audio' else False,
        "aFormat": "mp3" if download_type == 'audio' else "best"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=data, timeout=20) as resp:
                if resp.status != 200:
                    raise Exception("Server rejected the request. Link might be strictly private.")
                    
                result = await resp.json()
                
                status = result.get("status")
                if status == "error":
                    raise Exception(result.get("text", "Unknown Error"))
                elif status in ["stream", "redirect", "picker"]:
                    # Returns the direct raw media URL
                    return result.get("url"), "Media Extracted Successfully"
                else:
                    raise Exception("Unexpected response from extraction server.")
    except Exception as e:
        raise Exception(f"{str(e)}")
