import google.generativeai as genai
import aiohttp
from config import GEMINI_API_KEY, COHERE_API_KEY

if GEMINI_API_KEY: 
    genai.configure(api_key=GEMINI_API_KEY)

async def ask_gemini(prompt):
    if not GEMINI_API_KEY: 
        return "System Error: Gemini API Key is missing or invalid."
    try:
        # এখানে নতুন এবং ফাস্ট মডেল gemini-1.5-flash অ্যাড করা হয়েছে
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e: 
        return f"Service Interruption: {str(e)}"

async def get_ai_response(prompt, provider="gemini"):
    system_context = (
        "You are an elite, highly professional technical assistant and code solver. "
        "Provide accurate, clean, and deep explanations or debugged code for all problems. "
        "Do not introduce yourself as an AI. Do not use generic pleasantries. "
        "Deliver the solution directly and maintain a highly professional, technical tone throughout.\n\n"
    )
    return await ask_gemini(system_context + prompt)
