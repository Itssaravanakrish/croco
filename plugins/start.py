from time import time
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType
from words import choice
from mongo.users_and_chats import db, ChatNotFoundError
from config import SUDO_USERS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

CMD = ["/", "."]

# Inline keyboard for the game
inline_keyboard_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("ꜱᴇᴇ ᴡᴏʀᴅ 👀", callback_data="view"),
         InlineKeyboardButton("ɴᴇxᴛ ᴡᴏʀᴅ 🔄", callback_data="next")],
        [InlineKeyboardButton("ɪ ᴅᴏɴ'ᴛ ᴡᴀɴᴛ ᴛᴏ ʙᴇ ᴀ ʟᴇᴀᴅᴇʀ🙅‍♂", callback_data="end_game")]
    ]
)

# Inline keyboard for when the user opts out of being a leader
want_to_be_leader_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("ɪ ᴡᴀɴᴛ ᴏ ʙᴇ ᴀ ʟᴇᴀᴅᴇʀ🙋‍♂", callback_data="start_new_game")]
    ]
)

# Define the inline keyboard for private messages
inline_keyboard_markup_pm = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ 👥", url="https://t.me/Crocodile_game_enBot?startgroup=invite")],
        [InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ ᴏᴜʀ ɢʀᴏᴜᴘ 💖", url="https://t.me/Xtamilchat")]
    ]
)

async def make_sure_in_game(client: Client, message: Message) -> bool:
    game = await db.get_game(message.chat.id)  # Await the database call
    if game:
        if (time() - game['start']) >= 300:
            await end_game(client, message)  # End the game due to timeout
            return False  # Indicate that the game has ended
        return True
    return False  # No game is ongoing

async def make_sure_not_in_game(client, message):
    game = await db.get_game(message.chat.id)  # Check if a game is ongoing
    if game:
        raise Exception("ᴛʜᴇ ɢᴀᴍᴇ ʜᴀꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴛᴀʀᴛᴇᴅ! ᴅᴏ ɴᴏᴛ ʙʟᴀʙʙᴇʀ. 🤯")  # Simplified message

def requires_game_running(func):
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        await make_sure_in_game(client, message)  # Await the function call
        return await func(client, message, *args, **kwargs)  # Await the wrapped function
    return wrapper

def requires_game_not_running(func):
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        await make_sure_not_in_game(client, message)  # Await the function call
        return await func(client, message, *args, **kwargs)  # Await the wrapped function
    return wrapper

@requires_game_not_running
async def new_game(client: Client, message: Message) -> bool:
    await db.set_game(message.chat.id, {  # Await the database call
        'start': time(),
        'host': {
            'id': message.from_user.id,
            'first_name': message.from_user.first_name,
            'username': message.from_user.username,
        },
        'word': choice(),
    })
    logging.info(f"New game started by {message.from_user.first_name} in chat {message.chat.id}.")
    return True

@requires_game_running
async def get_game(client: Client, message: Message) -> dict:
    return await db.get_game(message.chat.id)  # Await the database call

@requires_game_running
async def next_word(client: Client, message: Message) -> str:
    game = await get_game(client, message)  # Await the function call
    game['word'] = choice()
    await db.set_game(message.chat.id, game)  # Await the database call
    logging.info(f"New word set for game in chat {message.chat.id}.")
    return game['word']

@requires_game_running
async def is_true(client: Client, message: Message, word: str) -> bool:
    game = await get_game(client, message)  # Await the function call
    if game['word'] == word.lower():
        await end_game(client, message)  # Await the end_game function
        return True
    return False

async def end_game(client: Client, message: Message) -> bool:
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
        if (time() - game['start']) >= 300:
            await end_game(client, message)  # End the current game due to inactivity
            return None  # Indicate that the game has ended
        return game  # Return the ongoing game
    return None  # No game is ongoing

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
        await message.reply_text("​🇾​​🇴​​🇺​ ​🇩​​🇴​​🇳​❜​🇹​ ​🇭​​🇦​​🇻​​🇪​ ​🇵​​🇪​​🇷​​🇲​​🇮​​🇸​​🇸​​🇮​​🇴​​🇳​ ​🇹​​о​ ​🇩​​о​ ​🇹​​н​​🇮​​🇸​.")

@Client.on_callback_query(filters.regex("end_game"))
async def end_now_callback(client: Client, callback_query: CallbackQuery):
    logging.info("End game button clicked.")
    game = await db.get_game(callback_query.message.chat.id)  # Check if a game is ongoing

    if game:
        if callback_query.from_user.id == game['host']['id']:  # Check if the user is the host
            await end_game(client, callback_query.message)  # End the current game
            await callback_query.message.reply_text("The game has been ended. You can now choose to start a new game.", reply_markup=want_to_be_leader_keyboard)
            await callback_query.answer("The game has been ended.", show_alert=True)
        else:
            await callback_query.answer("You are not the leader. You cannot end the game.", show_alert=True)
    else:
        await callback_query.answer("The game is already ended.", show_alert=True)

@Client.on_callback_query(filters.regex("start_new_game"))
async def start_new_game_callback(client: Client, callback_query: CallbackQuery):
    game = await db.get_game(callback_query.message.chat.id)  # Check if a game is ongoing
    if game:
        await callback_query.answer("A game is already ongoing. Please end the current game before starting a new one.", show_alert=True)
        return  # Exit if there is an ongoing game

    # Start a new game with the user who clicked the button as the host
    await new_game(client, callback_query.message)  # Start a new game
    await callback_query.message.reply_text(
        f"Game started! [{callback_query.from_user.first_name}](tg://user?id={callback_query.from_user.id}) 🥳 is explaining the word now.",
        reply_markup=inline_keyboard_markup  # Show the inline keyboard for the new game
    )

@Client.on_callback_query(filters.regex("view"))
async def view_word_callback(client: Client, callback_query: CallbackQuery):
    try:
        game = await get_game(client, callback_query.message)  # Await the function call
        if game:
            if callback_query.from_user.id == game['host']['id']:
                await callback_query.answer(f"The word is: {game['word']}", show_alert=True)
            else:
                await callback_query.answer("ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ꜰᴏʀ ʏᴏᴜ. ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ʟᴇᴀᴅᴇʀ.", show_alert=True)
    except Exception as e:
        if str(e) == 'The game has ended due to timeout.':
            await callback_query.answer("🇹​​🇭​​🇪​ ​🇬​​🇦​​🇲​​🇪​ ​🇭​​🇦​​🇸​ ​🇪​​🇳​​🇩​​🇪​​🇩​ ​🇩​​🇺​​🇪​ ​🇹​​о​ ​🇹​​🇮​​🇲​​🇪​​🇴​​🇺​​🇹​. ​🇵​​🇱​​🇪​​🇦​​🇸​​🇪​ ​🇸​​🇹​​🇦​​🇷​​🇹​ ​🇦​ ​🇳​​🇪​​ 🇼​🇪​ ​🇹​​🇦​​🇭​ ​🇹​​🇭​​🇪​ ​🇬​​🇦​​🇲​​🇪​ ​🇭​​🇦​​🇸​ ​🇪​​🇳​​🇩​​🇪​​🇩​ ​🇩​​🇺​​🇪​ ​🇹​​о​ ​🇹​​🇮​​🇲​​🇪​​🇴​​🇺​​🇹​. ​🇵​​🇱​​🇪​​🇦​​🇸​​🇪​ ​🇸​​🇹​​🇦​​🇷​​🇹​ ​🇦​ ​🇳​​🇪​​🇼​ ​🇬​​🇦​​🇲​​🇪​.", show_alert=True)
        else:
            await callback_query.answer("An unexpected error occurred.", show_alert=True)

@Client.on_callback_query(filters.regex("next"))
async def next_word_callback(client: Client, callback_query: CallbackQuery):
    try:
        game = await get_game(client, callback_query.message)  # Await the function call
        if game:
            if callback_query.from_user.id == game['host']['id']:
                new_word = await next_word(client, callback_query.message)  # Await the function call
                await callback_query.answer(f"The new word is: {new_word}", show_alert=True)
            else:
                await callback_query.answer("ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ꜰᴏʀ ʏᴏᴜ. ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ʟᴇᴀᴅᴇʀ.", show_alert=True)
    except Exception as e:
        if str(e) == 'The game has ended due to timeout.':
            await callback_query.answer("🇹​​🇭​​🇪​ ​🇬​​🇦​​🇲​​🇪​ ​🇭​​🇦​​🇸​ ​🇪​​🇳​​🇩​​🇪​​🇩​ ​🇩​​🇺​​🇪​ ​🇹​​о​ ​🇹​​🇮​​🇲​​🇪​​🇴​​🇺​​🇹​. ​🇵​​🇱​​🇪​​🇦​​🇸​​🇪​ ​🇸​​🇹​​🇦​​🇷​​🇹​ ​🇦​ ​🇳​​🇪​​🇼​ ​🇬​​🇦​​🇲​​🇪.", show_alert=True)
        else:
            await callback_query.answer("An unexpected error occurred.", show_alert=True)

@Client.on_message(filters.group & filters.command("start", CMD))
async def start_game(client: Client, message: Message):
    # Add the chat to the database
    chat_id = str(message.chat.id)
    chat_data = {
        "title": message.chat.title,
        "type": message.chat.type.name,  # Convert ChatType to string
    }
    
    # Check if the chat already exists
    try:
        await db.get_chat(chat_id)  # Attempt to retrieve the chat
        logging.info(f"Chat {chat_id} already exists in the database.")
    except ChatNotFoundError:
        # Add the chat to the database if it is not already present
        try:
            await db.add_chat(chat_id, chat_data)  # Add chat to the database
            logging.info(f"Chat {chat_id} added to the database.")
        except Exception as e:
            logging.error(f"Failed to add chat {chat_id}: {e}")
            await message.reply_text("An error occurred while adding the chat to the database. Please try again later.")
            return  # Exit if there was an error

    game = await check_game_status(client, message)  # Check if a game is ongoing
    if game:
        host_name = game["host"]["first_name"]  # Get the host's first name
        await message.reply_text(f"The game is already started by {host_name}.")  # Notify the user
        return  # Exit if the game is ongoing

    # Start a new game
    await new_game(client, message)  # Start a new game
    await message.reply_text(
        f"ɢᴀᴍᴇ ꜱᴛᴀʀᴛᴇᴅ! [{message.from_user.first_name}](tg://user?id={message.from_user.id}) 🥳 ɪꜱ ᴇxᴘʟᴀɪɴɪɴɢ ᴛʜᴇ ᴡᴏʀᴅ ɴᴏᴡ.",
        reply_markup =inline_keyboard_markup
    )

@Client.on_message(filters.private & filters.command("start", CMD))
async def start_private(client: Client, message: Message):
    user_id = str(message.from_user.id)
    user_data = {
        "first_name": message.from_user.first_name,
        "username": message.from_user.username,
        # Add any other user data you want to store
    }
    
    # Check if the user already exists
    try:
        await db.get_user(user_id)  # Attempt to retrieve the user
        logging.info(f"User  {user_id} already exists in the database.")
    except UserNotFoundError:
        # Add the user to the database if they are not already present
        try:
            await db.add_user(user_id, user_data)  # Add user to the database
            logging.info(f"User  {user_id} added to the database.")
        except Exception as e:
            logging.error(f"Failed to add user {user_id}: {e}")
            await message.reply_text("An error occurred while adding you to the database. Please try again later.")
            return  # Exit if there was an error

    welcome_message = (
        "Welcome to our advanced Crocodile Game Bot! 🐊\n\n"
        "Get ready to have fun and challenge your friends!"
    )
    
    await message.reply_text(
        welcome_message,
        reply_markup=inline_keyboard_markup_pm  # Optional: You can include an inline keyboard if needed
    )
    
@Client.on_message(filters.group)
async def check_for_correct_word(client: Client, message: Message):
    game = await db.get_game(message.chat.id)  # Check if a game is ongoing
    if game:
        # Check if the message is a text message
        if message.text:
            if message.text.lower() == game['word'].lower():  # Check if the message matches the word
                if message.from_user.id == game['host']['id']:  # Check if the host provided the answer
                    await message.reply_sticker("CAACAgUAAyEFAASMPZdPAAEBWjVnnj1fEKVElmmYXzBc828kgDZTQQACNBQAAu9OkFSKgGFg2iVa2R4E")
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
