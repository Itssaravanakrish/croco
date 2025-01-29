from typing import Union
from motor.motor_asyncio import AsyncIOMotorCollection
from . import database

collection: AsyncIOMotorCollection = database.users

async def get(user_id: int) -> Union[dict, bool]:
    try:
        return await collection.find_one({'user_id': user_id}) or False
    except Exception as e:
        print(f"Error retrieving user data: {e}")
        return False

async def update(chat_id: int, user_id: int, firstname: str, username: Union[str, None]) -> bool:
    try:
        chat_id = str(chat_id)
        find = await get(user_id)
        if not find:
            await collection.insert_one({
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
            await collection.update_one({
                'user_id': user_id
            }, {
                '$set': {
                    'firstname': firstname,
                    'username': username,
                    'scores': scores,
                },
            })
        return True
    except Exception as e:
        print(f"Error updating user data: {e}")
        return False

async def total_scores(user_id: int) -> Union[int, bool]:
    user = await get(user_id)
    if not user or 'scores' not in user:
        return 0
    return sum([user['scores'][chat_id] for chat_id in user['scores']])

async def scores_in_chat(chat_id: int, user_id: int) -> Union[int, bool]:
    chat_id = str(chat_id)
    user = await get(user_id)
    if not user or 'scores' not in user or chat_id not in user['scores']:
        return 0
    return user['scores'][chat_id]

async def top_ten() -> Union[list, bool]:
    try:
        find = await collection.find().to_list(None)
        if not find:
            return False
        _all = []
        for item in find:
            _all.append({
                'user_id': item['user_id'],
                'firstname': item['firstname'],
                'username': item['username'],
                'scores': await total_scores(item['user_id']),
            })
        return sorted(_all, key=lambda x: x['scores'])[:10]
    except Exception as e:
        print(f"Error retrieving top ten users: {e}")
        return False
