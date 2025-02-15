from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters
from mongo.users_and_chats import db
from utils import get_message, register_user, register_chat, is_user_admin
from script import Language # Import Language enum
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

CMD = ["/", "."]

# Inline keyboard for private messages
inline_keyboard_markup_pm = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "Add Me to Your Group 👥",
                url="https://t.me/Crocodile_game_enBot?startgroup=invite",  # Replace with your bot's invite link
            )
        ],
        [InlineKeyboardButton("Support Our Group 💖", url="https://t.me/YourSupportGroupLink")],  # Replace with your support group link
        [InlineKeyboardButton("Close ❌", callback_data="close")],
    ]
)

@Client.on_message(filters.group & filters.command("start", CMD))
async def start_group(client: Client, message: Message):
    user_id = str(message.from_user.id)
    user_data = {
        "first_name": message.from_user.first_name,
        "username": message.from_user.username,
    }

    if not await register_user(user_id, user_data):
        await message.reply_text(await get_message("en", "error_registering_user"))
        return

    chat_id = str(message.chat.id)
    chat_data = {"title": message.chat.title, "type": message.chat.type.name}

    if not await register_chat(chat_id, chat_data):
        await message.reply_text(await get_message("en", "error_registering_chat"))
        return

    group_language = await db.get_chat_language(message.chat.id)
    language = group_language if group_language else "en"

    inline_keyboard_markup_grp = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Add Me to Your Group 👥", url="https://t.me/YourBotUsername?startgroup=new"  # Replace with your bot's username
                )
            ],
            [
                InlineKeyboardButton(
                    "Support Our Group 💖", url="https://t.me/YourSupportGroupLink"  # Replace with your support group link
                )
            ],
            [InlineKeyboardButton("Settings ⚙️", callback_data="settings"),  # Settings and Close on the third row
             InlineKeyboardButton("Close ❌", callback_data="close")],
        ]
    )

    welcome_message = await get_message(language, "welcome")
    if not welcome_message:
        logging.error("The welcome message is empty.")
        return

    await message.reply_text(welcome_message, reply_markup=inline_keyboard_markup_grp)


@Client.on_message(filters.private & filters.command("start", CMD))
async def start_private(client: Client, message: Message):
    user_id = str(message.from_user.id)
    user_data = {
        "first_name": message.from_user.first_name,
        "username": message.from_user.username,
    }

    if not await register_user(user_id, user_data):
        await message.reply_text(await get_message("en", "error_registering_user"))
        return

    language = "en"  # Default language for private chats

    await message.reply_text(
        await get_message(language, "welcome"), reply_markup=inline_keyboard_markup_pm
    )


@Client.on_callback_query()
async def button_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

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


async def settings_callback(client: Client, callback_query: CallbackQuery):
    if not await is_user_admin(
        client, callback_query.message.chat.id, callback_query.from_user.id
    ):
        await callback_query.answer(await get_message("en", "not_admin"), show_alert=True)
        return

    try:
        await callback_query.message.edit_text(
            await get_message("en", "settings_option"),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Change Language 🌐", callback_data="change_language")],
                    [InlineKeyboardButton("Change Game Mode 🎮", callback_data="change_game_mode")],
                    [InlineKeyboardButton("Back 🔙", callback_data="back_settings")],
                ]
            ),
        )
    except Exception as e:
        logging.error(f"Error editing message: {e}")
        # Handle the error, maybe send a message to the user


async def change_language_callback(client: Client, callback_query: CallbackQuery):
    try:
        await callback_query.message.edit_text(
            await get_message("en", "select_language"),
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
        logging.error(f"Error editing message: {e}")


async def set_language_callback(client: Client, callback_query: CallbackQuery):
    new_language = callback_query.data.split("_")[-1]
    chat_id = callback_query.message.chat.id

    try:
        await db.set_chat_language(chat_id, new_language)  # Only set for groups

        await callback_query.message.edit_text(
            await get_message("en", "language_set").format(language=new_language.upper()),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Back 🔙", callback_data="back_settings")],
                ]
            ),
        )
    except Exception as e:
        logging.error(f"Error setting language: {e}")
        # Handle the error


async def change_game_mode_callback(client: Client, callback_query: CallbackQuery):
    try:
        await callback_query.message.edit_text(
            await get_message("en", "select_game_mode"),
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
        logging.error(f"Error editing message: {e}")


async def set_game_mode_callback(client: Client, callback_query: CallbackQuery):
    new_game_mode = callback_query.data.split("_")[-1]
    chat_id = callback_query.message.chat.id

    try:
        await db.set_group_game_mode(chat_id, new_game_mode)  # Only set for groups

        await callback_query.message.edit_text(
            await get_message("en", "game_mode_set").format(mode=new_game_mode.capitalize()),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Back 🔙", callback_data="back_settings")],
                ]
            ),
        )
    except Exception as e:
        logging.error(f"Error setting game mode: {e}")
