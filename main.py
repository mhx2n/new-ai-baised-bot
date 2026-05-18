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
    waiting_for_gemini_remove = State()
class ConversionStates(StatesGroup):
    selecting_base = State()
    entering_value = State()
class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_buttons = State()

async def handle_health(request): return web.Response(text="System Operational.")
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get('PORT', 10000))).start()

async def set_bot_commands(bot: Bot):
    await bot.set_my_commands([BotCommand(command="start", description="Start"), BotCommand(command="convert", description="Base Converter"), BotCommand(command="admin", description="Owner Dashboard")])

@dp.message(Command("start", prefix="/."))
async def start_cmd(message: types.Message):
    db.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await db.save()
    await message.reply("Welcome to Advanced Utility Suite.\nSystem Active.")

# ================= ADMIN & API PANEL =================
@dp.message(Command("admin", prefix="/."))
async def admin_panel(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Manage Gemini Keys", callback_data="admin_gemini")],
        [InlineKeyboardButton(text="📢 Adv. Broadcast", callback_data="admin_broadcast")]
    ])
    await message.reply(f"**Admin Dashboard**\nUsers: {len(db.data.get('users', {}))}", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "admin_gemini")
async def manage_gemini(callback: types.CallbackQuery):
    keys = db.get_api_keys("gemini")
    txt = f"**Gemini Keys: {len(keys)}**\n\n"
    for i, k in enumerate(keys): txt += f"{i+1}. `{k[:8]}...{k[-4:]}`\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Key", callback_data="add_gemini_key"), InlineKeyboardButton(text="➖ Remove Key", callback_data="rm_gemini_key")]
    ])
    await callback.message.edit_text(txt, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "add_gemini_key")
async def add_g_key(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send the new Gemini API Key:")
    await state.set_state(ConfigStates.waiting_for_gemini_key)

@dp.message(ConfigStates.waiting_for_gemini_key)
async def save_g_key(message: types.Message, state: FSMContext):
    db.add_api_key("gemini", message.text.strip())
    await db.save()
    await message.reply("✅ Key Added Successfully!")
    await state.clear()

@dp.callback_query(F.data == "rm_gemini_key")
async def rm_g_key_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send the NUMBER (1, 2, 3...) of the key you want to remove:")
    await state.set_state(ConfigStates.waiting_for_gemini_remove)

@dp.message(ConfigStates.waiting_for_gemini_remove)
async def rm_g_key_exec(message: types.Message, state: FSMContext):
    try:
        idx = int(message.text.strip()) - 1
        if db.remove_api_key("gemini", idx):
            await db.save()
            await message.reply("✅ Key Removed.")
        else: await message.reply("❌ Invalid number.")
    except: await message.reply("❌ Please send a valid number.")
    await state.clear()

# ================= ADVANCED BROADCAST =================
@dp.callback_query(F.data == "admin_broadcast")
async def ask_broadcast_msg(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send the message, photo, video, or sticker you want to broadcast:")
    await state.set_state(BroadcastStates.waiting_for_message)

@dp.message(BroadcastStates.waiting_for_message)
async def ask_broadcast_buttons(message: types.Message, state: FSMContext):
    await state.update_data(msg_id=message.message_id, chat_id=message.chat.id)
    txt = "Add inline buttons?\nFormat: `Button Name|url` (comma for same row, newline for new row).\nType `skip` if no buttons needed."
    await message.reply(txt, parse_mode="Markdown")
    await state.set_state(BroadcastStates.waiting_for_buttons)

@dp.message(BroadcastStates.waiting_for_buttons)
async def exec_broadcast(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id, source_chat = data['msg_id'], data['chat_id']
    reply_markup = None
    if message.text.lower() != 'skip':
        inline_kb = []
        for row in message.text.split('\n'):
            row_kb = [InlineKeyboardButton(text=btn.split('|')[0].strip(), url=btn.split('|')[1].strip()) for btn in row.split(',') if '|' in btn]
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
async def start_conv(message: types.Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Decimal", callback_data="cb_dec"), InlineKeyboardButton(text="Binary", callback_data="cb_bin")],
        [InlineKeyboardButton(text="Octal", callback_data="cb_oct"), InlineKeyboardButton(text="Hexadecimal", callback_data="cb_hex")],
        [InlineKeyboardButton(text="Text to ASCII", callback_data="cb_ascii")]
    ])
    await message.reply("Select source base:", reply_markup=kb)
    await state.set_state(ConversionStates.selecting_base)

@dp.callback_query(F.data.startswith("cb_"), ConversionStates.selecting_base)
async def conv_base_sel(callback: types.CallbackQuery, state: FSMContext):
    base = callback.data.split("_")[1]
    await state.update_data(chosen_base=base)
    await callback.message.edit_text(f"Source: **{base.upper()}**.\nSend value (Decimals supported like 101.11):")
    await state.set_state(ConversionStates.entering_value)

@dp.message(ConversionStates.entering_value)
async def conv_exec(message: types.Message, state: FSMContext):
    data = await state.get_data()
    res = convert_all(message.text.strip(), data.get("chosen_base"))
    try: await message.reply(res, parse_mode="Markdown")
    except: await message.reply(res) # Fallback if markdown breaks
    await state.clear()

# ================= UNIVERSAL HANDLER (AI & YT-DLP) =================
@dp.message()
async def univ_handler(message: types.Message):
    if message.text.startswith('/'): return
    text = message.text.strip()
    
    if any(d in text.lower() for d in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "tiktok.com", "fb.gg"]):
        msg = await message.reply("`Extracting media...`", parse_mode="Markdown")
        try:
            filepath, title = await download_media(text, "video") # Defaulting to video for fast workflow
            file = FSInputFile(filepath)
            await bot.send_document(message.chat.id, file, caption=f"Extracted: {title}")
            os.remove(filepath)
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"Extraction failed. Link might be private.\nLog: {str(e)[:50]}")
        return

    msg = await message.reply("`Thinking...`", parse_mode="Markdown")
    reply = await get_ai_response(text)
    
    # ADVANCED FALLBACK: To prevent Telegram "can't parse entities" error
    try:
        await msg.edit_text(reply, parse_mode="Markdown")
    except Exception:
        try:
            # If markdown fails, send purely as raw text
            await msg.edit_text(reply) 
        except Exception:
            await msg.edit_text("System Error: Could not display AI response correctly.")

async def main():
    await db.load()
    await set_bot_commands(bot)
    try: await bot.delete_webhook(drop_pending_updates=True)
    except: pass
    await asyncio.gather(start_web_server(), dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))

if __name__ == '__main__':
    asyncio.run(main())
