from aiohttp import web
from flask import Flask, request
from bot import bot  # Import your bot instance

app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    return "TamilBots"

@app.route("/your_webhook_path", methods=["POST"])  # Replace with your actual path
async def webhook_handler():
    update = request.get_json()
    if update:
        await bot.process_new_updates(update)
    return "ok"

async def web_server():
    aio_app = web.Application()
    aio_app.router.add_post("/your_webhook_path", webhook_adapter)
    aio_app.router.add_get("/", hello_adapter)
    return aio_app

def webhook_adapter(request):
    with app.test_request_context(environ=request.environ):
        return webhook_handler()

def hello_adapter(request):
    with app.test_request_context(environ=request.environ):
        return hello_world()
