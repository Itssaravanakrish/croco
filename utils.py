import logging
from typing import Dict, Optional
from mongo.users_and_chats import db, UserNotFoundError, ChatNotFoundError
from script import messages_en, messages_ta, messages_hi
from pyrogram import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def get_message(language: str, key: str, **kwargs) -> str:
    """Fetch localized message based on language."""
    messages = {
        "en": messages_en,
        "ta": messages_ta,
        "hi": messages_hi
    }
    
    # Get the message template
    message_template = messages.get(language, {}).get(key, "Message not found")
    
    # Format the message with any additional keyword arguments
    return message_template.format(**kwargs)

async def register_user(user_id: str, user_data: Dict) -> bool:
    """Register a user in the database."""
    try:
        await db.get_user(user_id)
        logging.info(f"User  {user_id} already exists.")
        return True
    except UserNotFoundError:
        try:
            await db.add_user(user_id, user_data)
            logging.info(f"User  {user_id} registered.")
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

async def is_user_admin(client: Client, chat_id: str, user_id: str) -> bool:
    """Check if a user is an admin in a specific chat."""
    try:
        chat_member = await client.get_chat_member(chat_id, user_id)
        return chat_member.status in ["administrator", "creator"]
    except Exception as e:
        logging.error(f"Failed to check if user {user_id} is admin in chat {chat_id}: {e}")
        return False

# Optional: Add utility functions for group language and game mode if needed
async def set_group_language(chat_id: str, language: str) -> bool:
    """Set the group language in the database."""
    try:
        await db.set_group_language(chat_id, language)
        logging.info(f"Group language for chat {chat_id} set to {language}.")
        return True
    except Exception as e:
        logging.error(f"Failed to set group language for chat {chat_id}: {e}")
        return False

async def get_group_language(chat_id: str) -> str:
    """Get the group language from the database."""
    try:
        language = await db.get_group_language(chat_id)
        logging.info(f"Retrieved group language for chat {chat_id}: {language}.")
        return language
    except Exception as e:
        logging.error(f"Failed to get group language for chat {chat_id}: {e}")
        return "en"  # Default to English if there's an error

async def set_group_game_mode(chat_id: str, game_mode: str) -> bool:
    """Set the group game mode in the database."""
    try:
        await db.set_group_game_mode(chat_id, game_mode)
        logging.info(f"Group game mode for chat {chat_id} set to {game_mode}.")
        return True
    except Exception as e:
        logging.error(f"Failed to set group game mode for chat {chat_id}: {e}")
        return False

async def get_group_game_mode(chat_id: str) -> str:
    """Get the group game mode from the database."""
    try:
        game_mode = await db.get_group_game_mode(chat_id)
        logging.info(f"Retrieved group game mode for chat {chat_id}: {game_mode}.")
        return game_mode
    except Exception as e:
        logging.error(f"Failed to get group game mode for chat {chat_id}: {e}")
        return "easy"  # Default to easy if there's an error
