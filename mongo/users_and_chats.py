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

    # For broadcast collection
    async def get_all_user_ids(self) -> list:
        """Fetch all user IDs from the users collection."""
        users = await self.users_collection.find({}, {'user_id': 1}).to_list(length=None)
        return [user['user_id'] for user in users]

    async def get_all_group_ids(self) -> list:
        """Fetch all group IDs from the chats collection."""
        groups = await self.chats_collection.find({}, {'chat_id': 1}).to_list(length=None)
        return [group['chat_id'] for group in groups]
        
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
        
    async def set_user_language(self, user_id: str, language: str) -> None:
        """Set the user's preferred language."""
        await self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"language": language}},
            upsert=True
        )
        logging.info(f"User  {user_id} language set to {language}.")

    async def get_user_language(self, user_id: str) -> str:
        """Get the user's preferred language."""
        user = await self.get_user(user_id)
        return user.get("language", "en")  # Default to English if not set
    
    async def total_scores(self, user_id: str) -> int:
        """Calculate total scores for the user."""
        # Implement your logic to calculate total scores here
        return 0  # Placeholder return value

    async def scores_in_chat(self, chat_id: str, user_id: str) -> int:
        """Calculate scores in a specific chat for the user."""
        # Implement your logic to calculate scores in a specific chat here
        return 0  # Placeholder return value

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

    # Game management methods
    async def set_game(self, chat_id: str, game_data: Dict[str, Any]) -> None:
        """Set the game state for a chat."""
        if 'host' in game_data and isinstance(game_data['host'], pyrogram.types.User):
            game_data['host'] = {
                'id': game_data['host'].id,
                'first_name': game_data['host'].first_name,
                'username': game_data['host'].username,
            }
        
        await self.games_collection.update_one(
            {"chat_id": chat_id},
            {"$set": game_data},
            upsert=True
        )

    async def get_game(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get the game state for a chat."""
        game = await self.games_collection.find_one({"chat_id": chat_id})
        return game

    async def delete_game(self, chat_id: str) -> None:
        """Delete the game state for a chat."""
        await self.games_collection.delete_one({"chat_id": chat_id})

    async def get_user_count(self) -> int:
        """Get the total number of users."""
        return await self.users_collection.count_documents({})

    async def get_chat_count(self) -> int:
        """Get the total number of chats."""
        return await self.chats_collection.count_documents({})

    async def get_game_count(self) -> int:
        """Get the total number of games played (if applicable)."""
        return await self.games_collection.count_documents({})

# Create a database instance
db = Database(MONGO_URI, MONGO_DB_NAME)
