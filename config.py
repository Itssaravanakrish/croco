from os import getenv
from dotenv import load_dotenv
import logging

# Load environment variables from a .env file
load_dotenv()

# Set up logging with a specific format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_env_variable(var_name, default=None):
    """Retrieve an environment variable or raise an error if not found."""
    value = getenv(var_name, default)
    if value is None:
        logging.error(f"{var_name} is not set")
        raise ValueError(f"{var_name} is not set")
    return value

# Retrieve the bot token from environment variables
BOT_TOKEN = get_env_variable('BOT_TOKEN')

# Retrieve the MongoDB URI from environment variables
MONGO_URI = get_env_variable('MONGO_URI', 'mongodb+srv://filestream:filestream@cluster0.d1dlfzv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

# Retrieve the MongoDB database name from environment variables
MONGO_DB_NAME = get_env_variable('MONGO_DB_NAME', 'crocogame')

# Retrieve the list of sudo users from environment variables
SUDO_USERS = list(map(int, get_env_variable('SUDO_USERS', '2063915639').split()))

# Retrieve the port number from environment variables
PORT = int(get_env_variable('PORT', '8080'))  # Convert to int
if PORT <= 0:
    logging.error("PORT must be a positive integer")
    raise ValueError("PORT must be a positive integer")

# Retrieve the API ID from environment variables
API_ID = int(get_env_variable('API_ID', '1779071'))
if API_ID <= 0:
    logging.error("API_ID must be a positive integer")
    raise ValueError("API_ID must be a positive integer")

# Retrieve the API hash from environment variables
API_HASH = get_env_variable('API_HASH', '3448177952613312689f44b9d909b5d3')

# Retrieve the log channel ID from environment variables
LOG_CHANNEL = int(get_env_variable('LOG_CHANNEL', '-1001566660231'))  # Default to your channel ID
if LOG_CHANNEL == 0:
    logging.error("LOG_CHANNEL is not set")
    raise ValueError("LOG_CHANNEL is not set")
