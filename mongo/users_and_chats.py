import logging
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from config import MONGO_URI, MONGO_DB_NAME
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
import pyrogram

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
        self.games_collection: AsyncIOMotorCollection = self.database.games  # Collection for games
        logging.info(f"Connected to MongoDB at {uri}, database: {database_name}")

    async def connect(self):
        """Establish a connection to the MongoDB database."""
        if self.client is None:
            raise DatabaseConnectionError("Database connection is not established.")

    async def close(self) -> None:
        """Close the database connection."""
        self.client.close()
        logging.info("Database connection closed.")

    async def handle_db_error(self, action: str, identifier: str, e: Exception):
        """Handle database errors by logging and raising exceptions."""
        logging.error(f"Failed to {action} for {identifier}: {e}")
        raise DatabaseConnectionError(f"Failed to {action} for {identifier}: {e}")

    # User management methods
    async def add_user(self, user_id: str, user_data: Dict[str, Any]) -> None:
        """Add a user to the database if they do not already exist."""
        existing_user = await self.users_collection.find_one({"user_id": user_id})
        if existing_user:
            logging.info(f"User  {user_id} already exists in the database. Skipping addition.")
            return  # User already exists, do not add again
        
        user = {"user_id": user_id, **user_data}
        try:
            await self.users_collection.insert_one(user)
            logging.info(f"User  {user_id} added to the database.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("add user", user_id, e)

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        user = await self.users_collection.find_one({"user_id": user_id})
        if user is None:
            raise UserNotFoundError(f"User  with ID {user_id} not found.")
        return user

    # Chat management methods
    async def add_chat(self, chat_id: str, chat_data: Dict[str, Any]) -> None:
        """Add a chat to the database if it does not already exist."""
        existing_chat = await self.chats_collection.find_one({"chat_id": chat_id})
        if existing_chat:
            logging.info(f"Chat {chat_id} already exists in the database. Skipping addition.")
            return  # Chat already exists, do not add again
        
        chat = {"chat_id": chat_id, **chat_data}
        try:
            await self.chats_collection.insert_one(chat)
            logging.info(f"Chat {chat_id} added to the database.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("add chat", chat_id, e)

    async def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        chat = await self.chats_collection.find_one({"chat_id": chat_id})
        if chat is None:
            raise ChatNotFoundError(f"Chat with ID {chat_id} not found.")
        return chat

    async def update_chat(self, chat_id: str, chat_title: str) -> None:
        """Update chat information."""
        await self.chats_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"title": chat_title}},
            upsert=True
        )

    # Group language management methods
    async def set_group_language(self, chat_id: str, language: str) -> None:
        """Set the language for a specific chat."""
        await self.chats_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"language": language}},
            upsert=True
        )
        logging.info(f"Chat {chat_id} language set to {language}.")

    async def get_group_language(self, chat_id: str) -> str:
        """Get the language for a specific chat."""
        chat = await self.get_chat(chat_id)
        return chat.get("language", "en")  # Default to English if not set

    # Group game mode management methods
    async def set_group_game_mode(self, chat_id: str, game_mode: str) -> None:
        """Set the game mode for a specific chat."""
        await self.chats_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"game_mode": game_mode}},
            upsert=True
        )
        logging.info(f"Chat {chat_id} game mode set to {game_mode}.")

    async def get_group_game_mode(self, chat_id: str) -> str:
        """Get the game mode for a specific chat."""
        chat = await self.get_chat(chat_id)
        return chat.get("game_mode", "easy")  # Default to easy if not set

# Create a database instance
db = Database(MONGO_URI, MONGO_DB_NAME)
