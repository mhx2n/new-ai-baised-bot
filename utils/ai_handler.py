import google.generativeai as genai
import aiohttp
from config import GEMINI_API_KEY, COHERE_API_KEY

if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)

async def ask_gemini(prompt):
    if not GEMINI_API_KEY: return "❌ Gemini API Key set করা নেই।"
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e: return f"❌ Gemini Error: {str(e)}"

async def get_ai_response(prompt, provider="gemini"):
    system_context = (
        "You are an expert advanced coding solver and unique technical assistant bot. "
        "Provide super-fast, accurate, clean and deep explanations or debugged code for all problems.\n\n"
    )
    return await ask_gemini(system_context + prompt)
