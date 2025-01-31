import logging
import logging.config
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, PORT  # Removed MONGO_URI and MONGO_DB_NAME since they are not needed here
from aiohttp import web
from plugins.web_support import web_server
from mongo.mongo import MongoDB  # Import the MongoDB class
from mongo.users_and_chats import Users, Chats  # Use absolute import for Users and Chats classes

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
        self.mongo_db = MongoDB()  # Initialize MongoDB connection
        self.users = Users(self.mongo_db)  # Pass the MongoDB instance
        self.chats = Chats(self.mongo_db)  # Pass the MongoDB instance

    async def start(self):
        try:
            await self.mongo_db.connect()  # Ensure MongoDB connection is established
            await super().start()  # Start the bot
            me = await self.get_me()  # Get bot information
            self.mention = me.mention  # Store mention format
            self.username = me.username  # Store username

            # Example usage of Users and Chats
            await self.users.add_user("123", {"name": "John Doe"})
            logging.info("User  added successfully: 123")

            user = await self.users.get_user("123")
            logging.info(f"Retrieved user: {user}")

            await self.chats.add_chat("456", {"title": "General Chat"})
            logging.info("Chat added successfully: 456")

            chat = await self.chats.get_chat("456")
            logging.info(f"Retrieved chat: {chat}")

            app = web.AppRunner(await web_server())  # Initialize the web server
            await app.setup()  # Set up the web server
            bind_address = "0.0.0.0"  # Bind to all interfaces
            await web.TCPSite(app, bind_address, PORT).start()  # Start the web server
            logging.info(f"{me.first_name} ✅✅ BOT started successfully ✅✅")
        except Exception as e:
            logging.error(f"Failed to start the bot: {e}")
            exit(1)  # Exit if the bot fails to start

    async def stop(self, *args):
        try:
            await self.mongo_db.close()  # Close the MongoDB connection
            await super().stop()  # Stop the bot
            logging.info("Bot Stopped 🙄")
        except Exception as e:
            logging.error(f"Failed to stop the bot: {e}")

# Create an instance of the Bot and run it
if __name__ == "__main__":
    bot = Bot()
    bot.run()
