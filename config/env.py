from os import getenv

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv('BOT_TOKEN')
MONGO_URI = getenv('MONGO_URI')
MONGO_DB_NAME = getenv('MONGO_DB_NAME')
SUDO_USERS = list(map(int, getenv('SUDO_USERS').split()))
PORT = getenv('PORT')
