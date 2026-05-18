import aiohttp
from utils.database import db

async def ask_gemini(prompt):
    keys = db.get_api_keys("gemini")
    if not keys: return "System Error: No Gemini API Keys configured by Admin."
    
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts":[{"text": prompt}]}]}
    
    # Try keys one by one. If one hits limit (503/429), try next.
    for api_key in keys:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result['candidates'][0]['content']['parts'][0]['text']
                    elif resp.status in [429, 503]:
                        continue # Key exhausted or overloaded, try next key
                    else:
                        continue # Other error, try next key
        except Exception: continue
        
    return "Service Interruption: All configured Gemini API keys failed or are currently overloaded."

async def get_ai_response(prompt, provider="gemini"):
    sys_prompt = "You are a highly professional assistant. Answer strictly without markdown format if possible, just plain text to avoid parse errors.\n\n"
    return await ask_gemini(sys_prompt + prompt)
