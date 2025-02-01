from time import time
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType
from words import choice
from helpers.wrappers import nice_errors, admin_only
from mongo.users_and_chats import db  # Import the database instance

CMD = ["/", "."]

inline_keyboard_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("View", callback_data="view")],
        [InlineKeyboardButton("Next", callback_data="next")],
    ]
)

async def make_sure_in_game(client: Client, message: Message) -> bool:
    game = await db.get_game(message.chat.id)  # Await the database call
    if game:
        if (time() - game['start']) >= 300:
            await end_game(client, message)  # Await the end_game function
            raise Exception('The game has ended due to timeout.')
        return True
    raise Exception('There is no game going on.')

async def make_sure_not_in_game(client: Client, message: Message) -> bool:
    game = await db.get_game(message.chat.id)  # Await the database call
    if game:
        if (time() - game['start']) >= 300:
            await end_game(client, message)  # Await the end_game function
            raise Exception('The game has ended due to timeout.')
        raise Exception('There is a game going on.')
    return True

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
        'host': message.from_user,
        'word': choice(),
    })
    return True

@requires_game_running
async def get_game(client: Client, message: Message) -> dict:
    return await db.get_game(message.chat.id)  # Await the database call

@requires_game_running
async def next_word(client: Client, message: Message) -> str:
    game = await get_game(client, message)  # Await the function call
    game['word'] = choice()
    await db.set_game(message.chat.id, game)  # Await the database call
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
            return True
        except Exception as e:
            raise Exception(f"Error ending the game: {e}")
    return False

@Client.on_message(filters.group & filters.command("score", CMD))
@admin_only
async def scores_callback(client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    total_user_scores = await db.total_scores(user_id)  # Use the database instance
    scores_in_current_chat = (
        await db.scores_in_chat(chat_id, user_id)  # Use the database instance
        if message.chat.type == ChatType.SUPERGROUP
        else "<code>not in group</code>"
    )
    await message.reply_text(
        f"Your total scores: {total_user_scores}\nYour scores in this chat: {scores_in_current_chat}",
        parse_mode="HTML",
    )

@Client.on_message(filters.command("start") & filters.group)
async def start_callback(client, message: Message):
    await new_game(client, message)
    try:
        await db.update_chat(message.chat.id, message.chat.title)  # Use the database instance
    except Exception as e:
        logging.error(f"Error updating database: {e}")

    user_mention = message.from_user.mention  # This will give you the mention in the format @username
    user_first_name = message.from_user.first_name  # Get the user's first name

    await message.reply_text(
        f"{user_mention} talks about a word.",
        reply_markup=inline_keyboard_markup,
    )

@Client.on_message(filters.command("alive", CMD))
async def check_alive(_, message: Message):
    await message.reply_text(
        "H eʟʟᴏ Bᴜᴅᴅʏ I Aᴍ Aʟɪ vᴇ Aɴᴅ Rᴇᴀᴅʏ Tᴏ Pʟᴀʏ!"
    )

@Client.on_callback_query(filters.regex("next"))
async def next_word_callback(client: Client, callback_query: CallbackQuery):
    message = callback_query.message
    word = await next_word(client, message)  # Await the next_word function
    await message.reply_text(f"The next word is: {word}")

@Client.on_callback_query(filters.regex("view"))
async def view_word_callback(client: Client, callback_query: CallbackQuery):
    message = callback_query.message
    game = await get_game(client, message)  # Await the get_game function
    await message.reply_text(f"The current word is: {game['word']}")

@Client.on_message(filters.command("end") & filters.group)
@requires_game_running
async def end_game_callback(client, message: Message):
    await end_game(client, message)  # Await the end_game function
    await message.reply_text("The game has ended.")
