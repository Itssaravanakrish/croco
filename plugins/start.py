import logging
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatMemberUpdated  # Correct import for pyrogram types
from pyrogram import Client, filters
from mongo.users_and_chats import db  # Replace with your actual module path
from utils import get_message, register_user, register_chat, is_user_admin  # Replace with your actual module path
from script import Language  # Replace with your actual module path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

CMD = ["/", "."]

user_states = {}  # Dictionary to track user states

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
            group_language = await db.get_chat_language(chat_id)  # Assuming this function exists
            welcome_message = await get_message(group_language, "welcome_new_group")  # Assuming this function exists
            await message.reply_text(welcome_message, reply_markup=settings_keyboard)
        else:  # Private chat
            # Register user
            if not await register_user(user_id, user_data):  # Assuming this function exists
                await message.reply_text(await get_message(Language.EN, "error_registering_user"))
                return

            await message.reply_text("Welcome! Use /connect to connect to a group.")

    except Exception as e:
        logging.exception(f"Error in start_command: {e}")
        await message.reply_text("An error occurred. Please try again.")

@Client.on_message(filters.command("settings"))
async def settings_command(client, message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply_text("You need to connect to a group to change settings. Use /connect to connect.")
        return

    await message.reply_text("Please choose an option:", reply_markup=settings_keyboard)

@Client.on_message(filters.command("connect"))
async def connect_command(client, message):
    user_id = str(message.from_user.id)

    if message.chat.type == "private":
        # In private chat, ask for group ID or link
        await message.reply_text("Please provide the group ID or link to connect.")
        user_states[user_id] = "awaiting_group_id"  # Set state to awaiting input
    else:
        # In group chat, connect the user directly
        chat_id = message.chat.id
        await message.reply_text("You have been connected to this group.")
        # Here you can implement logic to store the connection

@Client.on_message(filters.text)
async def handle_group_id_input(client, message):
    user_id = str(message.from_user.id)
    if user_id in user_states and user_states[user_id] == "awaiting_group_id":
        group_id_or_link = message.text
        # Validate the group ID or link here
        await message.reply_text(f"You have been connected to the group: {group_id_or_link}.")
        # Store the connection logic here
        del user_states[user_id]  # Clear the user's state

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
    user_id = str(callback_query.from_user.id)

    # Retrieve the connected chat ID for the user
    connected_chat_id = await db.get_user_connected_chat(user_id)  # Assume this function retrieves the connected chat ID

    if connected_chat_id:
        try:
            await db.set_chat_language(connected_chat_id, new_language_str)  # Store language as string in DB
            await callback_query.answer(f"Language changed to {new_language_str.upper()}!", show_alert=True)
        except Exception as e:
            logging.exception(f"Error setting language: {e}")
            await callback_query.answer("An error occurred while setting the language. Please try again.", show_alert=True)
    else:
        await callback_query.answer("You are not connected to any group. Please connect first using /connect.", show_alert=True)

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
    user_id = str(callback_query.from_user.id)

    # Retrieve the connected chat ID for the user
    connected_chat_id = await db.get_user_connected_chat(user_id)  # Assume this function retrieves the connected chat ID

    if connected_chat_id:
        try:
            await db.set_group_game_mode(connected_chat_id, [new_game_mode_str])  # Store as a list in DB
            await callback_query.answer(f"Game mode changed to {new_game_mode_str.capitalize()}!", show_alert=True)
        except Exception as e:
            logging.exception(f"Error setting game mode: {e}")
            await callback_query.answer("An error occurred while setting the game mode. Please try again.", show_alert=True)
    else:
        await callback_query.answer("You are not connected to any group. Please connect first using /connect.", show_alert=True)

@Client.on_callback_query(filters.regex("back_settings"))
async def back_settings_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge button press
    await settings_command(client, callback_query.message)

@Client.on_callback_query(filters.regex("close_settings"))
async def close_settings_callback(client, callback_query):
    await callback_query.answer()  # Acknowledge button press
    await callback_query.message.edit_reply_markup(reply_markup=None)  # Remove the reply markup
