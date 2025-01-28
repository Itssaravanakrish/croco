
from typing import Union
from motor.motor_asyncio import AsyncIOMotorCollection

collection: AsyncIOMotorCollection = database.chats

async def get(chat_id: int) -> Union[dict, bool]:
    try:
        return await collection.find_one({'chat_id': chat_id}) or False
    except Exception as e:
        print(f"Error retrieving chat data: {e}")
        return False

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
        print(f"Error updating chat data: {e}")
        return False

async def top_ten() -> Union[list, bool]:
    try:
        find = await collection.find().sort('games', -1).limit(10).to_list(None)
        if not find:
            return False
        return [{'chat_id': item['chat_id'], 'games': item['games']} for item in find]
    except Exception as e:
        print(f"Error retrieving top ten chats: {e}")
        return False
