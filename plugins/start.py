from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_message, register_user, register_chat

CMD = ["/", "."]

# Inline keyboard for private messages
inline_keyboard_pm = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Add to Group 👥", url="https://t.me/Crocodile_game_enBot?startgroup=invite")],
        [InlineKeyboardButton("Support Group 💬", url="https://t.me/Xtamilchat")]
    ]
)

@Client.on_message(filters.group & filters.command("start", CMD))
async def start_group(client: Client, message: Message):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)
    language = "en"  # Default language

    # Register user and chat
    user_registered = await register_user(user_id, {"first_name": message.from_user.first_name})
    chat_registered = await register_chat(chat_id, {"title": message.chat.title})

    if not user_registered or not chat_registered:
        await message.reply(await get_message(language, "registration_failed"))
        return

    await message.reply(
        await get_message(language, "welcome_group"),
        reply_markup=inline_keyboard_pm
    )

@Client.on_message(filters.private & filters.command("start", CMD))
async def start_private(client: Client, message: Message):
    user_id = str(message.from_user.id)
    language = "en"  # Default language

    if not await register_user(user_id, {"first_name": message.from_user.first_name}):
        await message.reply(await get_message(language, "registration_failed"))
        return

    await message.reply(
        await get_message(language, "welcome_private"),
        reply_markup=inline_keyboard_pm
    )
