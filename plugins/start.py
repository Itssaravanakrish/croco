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
        [InlineKeyboardButton("See word 👀", callback_data="view"),
         InlineKeyboardButton("Next word 🔄", callback_data="next")],
        [InlineKeyboardButton("I don't want to be a leader🙅‍♂", callback_data="end_game")]
    ]
)

# Inline keyboard for when the user opts out of being a leader
want_to_be_leader_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("I want to be a leader🙋‍♂", callback_data="start_new_game")]
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
        raise Exception(f'The game has already started by {message.from_user.mention}.')
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
        'host': {
            'id': message.from_user.id,
            'first_name': message.from_user.first_name,
            'username': message.from_user.username,
        },
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
            logging.info(f"Game ended for chat {message.chat.id}.")
            return True
        except Exception as e:
            logging.error(f"Error ending the game: {e}")
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
        f" Your total scores: {total_user_scores}\nScores in this chat: {scores_in_current_chat}"
    )

@Client.on_callback_query(filters.regex("end_game"))
async def end_game_callback(client: Client, callback_query: CallbackQuery):
    game = await db.get_game(callback_query.message.chat.id)  # Check if a game is ongoing
    if game:
        await end_game(client, callback_query.message)  # End the current game
        await callback_query.message.edit_reply_markup(want_to_be_leader_keyboard)  # Show the new button
        await callback_query.answer("The game has been ended. You can now choose to be a leader.", show_alert=True)
    else:
        await callback_query.answer("There is no game to end.", show_alert=True)

@Client.on_callback_query(filters.regex("start_new_game"))
async def start_new_game_callback(client: Client, callback_query: CallbackQuery):
    game = await db.get_game(callback_query.message.chat.id)  # Check if a game is ongoing
    if game:
        await end_game(client, callback_query.message)  # End the current game
    # Start a new game with the user who clicked the button as the host
    await new_game(client, callback_query.message)  # Start a new game
    await callback_query.answer("A new game has started! You are the leader now.", show_alert=True)
    await callback_query.message.reply_text(
        "Game started! Use the buttons below to view the word or skip to the next one.",
        reply_markup=inline_keyboard_markup
    )

@Client.on_callback_query(filters.regex("view"))
async def view_word_callback(client: Client, callback_query: CallbackQuery):
    game = await get_game(client, callback_query.message)  # Await the function call
    if game:
        if callback_query.from_user.id == game['host']['id']:
            await callback_query.answer(f"The word is: {game['word']}", show_alert=True)
        else:
            await callback_query.answer("This is not for you. You are not the leader.", show_alert=True)

@Client.on_callback_query(filters.regex("next"))
async def next_word_callback(client: Client, callback_query: CallbackQuery):
    game = await get_game(client, callback_query.message)  # Await the function call
    if game:
        if callback_query.from_user.id == game['host']['id']:
            new_word = await next_word(client, callback_query.message)  # Await the function call
            await callback_query.answer(f"The new word is: {new_word}", show_alert=True)
        else:
            await callback_query.answer("This is not for you. You are not the leader.", show_alert=True)

@Client.on_message(filters.group & filters.command("start", CMD))
@requires_game_not_running
async def start_game(client: Client, message: Message):
    await new_game(client, message)  # Await the function call
    await message.reply_text(
        "Game started! Use the buttons below to view the word or skip to the next one.",
        reply_markup=inline_keyboard_markup
    )

@Client.on_message(filters.group)
async def check_for_correct_word(client: Client, message: Message):
    game = await db.get_game(message.chat.id)  # Check if a game is ongoing
    if game:
        if message.text.lower() == game['word'].lower():  # Check if the message matches the word
            if message.from_user.id == game['host']['id']:  # Check if the host provided the answer
                # Send a sticker in response
                await message.reply_sticker("CAACAgUAAyEFAASMPZdPAAEBWjVnnj1fEKVElmmYXzBc828kgDZTQQACNBQAAu9OkFSKgGFg2iVa2R4E")
                await message.reply_text("Correct! But the game continues...")
            else:
                await end_game(client, message)  # End the current game for non-host
                await message.reply_text(f"Congratulations {message.from_user.mention}, you found the word! Starting a new game...")
                await new_game(client, message)  # Start a new game with the current user as the host
                await message.reply_text(
                    "Game started! Use the buttons below to view the word or skip to the next one.",
                    reply_markup=inline_keyboard_markup
                )

@Client.on_message(filters.group & filters.command("alive", CMD))
async def alive_callback(_, message):
    await message.reply_text("I am alive and running! 💪")

@Client.on_message(filters.group & filters.command("end", CMD))
@admin_only
async def end_game_callback(client: Client, message: Message):
    game = await db.get_game(message.chat.id)  # Check if a game is ongoing
    if game and game['host']['id'] == message.from_user.id:
        await end_game(client, message)  # End the current game
        await message.reply_text("The game has been ended by the host.")
    else:
        await message.reply_text("You are not the host or there is no game to end.")
