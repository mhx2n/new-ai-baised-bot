import aiohttp
from utils.database import db

async def ask_gemini(prompt):
    keys = db.get_api_keys("gemini")
    if not keys: return "❌ System Error: No Gemini API Keys configured. Use /admin to add."
    
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts":[{"text": prompt}]}]}
    
    error_msgs = []
    for api_key in keys:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result['candidates'][0]['content']['parts'][0]['text']
                    else:
                        err_text = await resp.text()
                        error_msgs.append(f"HTTP {resp.status}")
        except Exception as e:
            error_msgs.append(str(e))
            
    return f"❌ AI Error. The API Key might be invalid (must start with AIza...) or blocked.\nDetails: {', '.join(error_msgs)}"

async def get_ai_response(prompt, provider="gemini"):
    sys_prompt = "You are a highly professional assistant. Answer directly without complex markdown to avoid format errors.\n\n"
    return await ask_gemini(sys_prompt + prompt)
