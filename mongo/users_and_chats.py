import logging
from typing import Union, List
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorClient
from pymongo.errors import ConnectionError, ConfigurationError
from config import MONGO_URI, MONGO_DB_NAME

# MongoDB connection setup
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

    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get a collection from the database."""
        if self.database:
            return self.database[collection_name]
        else:
            logging.error("Database connection is not established.")
            raise Exception("Database connection is not established.")

# Users class
class Users:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def get(self, user_id: int) -> Union[dict, bool]:
        """Retrieve user data by user_id."""
        try:
            return await self.collection.find_one({'user_id': user_id}) or False
        except Exception as e:
            logging.error(f"Error retrieving user data: {e}")
            raise ValueError(f"Error retrieving user data: {e}")

    async def update(self, chat_id: int, user_id: int, firstname: str, username: Union[str, None]) -> bool:
        """Update user data or insert a new user if they don't exist."""
        try:
            chat_id = str(chat_id)
            find = await self.get(user_id)
            if not find:
                await self.collection.insert_one({
                    'user_id': user_id,
                    'firstname': firstname,
                    'username': username,
                    'scores': {chat_id: 1},
                })
            else:
                scores = find['scores']
                if chat_id not in scores:
                    scores[chat_id] = 1
                else:
                    scores[chat_id] += 1
                await self.collection.update_one(
                    {'user_id': user_id},
                    {'$set': {
                        'firstname': firstname,
                        'username': username,
                        'scores': scores,
                    }},
                )
            return True
        except Exception as e:
            logging.error(f"Error updating user data: {e}")
            raise ValueError(f"Error updating user data: {e}")

    async def total_scores(self, user_id: int) -> Union[int, bool]:
        """Calculate the total scores for a user."""
        user = await self.get(user_id)
        if not user or 'scores' not in user:
            return 0
        return sum(user['scores'].values())

    async def scores_in_chat(self, chat_id: int, user_id: int) -> Union[int, bool]:
        """Retrieve the scores of a user in a specific chat."""
        chat_id = str(chat_id)
        user = await self.get(user_id)
        if not user or 'scores' not in user or chat_id not in user['scores']:
            return 0
        return user['scores'][chat_id]

    async def top_ten(self) -> Union[List[dict], bool]:
        """Retrieve the top ten users based on their scores."""
        try:
            pipeline = [
                {'$unwind': '$scores'},
                {'$group': {'_id': '$user_id', 'scores': {'$sum': '$scores'}}},
                {'$sort': {'scores': -1}},
                {'$limit': 10}
            ]
            result = await self.collection.aggregate(pipeline).to_list(None)
            return [{'user_id': item['_id'], 'scores': item['scores']} for item in result]
        except Exception as e:
            logging.error(f"Error retrieving top ten users: {e}")
            raise ValueError(f"Error retrieving top ten users: {e}")

# Chats class
class Chats:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def get(self, chat_id: int) -> Union[dict, bool]:
        """Retrieve chat data by chat_id."""
        try:
            return await self.collection.find_one({'chat_id': chat_id}) or False
        except Exception as e:
            logging.error(f"Error retrieving chat data: {e}")
            raise ValueError(f"Error retrieving chat data: {e}")

    async def update(self, chat_id: int, title: str) -> bool:
        """Update chat data or insert a new chat if it doesn't exist."""
        try:
            find = await self.get(chat_id)
            if not find:
                await self.collection.insert_one({
                    'chat_id': chat_id,
                    'title': title,
                })
            else:
                await self.collection.update_one(
                    {'chat_id': chat_id},
                    {'$set': {'title': title}},
                )
            return True
        except Exception as e:
            logging.error(f"Error updating chat data: {e}")
            raise ValueError(f"Error updating chat data: {e}")

    async def top_ten(self) -> Union[List[dict], bool]:
        """Retrieve the top ten chats based on some criteria."""
        try:
            # Assuming we have a 'scores' field to determine top chats
            pipeline = [
                {'$sort': {'scores': -1}},
                {'$limit': 10}
            ]
            result = await self.collection.aggregate(pipeline).to_list(None)
            return [{'chat_id': item['chat_id'], 'title': item['title']} for item in result]
        except Exception as e:
            logging.error(f"Error retrieving top ten chats: {e}")
            raise ValueError(f"Error retrieving top ten chats: {e}")

# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        mongo_db = MongoDB(MONGO_URI, MONGO_DB_NAME)
        users_collection = Users(mongo_db.get_collection("users"))
        chats_collection = Chats(mongo_db.get_collection("chats"))

        # Example user and chat data
        await users_collection.update(1, 123456, "Alice", "alice_wonderland")
        await chats_collection.update(1, "General Chat")

        # Fetching data
        user_data = await users_collection.get(123456)
        chat_data = await chats_collection.get(1)

        print(f"User  Data: {user_data}")
        print(f"Chat Data: {chat_data}")

    asyncio.run(main())
