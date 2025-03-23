import logging
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatMemberUpdated  # Correct import for pyrogram types
from pyrogram import Client, filters
from mongo.users_and_chats import db  # Replace with your actual module path
from utils import get_message, register_user, register_chat, is_user_admin  # Replace with your actual module path
from script import Language  # Replace with your actual module path
from words import get_word_list, choice  # Import from words.py

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

CMD = ["/", "."]

# Inline keyboard for both private and group messages
inline_keyboard_markup = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "Add Me to Your Group 👥",
                url="https://t.me/Crocodile_game_enBot?startgroup=true",
            )
        ],
        [InlineKeyboardButton("Support Our Group 💖", url="https://t.me/TownBus")],
        [InlineKeyboardButton("Close ❌", callback_data="close_settings")],
    ]
)

# Inline keyboard for settings
settings_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Change Language 🌐", callback_data="change_language")],
        [InlineKeyboardButton("Change Game Mode 🎮", callback_data="change_game_mode")],
        [InlineKeyboardButton("Close ❌", callback_data="close_settings")],
    ]
)

@Client.on_message(filters.command("start"))
async def start_command(client, message):
    logging.info(f"/start command received in {'group' if message.chat.type in ['group', 'supergroup'] else 'private chat'} chat {message.chat.id} from user {message.from_user.id}.")
    await handle_start_command(client, message)

async def handle_start_command(client, message):
    user_id = str(message.from_user.id)
    user_data = {
        "first_name": message.from_user.first_name,
        "username": message.from_user.username,
    }

    try:
        chat_id = str(message.chat.id) if message.chat.type in ["group", "supergroup"] else None
        logging.info(f"/start command received from user {user_id} in {'group' if chat_id else 'private chat'}.")

        # Register user or chat based on context
        if chat_id:
            # Group context
            group_language = await db.get_chat_language(chat_id)
            logging.info(f"Group language retrieved: {group_language}")

            # Register the chat if it hasn't been registered yet
            chat_data = {"title": message.chat.title, "type": message.chat.type.name}
            if not await register_chat(chat_id, chat_data):
                await message.reply_text(await get_message(group_language, "error_registering_chat"))
                return
            
            # Use the existing welcome message for groups
            welcome_message = await get_message(group_language, "welcome_new_group")
            if welcome_message is None:
                logging.warning(f"Welcome message not found for language: {group_language}")
                await message.reply_text("Welcome message not found.")
                return
            
            await message.reply_text(welcome_message, reply_markup=inline_keyboard_markup)

        else:  # Private chat
            # Register user
            if not await register_user(user_id, user_data):
                await message.reply_text(await get_message(Language.EN, "error_registering_user"))
                return

            # Use the existing welcome message for private chats
            welcome_message = await get_message(Language.EN, "welcome")
            await message.reply_text(welcome_message, reply_markup=inline_keyboard_markup)

    except Exception as e:
        logging.exception(f"Error in handle_start_command: {e}")
        await message.reply_text(await get_message(Language.EN, "error_processing_command"))

@Client.on_message(filters.command("settings"))
async def settings_command(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Send settings options
    await message.reply_text("Please choose an option:", reply_markup=settings_keyboard)

@Client.on_callback_query(filters.regex("change_language"))
async def change_language_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge button press

    # Create language selection keyboard
    language_keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("English 🇬🇧", callback_data="set_language_en")],
            [InlineKeyboardButton("Tamil 🇮🇳", callback_data="set_language_ta")],
            [InlineKeyboardButton("Hindi 🇮🇳", callback_data="set_language_hi")],
            [InlineKeyboardButton("Back 🔙", callback_data="back_settings")],
        ]
    )

    await callback_query.message.edit_text("Select your language:", reply_markup=language_keyboard)

@Client.on_callback_query(filters.regex("set_language_"))
async def set_language_callback(client, callback_query):
    new_language_str = callback_query.data.split("_")[-1]  # Get language as string
    chat_id = callback_query.message.chat.id

    try:
        await db.set_chat_language(chat_id, new_language_str)  # Store language as string in DB
        await callback_query.answer(f"Language changed to {new_language_str.upper()}!", show_alert=True)
    except Exception as e:
        logging.exception(f"Error setting language: {e}")
        await callback_query.answer("An error occurred while setting the language. Please try again.", show_alert=True)

@Client.on_callback_query(filters.regex("change_game_mode"))
async def change_game_mode_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge button press

    # Create game mode selection keyboard
    game_mode_keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Easy 😌", callback_data="set_game_mode_easy")],
            [InlineKeyboardButton("Hard 😤", callback_data="set_game_mode_hard")],
            [InlineKeyboardButton("Adult 🔞", callback_data="set_game_mode_adult")],
            [InlineKeyboardButton("Back 🔙", callback_data="back_settings")],
        ]
    )

    await callback_query.message.edit_text("Select your game mode:", reply_markup=game_mode_keyboard)

@Client.on_callback_query(filters.regex("set_game_mode_"))
async def set_game_mode_callback(client, callback_query):
    new_game_mode_str = callback_query.data.split("_")[-1]  # Get the mode string (e.g., "easy")
    chat_id = callback_query.message.chat.id

    try:
        await db.set_group_game_mode(chat_id, [new_game_mode_str])  # Store as a list in DB
        await callback_query.answer(f"Game mode changed to {new_game_mode_str.capitalize()}!", show_alert=True)
    except Exception as e:
        logging.exception(f"Error setting game mode: {e}")
        await callback_query.answer("An error occurred while setting the game mode. Please try again.", show_alert=True)

@Client.on_callback_query(filters.regex("back_"))
async def back_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge button press
    await settings_command(client, callback_query.message)  # Go back to settings options

@Client.on_callback_query(filters.regex("close_settings"))
async def close_settings_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge button press
    await callback_query.message.edit_reply_markup(reply_markup=None)  # Remove the reply markup
