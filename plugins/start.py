from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from mongo.users_and_chats import db
from utils import get_message, register_user, register_chat, is_user_admin

CMD = ["/", "."]

# Inline keyboard for private messages
inline_keyboard_markup_pm = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Add Me to Your Group 👥", url="https://t.me/Crocodile_game_enBot?startgroup=invite")],
        [InlineKeyboardButton("Support Our Group 💖", url="https://t.me/Xtamilchat")],
        [InlineKeyboardButton("Close ❌", callback_data="close")]  # Close button
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
        await message.reply_text(await get_message("en", "error_registering_user"))  # Default to English
        return

    chat_id = str(message.chat.id)
    chat_data = {
        "title": message.chat.title,
        "type": message.chat.type.name,
    }

    # Register chat
    if not await register_chat(chat_id, chat_data):
        await message.reply_text(await get_message("en", "error_registering_chat"))  # Default to English
        return

    # Determine the group's preferred language
    group_language = await db.get_group_language(chat_id)  # Fetch the group's language preference
    language = group_language if group_language else "en"  # Default to English if not set

    inline_keyboard_markup_grp = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Add Me to Your Group 👥", url="https://t.me/YourBotUsername?startgroup=new")],  # Replace with your bot's username
            [InlineKeyboardButton("Settings ⚙️", callback_data="settings")],  # Settings button
            [InlineKeyboardButton("Support Our Group 💖", url="https://t.me/YourSupportGroupLink")],  # Replace with your support group link
            [InlineKeyboardButton("Close ❌", callback_data="close")]  # Close button
        ]
    )
    
    # Prepare the welcome message
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

    # Register user
    if not await register_user(user_id, user_data):
        await message.reply_text(await get_message("en", "error_registering_user"))  # Default to English
        return

    # Determine the user's preferred language
    user_language = await db.get_group_language(message.chat.id)  # Fetch the group's language preference
    language = user_language if user_language else "en"  # Default to English if not set

    await message.reply_text(
        await get_message(language, "welcome"),  # Use the user's preferred language
        reply_markup=inline_keyboard_markup_pm
    )

@Client.on_callback_query(filters.regex("settings"))
async def settings_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    
    # Check if the user is an admin or owner
    if not await is_user_admin(client, callback_query.message.chat.id, callback_query.from_user.id):
        await callback_query.answer(await get_message("en", "not_admin"), show_alert=True)  # Localized message for not being an admin
        return

    # Send settings options
    await callback_query.message.reply_text(await get_message("en", "settings_option"), reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Change Language 🌐", callback_data="change_language")],
        [InlineKeyboardButton("Change Game Mode 🎮", callback_data="change_game_mode")],
        [InlineKeyboardButton("Back 🔙", callback_data="back_settings")]  # Back button
    ]))

@Client.on_callback_query(filters.regex("change_language"))
async def change_language_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    
    # Create language selection buttons with Back button
    language_buttons = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="set_language_en")],
        [InlineKeyboardButton("Tamil 🇮🇳", callback_data="set_language_ta")],
        [InlineKeyboardButton("Hindi 🇮🇳", callback_data="set_language_hi")],
        [InlineKeyboardButton("Back 🔙", callback_data="back_language")]  # Back button
    ]
    
    await callback_query.message.reply_text(await get_message("en", "select_language"), reply_markup=InlineKeyboardMarkup(language_buttons))

@Client.on_callback_query(filters.regex("set_language_(en|ta|hi)"))
async def set_language_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    
    new_language = callback_query.data.split("_")[-1]  # Get the language code
    chat_id = callback_query.message.chat.id
    
    # Update the language in the database
    await db.set_group_language(chat_id, new_language)  # Ensure this method exists in your db module
    
    await callback_query.message.reply_text(await get_message("en", "language_set").format(language=new_language.upper()))

@Client.on_callback_query(filters.regex("change_game_mode"))
async def change_game_mode_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    
    # Create game mode selection buttons with Back button
    game_mode_buttons = [
        [InlineKeyboardButton("Easy 😌", callback_data="set_game_mode_easy")],
        [InlineKeyboardButton("Hard 😤", callback_data="set_game_mode_hard")],
        [InlineKeyboardButton("Adult 🔞", callback_data="set_game_mode_adult")],
        [InlineKeyboardButton("Back 🔙", callback_data="back_game_mode")]  # Back button
    ]
    
    await callback_query.message.reply_text(await get_message("en", "select_game_mode"), reply_markup=InlineKeyboardMarkup(game_mode_buttons))

@Client.on_callback_query(filters.regex("set_game_mode_(easy|hard|adult)"))
async def set_game_mode_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    
    new_game_mode = callback_query.data.split("_")[-1]  # Get the game mode
    chat_id = callback_query.message.chat.id
    
    # Update the game mode in the database
    await db.set_group_game_mode(chat_id, new_game_mode)  # Ensure this method exists in your db module
    
    await callback_query.message.reply_text(await get_message("en", "game_mode_set").format(mode=new_game_mode.capitalize()))

@Client.on_callback_query(filters.regex("close"))
async def close_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.reply_text("The menu has been closed.", reply_markup=InlineKeyboardMarkup([]))  # Close the inline keyboard

@Client.on_callback_query(filters.regex("back_settings"))
async def back_settings_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await settings_callback(client, callback_query)  # Call the settings callback to return to settings

@Client.on_callback_query(filters.regex("back_language"))
async def back_language_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await settings_callback(client, callback_query)  # Return to settings from language selection

@Client.on_callback_query(filters.regex("back_game_mode"))
async def back_game_mode_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await settings_callback(client, callback_query)  # Return to settings from game mode selection
