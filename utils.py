import logging
from typing import Dict, Optional
from mongo.users_and_chats import db, UserNotFoundError, ChatNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def get_message(language: str, key: str) -> str:
    """Fetch localized message based on language."""
    try:
        if language == "en":
            from script import messages_en
            return getattr(messages_en, key, "Message not found")
        elif language == "ta":
            from script import messages_ta
            return getattr(messages_ta, key, "Message not found")
        elif language == "hi":
            from script import messages_hi
            return getattr(messages_hi, key, "Message not found")
        else:
            return "Invalid language"
    except ImportError:
        logging.error("Language module not found")
        return "Message not found"

async def register_user(user_id: str, user_data: Dict) -> bool:
    """Register a user in the database."""
    try:
        await db.get_user(user_id)
        logging.info(f"User {user_id} already exists.")
        return True
    except UserNotFoundError:
        try:
            await db.add_user(user_id, user_data)
            logging.info(f"User {user_id} registered.")
            return True
        except Exception as e:
            logging.error(f"Failed to register user {user_id}: {e}")
            return False

async def register_chat(chat_id: str, chat_data: Dict) -> bool:
    """Register a chat in the database."""
    try:
        await db.get_chat(chat_id)
        logging.info(f"Chat {chat_id} already exists.")
        return True
    except ChatNotFoundError:
        try:
            await db.add_chat(chat_id, chat_data)
            logging.info(f"Chat {chat_id} registered.")
            return True
        except Exception as e:
            logging.error(f"Failed to register chat {chat_id}: {e}")
            return False
