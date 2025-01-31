import logging
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from config.env import MONGO_URI, MONGO_DB_NAME
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError

class UserNotFoundError(Exception):
    """Custom exception for user not found errors."""
    pass

class Users:
    def __init__(self, db: AsyncIOMotorCollection):
        self.db = db  # Reference to the MongoDB database

    async def add_user(self, user_id: str, user_data: Dict[str, Any]) -> None:
        """Add a new user to the database."""
        try:
            await self.db.users.insert_one({"user_id": user_id, **user_data})
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to add user {user_id}: {e}")
            raise

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Retrieve a user from the database."""
        try:
            user = await self.db.users.find_one({"user_id": user_id})
            if user is None:
                raise UserNotFoundError(f"User  with ID {user_id} not found.")
            return user
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to get user {user_id}: {e}")
            raise

    async def delete_user(self, user_id: str) -> None:
        """Delete a user from the database."""
        try:
            result = await self.db.users.delete_one({"user_id": user_id})
            if result.deleted_count == 0:
                raise UserNotFoundError(f"User  with ID {user_id} not found.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to delete user {user_id}: {e}")
            raise

class Chats:
    def __init__(self, db: AsyncIOMotorCollection):
        self.db = db  # Reference to the MongoDB database

    async def add_chat(self, chat_id: str, chat_data: Dict[str, Any]) -> None:
        """Add a new chat to the database."""
        try:
            await self.db.chats.insert_one({"chat_id": chat_id, **chat_data})
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to add chat {chat_id}: {e}")
            raise

    async def get_chat(self, chat_id: str) -> Dict[str, Any]:
        """Retrieve a chat from the database."""
        try:
            return await self.db.chats.find_one({"chat_id": chat_id})
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to get chat {chat_id}: {e}")
            raise

    async def delete_chat(self, chat_id: str) -> None:
        """Delete a chat from the database."""
        try:
            result = await self.db.chats.delete_one({"chat_id": chat_id})
            if result.deleted_count == 0:
                logging.warning(f"Chat with ID {chat_id} not found for deletion.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to delete chat {chat_id}: {e}")
            raise
