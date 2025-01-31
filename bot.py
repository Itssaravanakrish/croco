import logging
import logging.config
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, PORT
from aiohttp import web
from plugins.web_support import web_server
from mongo import MongoDB  # Import the MongoDB class

# Configure logging
logging.config.fileConfig('logging.conf')
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

    async def start(self):
        await super().start()  # Start the bot
        me = await self.get_me()  # Get bot information
        self.mention = me.mention  # Store mention format
        self.username = me.username  # Store username
        app = web.AppRunner(await web_server())  # Initialize the web server
        await app.setup()  # Set up the web server
        bind_address = "0.0.0.0"  # Bind to all interfaces
        await web.TCPSite(app, bind_address, PORT).start()  # Start the web server
        logging.info(f"{me.first_name} ✅✅ BOT started successfully ✅✅")

    async def stop(self, *args):
        await super().stop()  # Stop the bot
        logging.info("Bot Stopped 🙄")

# Create an instance of the Bot and run it
bot = Bot()
bot.run()
