import logging
from typing import Dict, Optional
from mongo.users_and_chats import db, UserNotFoundError, ChatNotFoundError  # Make sure this import is correct
from script import messages, Language  # Import Language enum as well
from pyrogram import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def get_message(language: str, key: str, **kwargs) -> Optional[str]:
    """Fetch localized message based on language."""

    try:
        language_enum = Language(language)  # Convert the language string to Language enum member
    except ValueError:  # If the language string is not a valid enum member
        language_enum = Language.EN  # Default to English

    message_template = messages.get(language_enum, {}).get(key)  # Use enum member as key, handle missing language

    if message_template is None:
        logging.warning(f"Message key '{key}' not found for language '{language_enum.name}'.")  # Use enum name
        return "Message not found"  # Or return None if you prefer
    return message_template.format(**kwargs)

async def register_item(item_type: str, item_id: str, item_data: Dict) -> bool:
    """Register a user or chat in the database."""
    collection = db.users_collection if item_type == "user" else db.chats_collection
    try:
        existing_item = await collection.find_one({f"{item_type}_id": item_id})
        if existing_item:
            logging.info(f"{item_type.capitalize()} {item_id} already exists.")
            return True
        else:
            await collection.insert_one({f"{item_type}_id": item_id, **item_data})
            logging.info(f"{item_type.capitalize()} {item_id} registered.")
            return True
    except Exception as e:
        logging.error(f"Failed to register {item_type} {item_id}: {e}")
        return False  # Return False on error

async def register_user(user_id: str, user_data: Dict) -> bool:
    return await register_item("user", user_id, user_data)

async def register_chat(chat_id: str, chat_data: Dict) -> bool:
    return await register_item("chat", chat_id, chat_data)

async def is_user_admin(client: Client, chat_id: str, user_id: str) -> bool:
    """Check if a user is an admin in a specific chat."""
    try:
        chat_member = await client.get_chat_member(chat_id, user_id)
        return chat_member.status in ["creator", "administrator", "restricted"]  # More concise check, include restricted
    except Exception as e:
        logging.error(f"Failed to check if user {user_id} is admin in chat {chat_id}: {e}")
        return False

async def set_chat_language(chat_id: str, language: str) -> bool:  # Correct Name
    """Set the chat language in the database."""
    try:
        await db.set_chat_language(chat_id, language)
        logging.info(f"Chat language for chat {chat_id} set to {language}.")
        return True
    except Exception as e:
        logging.error(f"Failed to set chat language for chat {chat_id}: {e}")
        return False

async def get_chat_language(chat_id: str) -> str:  # Correct Name
    """Get the chat language from the database."""
    try:
        language = await db.get_chat_language(chat_id)
        logging.info(f"Retrieved chat language for chat {chat_id}: {language}.")
        return language
    except Exception as e:
        logging.error(f"Failed to get chat language for chat {chat_id}: {e}")
        logging.warning(f"Error getting language for {chat_id}. Defaulting to 'en'.")  # Add warning
        return "en"  # Default to English if there's an error

async def set_group_game_mode(chat_id: str, game_modes: List[str]) -> bool:  # game_modes is a LIST
    """Set the group game mode in the database."""
    try:
        await db.set_group_game_mode(chat_id, game_modes)  # Pass the LIST to db
        logging.info(f"Group game mode for chat {chat_id} set to {game_modes}.")
        return True
    except Exception as e:
        logging.error(f"Failed to set group game mode for chat {chat_id}: {e}")
        return False

async def get_group_game_mode(chat_id: str) -> List[str]:  # Returns a LIST
    """Get the group game mode from the database."""
    try:
        game_modes = await db.get_group_game_mode(chat_id)  # Get the LIST from db
        logging.info(f"Retrieved group game mode for chat {chat_id}: {game_modes}.")
        return game_modes  # Return the LIST
    except Exception as e:
        logging.error(f"Failed to get group game mode for chat {chat_id}: {e}")
        logging.warning(f"Error getting game mode for {chat_id}. Defaulting to ['easy'].")
        return ["easy"]  # Default to a LIST
