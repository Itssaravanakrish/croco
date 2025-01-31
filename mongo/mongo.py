import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
from config import MONGO_URI, MONGO_DB_NAME

class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors."""
    pass

class MongoDB:
    def __init__(self):
        self.client = None
        self.database = None

    async def connect(self):
        """Establish a connection to the MongoDB database."""
        if self.client is None:
            try:
                self.client = AsyncIOMotorClient(MONGO_URI)
                self.database = self.client[MONGO_DB_NAME]
                logging.info(f"Connected to MongoDB at {MONGO_URI}, database: {MONGO_DB_NAME}")
            except (ServerSelectionTimeoutError, ConfigurationError) as e:
                logging.error(f"Failed to connect to MongoDB: {e}")
                raise

    def get_database(self):
        """Get the database instance."""
        if self.database is None:
            raise DatabaseConnectionError("Database connection is not established.")
        return self.database

    async def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        await self.connect()  # Ensure the connection is established
        try:
            return self.database[collection_name]
        except Exception as e:
            logging.error(f"Error retrieving collection {collection_name}: {e}")
            raise

    async def close(self):
        """Close the connection to the MongoDB database."""
        if self.client:
            self.client.close()
            self.client = None  # Reset client to None after closing
            logging.info("MongoDB connection closed.")
