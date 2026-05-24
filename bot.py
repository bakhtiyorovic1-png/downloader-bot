import os
import logging
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
from downloader import download_video, download_audio, detect_platform, search_youtube_music

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
        "2️⃣ Video yoki Audio tanlang\n"
        "3️⃣ Fayl yuklanib, sizga yuboriladi\n\n"
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
    else:
        await update.message.reply_text(f"🔍 *{text}* qidirilmoqda...", parse_mode="Markdown")
        url = search_youtube_music(text)
        if not url:
            await update.message.reply_text("❌ Qo'shiq topilmadi. Boshqa nom bilan sinab ko'ring.")
            return
        platform = "youtube"

    context.user_data["url"] = url
    context.user_data["platform"] = platform

    platform_name = PLATFORM_EMOJI.get(platform, "🌐")

    keyboard = [
        [
            InlineKeyboardButton("🎬 Video yukla", callback_data="download_video"),
            InlineKeyboardButton("🎵 Audio yukla", callback_data="download_audio"),
        ],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Topildi: *{platform_name}*\n\nNimani yuklamoqchisiz?",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Bekor qilindi.")
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
                await query.message.reply_text(f"✅ *{title}* yuklab olindi!", parse_mode="Markdown")
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

    elif query.data == "download_audio":
        await query.edit_message_text(f"⏳ *{platform_name}* dan audio yuklanmoqda...", parse_mode="Markdown")
        result = download_audio(url)

        if result["success"]:
            filepath = result["filepath"]
            title = result["title"]
            file_size = os.path.getsize(filepath) / (1024 * 1024)

            if file_size > 50:
                await query.message.reply_text(
                    f"⚠️ Fayl hajmi juda katta ({file_size:.1f} MB)."
                )
            else:
                await query.message.reply_text(f"✅ *{title}* audio yuklab olindi!", parse_mode="Markdown")
                with open(filepath, "rb") as audio_file:
                    await query.message.reply_audio(
                        audio=audio_file,
                        caption=f"🎵 {title}\n📌 {platform_name}",
                    )
            os.remove(filepath)
        else:
            await query.message.reply_text(
                f"❌ Xatolik yuz berdi:\n`{result['error']}`", parse_mode="Markdown"
            )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    logger.info("Bot ishga tushdi! ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
