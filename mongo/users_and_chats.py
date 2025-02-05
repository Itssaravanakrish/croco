# mongo/users_and_chats.py

import logging
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from config import MONGO_URI, MONGO_DB_NAME
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
import pyrogram
import asyncio

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
        user = {"user_id": user_id, **user_data}
        try:
            await self.users_collection.insert_one(user)
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to add user {user_id}: {e}")
            raise

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        user = await self.users_collection.find_one({"user_id": user_id})
        if user is None:
            raise UserNotFoundError(f"User  with ID {user_id} not found.")
        return user

    async def total_scores(self, user_id: str) -> int:
        # Implement logic to calculate total scores for the user
        pass

    async def scores_in_chat(self, chat_id: str, user_id: str) -> int:
        # Implement logic to calculate scores in a specific chat for the user
        pass

    # Chat management methods
    async def add_chat(self, chat_id: str, chat_data: Dict[str, Any]) -> None:
        chat = {"chat_id": chat_id, **chat_data}
        try:
            await self.chats_collection.insert_one(chat)
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to add chat {chat_id}: {e}")
            raise

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
        # Convert the host User object to a dictionary
        if 'host' in game_data and isinstance(game_data['host'], pyrogram.types.User):
            game_data['host'] = {
                'id': game_data['host'].id,
                'first_name': game_data['host'].first_name,
                'username': game_data['host'].username,
                # Add any other fields you want to store
            }
        
        await self.games_collection.update_one(
            {"chat_id": chat_id},
            {"$set": game_data},
            upsert=True  # Create a new document if it doesn't exist
        )

    async def get_game(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get the game state for a chat."""
        game = await self.games_collection.find_one({"chat_id": chat_id})
        return game

    async def delete_game(self, chat_id: str) -> None:
        """Delete the game state for a chat."""
        await self.games_collection.delete_one({"chat_id": chat_id})

# Create a database instance
db = Database(MONGO_URI, MONGO_DB_NAME)
