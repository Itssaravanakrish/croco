from time import time
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from words import choice
from mongo.users_and_chats import db
from utils import get_message  # Assuming get_message is defined in utils.py

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

CMD = ["/", "."]
GAME_TIMEOUT = 300  # Timeout duration in seconds

# Inline keyboard for the game
inline_keyboard_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("ꜱᴇᴇ ᴡᴏʀᴅ 👀", callback_data="view"),
         InlineKeyboardButton("ɴᴇxᴛ ᴡᴏʀᴅ 🔄", callback_data="next")],
        [InlineKeyboardButton("ɪ ᴅᴏɴ'ᴛ ᴡᴀɴᴛ ᴏ ʙᴇ ᴀ ʟᴇᴀᴅᴇʀ🙅‍♂", callback_data="end_game")]
    ]
)

async def new_game(client: Client, message: Message, language="en", game_mode="easy") -> bool:
    word = choice()  # Get a new word for the game

    # Get the bot's ID
    bot_info = await client.get_me()
    bot_id = bot_info.id

    # Ensure the host is not the bot
    host_id = message.from_user.id
    if host_id == bot_id:
        return False  # Prevent the bot from being set as the host

    await db.set_game(message.chat.id, {
        'start': time(),
        'host': {
            'id': host_id,
            'first_name': message.from_user.first_name,
            'username': message.from_user.username,
        },
        'word': word,
        'game_mode': game_mode  # Store the game mode
    })

    await message.reply_text(
        await get_message(language, "game_started", name=message.from_user.first_name),
        reply_markup=inline_keyboard_markup
    )
    return True

@Client.on_message(filters.group & filters.command("game", CMD))
async def game_command(client: Client, message: Message):
    chat_id = str(message.chat.id)
    ongoing_game = await db.get_game(chat_id)

    user_id = str(message.from_user.id)
    language = await get_user_language(user_id)  # Use the existing function
    game_mode = await db.get_group_game_mode(chat_id)  # Fetch the group's game mode from the database

    if ongoing_game:
        if (time() - ongoing_game['start']) >= GAME_TIMEOUT:
            await handle_end_game(client, message)
            await new_game(client, message, language, game_mode)  # Pass game_mode to new_game
            return

        host_id = ongoing_game["host"]["id"]
        if message.from_user.id != host_id:
            await message.reply_text(await get_message(language, "game_already_started"))
            return

    await new_game(client, message, language, game_mode)  # Pass game_mode to new_game

@Client.on_callback_query(filters.regex("view|next|end_game"))
async def game_action_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    user_id = str(callback_query.from_user.id)
    language = await get_user_language(user_id)  # Use the existing function

    game = await db.get_game(callback_query.message.chat.id)

    if callback_query.data == "view":
        if game:
            word = game['word']  # Retrieve the current word
            await callback_query.message.reply_text(await get_message(language, "current_word", word=word))
        else:
            await callback_query.answer(await get_message(language, "no_game_ongoing"), show_alert=True)

    elif callback_query.data == "next":
        if game:
            new_word = choice()  # Get a new word for the game
            await db.update_word(callback_query.message.chat.id, new_word)  # Update the word in the database
            await callback_query.message.reply_text(await get_message(language, "new_word", word=new_word))
        else:
            await callback_query.answer(await get_message(language, "no_game_ongoing"), show_alert=True)

    elif callback_query.data == "end_game":
        if game:
            if callback_query.from_user.id == game['host']['id']:
 await handle_end_game(client, callback_query.message)
                await callback_query.message.delete()
                await client.send_message(callback_query.message.chat.id, await get_message(language, "game_ended"))  # Use the localized message
                await callback_query.answer(await get_message(language, "game_ended_confirmation"), show_alert=True)
            else:
                await callback_query.answer(await get_message(language, "not_leader"), show_alert=True)
        else:
            await callback_query.answer(await get_message(language, "no_game_ongoing"), show_alert=True)

@Client.on_message(filters.group & filters.command("set_mode", CMD))
async def set_game_mode(client: Client, message: Message):
    user_id = str(message.from_user.id)
    language = await get_user_language(user_id)  # Use the existing function

    if message.from_user.id != message.chat.owner.id:  # Check if the user is the admin or group owner
        await message.reply_text(await get_message(language, "not_admin"))
        return

    mode = message.command[1] if len(message.command) > 1 else None
    if mode not in ["easy", "hard", "adult"]:
        await message.reply_text(await get_message(language, "invalid_mode"))
        return

    await db.set_group_game_mode(message.chat.id, mode)  # Store the new game mode in the database
    await message.reply_text(await get_message(language, "game_mode_set", mode=mode))

async def handle_end_game(client: Client, message: Message):
    chat_id = message.chat.id
    await db.remove_game(chat_id)
    await message.reply_text(await get_message(language, "game_ended"))  # Notify that the game has ended
    return True
