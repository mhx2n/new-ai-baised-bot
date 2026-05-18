import aiohttp
from utils.database import db

async def ask_gemini(prompt):
    api_key = db.get_api_key("gemini")
    if not api_key: return "System Error: Gemini API Key is not set by the Administrator."
    
    # Using REST API instead of the deprecated library for maximum stability
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts":[{"text": prompt}]}]}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result['candidates'][0]['content']['parts'][0]['text']
                elif resp.status == 503:
                    return "Service Interruption: Gemini server is currently overloaded. Please try again later."
                else:
                    return f"API Error: {resp.status} - {await resp.text()}"
    except Exception as e: return f"Service Interruption: {str(e)}"

async def get_ai_response(prompt, provider="gemini"):
    system_context = (
        "You are an elite, highly professional technical assistant and code solver. "
        "Provide accurate, clean, and deep explanations or debugged code. "
        "Do not introduce yourself. Deliver the solution directly.\n\n"
    )
    return await ask_gemini(system_context + prompt)
