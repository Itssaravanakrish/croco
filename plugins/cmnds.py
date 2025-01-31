from pyrogram import filters, Client
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
)
from pyrogram.enums import ChatType
from helpers.game import (
    get_game,
    new_game,
    next_word,
    is_true,
    end_game,
)
from helpers.wrappers import nice_errors, admin_only
from mongo import users, chats
import logging
from typing import Union

CMD = ["/", "."]

inline_keyboard_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("View", callback_data="view")],
        [InlineKeyboardButton("Next", callback_data="next")],
    ]
)

@Client.on_message(filters.group & filters.command("score", CMD))
@admin_only
async def scores_callback(client, message):
    """Handle the '/scores' command. Send the user's total scores and scores in the current chat."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    total_user_scores = await users.total_scores(user_id)
    scores_in_current_chat = (
        await users.scores_in_chat(chat_id, user_id)
        if message.chat.type == ChatType.SUPERGROUP
        else "<code>not in group</code>"
    )
    await message.reply_text(
        f"Your total scores: {total_user_scores}\nYour scores in this chat: {scores_in_current_chat}",
        parse_mode="HTML",
    )

@Client.on_message(filters.command("start") & filters.group)
async def start_callback(client, message):
    """Handle the '/start' command in a group chat. Start a new game and update the database with the chat details."""
    await new_game(message.from_user)
    try:
        await chats.update(message.chat.id, message.chat.title)
    except Exception as e:
        logging.error(f"Error updating database: {e}")
    await message.reply_text(
        f"{message.from_user.mention_html()} talks about a word.",
        reply_markup=inline_keyboard_markup,
    )

@Client.on_message(filters.command("alive", CMD))
async def check_alive(_, message):
    await message.reply_text(
        "Hᴇʟʟᴏ Bᴜᴅᴅʏ I Aᴍ Aʟɪᴠᴇ : 𝖧𝗂𝗍 /start \n𝖧𝗂𝗍 /help 𝖥𝗈𝗋 𝖧𝖾𝗅𝗉 \n\n𝖧𝗂𝗍 /ping 𝖳𝗈 𝖢𝗁𝖾𝖼𝗄 𝖡𝗈𝗍 𝖯𝗂𝗇𝗀 😁"
    )

@Client.on_callback_query(filters.regex("view"))
async def view_callback(_, callback_query: CallbackQuery):
    """Handle the 'view' button press in a game. If the user is the host, send the game word as an alert. Otherwise, send a message indicating that the button is not for them."""
    game = get_game(callback_query)
    if game and game["host"].id == callback_query.from_user.id:
        await callback_query.answer(game["word"], show_alert=True)
    else:
        await callback_query.answer("This is not for you.", show_alert=True)

@Client.on_callback_query(filters.regex("next"))
async def next_callback(_, callback_query: CallbackQuery):
    """Handle the 'next' button press in a game. If the user is the host, send the next word as an alert. Otherwise, send a message indicating that the button is not for them."""
    game = get_game(callback_query)
    if game and game["host"].id == callback_query.from_user.id:
        next_word_result = await next_word(callback_query)
        await callback_query.answer(next_word_result, show_alert=True)
    else:
        await callback_query.answer("This is not for you.", show_alert=True)

@Client.on_message(filters.text & filters.group)
async def guess_callback(bot, message):
    logging.info(f"Received message from {message.from_user.id}")
    try:
        game = get_game(message)
        if game and game["host"].id != message.from_user.id:
            if await is_true(message.text, message):
                await message.reply_text(
                    f"<b>{message.from_user.mention_html()} guessed the correct word, {game['word']}.</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👏 Well Done!", url="https://t.me/TamilBots")]]),
                    parse_mode="HTML",
                )
                try:
                    await users.update(
                        message.chat.id,
                        message.from_user.id,
                        message.from_user.first_name,
                        message.from_user.username,
                    )
                except Exception as e:
                    logging.error(f"Error updating database: {e}")
    except Exception as e:
        logging.error(f"Error handling user guess: {e}")

@Client.on_message(filters.command("end", CMD))
async def end_callback(client, message):
    """Handle the '/end' command. End the current game."""
    try:
        await end_game(message)
        await message.reply_text(
            f"{message.from_user.mention_html()} ended the game.",
            reply_markup=inline_keyboard_markup,
        )
        try:
            await chats.update(message.chat.id, message.chat.title)
        except Exception as e:
            logging.error(f"Error updating chat title: {e}")
    except Exception as e:
        logging.error(f"Error handling end command: {e}")
