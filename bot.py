import os
from pyrogram import Client, filters
import asyncio
from pyrogram.errors import FloodWait

# Get API details and bot token from environment variables
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

# Initialize the bot
app = Client("bulk_video_link_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Handler for /start command
@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply("👋 Welcome to the Bulk Video Link Generator bot! Send one or more videos, and I'll generate download links for them.")

# Handler for receiving single videos
@app.on_message(filters.video & ~filters.media_group)
async def forward_and_generate_link(client, message):
    try:
        # Get the file ID from the video
        file_id = message.video.file_id

        # Use get_file to fetch the file_path
        try:
            file = await client.get_file(file_id)
        except FloodWait as e:
            print(f"FloodWait: Waiting for {e.x} seconds")
            await asyncio.sleep(e.x)
            file = await client.get_file(file_id)
        file_path = file.file_path

        # Generate the download link using the file_path
        download_link = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

        # Send the download link
        await message.reply(f"✅ Video Download Link:\n{download_link}")
    except Exception as e:
        # Log the error and notify the user
        print(f"Error processing video: {e}")
        await message.reply("⚠️ Oops! Something went wrong while processing the video. Please try again later.")

# Handler for media groups (to support multiple videos sent together)
@app.on_message(filters.media_group)
async def handle_media_group(client, message):
    try:
        # Get all messages in the media group
        media_group_id = message.media_group_id
        messages = await client.get_media_group(message.chat.id, media_group_id)

        for msg in messages:
            if msg.video:
                # Get the file ID from the video
                file_id = msg.video.file_id

                # Use get_file to fetch the file_path
                try:
                    file = await client.get_file(file_id)
                except FloodWait as e:
                    print(f"FloodWait: Waiting for {e.x} seconds")
                    await asyncio.sleep(e.x)
                    file = await client.get_file(file_id)
                file_path = file.file_path

                # Generate the download link using the file_path
                download_link = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

                # Send the download link
                await msg.reply(f"✅ Video Download Link:\n{download_link}")
                await asyncio.sleep(1)  # Avoid rate limits
    except Exception as e:
        print(f"Error processing media group: {e}")
        await message.reply("⚠️ Oops! Something went wrong while processing the videos. Please try again later.")

# Run the bot with flood wait handling
async def main():
    while True:
        try:
            await app.start()
            await app.idle()
        except FloodWait as e:
            print(f"FloodWait: Waiting for {e.x} seconds before restarting")
            await asyncio.sleep(e.x)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    asyncio.run(main())
```
