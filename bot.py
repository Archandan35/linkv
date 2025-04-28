import os
from pyrogram import Client, filters

api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

app = Client("bulk_video_link_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.video)
async def forward_and_generate_link(client, message):
    file_info = await client.get_file(message.video.file_id)
    file_path = file_info.file_path

    download_link = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

    await message.reply(f"✅ Video Download Link:\n{download_link}")

app.run()
