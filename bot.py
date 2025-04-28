import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)
import requests
from urllib.parse import urlencode

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store video links in memory (for simplicity; consider a database for production)
VIDEO_LINKS = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    await update.message.reply_text(
        "Bot is running! Send videos in the source chat, and I'll forward them and generate links."
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming video messages."""
    source_chat_id = os.getenv("SOURCE_CHAT_ID")
    dest_chat_id = os.getenv("DEST_CHAT_ID")
    bot_token = os.getenv("BOT_TOKEN")

    # Check if the message is from the source chat
    if str(update.message.chat_id) != source_chat_id:
        return

    # Check if the message contains a video
    if not update.message.video:
        return

    try:
        # Forward the video to the destination chat
        forwarded_message = await context.bot.forward_message(
            chat_id=dest_chat_id,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )

        # Get the file ID of the video
        file_id = update.message.video.file_id
        # Get file details
        file = await context.bot.get_file(file_id)
        file_path = file.file_path

        # Construct the direct download link
        download_link = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

        # Store the link
        VIDEO_LINKS.append(download_link)

        # Notify user in source chat
        await update.message.reply_text(
            f"Video forwarded and link generated: {download_link}"
        )

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await update.message.reply_text("Failed to process video.")

async def get_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /links command to retrieve all generated links."""
    if not VIDEO_LINKS:
        await update.message.reply_text("No video links generated yet.")
        return

    # Send all links as a single message
    links_text = "\n".join(VIDEO_LINKS)
    await update.message.reply_text(f"Generated video links:\n{links_text}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Run the bot."""
    # Get the bot token from environment variables
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set.")
        return

    # Create the Application
    application = Application.builder().token(bot_token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("links", get_links))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
