import asyncio
import logging
import logging.config
import sys
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, PORT, MONGO_URI, MONGO_DB_NAME, LOG_CHANNEL
from aiohttp import web
from plugins.web_support import web_server
from mongo.users_and_chats import Database

# Configure logging
try:
    logging.config.fileConfig('logging.conf')
    logging.info("Logging configuration loaded successfully.")
except Exception as e:
    print(f"Error loading logging configuration: {e}")
    logging.basicConfig(level=logging.INFO)

# Set logging levels
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client):
    def __init__(self):
        super().__init__(
            "my_bot",
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

            start_message = f"{me.first_name} ✅✅ BOT started successfully ✅✅"
            logging.info(start_message)
            await self.send_message(LOG_CHANNEL, start_message)

            # Example usage of Database
            await self.database.add_user("123", {"name": "John Doe"})
            logging.info("User  added successfully: 123")

            user = await self.database.get_user("123")
            logging.info(f"Retrieved user: {user}")

            await self.database.add_chat("456", {"title": "General Chat"})
            logging.info("Chat added successfully: 456")

            chat = await self.database.get_chat("456")
            logging.info(f"Retrieved chat: {chat}")

            app = web.AppRunner(await web_server())
            await app.setup()
            bind_address = "0.0.0.0"
            await web.TCPSite(app, bind_address, PORT).start()
            logging.info(f"Web server started on {bind_address}:{PORT}")
        except Exception as e:
            logging.error(f"Failed to start the bot: {e}")
            if self.is_connected:
                await self.send_message(LOG_CHANNEL, f"Failed to start the bot: {e}")
            sys.exit(1)

    async def stop(self, *args):
        try:
            await self.database.close()
            await super().stop()
            logging.info("Bot Stopped 🙄")
            await self.send_message(LOG_CHANNEL, "Bot Stopped 🙄")
        except Exception as e:
            logging.error(f"Failed to stop the bot: {e}")
            await self.send_message(LOG_CHANNEL, f"Failed to stop the bot: {e}")

# Create an instance of the Bot and run it
if __name__ == "__main__":
    bot = Bot()
    bot.run()  # This starts the bot and blocks the main thread
