from os import getenv
from dotenv import load_dotenv
import logging

# Load environment variables from a .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Retrieve the bot token from environment variables
BOT_TOKEN = getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logging.error("BOT_TOKEN is not set")
    raise ValueError("BOT_TOKEN is not set")

# Retrieve the MongoDB URI from environment variables
MONGO_URI = getenv('MONGO_URI', 'mongodb+srv://BooksBot:BooksBot@cluster0.qtujn.mongodb.net/?retryWrites=true&w=majority')
if not MONGO_URI:
    logging.error("MONGO_URI is not set")
    raise ValueError("MONGO_URI is not set")

# Retrieve the MongoDB database name from environment variables
MONGO_DB_NAME = getenv('MONGO_DB_NAME', 'crocogame')
if not MONGO_DB_NAME:
    logging.error("MONGO_DB_NAME is not set")
    raise ValueError("MONGO_DB_NAME is not set")

# Retrieve the list of sudo users from environment variables
SUDO_USERS = list(map(int, getenv('SUDO_USERS', '2063915639').split()))
if not SUDO_USERS:
    logging.error("SUDO_USERS is not set")
    raise ValueError("SUDO_USERS is not set")

# Retrieve the port number from environment variables
PORT = int(getenv('PORT', '8080'))  # Convert to int
if PORT <= 0:
    logging.error("PORT must be a positive integer")
    raise ValueError("PORT must be a positive integer")

# Retrieve the API ID from environment variables
API_ID = int(getenv('API_ID', '1779071'))
if not API_ID:
    logging.error("API_ID is not set")
    raise ValueError("API_ID is not set")

# Retrieve the API hash from environment variables
API_HASH = getenv('API_HASH', '3448177952613312689f44b9d909b5d3')
if not API_HASH:
    logging.error("API_HASH is not set")
    raise ValueError("API_HASH is not set")
