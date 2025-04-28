import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

# Enable detailed logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Store video links in memory
VIDEO_LINKS = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    logger.debug(f"Received /start from chat {update.message.chat_id}")
    await update.message.reply_text(
        "Bot is running! Send videos in the source chat, and I'll forward them and generate links."
    )

@app.on_message()
async def send_chat_id(client, message):
    # Extract the chat ID of the user who sends the message
    chat_id = message.chat.id
    await message.reply(f"Your chat ID is: {chat_id}")

app.run()

async def debug_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log all incoming messages for debugging."""
    logger.debug(f"Received message in chat {update.message.chat_id}: {update.message}")
    if update.message.video:
        logger.debug(f"Video detected: file_id={update.message.video.file_id}, mime_type={update.message.video.mime_type}")
    else:
        logger.debug("No video in message")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming video messages."""
    source_chat_id = os.getenv("SOURCE_CHAT_ID")
    dest_chat_id = os.getenv("DEST_CHAT_ID")
    bot_token = os.getenv("BOT_TOKEN")

    logger.debug(f"Checking video in chat {update.message.chat_id}, expected source: {source_chat_id}")

    # Verify chat ID
    if str(update.message.chat_id) != source_chat_id:
        logger.debug(f"Ignored message from chat {update.message.chat_id}, not source chat")
        return

    # Verify video
    if not update.message.video:
        logger.debug("Message is not a video")
        return

    try:
        logger.debug(f"Processing video: file_id={update.message.video.file_id}")
        # Add delay to avoid rate limits
        await asyncio.sleep(1)
        # Forward video
        logger.debug(f"Forwarding to destination chat {dest_chat_id}")
        forwarded_message = await context.bot.forward_message(
            chat_id=dest_chat_id,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )
        logger.debug(f"Video forwarded, message_id={forwarded_message.message_id}")

        # Generate download link
        file_id = update.message.video.file_id
        logger.debug(f"Getting file for file_id={file_id}")
        file = await context.bot.get_file(file_id)
        file_path = file.file_path
        download_link = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        VIDEO_LINKS.append(download_link)
        logger.debug(f"Generated link: {download_link}")

        # Reply to user
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

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("links", get_links))
    application.add_handler(CommandHandler("env", env_check))
    application.add_handler(CommandHandler("testdest", test_dest))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.ALL, debug_message))  # Debug all messages
    application.add_error_handler(error_handler)

    logger.debug("Starting polling")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
