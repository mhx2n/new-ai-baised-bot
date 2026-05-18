import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile, BotCommand
from aiohttp import web

from config import BOT_TOKEN, OWNER_ID
from utils.database import db
from utils.converter import convert_all
from utils.downloader import download_media
from utils.ai_handler import get_ai_response

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class ConfigStates(StatesGroup):
    waiting_for_gemini_key = State()
    waiting_for_cohere_key = State()

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_buttons = State()

class ConversionStates(StatesGroup):
    selecting_base = State()
    entering_value = State()

async def handle_health(request): return web.Response(text="System Operational.")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def set_bot_commands(bot: Bot):
    commands = [BotCommand(command="start", description="Initialize System"), BotCommand(command="help", description="View commands"), BotCommand(command="convert", description="Base Converter")]
    await bot.set_my_commands(commands)

@dp.message(Command("start", prefix="/."))
async def start_command(message: types.Message):
    db.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await db.save()
    txt = f"Welcome to the Advanced Utility Suite.\n\nModules:\n• Media Extraction (URL)\n• Logic Resolution (Query)\n• Base Conversion (/convert)\n\nSystem Active."
    await message.reply(txt)

# ================= ADMIN PANEL & API MANAGEMENT =================
@dp.message(Command("admin", prefix="/."))
async def admin_panel(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Manage API Keys", callback_with_data="admin_api")],
        [InlineKeyboardButton(text="📢 Adv. Broadcast", callback_with_data="admin_broadcast")],
        [InlineKeyboardButton(text="📜 System Logs", callback_with_data="admin_logs")]
    ])
    await message.reply(f"**Admin Dashboard**\nTotal Users: {len(db.data.get('users', {}))}", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "admin_api")
async def manage_api(callback: types.CallbackQuery):
    g_key = "Set ✅" if db.get_api_key("gemini") else "Not Set ❌"
    c_key = "Set ✅" if db.get_api_key("cohere") else "Not Set ❌"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Set Gemini ({g_key})", callback_with_data="set_gemini")],
        [InlineKeyboardButton(text=f"Set Cohere ({c_key})", callback_with_data="set_cohere")]
    ])
    await callback.message.edit_text("Select API to Configure:", reply_markup=kb)

@dp.callback_query(F.data == "set_gemini")
async def ask_gemini_key(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send your Gemini API Key. Type /cancel to abort.")
    await state.set_state(ConfigStates.waiting_for_gemini_key)

@dp.message(ConfigStates.waiting_for_gemini_key)
async def save_gemini_key(message: types.Message, state: FSMContext):
    if message.text == "/cancel": return await state.clear()
    db.set_api_key("gemini", message.text.strip())
    await db.save()
    await message.reply("✅ Gemini API Key Updated!")
    await state.clear()

# ================= ADVANCED BROADCAST =================
@dp.callback_query(F.data == "admin_broadcast")
async def ask_broadcast_msg(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send the message, photo, video, or sticker you want to broadcast:")
    await state.set_state(BroadcastStates.waiting_for_message)

@dp.message(BroadcastStates.waiting_for_message)
async def ask_broadcast_buttons(message: types.Message, state: FSMContext):
    # Store the message id to copy it later
    await state.update_data(msg_id=message.message_id, chat_id=message.chat.id)
    txt = ("Do you want to add inline buttons?\nFormat: `Button1|url1, Button2|url2` (comma for same row, newline for next row).\nType `skip` if no buttons needed.")
    await message.reply(txt, parse_mode="Markdown")
    await state.set_state(BroadcastStates.waiting_for_buttons)

@dp.message(BroadcastStates.waiting_for_buttons)
async def exec_broadcast(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data['msg_id']
    source_chat = data['chat_id']
    
    reply_markup = None
    if message.text.lower() != 'skip':
        # Parse advanced buttons
        rows = message.text.split('\n')
        inline_kb = []
        for row in rows:
            btns = row.split(',')
            row_kb = []
            for btn in btns:
                if '|' in btn:
                    text, url = btn.split('|')
                    row_kb.append(InlineKeyboardButton(text=text.strip(), url=url.strip()))
            if row_kb: inline_kb.append(row_kb)
        reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)

    users = db.data.get("users", {})
    success = 0
    status = await message.reply("Broadcasting...")
    
    for uid in users.keys():
        try:
            await bot.copy_message(chat_id=int(uid), from_chat_id=source_chat, message_id=msg_id, reply_markup=reply_markup)
            success += 1
            await asyncio.sleep(0.05)
        except: continue
        
    await status.edit_text(f"✅ Broadcast Complete! Sent to {success} users.")
    await state.clear()

# ================= MEDIA & AI HANDLER =================
@dp.message(Command("convert", prefix="/."))
async def start_conversion(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Decimal", callback_with_data="cb_dec")]]) # Simplified for brevity, add others if needed
    await message.reply("Select source:", reply_markup=keyboard)

@dp.message()
async def universal_handler(message: types.Message):
    if message.from_user.id == OWNER_ID and message.text.startswith('/'): return
    text = message.text.strip()
    is_media = any(d in text.lower() for d in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "tiktok.com", "fb.gg"])
    
    if is_media:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Video", callback_with_data=f"dl_video|{text}"), InlineKeyboardButton(text="Audio", callback_with_data=f"dl_audio|{text}")]])
        return await message.reply("Select Format:", reply_markup=kb)

    msg = await message.reply("`Processing...`", parse_mode="Markdown")
    try:
        reply = await get_ai_response(text)
        await msg.edit_text(reply, parse_mode="Markdown")
    except: await msg.edit_text("System Error.")

@dp.callback_query(F.data.startswith("dl_"))
async def process_dl(callback: types.CallbackQuery):
    action, url = callback.data.split("|", 1) # Split only on first pipe
    dl_type = "audio" if "audio" in action else "video"
    await callback.message.edit_text("`Extracting...`", parse_mode="Markdown")
    try:
        filepath, title = await download_media(url, dl_type)
        await callback.message.edit_text("`Uploading...`", parse_mode="Markdown")
        file = FSInputFile(filepath)
        if dl_type == "audio": await bot.send_audio(callback.message.chat.id, file)
        else: await bot.send_video(callback.message.chat.id, file)
        await callback.message.delete()
        if os.path.exists(filepath): os.remove(filepath)
    except Exception as e:
        await callback.message.edit_text(f"Extraction failed. Media might be private. Error: {str(e)[:40]}")

async def main():
    await db.load()
    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(start_web_server(), dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))

if __name__ == '__main__':
    asyncio.run(main())
