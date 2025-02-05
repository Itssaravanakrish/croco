from time import time
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from mongo.users_and_chats import db  # Import the database instance
from config import SUDO_USERS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

CMD = ["/", "."]

@Client.on_message(filters.command("alive", CMD))
async def alive_callback(client: Client, message: Message):
    logging.info(f"Alive command received from {message.from_user.first_name} in chat {message.chat.id}.")
    await message.reply_text("I am alive and running! 💪")

@Client.on_message(filters.command("ping", CMD))
async def ping_callback(client: Client, message: Message):
    await message.reply_text("Pong! 🏓")

@Client.on_message(filters.command("broadcast_pm", CMD) & filters.user(SUDO_USERS))
async def broadcast_pm_callback(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Please provide a message to broadcast.")
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

    await message.reply_text(
        f"Broadcast to PM completed!\n"
        f"Total Users: {total_users}\n"
        f"Success: {success_count}\n"
        f"Failed: {fail_count}\n"
        f"Pending: {pending_count}"
    )

@Client.on_message(filters.command("broadcast_group", CMD) & filters.user(SUDO_USERS))
async def broadcast_group_callback(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Please provide a message to broadcast.")
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

    await message.reply_text(
        f"Broadcast to groups completed!\n"
        f"Total Groups: {total_groups}\n"
        f"Success: {success_count}\n"
        f"Failed: {fail_count}\n"
        f"Pending: {pending_count}"
    )
