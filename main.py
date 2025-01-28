from pyrogram import Client, filters
from pyrogram.types import Message
from config import BOT_TOKEN, API_ID, API_HASH, PORT, SUDO_USERS
import os
import sys
import asyncio
from aiohttp import web

# Web server
async def web_server():
    app = web.Application()
    app.router.add_get('/', lambda request: web.Response(text="Web server is running"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()

# Pyrogram client
app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Restart handler
async def restart(_, message: Message):
    await message.reply_text("Restarting...")
    os.execl(sys.argv[0], *sys.argv)

# Add handlers
app.add_handler(filters.command("r", prefixes="/") & filters.user(SUDO_USERS), restart)

# Run the bot and web server
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(web_server())
    loop.run_until_complete(app.start())
    app.idle()

