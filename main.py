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

# ================= STATES =================
class ConfigStates(StatesGroup):
    waiting_for_gemini_key = State()
    waiting_for_cohere_key = State()

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_buttons = State()

class ConversionStates(StatesGroup):
    selecting_base = State()
    entering_value = State()

class MediaDL(StatesGroup):
    waiting_for_format = State()

# ================= WEB SERVER =================
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

# ================= COMMANDS =================
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Initialize System"), 
        BotCommand(command="help", description="View commands"), 
        BotCommand(command="convert", description="Base Converter"),
        BotCommand(command="admin", description="Admin Dashboard")
    ]
    await bot.set_my_commands(commands)

@dp.message(Command("start", prefix="/."))
async def start_command(message: types.Message):
    db.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await db.save()
    txt = f"Welcome to the Advanced Utility Suite, {message.from_user.first_name}.\n\nModules:\n• Media Extraction (Paste URL)\n• Logic Resolution (Ask AI directly)\n• Base Conversion (/convert)\n\nSystem Active."
    await message.reply(txt)

# ================= ADMIN PANEL =================
@dp.message(Command("admin", prefix="/."))
async def admin_panel(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Manage API Keys", callback_data="admin_api")],
        [InlineKeyboardButton(text="📢 Adv. Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📜 System Logs", callback_data="admin_logs")]
    ])
    await message.reply(f"**Admin Dashboard**\n• Total Users: {len(db.data.get('users', {}))}\n• Status: Operational", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "admin_api")
async def manage_api(callback: types.CallbackQuery):
    g_key = "Set ✅" if db.get_api_key("gemini") else "Not Set ❌"
    c_key = "Set ✅" if db.get_api_key("cohere") else "Not Set ❌"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Gemini: {g_key}", callback_data="set_gemini")],
        [InlineKeyboardButton(text=f"Cohere: {c_key}", callback_data="set_cohere")]
    ])
    await callback.message.edit_text("Select API to Configure:", reply_markup=kb)

@dp.callback_query(F.data == "set_gemini")
async def ask_gemini_key(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send your Gemini API Key. Type /cancel to abort.")
    await state.set_state(ConfigStates.waiting_for_gemini_key)

@dp.message(ConfigStates.waiting_for_gemini_key)
async def save_gemini_key(message: types.Message, state: FSMContext):
    if message.text == "/cancel": 
        await message.reply("Cancelled.")
        return await state.clear()
    
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
    await state.update_data(msg_id=message.message_id, chat_id=message.chat.id)
    txt = ("Do you want to add inline buttons?\nFormat: `Button Name|url`\n(Use commas for buttons in the same row, newline for a new row).\n\nType `skip` if no buttons needed.")
    await message.reply(txt, parse_mode="Markdown")
    await state.set_state(BroadcastStates.waiting_for_buttons)

@dp.message(BroadcastStates.waiting_for_buttons)
async def exec_broadcast(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data['msg_id']
    source_chat = data['chat_id']
    
    reply_markup = None
    if message.text.lower() != 'skip':
        rows = message.text.split('\n')
        inline_kb = []
        for row in rows:
            btns = row.split(',')
            row_kb = []
            for btn in btns:
                if '|' in btn:
                    text, url = btn.split('|', 1)
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

# ================= CONVERTER =================
@dp.message(Command("convert", prefix="/."))
async def start_conversion(message: types.Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Decimal", callback_data="cb_dec"),
         InlineKeyboardButton(text="Binary", callback_data="cb_bin")],
        [InlineKeyboardButton(text="Octal", callback_data="cb_oct"),
         InlineKeyboardButton(text="Hexadecimal", callback_data="cb_hex")],
        [InlineKeyboardButton(text="Gray Code", callback_data="cb_gray"),
         InlineKeyboardButton(text="Excess-3", callback_data="cb_excess3")]
    ])
    await message.reply("Select source number system:", reply_markup=kb)
    await state.set_state(ConversionStates.selecting_base)

@dp.callback_query(F.data.startswith("cb_"), ConversionStates.selecting_base)
async def base_selected(callback: types.CallbackQuery, state: FSMContext):
    base = callback.data.split("_")[1]
    await state.update_data(chosen_base=base)
    await callback.message.edit_text(f"Source: **{base.upper()}**.\nProvide the value:")
    await state.set_state(ConversionStates.entering_value)

@dp.message(ConversionStates.entering_value)
async def process_conversion_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    res = convert_all(message.text.strip(), data.get("chosen_base"))
    await message.reply(res, parse_mode="Markdown")
    await state.clear()

# ================= AI & MEDIA DOWNLOADER =================
@dp.message()
async def universal_handler(message: types.Message, state: FSMContext):
    if message.text.startswith('/') or message.text.startswith('.'):
        return # Ignore invalid commands
        
    text = message.text.strip()
    is_media = any(d in text.lower() for d in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "tiktok.com", "fb.gg"])
    
    if is_media:
        await state.update_data(media_url=text) # Saves large URL in state safely
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Video Format", callback_data="dl_video")],
            [InlineKeyboardButton(text="🎵 Audio Format", callback_data="dl_audio")]
        ])
        await message.reply("Media link detected. Select format to extract:", reply_markup=kb)
        await state.set_state(MediaDL.waiting_for_format)
        return

    msg = await message.reply("`Processing request...`", parse_mode="Markdown")
    try:
        reply = await get_ai_response(text)
        await msg.edit_text(reply, parse_mode="Markdown")
    except Exception as e: 
        await msg.edit_text(f"System Error: {str(e)[:50]}")

@dp.callback_query(MediaDL.waiting_for_format)
async def process_media(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    url = data.get("media_url")
    dl_type = "audio" if callback.data == "dl_audio" else "video"
    
    await callback.message.edit_text("`Extracting media... Please wait.`", parse_mode="Markdown")
    try:
        filepath, title = await download_media(url, dl_type)
        await callback.message.edit_text("`Uploading payload to server...`", parse_mode="Markdown")
        
        file = FSInputFile(filepath)
        if dl_type == "audio": 
            await bot.send_audio(callback.message.chat.id, file, caption="Extracted via Utility Suite.")
        else: 
            await bot.send_video(callback.message.chat.id, file, caption="Extracted via Utility Suite.")
            
        await callback.message.delete()
        if os.path.exists(filepath): os.remove(filepath)
    except Exception as e:
        await callback.message.edit_text(f"Extraction failed. Video might be private or invalid.\nError: {str(e)[:40]}")
    finally:
        await state.clear()

# ================= MAIN =================
async def main():
    await db.load()
    await set_bot_commands(bot)
    try:
        await bot.delete_webhook(drop_pending_updates=True) # Cleans up conflicts
    except: pass
    
    await asyncio.gather(
        start_web_server(), 
        dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    )

if __name__ == '__main__':
    asyncio.run(main())
