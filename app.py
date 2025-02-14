from flask import Flask

app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    return "TamilBots"

# Import bot and webhook_handler AFTER app is defined.
from main import bot
from plugins.web_support import webhook_handler # Import webhook_handler

@app.route("/your_webhook_path", methods=["POST"])  # Your webhook route
async def handle_webhook(): # Call the imported webhook handler
    return await webhook_handler() # Await the coroutine
