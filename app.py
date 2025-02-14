from flask import Flask, request
from main import bot  # Import bot after app
from aiohttp import web
import asyncio
from plugins.web_support import web_server # Import web_server

app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    return "TamilBots"

@app.route("/your_webhook_path", methods=["POST"])  # Your webhook route
async def webhook_handler():
    update = request.get_json()
    if update:
        await bot.process_new_updates(update)
    return "ok"


async def handle_webhook(): # Call the imported webhook handler
    return await webhook_handler() # Await the coroutine


async def start_server(): # Start the aiohttp server
    web_app = await web_server()  # Get the aiohttp web app
    app_runner = web.AppRunner(web_app)
    await app_runner.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app_runner, bind_address, int(os.environ.get("PORT", 8080))).start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start())
    loop.run_until_complete(start_server())
