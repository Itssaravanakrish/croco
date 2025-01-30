from pyrogram import Client, filters, errors
from pyrogram.types import Message
from config import BOT_TOKEN, API_ID, API_HASH, PORT, SUDO_USERS
import os
import sys
import asyncio
from aiohttp import web
import logging
import pathlib
import time

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# Web server
async def web_server():
    try:
        app = web.Application()
        app.router.add_get('/', lambda request: web.Response(text="Web server is running"))
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, '0.0.0.0', PORT).start()
        logging.info("Web server is running!")
    except Exception as e:
        logging.error(f"Error starting web server: {e}")

# Pyrogram client
app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root='plugins')
)

# Restart handler
async def restart(_, message: Message):
    await message.reply_text("Restarting...")
    logging.info("Bot is restarting...")
    os.execl(sys.argv[0], *sys.argv)

# Alive handler
async def alive(_, message: Message):
    await message.reply_text("Bot is alive!")

# Add handlers
app.add_handler(filters.command("r", prefixes="/") & filters.user(SUDO_USERS), restart)
app.add_handler(filters.command("alive", prefixes="/"), alive)

# Send alive message to specific chat on startup
CHAT_ID = -1001566660231
ALIVE_MESSAGE = "Bot is alive!"

async def startup():
    try:
        await app.send_message(CHAT_ID, ALIVE_MESSAGE)
        logging.info("Alive message sent to chat!")
    except Exception as e:
        logging.error(f"Error sending alive message: {e}")

# Run the bot and web server
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logging.info("Bot is starting...")
    loop.run_until_complete(web_server())
    loop.run_until_complete(startup())
    app.start()
    logging.info("Bot is running!")
