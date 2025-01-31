import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionError, ConfigurationError
from config import MONGO_URI, MONGO_DB_NAME

class MongoDB:
    def __init__(self, uri: str, db_name: str):
        self.client = None
        self.database = None
        self.uri = uri
        self.db_name = db_name
        self.connect()

    def connect(self):
        """Establish a connection to the MongoDB database."""
        try:
            self.client = AsyncIOMotorClient(self.uri)
            self.database = self.client[self.db_name]
            logging.info(f"Connected to MongoDB at {self.uri}, database: {self.db_name}")
        except (ConnectionError, ConfigurationError) as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise

    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        if self.database:
            return self.database[collection_name]
        else:
            logging.error("Database connection is not established.")
            raise Exception("Database connection is not established.")
