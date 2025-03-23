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
        [InlineKeyboardButton("Support Our Group 💖", url="https://t.me/TownBus")],
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
                "Support Our Group 💖", url="https://t.me/TownBus"
            )
        ],
        [InlineKeyboardButton("Settings ⚙️", callback_data="settings"),
         InlineKeyboardButton("Close ❌", callback_data="close")],
    ]
)

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
        [InlineKeyboardButton("Close ❌", callback_data="close")],
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

@Client.on_callback_query()
async def button_callback(client, callback_query):
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
        await callback_query.message.reply_text(await get_message(Language.EN, "error_processing_command"))

async def settings_callback(client, callback_query):
    if not await is_user_admin(client, callback_query.message.chat.id, callback_query.from_user.id):
        await callback_query.answer(await get_message(Language.EN, "not_admin"), show_alert=True)
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
        await callback_query.answer(await get_message(Language.EN, "error_editing_message"), show_alert=True)

async def change_language_callback(client, callback_query):
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
        await callback_query.answer(await get_message(Language.EN, "error_editing_message"), show_alert=True)

async def set_language_callback(client, callback_query):
    new_language_str = callback_query.data.split("_")[-1]
    try:
        new_language = Language(new_language_str)
    except ValueError:
        new_language = Language.EN
        new_language_str = "en"

    chat_id = callback_query.message.chat.id

    try:
        await db.set_chat_language(chat_id, new_language_str)

        language_set_message = await get_message(new_language, "language_set")
        if language_set_message is None:
            language_set_message = await get_message(Language.EN, "language_set")

        await callback_query.message.edit_text(
            language_set_message.format(language=new_language_str.upper()),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Back 🔙", callback_data="back_settings")],
                ]
            ),
        )
    except Exception as e:
        logging.exception(f"Error setting language: {e}")
        await callback_query.answer("An error occurred while setting the language. Please try again.", show_alert=True)

async def change_game_mode_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    try:
        await callback_query.message.edit_text(
            await get_message(language, "select_game_mode"),
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
        await callback_query.answer(await get_message(Language.EN, "error_editing_message"), show_alert=True)

async def set_game_mode_callback(client, callback_query):
    new_game_mode_str = callback_query.data.split("_")[-1]
    chat_id = callback_query.message.chat.id
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    try:
        game_mode_set_message = await get_message(language, "game_mode_set")
        if game_mode_set_message is None:
            game_mode_set_message = await get_message(Language.EN, "game_mode_set")

        await callback_query.message.edit_text(
            game_mode_set_message.format(mode=new_game_mode_str.capitalize()),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Back 🔙", callback_data="back_settings")],
                ]
            ),
        )
        await db.set_group_game_mode(chat_id, [new_game_mode_str])
    except Exception as e:
        logging.exception(f"Error setting game mode: {e}")
        await callback_query.answer(await get_message(Language.EN, "error_setting_game_mode"), show_alert=True)
