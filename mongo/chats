# chats.py

from typing import Union, List
from motor.motor_asyncio import AsyncIOMotorCollection
import logging

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

    async def update(self, chat_id: int, title: str) ```python
        """Update chat data or insert a new chat if it doesn't exist."""
        try:
            find = await self.get(chat_id)
            if not find:
                await self.collection.insert_one({
                    'chat_id': chat_id,
                    'title': title,
                    'games': 1,
                })
            else:
                await self.collection.update_one(
                    {'chat_id': chat_id},
                    {'$set': {
                        'title': title,
                        'games': find['games'] + 1,
                    }},
                )
            return True
        except Exception as e:
            logging.error(f"Error updating chat data: {e}")
            raise ValueError(f"Error updating chat data: {e}")

    async def top_ten(self) -> Union[List[dict], bool]:
        """Retrieve the top ten chats based on the number of games played."""
        try:
            pipeline = [
                {'$sort': {'games': -1}},
                {'$limit': 10},
                {'$project': {'_id': 0, 'chat_id': 1, 'games': 1}}
            ]
            result = await self.collection.aggregate(pipeline).to_list(None)
            return result
        except Exception as e:
            logging.error(f"Error retrieving top ten chats: {e}")
            raise ValueError(f"Error retrieving top ten chats: {e}")

