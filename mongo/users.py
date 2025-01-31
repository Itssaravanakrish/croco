# users.py

from typing import Union, List
from motor.motor_asyncio import AsyncIOMotorCollection
import logging

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
