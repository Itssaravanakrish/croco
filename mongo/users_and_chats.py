import logging
from typing import Union, List
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorClient
from config import MONGO_URI, MONGO_DB_NAME
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError  # Updated import

class Users:
    def __init__(self, db):
        self.db = db  # Reference to the MongoDB database

    async def add_user(self, user_id, user_data):
        """Add a new user to the database."""
        try:
            await self.db.users.insert_one({"user_id": user_id, **user_data})
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to add user {user_id}: {e}")
            raise

    async def get_user(self, user_id):
        """Retrieve a user from the database."""
        try:
            return await self.db.users.find_one({"user_id": user_id})
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to get user {user_id}: {e}")
            raise

    async def delete_user(self, user_id):
        """Delete a user from the database."""
        try:
            await self.db.users.delete_one({"user_id": user_id})
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to delete user {user_id}: {e}")
            raise

class Chats:
    def __init__(self, db):
        self.db = db  # Reference to the MongoDB database

    async def add_chat(self, chat_id, chat_data):
        """Add a new chat to the database."""
        try:
            await self.db.chats.insert_one({"chat_id": chat_id, **chat_data})
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to add chat {chat_id}: {e}")
            raise

    async def get_chat(self, chat_id):
        """Retrieve a chat from the database."""
        try:
            return await self.db.chats.find_one({"chat_id": chat_id})
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to get chat {chat_id}: {e}")
            raise

    async def delete_chat(self, chat_id):
        """Delete a chat from the database."""
        try:
            await self.db.chats.delete_one({"chat_id": chat_id})
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to delete chat {chat_id}: {e}")
            raise
