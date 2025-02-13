import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from mongo.users_and_chats import db  # Import the database instance
from config import SUDO_USERS
from utils import get_message  # Import get_message from utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

CMD = ["/", "."]

@Client.on_message(filters.command("alive", CMD))
async def alive_callback(client: Client, message: Message):
    user_id = str(message.from_user.id)
    language = await db.get_user_language(user_id)  # Fetch the user's preferred language
    logging.info(f"Alive command received from {message.from_user.first_name} in chat {message.chat.id}.")
    await message.reply_text(await get_message(language, "alive"))  # Use the user's language

@Client.on_message(filters.command("ping", CMD))
async def ping_callback(client: Client, message: Message):
    user_id = str(message.from_user.id)
    language = await db.get_user_language(user_id)  # Fetch the user's preferred language
    await message.reply_text(await get_message(language, "ping"))  # Use the user's language

@Client.on_message(filters.command("broadcast_pm", CMD) & filters.user(SUDO_USERS))
async def broadcast_pm_callback(client: Client, message: Message):
    if len(message.command) < 2:
        user_id = str(message.from_user.id)
        language = await db.get_user_language(user_id)  # Fetch the user's preferred language
        await message.reply_text(await get_message(language, "provide_message"))  # Use the user's language
        return

    broadcast_message = " ".join(message.command[1:])
    user_ids = await db.get_all_user_ids()  # Fetch user IDs from the database

    total_users = len(user_ids)
    success_count = 0
    fail_count = 0

    for user_id in user_ids:
        try:
            await client.send_message(user_id, broadcast_message)
            success_count += 1
            await asyncio.sleep(0.1)  # Adding delay to prevent hitting rate limits
        except Exception as e:
            logging.error(f"Failed to send message to user {user_id}: {e}")
            fail_count += 1

    pending_count = total_users - (success_count + fail_count)

    user_id = str(message.from_user.id)
    language = await db.get_user_language(user_id)  # Fetch the user's preferred language
    await message.reply_text(
        await get_message(language, "broadcast_pm_success", total=total_users, success=success_count, failed=fail_count, pending=pending_count)  # Use the user's language
    )

@Client.on_message(filters.command("broadcast_group", CMD) & filters.user(SUDO_USERS))
async def broadcast_group_callback(client: Client, message: Message):
    if len(message.command) < 2:
        user_id = str(message.from_user.id)
        language = await db.get_user_language(user_id)  # Fetch the user's preferred language
        await message.reply_text(await get_message(language, "provide_message"))  # Use the user's language
        return

    broadcast_message = " ".join(message.command[1:])
    group_ids = await db.get_all_group_ids()  # Fetch group IDs from the database

    total_groups = len(group_ids)
    success_count = 0
    fail_count = 0

    for group_id in group_ids:
        try:
            await client.send_message(group_id, broadcast_message)
            success_count += 1
            await asyncio.sleep(0.1)  # Adding delay to prevent hitting rate limits
        except Exception as e:
            logging.error(f"Failed to send message to group {group_id}: {e}")
            fail_count += 1

    pending_count = total_groups - (success_count + fail_count)

    user_id = str(message.from_user.id)
    language = await db.get_user_language(user_id)  # Fetch the user's preferred language
    await message.reply_text(
        await get_message(language, "broadcast_group_success", total=total_groups, success=success_count, failed=fail_count, pending=pending_count)  # Use the user's language
    )

@Client.on_message(filters.command("stats", CMD) & filters.user(SUDO_USERS))
async def stats_callback(client: Client, message: Message):
    user_id = str(message.from_user.id)
    language = await db.get_user_language(user_id)  # Fetch the user's preferred language

    user_count = await db.get_user_count()  # Get total user count
    chat_count = await db.get_chat_count()  # Get total chat count
    game_count = await db.get_game_count()  # Get total game count

    stats_message = await get_message(language, "stats", user_count=user_count, chat_count=chat_count, game_count=game_count)  # Use the user's language

    await message.reply_text(stats_message)
