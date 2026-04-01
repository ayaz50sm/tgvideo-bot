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

from downloader import (
    extract_url,
    get_info,
    download_video,
    choose_cookie_file,
    download_thumbnail,
    build_caption,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads").strip()
COOKIE_DIR = os.getenv("COOKIE_DIR", "./secrets").strip()
DEFAULT_COOKIE_FILE = os.getenv("DEFAULT_COOKIE_FILE", "./secrets/default.txt").strip()
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "1900"))
YTDLP_TIMEOUT = int(os.getenv("YTDLP_TIMEOUT", "180"))

Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(COOKIE_DIR).mkdir(parents=True, exist_ok=True)

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

async def process_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, to_channel: bool = False):
    msg = await update.message.reply_text("Processing link...")
    cookie_file = choose_cookie_file(url, COOKIE_DIR, DEFAULT_COOKIE_FILE)

    try:
        info = await get_info(url, cookie_file, YTDLP_TIMEOUT)
        caption = build_caption(info)
        thumb_path = download_thumbnail(info.get("thumbnail"), DOWNLOAD_DIR)

        await msg.edit_text("Downloading video...")
        file_path = await download_video(url, DOWNLOAD_DIR, cookie_file, YTDLP_TIMEOUT)

        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            await msg.edit_text(f"Downloaded but too large: {size_mb:.1f} MB")
            return

        duration = info.get("duration")
        width = info.get("width")
        height = info.get("height")

        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.UPLOAD_VIDEO)

        if to_channel:
            with open(file_path, "rb") as vf:
                if thumb_path and os.path.exists(thumb_path):
                    with open(thumb_path, "rb") as tf:
                        await context.bot.send_video(
                            chat_id=CHANNEL_ID,
                            video=vf,
                            caption=caption,
                            supports_streaming=True,
                            duration=duration,
                            width=width,
                            height=height,
                            thumbnail=tf,
                        )
                else:
                    await context.bot.send_video(
                        chat_id=CHANNEL_ID,
                        video=vf,
                        caption=caption,
                        supports_streaming=True,
                        duration=duration,
                        width=width,
                        height=height,
                    )
            await msg.edit_text("Channel e post hoye geche.")
        else:
            with open(file_path, "rb") as vf:
                if thumb_path and os.path.exists(thumb_path):
                    with open(thumb_path, "rb") as tf:
                        await update.message.reply_video(
                            video=vf,
                            caption=caption,
                            supports_streaming=True,
                            duration=duration,
                            width=width,
                            height=height,
                            thumbnail=tf,
                        )
                else:
                    await update.message.reply_video(
                        video=vf,
                        caption=caption,
                        supports_streaming=True,
                        duration=duration,
                        width=width,
                        height=height,
                    )
            await msg.edit_text("Done.")

    except Exception as e:
        await msg.edit_text(f"Error: {e}")

async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_admin(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    url = extract_url(" ".join(context.args).strip())
    if not url:
        await update.message.reply_text("Valid URL dao.")
        return

    cookie_file = choose_cookie_file(url, COOKIE_DIR, DEFAULT_COOKIE_FILE)
    msg = await update.message.reply_text("Info nicchi...")

    try:
        info = await get_info(url, cookie_file, YTDLP_TIMEOUT)
        await msg.edit_text(build_caption(info))
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

    await process_url(update, context, url, to_channel=False)

async def post_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_admin(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    url = extract_url(" ".join(context.args).strip())
    if not url:
        await update.message.reply_text("Valid URL dao.")
        return

    await process_url(update, context, url, to_channel=True)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_admin(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    url = extract_url(update.message.text or "")
    if not url:
        await update.message.reply_text("URL dao ba /info /dl /post use koro.")
        return

    await process_url(update, context, url, to_channel=False)

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
