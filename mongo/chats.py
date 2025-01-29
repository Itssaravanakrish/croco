from typing import Union
from motor.motor_asyncio import AsyncIOMotorCollection
from . import database

collection: AsyncIOMotorCollection = database.chats

async def get(chat_id: int) -> Union[dict, bool]:
    try:
        return await collection.find_one({'chat_id': chat_id}) or False
    except Exception as e:
        raise ValueError(f"Error retrieving chat data: {e}")

async def update(chat_id: int, title: str) -> bool:
    try:
        find = await get(chat_id)
        if not find:
            await collection.insert_one({
                'chat_id': chat_id,
                'title': title,
                'games': 1,
            })
        else:
            await collection.update_one({
                'chat_id': chat_id
            }, {
                '$set': {
                    'title': title,
                    'games': find['games'] + 1,
                },
            })
        return True
    except Exception as e:
        raise ValueError(f"Error updating chat data: {e}")

async def top_ten() -> Union[list, bool]:
    try:
        pipeline = [
            {'$sort': {'games': -1}},
            {'$limit': 10},
            {'$project': {'_id': 0, 'chat_id': 1, 'games': 1}}
        ]
        result = await collection.aggregate(pipeline).to_list(None)
        return result
    except Exception as e:
        raise ValueError(f"Error retrieving top ten chats: {e}")
