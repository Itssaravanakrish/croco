from aiohttp import web
from app import app  # Import app from app.py

async def web_server():
    return app  # Return the Flask app instance
