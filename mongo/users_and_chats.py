import logging
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from config import MONGO_URI, MONGO_DB_NAME
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
from pymongo.results import UpdateResult

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

    async def connect(self) -> None:
        """Connect to the MongoDB database."""
        try:
            await self.client.admin.command('ping')
            logging.info(f"Successfully connected to MongoDB at {MONGO_URI}, database: {MONGO_DB_NAME}")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            raise DatabaseConnectionError(f"Failed to connect to MongoDB: {e}")

    async def close(self) -> None:
        """Close the database connection."""
        await self.client.close()  # Ensure to await the close operation
        logging.info("Database connection closed.")

    async def initialize_database(self) -> None:
        """Initialize the database by creating a default user or chat if none exist."""
        # Check if any users exist
        user_count = await self.users_collection.count_documents({})
        if user_count == 0:
            default_user = {
                "user_id": "default_user",
                "name": "Default User",
                "score": 0,
                "coins": 0,
                "xp": 0
            }
            await self.users_collection.insert_one(default_user)
            logging.info("Default user created in the database.")

        # Check if any chats exist
        chat_count = await self.chats_collection.count_documents({})
        if chat_count == 0:
            default_chat = {
                "chat_id": "default_chat",
                "title": "Default Chat",
                "language": "en",
                "game_mode": ["easy"]
            }
            await self.chats_collection.insert_one(default_chat)
            logging.info("Default chat created in the database.")

    async def get_user_count(self) -> int:
        """Retrieve the count of users in the database."""
        try:
            count = await self.users_collection.count_documents({})
            logging.info(f"Total users count: {count}")
            return count
        except Exception as e:
            logging.error(f"Error getting user count: {e}")
            return 0  # Return 0 if there's an error

    async def get_chat_count(self) -> int:
        """Retrieve the count of chats in the database."""
        try:
            count = await self.chats_collection.count_documents({})
            logging.info(f"Total chats count: {count}")
            return count
        except Exception as e:
            logging.error(f"Error getting chat count: {e}")
            return 0  # Return 0 if there's an error

    async def get_game_count(self) -> int:
        """Retrieve the count of games in the database."""
        try:
            count = await self.games_collection.count_documents({})
            logging.info(f"Total games count: {count}")
            return count
        except Exception as e:
            logging.error(f"Error getting game count: {e}")
            return 0  # Return 0 if there's an error

    async def handle_db_error(self, action: str, identifier: str, e: Exception, query: Optional[Dict] = None) -> None:
        """Handle database errors by logging and raising a custom exception."""
        log_message = f"Failed to {action} for {identifier}: {e}"
        if query:
            log_message += f" (Query: {query})"
        logging.error(log_message, exc_info=e)
        raise DatabaseConnectionError(log_message)

    # User management methods
    async def add_user(self, user_id: str, user_data: Dict[str, Any]) -> None:
        """Add a new user to the database."""
        existing_user = await self.users_collection.find_one({"user_id": user_id})
        if existing_user:
            logging.info(f"User  {user_id} already exists in the database. Skipping addition.")
            return

        user = {"user_id": user_id, **user_data}
        try:
            await self.users_collection.insert_one(user)
            logging.info(f"User  {user_id} added to the database.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("add user", user_id, e)

    async def get_user(self, user_id: str) -> dict:
        """Retrieve a user from the database by user ID."""
        user = await self.users_collection.find_one({"user_id": user_id})
        if user is None:
            raise UserNotFoundError(f"User  with ID {user_id} not found.")
        return user

    # Game management methods
    async def set_game(self, chat_id: str, game_data: Dict[str, Any]) -> None:
        """Set or update the game data for a specific chat."""
        try:
            await self.games_collection.update_one(
                {"chat_id": chat_id},
                {"$set": game_data},
                upsert=True
            )
            logging.info(f"Game for chat {chat_id} has been set/updated.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("set game", chat_id, e)

    async def get_game(self, chat_id: str) -> Optional[dict]:
        """Retrieve the game data for a specific chat."""
        try:
            game = await self.games_collection.find_one({"chat_id": chat_id})
            return game
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            logging.error(f"Failed to get game for {chat_id}: {e}")
            return None

    async def remove_game(self, chat_id: str) -> None:
        """Remove the game data for a specific chat."""
        try:
            await self.games_collection.delete_one({"chat_id": chat_id})
            logging.info(f"Game for chat {chat_id} has been removed.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("remove game", chat_id, e)

    async def update_game(self, chat_id: str, update_data: Dict[str, Any]) -> UpdateResult:
        """Update the game data for a specific chat."""
        try:
            result = await self.games_collection.update_one(
                {"chat_id": chat_id},
                {"$set": update_data}
            )
            return result
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("update game", chat_id, e)
            raise
        except Exception as e:
            logging.error(f"Error in update_game: {e}")
            raise

    # Chat management methods
    async def add_chat(self, chat_id: str, chat_data: Dict[str, Any]) -> None:
        """Add a new chat to the database."""
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

    async def get_chat(self, chat_id: str) -> Optional[dict]:
        """Retrieve a chat from the database by chat ID."""
        try:
            chat = await self.chats_collection.find_one({"chat_id": chat_id})
            return chat
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("get chat", chat_id, e)
            return None
        except Exception as e:
            logging.error(f"Error in get_chat: {e}")
            return None

    async def update_chat(self, chat_id: str, chat_title: str) -> None:
        """Update the title of a chat."""
        try:
            await self.chats_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"title": chat_title}},
                upsert=True
            )
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("update chat", chat_id, e)

    # User score management methods
    async def add_user_score(self, chat_id: str, user_id: str, score: int, coins: int, xp: int) -> None:
        """Add a new user score entry to the database."""
        user_score = {
            "chat_id": chat_id,
            "user_id": user_id,
            "score": score,
            "coins": coins,
            "xp": xp
        }
        try:
            await self.users_collection.insert_one(user_score)
            logging.info(f"User   {user_id} score added to chat {chat_id}.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("add user score", user_id, e)

    async def get_user_score(self, chat_id: str, user_id: str) -> Optional[dict]:
        """Retrieve a user's score, coins, and XP from the database."""
        user_score = await self.users_collection.find_one({"chat_id": chat_id, "user_id": user_id})
        if user_score is None:
            raise UserNotFoundError(f"User    {user_id} not found in chat {chat_id}.")
        return user_score

    async def update_user_score(self, chat_id: str, user_id: str, score: int, coins: int, xp: int) -> None:
        """Update the user's score, coins, and XP in the database."""
        try:
            await self.users_collection.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$set": {
                    "score": score,
                    "coins": coins,
                    "xp": xp
                }},
                upsert=True  # Create a new entry if it doesn't exist
            )
            logging.info(f"User    {user_id} score updated in chat {chat_id}.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("update user score", user_id, e)

    async def increment_user_score(self, chat_id: str, user_id: str, score: int, coins: int, xp: int) -> None:
        """Increment the user's score, coins, and XP in the database."""
        user_score = await self.get_user_score(chat_id, user_id)

        new_score = user_score['score'] + score
        new_coins = user_score['coins'] + coins
        new_xp = user_score['xp'] + xp

        await self.update_user_score(chat_id, user_id, new_score, new_coins, new_xp)

    async def get_top_users(self, chat_id: str, limit: int = 10) -> List[dict]:
        """Retrieve the top users based on their scores in a specific chat."""
        top_users = await self.users_collection.find({"chat_id": chat_id}).sort("score", -1).limit(limit).to_list()
        return top_users
        
    # Group language management methods
    async def set_chat_language(self, chat_id: str, language: str) -> None:
        """Set the language for a specific chat."""
        try:
            await self.chats_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"language": language}},
                upsert=True
            )
            logging.info(f"Chat {chat_id} language set to {language}.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("set language", chat_id, e)

    async def get_chat_language(self, chat_id: str) -> str:
        """Get the language for a specific chat."""
        chat = await self.get_chat(chat_id)
        if chat:
            return chat.get("language", "en")
        else:
            return "en"

    # Group game mode management methods
    async def set_group_game_mode(self, chat_id: str, game_modes: List[str]) -> None:
        """Set the game mode for a specific chat."""
        try:
            await self.chats_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"game_mode": game_modes}},  # Store as a LIST
                upsert=True
            )
            logging.info(f"Chat {chat_id} game mode set to {game_modes}.")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            await self.handle_db_error("set game mode", chat_id, e)

    async def get_group_game_mode(self, chat_id: str) -> List[str]:
        """Get the game mode for a specific chat."""
        chat = await self.get_chat(chat_id)
        if chat:
            return chat.get("game_mode", ["easy"])  # Default is a LIST: ["easy"]
        else:
            return ["easy"]  # Return a LIST

# Create a database instance (but don't connect yet)
db = Database(MONGO_URI, MONGO_DB_NAME)
