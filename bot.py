import os
from pyrogram import Client, filters

# Get API details and bot token from environment variables
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

# Initialize the bot
app = Client("bulk_video_link_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Handler for /start command
@app.on_message(filters.command("start"))
async def start_command(client, message):
    # Send a welcome message when /start is typed
    await message.reply("👋 Welcome to the Bulk Video Link Generator bot! Send a video and I'll generate a download link for you.")

# Handler for receiving videos
@app.on_message(filters.video)
async def forward_and_generate_link(client, message):
    try:
        # Await the file info properly (use get_file correctly)
        file_info = await client.get_file(message.video.file_id)
        file_path = file_info.file_path
        
        # Generate the download link
        download_link = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

        # Send the download link
        await message.reply(f"✅ Video Download Link:\n{download_link}")
    except Exception as e:
        # If there's an error, log it and reply with an error message
        print(f"Error processing video: {e}")
        await message.reply("⚠️ Oops! Something went wrong while processing the video. Please try again later.")

# Run the bot
app.run()
