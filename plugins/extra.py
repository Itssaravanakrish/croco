# extra.py
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from mongo.users_and_chats import db
from config import SUDO_USERS
from utils import get_message
from script import Language  # Import Language enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

CMD = ["/", "."]

@Client.on_message(filters.command("alive", CMD))
async def alive_callback(client: Client, message: Message):
    language_str = await db.get_chat_language(message.chat.id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN
    logging.info(f"Alive command received from {message.from_user.first_name} in chat {message.chat.id}.")
    await message.reply_text(await get_message(language, "alive"))

@Client.on_message(filters.command("ping", CMD))
async def ping_callback(client: Client, message: Message):
    language_str = await db.get_chat_language(message.chat.id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN
    await message.reply_text(await get_message(language, "ping"))

@Client.on_message(filters.command("broadcast_pm", CMD) & filters.user(SUDO_USERS))
async def broadcast_pm_callback(client: Client, message: Message):
    if len(message.command) < 2:
        language = await db.get_chat_language(message.chat.id)
        await message.reply_text(await get_message(language, "provide_message"))
        return

    broadcast_message = " ".join(message.command[1:])
    user_ids = await db.get_all_user_ids()

    total_users = len(user_ids)
    success_count = 0
    fail_count = 0
    error_messages = []  # Store error messages

    for user_id in user_ids:
        try:
            await client.send_message(user_id, broadcast_message)
            success_count += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            logging.error(f"Failed to send message to user {user_id}: {e}")
            fail_count += 1
            error_messages.append(f"Failed to send to {user_id}: {e}")  # Add error details

    pending_count = total_users - (success_count + fail_count)

    language = await db.get_chat_language(message.chat.id)
    summary_message = await get_message(
        language,
        "broadcast_pm_success",
        total=total_users,
        success=success_count,
        failed=fail_count,
        pending=pending_count,
    )

    if error_messages:
        summary_message += "\n\nErrors:\n" + "\n".join(error_messages)  # Include error details

    await message.reply_text(summary_message)



@Client.on_message(filters.command("broadcast_group", CMD) & filters.user(SUDO_USERS))
async def broadcast_group_callback(client: Client, message: Message):
    if len(message.command) < 2:
        language = await db.get_chat_language(message.chat.id)
        await message.reply_text(await get_message(language, "provide_message"))
        return

    broadcast_message = " ".join(message.command[1:])
    group_ids = await db.get_all_group_ids()

    total_groups = len(group_ids)
    success_count = 0
    fail_count = 0
    error_messages = []

    for group_id in group_ids:
        try:
            await client.send_message(group_id, broadcast_message)
            success_count += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            logging.error(f"Failed to send message to group {group_id}: {e}")
            fail_count += 1
            error_messages.append(f"Failed to send to {group_id}: {e}")

    pending_count = total_groups - (success_count + fail_count)

    language = await db.get_chat_language(message.chat.id)
    summary_message = await get_message(
        language,
        "broadcast_group_success",
        total=total_groups,
        success=success_count,
        failed=fail_count,
        pending=pending_count,
    )

    if error_messages:
        summary_message += "\n\nErrors:\n" + "\n".join(error_messages)

    await message.reply_text(summary_message)



@Client.on_message(filters.command("stats", CMD) & filters.user(SUDO_USERS))
async def stats_callback(client: Client, message: Message):
    language_str = await db.get_chat_language(message.chat.id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    user_count = 0
    chat_count = 0
    game_count = 0
    error_message = None  # Initialize error message

    try:
        user_count = await db.get_user_count()
    except Exception as e:
        logging.error(f"Error getting user count: {e}")
        error_message = await get_message(Language.EN, "error_getting_user_count")  # Store the error message

    try:
        chat_count = await db.get_chat_count()
    except Exception as e:
        logging.error(f"Error getting chat count: {e}")
        if not error_message: # if there is no error message yet
            error_message = await get_message(Language.EN, "error_getting_chat_count")

    try:
        game_count = await db.get_game_count()
    except Exception as e:
        logging.error(f"Error getting game count: {e}")
        if not error_message: # if there is no error message yet
            error_message = await get_message(Language.EN, "error_getting_game_count")

    stats_message = await get_message(language, "stats", user_count=user_count, chat_count=chat_count, game_count=game_count)

    if error_message:  # Send the error message separately
        await message.reply_text(error_message)

    await message.reply_text(stats_message)  # Then send the stats message
