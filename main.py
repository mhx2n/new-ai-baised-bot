import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiohttp import web

from config import BOT_TOKEN, OWNER_ID
from utils.database import db
from utils.converter import convert_all
from utils.downloader import download_media
from utils.ai_handler import get_ai_response

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class ConversionStates(StatesGroup):
    selecting_base = State()
    entering_value = State()

class BroadcastStates(StatesGroup):
    entering_message = State()

async def handle_health(request):
    return web.Response(text="System Operational.")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

@dp.message(CommandStart())
async def start_command(message: types.Message):
    user = message.from_user
    if db.add_user(user.id, user.username, user.first_name):
        await db.save()
        
    welcome_text = (
        f"Welcome to the Advanced Utility Suite, {user.first_name}.\n\n"
        f"**Available Modules:**\n"
        f"• Media Extraction (Submit a supported URL)\n"
        f"• Code & Logic Resolution (Submit your technical query)\n"
        f"• Number Base Conversion (Execute /convert)\n\n"
        f"System is active and awaiting input."
    )
    await message.reply(welcome_text, parse_mode="Markdown")

@dp.message(Command("convert"))
async def start_conversion(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Decimal", callback_with_data="cb_dec"),
         InlineKeyboardButton(text="Binary", callback_with_data="cb_bin")],
        [InlineKeyboardButton(text="Octal", callback_with_data="cb_oct"),
         InlineKeyboardButton(text="Hexadecimal", callback_with_data="cb_hex")],
        [InlineKeyboardButton(text="Gray Code", callback_with_data="cb_gray"),
         InlineKeyboardButton(text="Excess-3", callback_with_data="cb_excess3")]
    ])
    await message.reply("Select the source number system:", reply_markup=keyboard)
    await state.set_state(ConversionStates.selecting_base)

@dp.callback_query(F.data.startswith("cb_"), ConversionStates.selecting_base)
async def base_selected(callback: types.CallbackQuery, state: FSMContext):
    base = callback.data.split("_")[1]
    await state.update_data(chosen_base=base)
    await callback.message.edit_text(f"Source system configured: **{base.upper()}**.\nProvide the value to convert:")
    await state.set_state(ConversionStates.entering_value)

@dp.message(ConversionStates.entering_value)
async def process_conversion_value(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    result_text = convert_all(message.text.strip(), user_data.get("chosen_base"))
    await message.reply(result_text, parse_mode="Markdown")
    await state.clear()

# Admin Interface
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    
    total_users = len(db.data.get("users", {}))
    admin_text = (
        f"**System Administrator Dashboard**\n\n"
        f"• Total Active Users: `{total_users}`\n"
        f"• Server Status: `Operational`\n\n"
        f"Commands: /broadcast | /logs"
    )
    await message.reply(admin_text, parse_mode="Markdown")

@dp.message(Command("logs"))
async def view_logs(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    logs = db.data.get("logs", [])
    if not logs:
        return await message.reply("No recent activity logged.")
    await message.reply(f"**System Logs:**\n\n" + "\n".join(logs[-15:]), parse_mode="Markdown")

@dp.message(Command("broadcast"))
async def start_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != OWNER_ID: return
    await message.reply("Provide the broadcast message payload:")
    await state.set_state(BroadcastStates.entering_message)

@dp.message(BroadcastStates.entering_message)
async def execute_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != OWNER_ID: return
    users = db.data.get("users", {})
    success_count = 0
    
    status_msg = await message.reply("Executing broadcast protocol...")
    
    for user_id in users.keys():
        try:
            await bot.send_message(chat_id=int(user_id), text=message.text)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            continue
            
    await status_msg.edit_text(f"Broadcast complete. Payload delivered to `{success_count}` users.")
    await state.clear()

@dp.message()
async def universal_handler(message: types.Message):
    text = message.text.strip()
    is_media_link = any(d in text.lower() for d in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "tiktok.com"])
    
    if is_media_link:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Video Format", callback_with_data=f"dl_video|{text}"),
             InlineKeyboardButton(text="Audio Format", callback_with_data=f"dl_audio|{text}")]
        ])
        await message.reply("Media source identified. Select extraction protocol:", reply_markup=keyboard)
        return

    msg = await message.reply("`Processing request...`", parse_mode="Markdown")
    ai_reply = await get_ai_response(text)
    try: 
        await msg.edit_text(ai_reply, parse_mode="Markdown")
    except: 
        await msg.edit_text(ai_reply)

@dp.callback_query(F.data.startswith("dl_"))
async def process_media_download(callback: types.CallbackQuery):
    action, url = callback.data.split("|")
    dl_type = "audio" if "audio" in action else "video"
    await callback.message.edit_text("`Extracting media...`", parse_mode="Markdown")
    try:
        filepath, title = await download_media(url, dl_type)
        await callback.message.edit_text("`Uploading payload to server...`", parse_mode="Markdown")
        
        file = FSInputFile(filepath)
        if dl_type == "audio": 
            await bot.send_audio(chat_id=callback.message.chat.id, audio=file, caption="Extracted via Utility Suite.")
        else: 
            await bot.send_video(chat_id=callback.message.chat.id, video=file, caption="Extracted via Utility Suite.")
            
        await callback.message.delete()
        if os.path.exists(filepath): os.remove(filepath)
    except Exception as e:
        await callback.message.edit_text(f"Extraction failed: {str(e)[:50]}")

async def main():
    await db.load()
    await asyncio.gather(start_web_server(), dp.start_polling(bot))

if __name__ == '__main__':
    asyncio.run(main())
