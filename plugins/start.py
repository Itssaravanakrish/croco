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
    inline_keyboard_markup_grp = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Add Me to Your Group 👥", url="https://t.me/YourBotUsername?startgroup=new")],  # Replace with your bot's username
            [InlineKeyboardButton("Settings ⚙️", callback_data="settings")],  # Settings button
            [InlineKeyboardButton("Support Our Group 💖", url="https://t.me/YourSupportGroupLink")]  # Replace with your support group link
        ]
    )
    await message.reply_text(
        get_message(language, "welcome"),  # Use the user's preferred language
        reply_markup=inline_keyboard_markup_grp
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
    
@Client.on_callback_query(filters.regex("settings"))
async def settings_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    
    # Check if the user is an admin or owner
    chat_member = await client.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await callback_query.answer("You need to be an admin to change settings.", show_alert=True)
        return

    # Create language selection buttons
    language_buttons = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="set_language_en")],
        [InlineKeyboardButton("Tamil 🇮🇳", callback_data="set_language_ta")],
        [InlineKeyboardButton("Hindi 🇮🇳", callback_data="set_language_hi")]
    ]
    
    # Create game mode selection buttons
    game_mode_buttons = [
        [InlineKeyboardButton("Easy 😌", callback_data="set_game_mode_easy")],
        [InlineKeyboardButton("Hard 😤", callback_data="set_game_mode_hard")],
        [InlineKeyboardButton("Adult 🔞", callback_data="set_game_mode_adult")]
    ]
    
    # Send settings options
    await callback_query.message.reply_text("Choose an option:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Change Language 🌐", callback_data="change_language")],
        [InlineKeyboardButton("Change Game Mode 🎮", callback_data="change_game_mode")]
    ]))
@Client.on_callback_query(filters.regex("change_language"))
async def change_language_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    
    # Create language selection buttons
    language_buttons = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="set_language_en")],
        [InlineKeyboardButton("Tamil 🇮🇳", callback_data="set_language_ta")],
        [InlineKeyboardButton("Hindi 🇮🇳", callback_data="set_language_hi")]
    ]
    
    await callback_query.message.reply_text("Select a language:", reply_markup=InlineKeyboardMarkup(language_buttons))

@Client.on_callback_query(filters.regex("set_language_(en|ta|hi)"))
async def set_language_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    
    new_language = callback_query.data.split("_")[-1]  # Get the language code
    chat_id = callback_query.message.chat.id
    
    # Update the language in the database
    await db.set_group_language(chat_id, new_language)  # Ensure this method exists in your db module
    
    await callback_query.message.reply_text(f"Group language has been updated to {new_language.upper()}!")

@Client.on_callback_query(filters.regex("change_game_mode"))
async def change_game_mode_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    
    # Create game mode selection buttons
    game_mode_buttons = [
        [InlineKeyboardButton("Easy 😌", callback _query.data="set_game_mode_easy")],
        [InlineKeyboardButton("Hard 😤", callback_data="set_game_mode_hard")],
        [InlineKeyboardButton("Adult 🔞", callback_data="set_game_mode_adult")]
    ]
    
    await callback_query.message.reply_text("Select a game mode:", reply_markup=InlineKeyboardMarkup(game_mode_buttons))

@Client.on_callback_query(filters.regex("set_game_mode_(easy|hard|adult)"))
async def set_game_mode_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    
    new_game_mode = callback_query.data.split("_")[-1]  # Get the game mode
    chat_id = callback_query.message.chat.id
    
    # Update the game mode in the database
    await db.set_group_game_mode(chat_id, new_game_mode)  # Ensure this method exists in your db module
    
    await callback_query.message.reply_text(f"Game mode has been updated to {new_game_mode.capitalize()}!")
