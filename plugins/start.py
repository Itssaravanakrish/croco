from time import time
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType
from words import choice
from mongo.users_and_chats import db, ChatNotFoundError, UserNotFoundError
from config import SUDO_USERS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

CMD = ["/", "."]
WELCOME_MESSAGE = "Welcome to our advanced Crocodile Game Bot! 🐊\n\nGet ready to have fun and challenge your friends!"

# Define the inline keyboard for private messages
inline_keyboard_markup_pm = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ 👥", url="https://t.me/Crocodile_game_enBot?startgroup=invite")],
        [InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ ᴏᴜʀ ɢʀᴏᴜᴘ 💖", url="https://t.me/Xtamilchat")]
    ]
)

async def register_user(user_id: str, user_data: dict):
    """Register a user in the database."""
    try:
        await db.get_user(user_id)  # Attempt to retrieve the user
        logging.info(f"User   {user_id} already exists in the database.")
    except UserNotFoundError:
        # Add the user to the database if they are not already present
        try:
            await db.add_user(user_id, user_data)  # Add user to the database
            logging.info(f"User   {user_id} added to the database.")
        except Exception as e:
            logging.error(f"Failed to add user {user_id}: {e}")
            return False
    return True

async def register_chat(chat_id: str, chat_data: dict):
    """Register a chat in the database."""
    try:
        await db.get_chat(chat_id)  # Attempt to retrieve the chat
        logging.info(f"Chat {chat_id} already exists in the database.")
    except ChatNotFoundError:
        # Add the chat to the database if it is not already present
        try:
            await db.add_chat(chat_id, chat_data)  # Add chat to the database
            logging.info(f"Chat {chat_id} added to the database.")
        except Exception as e:
            logging.error(f"Failed to add chat {chat_id}: {e}")
            return False
    return True

@Client.on_message(filters.group & filters.command("start", CMD))
async def start_group(client: Client, message: Message):
    user_id = str(message.from_user.id)
    user_data = {
        "first_name": message.from_user.first_name,
        "username": message.from_user.username,
    }

    if not await register_user(user_id, user_data):
        await message.reply_text("An error occurred while adding you to the database. Please try again later.")
        return

    chat_id = str(message.chat.id)
    chat_data = {
        "title": message.chat.title,
        "type": message.chat.type.name,  # Convert ChatType to string
    }

    if not await register_chat(chat_id, chat_data):
        await message.reply_text("An error occurred while adding the chat to the database. Please try again later.")
        return

    await message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=inline_keyboard_markup_pm  # Use the existing inline keyboard for private messages
    )

@Client.on_message(filters.private & filters.command("start", CMD))
async def start_private(client: Client, message: Message):
    user_id = str(message.from_user.id)
    user_data = {
        "first_name": message.from_user.first_name,
        "username": message.from_user.username,
    }

    if not await register_user(user_id, user_data):
        await message.reply_text("An error occurred while adding you to the database. Please try again later.")
        return

    await message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=inline_keyboard_markup_pm  # Optional: You can include an inline keyboard if needed
    )
