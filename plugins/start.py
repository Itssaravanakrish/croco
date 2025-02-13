from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from mongo.users_and_chats import db
from utils import get_message, register_user, register_chat

CMD = ["/", "."]

# Inline keyboard for private messages
inline_keyboard_markup_pm = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Add Me to Your Group 👥", url="https://t.me/Crocodile_game_enBot?startgroup=invite")],
        [InlineKeyboardButton("Support Our Group 💖", url="https://t.me/Xtamilchat")]
    ]
)

@Client.on_message(filters.group & filters.command("start", CMD))
async def start_group(client: Client, message: Message):
    user_id = str(message.from_user.id)
    user_data = {
        "first_name": message.from_user.first_name,
        "username": message.from_user.username,
    }

    # Register user
    if not await register_user(user_id, user_data):
        await message.reply_text(get_message("en", "error_registering_user"))  # Default to English
        return

    chat_id = str(message.chat.id)
    chat_data = {
        "title": message.chat.title,
        "type": message.chat.type.name,
    }

    # Register chat
    if not await register_chat(chat_id, chat_data):
        await message.reply_text(get_message("en", "error_registering_chat"))  # Default to English
        return

    # Determine the user's preferred language
    user_language = await db.get_user_language(user_id)  # Fetch the user's language preference
    language = get_user_language(user_language)  # Ensure valid language

    await message.reply_text(
        get_message(language, "welcome"),  # Use the user's preferred language
        reply_markup=inline_keyboard_markup_pm
    )
@Client.on_message(filters.private & filters.command("start", CMD))
async def start_private(client: Client, message: Message):
    user_id = str(message.from_user.id)
    user_data = {
        "first_name": message.from_user.first_name,
        "username": message.from_user.username,
    }

    # Register user
    if not await register_user(user_id, user_data):
        await message.reply_text(get_message("en", "error_registering_user"))  # Default to English
        return

    # Determine the user's preferred language
    user_language = await db.get_user_language(user_id)  # Fetch the user's language preference
    language = get_user_language(user_language)  # Ensure valid language

    await message.reply_text(
        get_message(language, "welcome"),  # Use the user's preferred language
        reply_markup=inline_keyboard_markup_pm
    )
