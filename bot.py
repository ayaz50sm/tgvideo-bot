import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from downloader import extract_url, get_info, download_video

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()
COOKIE_FILE = os.getenv("COOKIE_FILE", "./secrets/cookies.txt").strip()
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads").strip()
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "1900"))

Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_USER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_admin(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return
    await update.message.reply_text(
        "Link pathao.\n"
        "/info <url> = info\n"
        "/dl <url> = download and send here\n"
        "/post <url> = download and post to channel"
    )

async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_admin(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    url = extract_url(" ".join(context.args).strip())
    if not url:
        await update.message.reply_text("Valid URL dao.")
        return

    msg = await update.message.reply_text("Info nicchi...")
    try:
        info = await get_info(url, COOKIE_FILE)
        title = info.get("title", "N/A")
        uploader = info.get("uploader", "N/A")
        duration = info.get("duration", "N/A")
        webpage_url = info.get("webpage_url", url)
        await msg.edit_text(
            f"Title: {title}\nUploader: {uploader}\nDuration: {duration}\nURL: {webpage_url}"
        )
    except Exception as e:
        await msg.edit_text(f"Error: {e}")

async def dl_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_admin(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    url = extract_url(" ".join(context.args).strip())
    if not url:
        await update.message.reply_text("Valid URL dao.")
        return

    msg = await update.message.reply_text("Download start hocche...")
    try:
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.UPLOAD_VIDEO)
        file_path = await download_video(url, DOWNLOAD_DIR, COOKIE_FILE)
        size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if size_mb > MAX_FILE_SIZE_MB:
            await msg.edit_text(f"Downloaded but too large: {size_mb:.1f} MB")
            return

        with open(file_path, "rb") as f:
            await update.message.reply_video(
                video=f,
                supports_streaming=True,
                caption=os.path.basename(file_path),
            )
        await msg.edit_text("Done.")
    except Exception as e:
        await msg.edit_text(f"Error: {e}")

async def post_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_admin(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    url = extract_url(" ".join(context.args).strip())
    if not url:
        await update.message.reply_text("Valid URL dao.")
        return

    msg = await update.message.reply_text("Channel e post er jonno download hocche...")
    try:
        file_path = await download_video(url, DOWNLOAD_DIR, COOKIE_FILE)
        size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if size_mb > MAX_FILE_SIZE_MB:
            await msg.edit_text(f"Downloaded but too large: {size_mb:.1f} MB")
            return

        with open(file_path, "rb") as f:
            await context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=f,
                supports_streaming=True,
                caption=os.path.basename(file_path),
            )
        await msg.edit_text("Channel e post hoye geche.")
    except Exception as e:
        await msg.edit_text(f"Error: {e}")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_admin(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    url = extract_url(update.message.text or "")
    if not url:
        await update.message.reply_text("URL dao ba /info /dl /post use koro.")
        return

    context.args = [url]
    await dl_cmd(update, context)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing in .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("dl", dl_cmd))
    app.add_handler(CommandHandler("post", post_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
