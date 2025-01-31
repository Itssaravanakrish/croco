import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError  # Updated import
from config import MONGO_URI, MONGO_DB_NAME

class MongoDB:
    def __init__(self):
        self.client = None
        self.database = None
        self.connect()

    def connect(self):
        """Establish a connection to the MongoDB database."""
        try:
            self.client = AsyncIOMotorClient(MONGO_URI)
            self.database = self.client[MONGO_DB_NAME]
            logging.info(f"Connected to MongoDB at {MONGO_URI}, database: {MONGO_DB_NAME}")
        except (ServerSelectionTimeoutError, ConfigurationError) as e:  # Updated exception handling
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise

    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        if self.database:
            return self.database[collection_name]
        else:
            logging.error("Database connection is not established.")
            raise Exception("Database connection is not established.")
