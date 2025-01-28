from os import getenv
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set")

MONGO_URI = getenv('MONGO_URI')
if not MONGO_URI:
    raise ValueError("MONGO_URI is not set")

MONGO_DB_NAME = getenv('MONGO_DB_NAME')
if not MONGO_DB_NAME:
    raise ValueError("MONGO_DB_NAME is not set")

SUDO_USERS = list(map(int, getenv('SUDO_USERS', '1169076058').split()))
if not SUDO_USERS:
    raise ValueError("SUDO_USERS is not set")

PORT = getenv('PORT')
if not PORT:
    raise ValueError("PORT is not set")

API_ID = int(getenv('API_ID', '1779071'))
if not API_ID:
raise ValueError("API_ID is not set")

API_HASH = getenv('API_HASH', '3448177952613312689f44b9d909b5d3')
if not API_HASH:
raise ValueError("API_HASH is not set")
