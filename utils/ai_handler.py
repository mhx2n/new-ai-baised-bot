from google import genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None

async def ask_gemini(prompt):
    if not client:
        return "System Error: Gemini API Key is missing or invalid."
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
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
