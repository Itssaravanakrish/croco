import logging
from typing import Dict, Optional
from mongo.users_and_chats import db, UserNotFoundError, ChatNotFoundError
from script import messages_en, messages_ta, messages_hi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def get_message(language: str, key: str) -> str:
    """Fetch localized message based on language."""
    messages = {
        "en": messages_en,
        "ta": messages_ta,
        "hi": messages_hi
    }
    return messages.get(language, {}).get(key, "Message not found")

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
