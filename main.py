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

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_buttons = State()

class ConversionStates(StatesGroup):
    selecting_base = State()
    entering_value = State()

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

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Initialize System"), 
        BotCommand(command="help", description="View commands"), 
        BotCommand(command="convert", description="Base Converter"),
        BotCommand(command="admin", description="Owner Dashboard")
    ]
    await bot.set_my_commands(commands)

@dp.message(Command("start", prefix="/."))
async def start_command(message: types.Message):
    db.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await db.save()
    txt = f"Welcome to the Advanced Utility Suite, {message.from_user.first_name}.\n\nModules:\n• Media Extraction (Paste URL)\n• Logic Resolution (Ask AI directly)\n• Base Conversion (/convert)\n\nSystem Active."
    await message.reply(txt)

@dp.message(Command("help", prefix="/."))
async def help_command(message: types.Message):
    await message.reply("**Command Menu:**\n`.start` / `/start` - Boot\n`.convert` / `/convert` - Num Converter\n\n*(Send any Media link to download or ask any question to chat with AI)*", parse_mode="Markdown")

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
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Set Gemini API ({g_key})", callback_with_data="set_gemini")]
    ])
    await callback.message.edit_text("Select API to Configure:", reply_markup=kb)

@dp.callback_query(F.data == "set_gemini")
async def ask_gemini_key(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send your Gemini API Key. Type `/cancel` to abort.", parse_mode="Markdown")
    await state.set_state(ConfigStates.waiting_for_gemini_key)

@dp.message(ConfigStates.waiting_for_gemini_key)
async def save_gemini_key(message: types.Message, state: FSMContext):
    if message.text.strip() == "/cancel": 
        await message.reply("Cancelled.")
        return await state.clear()
    db.set_api_key("gemini", message.text.strip())
    await db.save()
    await message.reply("✅ Gemini API Key Updated!")
    await state.clear()

@dp.callback_query(F.data == "admin_logs")
async def view_logs(callback: types.CallbackQuery):
    logs = db.data.get("logs", [])
    txt = "**System Logs:**\n\n" + "\n".join(logs[-15:]) if logs else "No activity yet."
    await callback.message.edit_text(txt, parse_mode="Markdown")

# ================= ADVANCED BROADCAST =================
@dp.callback_query(F.data == "admin_broadcast")
async def ask_broadcast_msg(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send the Message, Photo, Video, File or Sticker you want to broadcast:")
    await state.set_state(BroadcastStates.waiting_for_message)

@dp.message(BroadcastStates.waiting_for_message)
async def ask_broadcast_buttons(message: types.Message, state: FSMContext):
    await state.update_data(msg_id=message.message_id, chat_id=message.chat.id)
    txt = ("Do you want to add inline buttons?\nFormat: `Button1|url1, Button2|url2` (comma for same row, newline for next).\nType `skip` if no buttons needed.")
    await message.reply(txt, parse_mode="Markdown")
    await state.set_state(BroadcastStates.waiting_for_buttons)

@dp.message(BroadcastStates.waiting_for_buttons)
async def exec_broadcast(message: types.Message, state: FSMContext):
    if not message.text:
        return await message.reply("❌ Error: You must send the button format as TEXT, or type `skip`.", parse_mode="Markdown")
        
    data = await state.get_data()
    reply_markup = None
    
    if message.text.lower() != 'skip':
        try:
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
        except:
            return await message.reply("❌ Invalid button format. Try again or type `skip`.")

    users = db.data.get("users", {})
    success = 0
    status = await message.reply("`Broadcasting payload...`", parse_mode="Markdown")
    
    for uid in users.keys():
        try:
            await bot.copy_message(chat_id=int(uid), from_chat_id=data['chat_id'], message_id=data['msg_id'], reply_markup=reply_markup)
            success += 1
            await asyncio.sleep(0.05)
        except: continue
        
    await status.edit_text(f"✅ Broadcast Complete! Successfully delivered to `{success}` users.", parse_mode="Markdown")
    await state.clear()

# ================= NUMBER CONVERTER =================
@dp.message(Command("convert", prefix="/."))
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
    await callback.message.edit_text(f"Source system: **{base.upper()}**.\nProvide the value:")
    await state.set_state(ConversionStates.entering_value)

@dp.message(ConversionStates.entering_value)
async def process_conversion_value(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    result_text = convert_all(message.text.strip(), user_data.get("chosen_base"))
    await message.reply(result_text, parse_mode="Markdown")
    await state.clear()

# ================= UNIVERSAL HANDLER (MEDIA + AI) =================
@dp.message()
async def universal_handler(message: types.Message):
    text = message.text.strip()
    is_media = any(d in text.lower() for d in ["youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com", "tiktok.com", "fb.gg"])
    
    if is_media:
        # 64-byte limit fix: We don't put the URL in callback_data anymore
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Video Format", callback_with_data="dl_video"),
             InlineKeyboardButton(text="🎵 Audio Format", callback_with_data="dl_audio")]
        ])
        return await message.reply("Media source identified. Select extraction protocol:", reply_markup=kb)

    msg = await message.reply("`Processing request...`", parse_mode="Markdown")
    db.add_log(f"AI Query from {message.from_user.id}")
    try:
        reply = await get_ai_response(text)
        await msg.edit_text(reply, parse_mode="Markdown")
    except: 
        await msg.edit_text("System Error: Unable to format response properly.")

@dp.callback_query(F.data.in_(["dl_video", "dl_audio"]))
async def process_dl(callback: types.CallbackQuery):
    dl_type = "audio" if callback.data == "dl_audio" else "video"
    
    # Extract original URL from the message the bot replied to
    if not callback.message.reply_to_message or not callback.message.reply_to_message.text:
        return await callback.message.edit_text("❌ Error: Original URL not found.")
        
    url = callback.message.reply_to_message.text.strip()
    await callback.message.edit_text("`Extracting media. This may take a moment...`", parse_mode="Markdown")
    db.add_log(f"Media Download ({dl_type}) by {callback.from_user.id}")
    
    try:
        filepath, title = await download_media(url, dl_type)
        await callback.message.edit_text("`Uploading payload to Telegram...`", parse_mode="Markdown")
        file = FSInputFile(filepath)
        
        if dl_type == "audio": 
            await bot.send_audio(callback.message.chat.id, file, caption="Extracted via Utility Suite.")
        else: 
            await bot.send_video(callback.message.chat.id, file, caption="Extracted via Utility Suite.")
            
        await callback.message.delete()
        if os.path.exists(filepath): os.remove(filepath)
    except Exception as e:
        await callback.message.edit_text(f"❌ Extraction failed. Media might be private or unsupported format.\n`{str(e)[:40]}`", parse_mode="Markdown")

async def main():
    await db.load()
    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(start_web_server(), dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot Terminated.")
