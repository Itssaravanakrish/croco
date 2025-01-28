from pyrogram import Client, filters
from pyrogram.types import Message, Update
from config import BOT_TOKEN, PORT, SUDO_USERS
import os
import sys
import asyncio
from aiohttp import web

async def web_server():
    async def handle(request):
        return web.Response(text="Web server is running")
    app = web.Application()
    app.router.add_get('/', handle)
    return app

app = Client("my_bot", bot_token=BOT_TOKEN)

async def restart(_, message: Message):
    await message.reply_text("Restarting...")
    os.execl(sys.argv[0], *sys.argv)

app.add_handler(filters.command("r", prefixes="/") & filters.user(SUDO_USERS), restart)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.start())
    loop.run_until_complete(web_server())
    app.idle()
