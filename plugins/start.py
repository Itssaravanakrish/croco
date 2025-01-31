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

def make_sure_in_game(client: Client, message: Message) -> bool:
    game = db.get_game(message.chat.id)  # Use the database instance to get the game
    if game:
        if (time() - game['start']) >= 300:
            end_game(client, message)
            raise Exception('The game has ended due to timeout.')
        return True
    raise Exception('There is no game going on.')

def make_sure_not_in_game(client: Client, message: Message) -> bool:
    game = db.get_game(message.chat.id)  # Use the database instance to get the game
    if game:
        if (time() - game['start']) >= 300:
            end_game(client, message)
            raise Exception('The game has ended due to timeout.')
        raise Exception('There is a game going on.')
    return True

def requires_game_running(func):
    def wrapper(client: Client, message: Message, *args, **kwargs):
        make_sure_in_game(client, message)
        return func(client, message, *args, **kwargs)
    return wrapper

def requires_game_not_running(func):
    def wrapper(client: Client, message: Message, *args, **kwargs):
        make_sure_not_in_game(client, message)
        return func(client, message, *args, **kwargs)
    return wrapper

@requires_game_not_running
def new_game(client: Client, message: Message) -> bool:
    db.set_game(message.chat.id, {  # Use the database instance to set the game
        'start': time(),
        'host': message.from_user,
        'word': choice(),
    })
    return True

@requires_game_running
def get_game(client: Client, message: Message) -> dict:
    return db.get_game(message.chat.id)  # Use the database instance to get the game

@requires_game_running
def next_word(client: Client, message: Message) -> str:
    game = get_game(client, message)
    game['word'] = choice()
    db.set_game(message.chat.id, game)  # Use the database instance to update the game
    return game['word']

@requires_game_running
def is_true(client: Client, message: Message, word: str) -> bool:
    game = get_game(client, message)
    if game['word'] == word.lower():
        end_game(client, message)
        return True
    return False

def end_game(client: Client, message: Message) -> bool:
    if db.get_game(message.chat.id):  # Use the database instance to check the game
        try:
            db.delete_game(message.chat.id)  # Use the database instance to delete the game
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
    await message.reply_text(
        f"{message.from_user.mention_html()} talks about a word.",
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
    word = next_word(client, message)
    await message.reply_text(f"The next word is: {word}")

@Client.on_callback_query(filters.regex("view"))
async def view_word_callback(client: Client, callback_query: CallbackQuery):
    message = callback_query.message
    game = get_game(client, message)
    await message.reply_text(f"The current word is: {game['word']}")

@Client.on_message(filters.command("end") & filters.group)
@requires_game_running
async def end_game_callback(client, message: Message):
    end_game(client, message)
    await message.reply_text("The game has ended.")
