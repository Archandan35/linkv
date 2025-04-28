import os
import logging
import asyncio
import aiofiles
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)
from pathlib import Path
from urllib.parse import urlencode

# Enable detailed logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Store video links in memory
VIDEO_LINKS = []

# Directory for temporary file storage
TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    logger.debug(f"Received /start from chat {update.message.chat_id}")
    await update.message.reply_text(
        "Bot is running! Send videos in the source chat, and I'll forward them. Links generated for videos ≤20MB."
    )

async def debug_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log all incoming messages for debugging."""
    logger.debug(f"Received message in chat {update.message.chat_id}: {update.message}")
    if update.message.video:
        logger.debug(f"Video detected: file_id={update.message.video.file_id}, mime_type={update.message.video.mime_type}, size={update.message.video.file_size}")
    else:
        logger.debug("No video in message")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming video messages."""
    source_chat_id = os.getenv("SOURCE_CHAT_ID")
    dest_chat_id = os.getenv("DEST_CHAT_ID")
    bot_token = os.getenv("BOT_TOKEN")

    logger.debug(f"Checking video in chat {update.message.chat_id}, expected source: {source_chat_id}")

    if str(update.message.chat_id) != source_chat_id:
        logger.debug(f"Ignored message from chat {update.message.chat_id}, not source chat")
        return

    if not update.message.video:
        logger.debug("Message is not a video")
        return

    try:
        video = update.message.video
        file_size_mb = video.file_size / (1024 * 1024)  # Convert bytes to MB
        logger.debug(f"Processing video: file_id={video.file_id}, size={file_size_mb:.2f}MB")

        # Forward video (no size limit for forwarding)
        await asyncio.sleep(1)  # Avoid rate limits
        logger.debug(f"Forwarding to destination chat {dest_chat_id}")
        forwarded_message = await context.bot.forward_message(
            chat_id=dest_chat_id,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )
        logger.debug(f"Video forwarded, message_id={forwarded_message.message_id}")

        # Generate link only for videos ≤20MB
        if file_size_mb > 20:
            logger.debug("Video too large for link generation (>20MB)")
            await update.message.reply_text(
                "Video forwarded, but link not generated: File is too big (>20MB). Use videos ≤20MB for links."
            )
            return

        # Get file and download it
        file_id = video.file_id
        logger.debug(f"Getting file for file_id={file_id}")
        file = await context.bot.get_file(file_id)
        file_path = file.file_path

        # Download file to temporary directory
        temp_file_path = TEMP_DIR / f"{file_id}.mp4"
        logger.debug(f"Downloading file to {temp_file_path}")
        await file.download_to_drive(temp_file_path)

        # Generate a local link (for testing; in production, use a public URL)
        download_link = f"file://{temp_file_path}"  # Placeholder; see notes below
        VIDEO_LINKS.append(download_link)
        logger.debug(f"Generated link: {download_link}")

        await update.message.reply_text(f"Video forwarded and link generated: {download_link}")

    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        await update.message.reply_text(f"Failed to process video: {str(e)}")

async def get_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve all generated links."""
    logger.debug(f"Received /links from chat {update.message.chat_id}")
    if not VIDEO_LINKS:
        await update.message.reply_text("No video links generated yet.")
        return
    links_text = "\n".join(VIDEO_LINKS)
    await update.message.reply_text(f"Generated video links:\n{links_text}")

async def env_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check environment variables."""
    logger.debug(f"Received /env from chat {update.message.chat_id}")
    await update.message.reply_text(
        f"SOURCE_CHAT_ID: {os.getenv('SOURCE_CHAT_ID')}\n"
        f"DEST_CHAT_ID: {os.getenv('DEST_CHAT_ID')}"
    )

async def test_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test sending a message to the destination chat."""
    dest_chat_id = os.getenv("DEST_CHAT_ID")
    logger.debug(f"Received /testdest, testing destination chat {dest_chat_id}")
    try:
        await context.bot.send_message(chat_id=dest_chat_id, text="Test message from bot")
        await update.message.reply_text("Test message sent to destination chat.")
    except Exception as e:
        logger.error(f"Failed to send to destination: {str(e)}")
        await update.message.reply_text(f"Failed to send to destination: {str(e)}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Run the bot."""
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set.")
        return

    logger.debug("Starting bot application")
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("links", get_links))
    application.add_handler(CommandHandler("env", env_check))
    application.add_handler(CommandHandler("testdest", test_dest))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.ALL, debug_message))
    application.add_error_handler(error_handler)

    logger.debug("Starting polling")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
