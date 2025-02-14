from flask import Flask

app = Flask(__name__)  # Create the Flask app instance here

@app.route("/", methods=["GET"])
def hello_world():
    return "TamilBots"

# Import bot AFTER the app is created
from main import bot  # Import bot after app

@app.route("/your_webhook_path", methods=["POST"])  # Your webhook route
async def webhook_handler():
    update = request.get_json()
    if update:
        await bot.process_new_updates(update)
    return "ok"
