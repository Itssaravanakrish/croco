import logging
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatMemberUpdated  # Correct import for pyrogram types
from pyrogram import Client, filters
from mongo.users_and_chats import db  # Replace with your actual module path
from utils import get_message, register_user, register_chat, is_user_admin  # Replace with your actual module path
from script import Language  # Replace with your actual module path
from words import get_word_list, choice  # Import from words.py

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

CMD = ["/", "."]

# Inline keyboard for private messages
inline_keyboard_markup_pm = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "Add Me to Your Group 👥",
                url="https://t.me/Crocodile_game_enBot?startgroup=true",
            )
        ],
        [InlineKeyboardButton("Support Our Group 💖", url="https://t.me/xTamilChat")],
        [InlineKeyboardButton("Close ❌", callback_data="close")],
    ]
)

# Inline keyboard for group messages
inline_keyboard_markup_grp = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "Add Me to Your Group 👥", url="https://t.me/Crocodile_game_enBot?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton(
                "Support Our Group 💖", url="https://t.me/Xtamilchat"
            )
        ],
        [InlineKeyboardButton("Settings ⚙️", callback_data="settings"),
         InlineKeyboardButton("Close ❌", callback_data="close")],
    ]
)

async def handle_start_command(client, message, is_group: bool):
    user_id = str(message.from_user.id)
    user_data = {
        "first_name": message.from_user.first_name,
        "username": message.from_user.username,
    }

    try:
        if is_group:
            chat_id = str(message.chat.id)
            logging.info(f"/start command received in group chat {chat_id} from user {user_id}.")

            # Retrieve the group language
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
            
            await message.reply_text(welcome_message, reply_markup=inline_keyboard_markup_grp)

        else:  # Private chat
            logging.info(f"/start command received in private chat from user {user_id}.")

            # Register user
            if not await register_user(user_id, user_data):
                await message.reply_text(await get_message(Language.EN, "error_registering_user"))
                return

            # Use the existing welcome message for private chats
            welcome_message = await get_message(Language.EN, "welcome")
            await message.reply_text(welcome_message, reply_markup=inline_keyboard_markup_pm)

    except Exception as e:
        logging.exception(f"Error in handle_start_command: {e}")
        await message.reply_text(await get_message(Language.EN, "error_processing_command"))

# Command handler for /start in private messages
@Client.on_message(filters.command("start") & filters.private)
async def start_private_handler(client, message):
    await handle_start_command(client, message, is_group=False)

# Command handler for /start in group messages
@Client.on_message(filters.command("start") & filters.group)
async def start_group_handler(client, message):
    await handle_start_command(client, message, is_group=True)
    
@Client.on_callback_query()
async def button_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()  # Acknowledge button press

    try:
        if callback_query.data == "close":
            await callback_query.message.edit_reply_markup(reply_markup=None)

        elif callback_query.data == "settings":
            await settings_callback(client, callback_query)

        elif callback_query.data.startswith("change_language"):
            await change_language_callback(client, callback_query)

        elif callback_query.data.startswith("set_language_"):
            await set_language_callback(client, callback_query)

        elif callback_query.data.startswith("change_game_mode"):
            await change_game_mode_callback(client, callback_query)

        elif callback_query.data.startswith("set_game_mode_"):
            await set_game_mode_callback(client, callback_query)

        elif callback_query.data.startswith("back_"):
            target = callback_query.data.split("_")[1]
            if target == "settings":
                await settings_callback(client, callback_query)
            elif target == "language":
                await change_language_callback(client, callback_query)
            elif target == "game_mode":
                await change_game_mode_callback(client, callback_query)

    except Exception as e:
        logging.exception(f"Error in button_callback: {e}")
        await callback_query.message.reply_text(await get_message(Language.EN, "error_processing_command"))  # Or a more specific message

async def settings_callback(client: Client, callback_query: CallbackQuery):
    if not await is_user_admin(client, callback_query.message.chat.id, callback_query.from_user.id):
        await callback_query.answer(await get_message(Language.EN, "not_admin"), show_alert=True)  # English fallback
        return

    chat_id = callback_query.message.chat.id
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    try:
        await callback_query.message.edit_text(
            await get_message(language, "settings_option"),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Change Language 🌐", callback_data="change_language")],
                    [InlineKeyboardButton("Change Game Mode 🎮", callback_data="change_game_mode")],
                    [InlineKeyboardButton("Back 🔙", callback_data="back_settings")],
                ]
            ),
        )
    except Exception as e:
        logging.exception(f"Error editing message: {e}")
        await callback_query.answer(await get_message(Language.EN, "error_editing_message"), show_alert=True)  # English fallback

async def change_language_callback(client: Client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    try:
        await callback_query.message.edit_text(
            await get_message(language, "select_language"),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("English 🇬🇧", callback_data="set_language_en")],
                    [InlineKeyboardButton("Tamil 🇮🇳", callback_data="set_language_ta")],
                    [InlineKeyboardButton("Hindi 🇮🇳", callback_data="set_language_hi")],
                    [InlineKeyboardButton("Back 🔙", callback_data="back_language")],
                ]
            ),
        )
    except Exception as e:
        logging.exception(f"Error editing message: {e}")
        await callback_query.answer(await get_message(Language.EN, "error_editing_message"), show_alert=True)  # English fallback
        
async def set_language_callback(client: Client, callback_query: CallbackQuery):
    new_language_str = callback_query.data.split("_")[-1]  # Get language as string
    try:
        new_language = Language(new_language_str)  # Convert to enum
    except ValueError:
        new_language = Language.EN  # Default to English
        new_language_str = "en"  # Also set the string to "en" for consistency

    chat_id = callback_query.message.chat.id

    try:
        await db.set_chat_language(chat_id, new_language_str)  # Store language as string in DB

        # Get the correct "language_set" message based on the *new* language:
        language_set_message = await get_message(new_language, "language_set")
        if language_set_message is None:  # Check if message exists for the language
            language_set_message = await get_message(Language.EN, "language_set")  # fallback to english

        await callback_query.message.edit_text(
            language_set_message.format(language=new_language_str.upper()),  # Format with string
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Back 🔙", callback_data="back_settings")],
                ]
            ),
        )
    except Exception as e:
        logging.exception(f"Error setting language: {e}")
        await callback_query.answer("An error occurred while setting the language. Please try again.", show_alert=True)

async def change_game_mode_callback(client: Client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    try:
        await callback_query.message.edit_text(
            await get_message(language, "select_game_mode"),  # Use correct language
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Easy 😌", callback_data="set_game_mode_easy")],
                    [InlineKeyboardButton("Hard 😤", callback_data="set_game_mode_hard")],
                    [InlineKeyboardButton("Adult 🔞", callback_data="set_game_mode_adult")],
                    [InlineKeyboardButton("Back 🔙", callback_data="back_game_mode")],
                ]
            ),
        )
    except Exception as e:
        logging.exception(f"Error editing message: {e}")
        await callback_query.answer(await get_message(Language.EN, "error_editing_message"), show_alert=True)  # English fallback

async def set_game_mode_callback(client: Client, callback_query: CallbackQuery):
    new_game_mode_str = callback_query.data.split("_")[-1]  # Get the mode string (e.g., "easy")
    chat_id = callback_query.message.chat.id
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    try:
        # No database update needed! Just acknowledge and update the message
        game_mode_set_message = await get_message(language, "game_mode_set")
        if game_mode_set_message is None:
            game_mode_set_message = await get_message(Language.EN, "game_mode_set")

        await callback_query.message.edit_text(
            game_mode_set_message.format(mode=new_game_mode_str.capitalize()),  # Use the string
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Back 🔙", callback_data="back_settings")],
                ]
            ),
        )
        # Here, you would likely want to store new_game_mode_str in the database
        # if you want the game mode to persist.
        await db.set_group_game_mode(chat_id, [new_game_mode_str])  # Store as a list in DB
    except Exception as e:
        logging.exception(f"Error setting game mode: {e}")
        await callback_query.answer(await get_message(Language.EN, "error_setting_game_mode"), show_alert=True)
