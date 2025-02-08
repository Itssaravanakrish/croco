from time import time
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType
from words import choice
from mongo.users_and_chats import db, ChatNotFoundError, UserNotFoundError
from config import SUDO_USERS

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

# Inline keyboard for when the user opts to become a leader
want_to_be_leader_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("ɪ ᴡᴀɴᴛ Tᴏ ʙᴇ ᴀ ʟᴇᴀᴅᴇʀ🙋‍♂", callback_data="start_new_game")]
    ]
)

async def make_sure_in_game(client: Client, message: Message) -> bool:
    game = await db.get_game(message.chat.id)  # Await the database call
    if game:
        if (time() - game['start']) >= GAME_TIMEOUT:
            await handle_end_game(client, message)  # End the game due to timeout
            return False  # Indicate that the game has ended
        return True
    return False  # No game is ongoing

async def make_sure_not_in_game(client, message):
    game = await db.get_game(message.chat.id)  # Check if a game is ongoing
    if game:
        await message.reply_text("ᴛʜᴇ ɢᴀᴍᴇ ʜᴀꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴛᴀʀᴛᴇᴅ! ᴅᴏ ɴᴏᴛ ʙʟᴀʙʙᴇʀ. 🤯")  # Notify the user
        return True  # Indicate that the game is ongoing
    return False  # No game is ongoing

def requires_game_not_running(func):
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        if await make_sure_not_in_game(client, message):  # Check if a game is ongoing
            return  # Exit if a game is ongoing
        return await func(client, message, *args, **kwargs)  # Await the wrapped function
    return wrapper
    
async def new_game(client: Client, message: Message) -> bool:
    word = choice()  # Get a new word for the game

    # Get the bot's ID
    bot_info = await client.get_me()
    bot_id = bot_info.id

    # Ensure the host is not the bot
    host_id = message.from_user.id
    if host_id == bot_id:
        return False  # Prevent the bot from being set as the host

    await db.set_game(message.chat.id, {  # Await the database call
        'start': time(),
        'host': {
            'id': host_id,  # Set the host ID to the user starting the game
            'first_name': message.from_user.first_name,
            'username': message.from_user.username,
        },
        'word': word,  # Set the word for the game
    })
    return True

async def get_game(client: Client, message: Message) -> dict:
    return await db.get_game(message.chat.id)  # Await the database call

async def next_word(client: Client, message: Message) -> str:
    game = await get_game(client, message)  # Await the function call
    game['word'] = choice()
    await db.set_game(message.chat.id, game)  # Await the database call
    logging.info(f"New word set for game in chat {message.chat.id}.")
    return game['word']

async def is_true(client: Client, message: Message, word: str) -> bool:
    game = await get_game(client, message)  # Await the function call
    if game['word'] == word.lower():
        await handle_end_game(client, message)  # Await the end_game function
        return True
    return False

async def handle_end_game(client: Client, message: Message) -> bool:
    if await db.get_game(message.chat.id):  # Await the database call
        try:
            await db.delete_game(message.chat.id)  # Await the database call
            logging.info(f"Game ended for chat {message.chat.id}.")
            return True  # Indicate that the game has ended
        except Exception as e:
            logging.error(f"Error ending the game: {e}")
            await message.reply_text("An error occurred while ending the game. Please try again.")
            return False  # Indicate that there was an error
    return False  # No game was found to end

async def is_user_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        chat_member = await client.get_chat_member(chat_id, user_id)
        return chat_member.status in ["administrator", "creator"]
    except Exception as e:
        logging.error(f"Error checking admin status: {e}")
        return False

async def check_game_status(client: Client, message: Message):
    game = await db.get_game(message.chat.id)
    if game:
        if (time() - game['start']) >= GAME_TIMEOUT:
            await handle_end_game(client, message)  # End the current game due to inactivity
            return None  # Indicate that the game has ended
        return game  # Return the ongoing game
    return None  # No game is ongoing

@Client.on_message(filters.group & filters.command("game", CMD))
async def game_command(client: Client, message: Message):
    chat_id = str(message.chat.id)

    # Check if a game is already ongoing
    ongoing_game = await db.get_game(chat_id)  # Fetch the game state from the database

    if ongoing_game:
        # Check if the game has timed out
        if (time() - ongoing_game['start']) >= GAME_TIMEOUT:
            # Game has timed out, start a new game
            await handle_end_game(client, message)  # End the current game due to timeout
            await new_game(client, message)  # Start a new game
            return  # Exit after starting a new game

        # If the game is ongoing and has not timed out
        host_id = ongoing_game["host"]["id"]  # Get the host's ID
        if message.from_user.id != host_id:
            await message.reply_text("ᴛʜᴇ ɢᴀᴍᴇ ʜᴀꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴛᴀʀᴛᴇᴅ! ᴅᴏ ɴᴏᴛ ʙʟᴀʙʙᴇʀ. 🤯")
            return  # Exit if the user is not the host

        # If the user is the host, do nothing (or you can send a message if needed)
        return  # Exit if the game is already ongoing

    # If no game is ongoing, start a new game
    await new_game(client, message)  # This function should contain your game initialization logic

    # Notify the group that the game has started
    await message.reply_text(f"The game has started! {message.from_user.first_name} is explaining the word now.", reply_markup=inline_keyboard_markup)  # Show the keyboard

@Client.on_message(filters.group & filters.command("score", CMD))
async def scores_callback(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check if the user is an admin or creator
    if await is_user_admin(client, chat_id, user_id):
        total_user_scores = await db.total_scores(user_id)  # Use the database instance
        scores_in_current_chat = (
            await db.scores_in_chat(chat_id, user_id)  # Use the database instance
            if message.chat.type == ChatType.SUPERGROUP
            else "<code>not in group</code>"
        )
        await message.reply_text(
            f"Your total scores: {total_user_scores}\nScores in this chat: {scores_in_current_chat}"
        )
    else:
        await message.reply_text("🇾🇴🇺 🇩🇴🇳❜🇹 🇭🇦🇻🇪 🇵🇪🇷🇲🇮🇸🇸🇮🇴🇳 🇹о 🇩о 🇹н🇮🇸.")

@Client.on_callback_query(filters.regex("end_game"))
async def end_now_callback(client: Client, callback_query: CallbackQuery):
    logging.info("End game button clicked.")
    game = await db.get_game(callback_query.message.chat.id)  # Check if a game is ongoing

    if game:
        if callback_query.from_user.id == game['host']['id']:  # Check if the user is the host
            await handle_end_game(client, callback_query.message)  # End the current game
            await callback_query.message.delete()  # Delete the old message
            await client.send_message(
                callback_query.message.chat.id,
                "The game has been ended. You can now choose to start a new game.",
                reply_markup=want_to_be_leader_keyboard
            )
            await callback_query.answer("The game has been ended.", show_alert=True)
        else:
            await callback_query.answer("You are not the leader. You cannot end the game.", show_alert=True)
    else:
        await callback_query.answer("The game is already ended.", show_alert=True)

@Client.on_callback_query(filters.regex("start_new_game"))
async def start_new_game_callback(client: Client, callback_query: CallbackQuery):
    logging.info(f"Start new game button clicked by user: {callback_query.from_user.id} in chat: {callback_query.message.chat.id}")
    # Acknowledge the callback query
    await callback_query.answer()
    # Start a new game with the user who clicked the button as the host
    await new_game(client, callback_query.message)  # Start a new game
    # Retrieve the new game state to ensure it's set up correctly
    new_game_state = await db.get_game(callback_query.message.chat.id)

    if new_game_state:
        # Delete the old message to clean up
        await callback_query.message.delete()
        # Notify that a new game has started
        await client.send_message(
            callback_query.message.chat.id,
            f"Game started! [{callback_query.from_user.first_name}](tg://user?id={callback_query.from_user.id}) 🥳 is explaining the word now.",
            reply_markup=inline_keyboard_markup  # Use your existing inline keyboard for the game
        )
        await callback_query.answer("A new game has started! You are the leader now.", show_alert=True)
    else:
        await callback_query.answer("Failed to retrieve the new game state. Please try again.", show_alert=True)

@Client.on_callback_query(filters.regex("view|next"))
async def handle_view_next_callback(client: Client, callback_query: CallbackQuery):
    try:
        game = await get_game(client, callback_query.message)  # Await the function call
        if game:
            if callback_query.from_user.id == game['host']['id']:
                if callback_query.data == "view":
                    await callback_query.answer(f"The word is: {game['word']}", show_alert=True)
                elif callback_query.data == "next":
                    new_word = await next_word(client, callback_query.message)  # Await the function call
                    await callback_query.answer(f"The new word is: {new_word}", show_alert=True)
            else:
                await callback_query.answer("ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ꜰᴏʀ ʏᴏᴜ. ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ʟᴇᴀᴅᴇʀ.", show_alert=True)
    except Exception as e:
        if str(e) == 'The game has ended due to timeout.':
            await callback_query.answer("🇹🇭🇪 🇬🇦🇲🇪 🇭🇦🇸 🇪🇳🇩🇪 🇩 🇩🇺🇪 🇹о 🇹🇮🇲🇪🇴🇺🇹. 🇵🇱🇪🇦🇸🇪 🇸🇹🇦🇷🇹 🇦 🇳🇪 🇼🇪 🇹🇦🇭 🇹🇭🇪 🇬🇦🇲🇪 🇭🇦🇸 🇪🇳🇩🇪🇩 🇩🇺🇪 🇹о 🇹🇮🇲🇪🇴🇺🇹. 🇵🇱🇪🇦🇸🇪 🇸🇹🇦🇷🇹 🇦 🇳🇪🇼 🇬🇦🇲🇪.", show_alert=True)
        else:
            await callback_query.answer("An unexpected error occurred.", show_alert=True)

@Client.on_message(filters.group)
async def check_for_correct_word(client: Client, message: Message):
    game = await db.get_game(message.chat.id)  # Check if a game is ongoing
    if game:
        # Check if the message is a text message
        if message.text:
            if message.text.lower() == game['word'].lower():  # Check if the message matches the word
                if message.from_user.id == game['host']['id']:  # Check if the host provided the answer
                    await message.reply_sticker("CAACAg UAAyEFAASMPZdPAAEBWjVnnj1fEKVElmmYXzBc828kgDZTQQACNBQAAu9OkFSKgGFg2iVa2R4E")
                    await message.reply_text("Correct! But the game continues...")
                else:
                    # End the game for non-host and notify
                    await handle_end_game(client, message)  # End the current game for non-host
                    await message.reply_text(
                        f"Congratulations {message.from_user.first_name}, you found the word! The game has ended due to inactivity. Starting a new game...",
                    )
                    await new_game(client, message)  # Start a new game with the current user as the host
                    await message.reply_text(
                        f"Game started! {message.from_user.first_name} 🥳 is explaining the word now.",
                        reply_markup=inline_keyboard_markup  # Show the inline keyboard for the new game
                    )

@Client.on_message(filters.group & filters.command("end", CMD))
async def end_game_callback(client: Client, message: Message):
    game = await db.get_game(message.chat.id)  # Check if a game is ongoing
    if game:
        if game['host']['id'] == message.from_user.id:  # Check if the user is the host
            if await handle_end_game(client, message):  # End the current game
                await message.reply_text("ᴛʜᴇ ɢᴀᴍᴇ ʜᴀꜱ ʙᴇᴇɴ ᴇɴᴅᴇᴅ ʙʏ ᴛʜᴇ ʜᴏꜱᴛ.")
            else:
                await message.reply_text("An error occurred while trying to end the game. Please try again.")
        else:
            await message.reply_text("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ʜᴏꜱᴛ ᴏʀ ᴛʜᴇʀᴇ ɪꜱ ɴᴏ ɢᴀᴍᴇ ᴛᴏ ᴇɴᴅ.")
    else:
        await message.reply_text("ᴛʜᴇʀᴇ ɪꜱ ɴᴏ ɢᴀᴍᴇ ᴏɴɢᴏɪɴɢ ᴛᴏ ᴇɴᴅ.")
