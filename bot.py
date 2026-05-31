import os
import logging
import asyncio
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
from downloader import download_video, detect_platform, search_youtube_music

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

PLATFORM_EMOJI = {
    "youtube": "▶️ YouTube",
    "instagram": "📸 Instagram",
    "pinterest": "📌 Pinterest",
    "tiktok": "🎵 TikTok",
    "snapchat": "👻 Snapchat",
    "unknown": "🌐 Boshqa",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Salom! Media Downloader Botga xush kelibsiz!*\n\n"
        "Men quyidagilarni yuklab beraman:\n\n"
        "▶️ YouTube — havola yoki qo'shiq nomi\n"
        "📸 Instagram\n"
        "📌 Pinterest\n"
        "🎵 TikTok\n"
        "👻 Snapchat\n\n"
        "📎 Havola yoki qo'shiq nomini yuboring!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Foydalanish yo'riqnomasi:*\n\n"
        "1️⃣ Havola yoki qo'shiq nomini yuboring\n"
        "2️⃣ Video yuklanib, sizga yuboriladi\n\n"
        "⚠️ *Eslatma:* Katta fayllar biroz vaqt olishi mumkin."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith("http"):
        url = text
        platform = detect_platform(url)
        if platform == "unknown":
            await update.message.reply_text(
                "❌ Bu havola qo'llab-quvvatlanmaydi.\n"
                "Iltimos, YouTube, Instagram, Pinterest, TikTok yoki Snapchat havolasini yuboring."
            )
            return
        context.user_data["url"] = url
        context.user_data["platform"] = platform
        platform_name = PLATFORM_EMOJI.get(platform, "🌐")
        keyboard = [
            [InlineKeyboardButton("🎬 Video yukla", callback_data="download_video")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")],
        ]
        await update.message.reply_text(
            f"✅ Havola aniqlandi: *{platform_name}*\n\nNimani yuklamoqchisiz?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(f"🔍 *{text}* qidirilmoqda...", parse_mode="Markdown")
        songs = search_youtube_music(text, limit=5)
        if not songs:
            await update.message.reply_text("❌ Qo'shiq topilmadi. Boshqa nom bilan sinab ko'ring.")
            return
        context.user_data["search_results"] = songs
        keyboard = []
        for i, song in enumerate(songs):
            keyboard.append([InlineKeyboardButton(song["display"], callback_data=f"song_{i}")])
        keyboard.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")])
        await update.message.reply_text(
            "🎵 *Quyidagilardan birini tanlang:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Bekor qilindi.")
        return

    if query.data.startswith("song_"):
        index = int(query.data.split("_")[1])
        songs = context.user_data.get("search_results", [])
        if index < len(songs):
            song = songs[index]
            context.user_data["url"] = song["url"]
            context.user_data["platform"] = "youtube"
            keyboard = [
                [InlineKeyboardButton("🎬 Video yukla", callback_data="download_video")],
                [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")],
            ]
            await query.edit_message_text(
                f"✅ *{song['display']}*\n\nNimani yuklamoqchisiz?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        return

    url = context.user_data.get("url")
    platform = context.user_data.get("platform", "")

    if not url:
        await query.edit_message_text("⚠️ Havola topilmadi. Qaytadan yuboring.")
        return

    platform_name = PLATFORM_EMOJI.get(platform, "🌐")

    if query.data == "download_video":
        await query.edit_message_text(f"⏳ *{platform_name}* dan video yuklanmoqda...", parse_mode="Markdown")
        result = download_video(url)
        if result["success"]:
            filepath = result["filepath"]
            title = result["title"]
            file_size = os.path.getsize(filepath) / (1024 * 1024)
            if file_size > 50:
                await query.message.reply_text(
                    f"⚠️ Fayl hajmi juda katta ({file_size:.1f} MB).\n"
                    "Telegram 50MB gacha fayllarni qabul qiladi."
                )
            else:
                with open(filepath, "rb") as video_file:
                    await query.message.reply_video(
                        video=video_file,
                        caption=f"🎬 {title}\n📌 {platform_name}",
                    )
            os.remove(filepath)
        else:
            await query.message.reply_text(
                f"❌ Xatolik yuz berdi:\n`{result['error']}`", parse_mode="Markdown"
            )

def main():
    async def delete_webhook():
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
            )
            logger.info("Webhook o'chirildi!")

    asyncio.run(delete_webhook())

    import time
    time.sleep(3)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    logger.info("Bot ishga tushdi! ✅")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
