import logging
import logging.config
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, PORT, MONGO_URI, MONGO_DB_NAME
import os
from mongo.users_and_chats import Database
from aiohttp import web
import asyncio
from plugins.web_support import web_server  # Import the web server function

# Configure logging with error handling
try:
    logging.config.fileConfig('logging.conf')
    logging.info("Logging configuration loaded successfully.")
except Exception as e:
    print(f"Error loading logging configuration: {e}")

# Set logging levels
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Tamil-corobot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )
        self.database = Database(MONGO_URI, MONGO_DB_NAME)

    async def start(self):
        try:
            await self.database.connect()
            await super().start()
            me = await self.get_me()
            self.mention = me.mention
            self.username = me.username

            # Example usage of Database (You can remove these in production)
            await self.database.add_user("123", {"name": "John Doe"})
            logging.info("User added successfully: 123")

            user = await self.database.get_user("123")
            logging.info(f"Retrieved user: {user}")

            await self.database.add_chat("456", {"title": "General Chat"})
            logging.info("Chat added successfully: 456")

            chat = await self.database.get_chat("456")
            logging.info(f"Retrieved chat: {chat}")

            web_app = await web_server()  # Get the aiohttp web app
            app_runner = web.AppRunner(web_app)
            await app_runner.setup()
            bind_address = "0.0.0.0"
            await web.TCPSite(app_runner, bind_address, int(os.environ.get("PORT", 8080))).start()
            logging.info(f"{me.first_name} ✅✅ BOT started successfully ✅✅")

        except Exception as e:
            logging.error(f"Failed to start the bot: {e}")
            exit(1)

    async def stop(self, *args):
        try:
            await self.database.close()
            await super().stop()
            logging.info("Bot Stopped 🙄")
        except Exception as e:
            logging.error(f"Failed to stop the bot: {e}")

bot = Bot()

# The corrected way to run the bot:
loop = asyncio.get_event_loop()
loop.create_task(bot.start())
# No app.run() here. It's handled by aiohttp now
