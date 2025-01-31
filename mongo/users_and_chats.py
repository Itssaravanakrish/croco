# mongo/users_and_chats.py

import logging
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from config import MONGO_URI, MONGO_DB_NAME
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError

class UserNotFoundError(Exception):
    """Custom exception for user not found errors."""
    pass

class ChatNotFoundError(Exception):
    """Custom exception for chat not found errors."""
    pass

class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors."""
    pass

class Database:
    def __init__(self, uri: str, database_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.database = self.client[database_name]
        self.users_collection: AsyncIOMotorCollection = self.database.users
        self.chats_collection: AsyncIOMotorCollection = self.database.chats
        logging.info(f"Connected to MongoDB at {uri}, database: {database_name}")

    async def connect(self):
        """Establish a connection to the MongoDB database."""
        # This method can be used to check the connection or perform any setup if needed
        if self.client is None:
            raise DatabaseConnectionError("Database connection is not established.")

    def new_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user dictionary."""
        return {"user_id": user_id, **user_data}

    def new_chat(self, chat_id: str, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new chat dictionary."""
        return {"chat_id": chat_id, **chat_data}

    async def add_user(self, user_id: str, user_data: Dict[str, Any]) -> None:
        """Add a new user to the database."""
        user = self.new_user(user_id, user_data)
        try:
            await self.users_collection.insert_one(user)
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to add user {user_id}: {e}")
            raise

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Retrieve a user from the database."""
        try:
            user = await self.users_collection.find_one({"user_id": user_id})
            if user is None:
                raise UserNotFoundError(f"User  with ID {user_id} not found.")
            return user
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to get user {user_id}: {e}")
            raise

    async def delete_user(self, user_id: str) -> None:
        """Delete a user from the database."""
        try:
            result = await self.users_collection.delete_one({"user_id": user_id})
            if result.deleted_count == 0:
                raise UserNotFoundError(f"User  with ID {user_id} not found.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to delete user {user_id}: {e}")
            raise

    async def add_chat(self, chat_id: str, chat_data: Dict[str, Any]) -> None:
        """Add a new chat to the database."""
        chat = self.new_chat(chat_id, chat_data)
        try:
            await self.chats_collection.insert_one(chat)
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to add chat {chat_id}: {e}")
            raise

    async def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a chat from the database."""
        try:
            chat = await self.chats_collection.find_one({"chat_id": chat_id})
            if chat is None:
                raise ChatNotFoundError(f"Chat with ID {chat_id} not found.")
            return chat
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to get chat {chat_id}: {e}")
            raise

    async def close(self) -> None:
        """Close the database connection."""
        self.client.close()
        logging.info("Database connection closed.") ### Key Changes Made to `users_and_chats.py`

