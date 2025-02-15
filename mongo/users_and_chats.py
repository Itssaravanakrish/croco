# mongo/users_and_chats.py
import logging
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from config import MONGO_URI, MONGO_DB_NAME  # Ensure this file exists with your MongoDB URI
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
from pymongo.results import UpdateResult  # Import UpdateResult

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
        self.games_collection: AsyncIOMotorCollection = self.database.games
        logging.info(f"MongoDB client initialized at {uri}, database: {database_name}")

    async def connect(self):
        try:
            await self.client.admin.command('ping')  # Try to ping the server
            logging.info(f"Successfully connected to MongoDB at {MONGO_URI}, database: {MONGO_DB_NAME}")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            raise DatabaseConnectionError(f"Failed to connect to MongoDB: {e}")

    async def close(self) -> None:
        self.client.close()
        logging.info("Database connection closed.")

    async def handle_db_error(self, action: str, identifier: str, e: Exception, query: Optional[Dict] = None):
        log_message = f"Failed to {action} for {identifier}: {e}"
        if query:
            log_message += f" (Query: {query})"
        logging.error(log_message, exc_info=e)  # Include the original exception
        raise DatabaseConnectionError(log_message)

    # User management methods
    async def add_user(self, user_id: str, user_data: Dict[str, Any]) -> None:
        existing_user = await self.users_collection.find_one({"user_id": user_id})
        if existing_user:
            logging.info(f"User {user_id} already exists in the database. Skipping addition.")
            return

        user = {"user_id": user_id, **user_data}
        try:
            await self.users_collection.insert_one(user)
            logging.info(f"User {user_id} added to the database.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("add user", user_id, e)

    async def get_user(self, user_id: str) -> dict:  # More common type hint
        user = await self.users_collection.find_one({"user_id": user_id})
        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found.")
        return user

    # Game management methods
    async def set_game(self, chat_id: str, game_data: Dict[str, Any]) -> None:
        try:
            await self.games_collection.update_one(
                {"chat_id": chat_id},
                {"$set": game_data},
                upsert=True
            )
            logging.info(f"Game for chat {chat_id} has been set/updated.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("set game", chat_id, e)

    async def get_game(self, chat_id: str) -> Optional[dict]:  # More precise return type
        try:
            game = await self.games_collection.find_one({"chat_id": chat_id})
            return game
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to get game for {chat_id}: {e}")  # Log the error
            return None  # Return None on error

    async def remove_game(self, chat_id: str) -> None:
        try:
            await self.games_collection.delete_one({"chat_id": chat_id})
            logging.info(f"Game for chat {chat_id} has been removed.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("remove game", chat_id, e)

    async def update_game(self, chat_id: str, update_data: Dict[str, Any]) -> UpdateResult:  # Specific return type
        try:
            result = await self.games_collection.update_one(
                {"chat_id": chat_id},
                {"$set": update_data}
            )
            return result
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("update game", chat_id, e)

    # Chat management methods
    async def add_chat(self, chat_id: str, chat_data: Dict[str, Any]) -> None:
        existing_chat = await self.chats_collection.find_one({"chat_id": chat_id})
        if existing_chat:
            logging.info(f"Chat {chat_id} already exists in the database. Skipping addition.")
            return

        chat = {"chat_id": chat_id, **chat_data}
        try:
            await self.chats_collection.insert_one(chat)
            logging.info(f"Chat {chat_id} added to the database.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("add chat", chat_id, e)

    async def get_chat(self, chat_id: str) -> Optional[dict]:  # Consistent return type
        try:
            chat = await self.chats_collection.find_one({"chat_id": chat_id})
            return chat
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("get chat", chat_id, e)

    async def update_chat(self, chat_id: str, chat_title: str) -> None:
        try:
            await self.chats_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"title": chat_title}},
                upsert=True
            )
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("update chat", chat_id, e)

    # Group language management methods
    async def set_chat_language(self, chat_id: str, language: str) -> None:  # Correct Name
        try:
            await self.chats_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"language": language}},
                upsert=True
            )
            logging.info(f"Chat {chat_id} language set to {language}.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("set language", chat_id, e)

    async def get_chat_language(self, chat_id: str) -> str:  # Correct Name
        chat = await self.get_chat(chat_id)
        return chat.get("language", "en")

    # Group game mode management methods
    async def set_group_game_mode(self, chat_id: str, game_mode: str) -> None:
        try:
            await self.chats_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"game_mode": game_mode}},
                upsert=True
            )
            logging.info(f"Chat {chat_id} game mode set to {game_mode}.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("set game mode", chat_id, e)

    async def get_group_game_mode(self, chat_id: str) -> str:
        chat = await self.get_chat(chat_id)
        return chat.get("game_mode", "easy")

# Create a database instance (but don't connect yet)
db = Database(MONGO_URI, MONGO_DB_NAME)
