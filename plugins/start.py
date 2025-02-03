from time import time
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType
from words import choice
from mongo.users_and_chats import db  # Import the database instance

CMD = ["/", "."]

# Inline keyboard for the game
inline_keyboard_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("ꜱᴇᴇ ᴡᴏʀᴅ 👀", callback_data="view"),
         InlineKeyboardButton("ɴᴇxᴛ ᴡᴏʀᴅ 🔄", callback_data="next")],
        [InlineKeyboardButton("ɪ ᴅᴏɴ'ᴛ ᴡᴀɴᴛ ᴛᴏ ʙᴇ ᴀ ʟᴇᴀᴅᴇʀ🙅‍♂", callback_data="end_game_now")]
    ]
)

# Inline keyboard for when the user opts out of being a leader
want_to_be_leader_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("ɪ ᴡᴀɴᴛ ᴛᴏ ʙᴇ ᴀ ʟᴇᴀᴅᴇʀ🙋‍♂", callback_data="start_new_game")]
    ]
)

#time out close 
close_to_be_leader_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ 👥", url="https://t.me/Crocodile_game_enBot?startgroup=invite")]
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
            await end_game(client, message)  # Await the end_game function
            raise Exception('The game has ended due to timeout.')
        return True
    raise Exception('There is no game going on.')

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
            await message.reply_text("ᴛʜᴇ ɢᴀᴍᴇ ʜᴀꜱ ᴇɴᴅᴇᴅ ᴅᴜᴇ ᴛᴏ ᴛɪᴍᴇᴏᴜᴛ. ꜱᴛᴀʀᴛ ᴛʜᴇ ɴᴇᴡ ɢᴀᴍᴇ.")  # Notify users that the game has ended
            return True
        except Exception as e:
            logging.error(f"Error ending the game: {e}")
            raise Exception(f"Error ending the game: {e}")
    return False

@Client.on_message(filters.group & filters.command("score", CMD))
async def scores_callback(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Retrieve chat member information
    chat_member = await client.get_chat_member(chat_id, user_id)

    if chat_member.status in ["administrator", "creator"]:
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
        await message.reply_text("​🇾​​🇴​​🇺​ ​🇩​​🇴​​🇳​❜​🇹​ ​🇭​​🇦​​🇻​​🇪​ ​🇵​​🇪​​🇷​​🇲​​🇮​​🇸​​🇸​​🇮​​🇴​​🇳​ ​🇹​​🇴​ ​🇩​​🇴​ ​🇹​​🇭​​🇮​​🇸​.")

@Client.on_callback_query(filters.regex("end_game_now"))
async def end_game_callback(client: Client, callback_query: CallbackQuery):
    game = await db.get_game(callback_query.message.chat.id)  # Check if a game is ongoing
    if game:
        if callback_query.from_user.id == game['host']['id']:  # Check if the user is the host
            await end_game(client, callback_query.message)  # End the current game
            await callback_query.message.edit_reply_markup(want_to_be_leader_keyboard)  # Show the new button
            await callback_query.answer("ᴛʜᴇ ɢᴀᴍᴇ ʜᴀꜱ ʙᴇᴇɴ ᴇɴᴅᴇᴅ. ʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴄʜᴏᴏꜱᴇ ᴛᴏ ʙᴇ ᴀ ʟᴇᴀᴅᴇʀ.", show_alert=True)
        else:
            await callback_query.answer("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ʟᴇᴀᴅᴇʀ. ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴇɴᴅ ᴛʜᴇ ɢᴀᴍᴇ.", show_alert=True)
    else:
        await callback_query.answer("​🇹​​🇭​​🇪​​🇷​​🇪​ ​🇮​​🇸​ ​🇳​​🇴​ ​🇬​​🇦​​🇲​​🇪​ ​🇹​​🇴​ ​🇪​​🇳​​🇩​.", show_alert=True)
        
@Client.on_callback_query(filters.regex("start_new_game"))
async def start_new_game_callback(client: Client, callback_query: CallbackQuery):
    game = await db.get_game(callback_query.message.chat.id)  # Check if a game is ongoing
    if game:
        await end_game(client, callback_query.message)  # End the current game
    # Start a new game with the user who clicked the button as the host
    await new_game(client, callback_query.message)  # Start a new game
    await callback_query.answer("ᴀ ɴᴇᴡ ɢᴀᴍᴇ ʜᴀꜱ ꜱᴛᴀʀᴛᴇᴅ! ʏᴏᴜ ᴀʀᴇ ᴛʜᴇ ʟᴇᴀᴅᴇʀ ɴᴏᴡ.", show_alert=True)
    await callback_query.message.reply_text(
        "ɢᴀᴍᴇ ꜱᴛᴀʀᴛᴇᴅ! [{message.from_user.first_name}](tg://user?id={message.from_user.id}) 🥳 ɪꜱ ᴇxᴘʟᴀɪɴɪɴɢ ᴛʜᴇ ᴡᴏʀᴅ ɴᴏᴡ.",
        reply_markup=inline_keyboard_markup
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
            await callback_query.answer("🇹​​🇭​​🇪​ ​🇬​​🇦​​🇲​​🇪​ ​🇭​​🇦​​🇸​ ​🇪​​🇳​​🇩​​🇪​​🇩​ ​🇩​​🇺​​🇪​ ​🇹​​🇴​ ​🇹​​🇮​​🇲​​🇪​​🇴​​🇺​​🇹​. ​🇵​​🇱​​🇪​​🇦​​🇸​​🇪​ ​🇸​​🇹​​🇦​​🇷​​🇹​ ​🇦​ ​🇳​​🇪​​🇼​ ​🇬​​🇦​​🇲​​🇪​.", show_alert=True)
        else:
            await callback_query.answer("An unexpected error occurred.", show_alert=True)

@Client.on_callback_query(filters.regex("next"))
async def next_word_callback(client: Client, callback_query: CallbackQuery):
    game = await get_game(client, callback_query.message)  # Await the function call
    if game:
        if callback_query.from_user.id == game['host']['id']:
            new_word = await next_word(client, callback_query.message)  # Await the function call
            await callback_query.answer(f"The new word is: {new_word}", show_alert=True)
        else:
            await callback_query.answer("ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ꜰᴏʀ ʏᴏᴜ. ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ʟᴇᴀᴅᴇʀ.", show_alert=True)
    except Exception as e:
        if str(e) == 'The game has ended due to timeout.':
            await callback_query.answer("🇹​​🇭​​🇪​ ​🇬​​🇦​​🇲​​🇪​ ​🇭​​🇦​​🇸​ ​🇪​​🇳​​🇩​​🇪​​🇩​ ​🇩​​🇺​​🇪​ ​🇹​​🇴​ ​🇹​​🇮​​🇲​​🇪​​🇴​​🇺​​🇹​. ​🇵​​🇱​​🇪​​🇦​​🇸​​🇪​ ​🇸​​🇹​​🇦​​🇷​​🇹​ ​🇦​ ​🇳​​🇪​​🇼​ ​🇬​​🇦​​🇲​​🇪.", show_alert=True)
        else:
            await callback_query.answer("An unexpected error occurred.", show_alert=True)

@Client.on_message(filters.group & filters.command("start", CMD))
async def start_game(client: Client, message: Message):
    game = await db.get_game(message.chat.id)  # Check if a game is ongoing
    if game:
        # Check if the game has been inactive for more than 5 minutes
        if (time() - game['start']) >= 300:
            await end_game(client, message)  # End the current game due to inactivity
            await message.reply_text(
                f"ɢᴀᴍᴇ ʜᴀꜱ ᴇɴᴅᴇᴅ ᴅᴜᴇ ᴛᴏ ɪɴᴀᴄᴛɪᴠɪᴛʏ. [{message.from_user.first_name}](tg://user?id={message.from_user.id}) 🥳, ᴘʟᴇᴀꜱᴇ ꜱᴛᴀʀᴛ ᴀ ɴᴇᴡ ɢᴀᴍᴇ ᴡɪᴛʜ.",
                reply_markup=close_to_be_leader_keyboard
            )
        else:
            host_name = game["host"]["first_name"]  # Get the host's first name
            await message.reply_text(f"The game is already started by {host_name}.")  # Notify the user
    else:
        await new_game(client, message)  # Start a new game
        await message.reply_text(
            f"ɢᴀᴍᴇ ꜱᴛᴀʀᴛᴇᴅ! [{message.from_user.first_name}](tg://user?id={message.from_user.id}) 🥳 ɪꜱ ᴇxᴘʟᴀɪɴɪɴɢ ᴛʜᴇ ᴡᴏʀᴅ ɴᴏᴡ.",
            reply_markup=inline_keyboard_markup
        )
        
@Client.on_message(filters.private & filters.command("start", CMD))
async def start_private(client: Client, message: Message):
    welcome_message = "Welcome to our advanced Crocodile Game Bot! 🐊\n\n" \
                      "Get ready to have fun and challenge your friends!"
    
    await message.reply_text(
        welcome_message,
        reply_markup=inline_keyboard_markup_pm
    )

@Client.on_message(filters.group)
async def check_for_correct_word(client: Client, message: Message):
    game = await db.get_game(message.chat.id)  # Check if a game is ongoing
    if game:
        if message.text.lower() == game['word'].lower():  # Check if the message matches the word
            if message.from_user.id == game['host']['id']:  # Check if the host provided the answer
                await message.reply_sticker("CAACAgUAAyEFAASMPZdPAAEBWjVnnj1fEKVElmmYXzBc828kgDZTQQACNBQAAu9OkFSKgGFg2iVa2R4E")
                await message.reply_text("ᴄᴏʀʀᴇᴄᴛ! ʙᴜᴛ ᴛʜᴇ ɢᴀᴍᴇ ᴄᴏɴᴛɪɴᴜᴇꜱ...")
            else:
                await end_game(client, message)  # End the current game for non-host
                await message.reply_text(f"ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴꜱ {message.from_user.mention}, ʏᴏᴜ ꜰᴏᴜɴᴅ ᴛʜᴇ ᴡᴏʀᴅ! ꜱᴛᴀʀᴛɪɴɢ ᴀ ɴᴇᴡ ɢᴀᴍᴇ...")
                await new_game(client, message)  # Start a new game with the current user as the host
                await message.reply_text(
                    "ɢᴀᴍᴇ ꜱᴛᴀʀᴛᴇᴅ!  [{message.from_user.first_name}](tg://user?id={message.from_user.id}) 🥳 ɪꜱ ᴇxᴘʟᴀɪɴɪɴɢ ᴛʜᴇ ᴡᴏʀᴅ ɴᴏᴡ.",
                    reply_markup=inline_keyboard_markup
                )

@Client.on_message(filters.group & filters.command("alive", CMD))
async def alive_callback(_, message: Message):
    await message.reply_text("I am alive and running! 💪")

@Client.on_message(filters.group & filters.command("end", CMD))
async def end_game_callback(client: Client, message: Message):
    game = await db.get_game(message.chat.id)  # Check if a game is ongoing
    if game and game['host']['id'] == message.from_user.id:
        await end_game(client, message)  # End the current game
        await message.reply_text("ᴛʜᴇ ɢᴀᴍᴇ ʜᴀꜱ ʙᴇᴇɴ ᴇɴᴅᴇᴅ ʙʏ ᴛʜᴇ ʜᴏꜱᴛ.")
    else:
        await message.reply_text("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ʜᴏꜱᴛ ᴏʀ ᴛʜᴇʀᴇ ɪꜱ ɴᴏ ɢᴀᴍᴇ ᴛᴏ ᴇɴᴅ.")
