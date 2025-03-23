import logging
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters
from mongo.users_and_chats import db
from utils import get_message, register_user, is_user_admin
from script import Language

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

CMD = ["/", "."]

@Client.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = str(message.from_user.id)
    user_data = {
        "first_name": message.from_user.first_name,
        "username": message.from_user.username,
    }

    try:
        chat_id = str(message.chat.id) if message.chat.type in ["group", "supergroup"] else None
        logging.info(f"/start command received from user {user_id} in {'group' if chat_id else 'private chat'}.")

        if chat_id:
            # Group context
            group_language = await db.get_chat_language(chat_id)
            welcome_message = await get_message(group_language, "welcome_new_group")
            await message.reply_text(welcome_message, reply_markup=settings_keyboard)
        else:  # Private chat
            # Register user
            if not await register_user(user_id, user_data):
                await message.reply_text(await get_message(Language.EN, "error_registering_user"))
                return

            await message.reply_text("Welcome! Use /connect to connect to a group.")

    except Exception as e:
        logging.exception(f"Error in start_command: {e}")
        await message.reply_text("An error occurred. Please try again.")

@Client.on_callback_query(filters.regex("settings"))
async def settings_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge button press

    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    # Check if the user is an admin
    is_admin = await is_user_admin(client, chat_id, user_id)

    if is_admin:
        # Create settings keyboard for admins
        settings_keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Change Language 🌐", callback_data="change_language")],
                [InlineKeyboardButton("Change Game Mode 🎮", callback_data="change_game_mode")],
                [InlineKeyboardButton("Close ❌", callback_data="close_settings")],  # Close button
            ]
        )

        await callback_query.message.reply_text("Settings options:", reply_markup=settings_keyboard)
    else:
        await callback_query.answer("You do not have permission to access settings.", show_alert=True)

@Client.on_callback_query(filters.regex("change_language"))
async def change_language_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge button press

    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    # Check if the user is an admin
    is_admin = await is_user_admin(client, chat_id, user_id)

    if not is_admin:
        await callback_query.answer("You do not have permission to access this setting.", show_alert=True)
        return

    # Create language selection keyboard
    language_keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("English 🇬🇧", callback_data="set_language_en")],
            [InlineKeyboardButton("Tamil 🇮🇳", callback_data="set_language_ta")],
            [InlineKeyboardButton("Hindi 🇮🇳", callback_data="set_language_hi")],
            [InlineKeyboardButton("Back 🔙", callback_data="back_to_settings_language")],  # Back button
        ]
    )

    await callback_query.message.edit_text("Select your language:", reply_markup=language_keyboard)

@Client.on_callback_query(filters.regex("set_language_"))
async def set_language_callback(client, callback_query):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    # Check if the user is an admin
    is_admin = await is_user_admin(client, chat_id, user_id)

    if not is_admin:
        await callback_query.answer("You do not have permission to change settings.", show_alert=True)
        return

    new_language_str = callback_query.data.split("_")[-1]  # Get language as string

    try:
        await db.set_chat_language(chat_id, new_language_str)  # Store language as string in DB
        await callback_query.answer(f"Language changed to {new_language_str.upper()}!", show_alert=True)
    except Exception as e:
        logging.exception(f"Error setting language: {e}")
        await callback_query.answer("An error occurred while setting the language. Please try again.", show_alert=True)

@Client.on_callback_query(filters.regex("change_game_mode"))
async def change_game_mode_callback(client , callback_query):
    await callback_query.answer()  # Acknowledge button press

    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    # Check if the user is an admin
    is_admin = await is_user_admin(client, chat_id, user_id)

    if not is_admin:
        await callback_query.answer("You do not have permission to access this setting.", show_alert=True)
        return

    # Create game mode selection keyboard
    game_mode_keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Easy 😌", callback_data="set_game_mode_easy")],
            [InlineKeyboardButton("Hard 😤", callback_data="set_game_mode_hard")],
            [InlineKeyboardButton("Adult 🔞", callback_data="set_game_mode_adult")],
            [InlineKeyboardButton("Back 🔙", callback_data="back_to_settings_game_mode")],  # Back button
        ]
    )

    await callback_query.message.edit_text("Select your game mode:", reply_markup=game_mode_keyboard)

@Client.on_callback_query(filters.regex("set_game_mode_"))
async def set_game_mode_callback(client, callback_query):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    # Check if the user is an admin
    is_admin = await is_user_admin(client, chat_id, user_id)

    if not is_admin:
        await callback_query.answer("You do not have permission to change settings.", show_alert=True)
        return

    new_game_mode_str = callback_query.data.split("_")[-1]  # Get the mode string (e.g., "easy")

    try:
        await db.set_group_game_mode(chat_id, [new_game_mode_str])  # Store as a list in DB
        await callback_query.answer(f"Game mode changed to {new_game_mode_str.capitalize()}!", show_alert=True)
    except Exception as e:
        logging.exception(f"Error setting game mode: {e}")
        await callback_query.answer("An error occurred while setting the game mode. Please try again.", show_alert=True)

@Client.on_callback_query(filters.regex("back_to_settings_language"))
async def back_to_settings_language_callback(client, callback_query):
    await settings_callback(client, callback_query)

@Client.on_callback_query(filters.regex("back_to_settings_game_mode"))
async def back_to_settings_game_mode_callback(client, callback_query):
    await settings_callback(client, callback_query)

@Client.on_callback_query(filters.regex("close_settings"))
async def close_settings_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge button press
    await callback_query.message.edit_reply_markup(reply_markup=None)  # Remove the reply markup
