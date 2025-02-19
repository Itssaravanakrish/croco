from time import time
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from mongo.users_and_chats import db
from utils import get_message

# Configure logging
logging.basicConfig(level=logging.INFO)

CMD = ["/", "."]

# Pay Command
@Client.on_message(filters.command("pay", CMD) & filters.group)
async def pay_command(client, message):
    """Command to pay coins to another user."""
    if not message.chat:
        await message.reply_text("This command can only be used in group chats.")
        return

    if not message.reply_to_message:
        await message.reply_text("Please reply to the user's message to pay coins.")
        return

    try:
        # Get the recipient ID from the replied message
        recipient_id = message.reply_to_message.from_user.id
        amount = int(message.text.split()[1])  # Get the amount from the command

        sender_id = message.from_user.id
        chat_id = message.chat.id

        # Fetch sender's current coins and XP
        sender_data = await db.get_user_score(chat_id, sender_id)
        if sender_data['coins'] < amount:
            await message.reply_text(get_message("insufficient_coins", language="en"))
            return

        # Calculate XP to deduct (1 XP per coin)
        xp_to_deduct = amount
        if sender_data['xp'] < xp_to_deduct:
            await message.reply_text(get_message("insufficient_xp", language="en"))
            return

        # Fetch recipient's current coins and XP
        recipient_data = await db.get_user_score(chat_id, recipient_id)

        # Update sender's and recipient's coins and XP
        new_sender_coins = sender_data['coins'] - amount
        new_sender_xp = sender_data['xp'] - xp_to_deduct
        new_recipient_coins = recipient_data['coins'] + amount
        new_recipient_xp = recipient_data['xp'] + xp_to_deduct

        await db.update_user_score(chat_id, sender_id, sender_data['score'], new_sender_coins, new_sender_xp)
        await db.update_user_score(chat_id, recipient_id, recipient_data['score'], new_recipient_coins, new_recipient_xp)

        await message.reply_text(get_message("payment_done", language="en").format(amount=amount, recipient_id=recipient_id, xp_to_deduct=xp_to_deduct))
    except ValueError:
        await message.reply_text("Usage: .pay <amount>")
    except UserNotFoundError:
        await message.reply_text("Recipient not found.")
    except Exception as e:
        logging.error(f"Error in pay_command: {e}")
        await message.reply_text("An error occurred while processing your payment.")

# Score Command
@Client.on_message(filters.command("score", CMD) & filters.group)
async def score_command(client, message):
    """Command to check the user's score, coins, and XP."""
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        # Fetch the user's score, coins, and XP from the database
        user_data = await db.get_user_score(chat_id, user_id)

        if user_data:
            await message.reply_text(
                f"Your score: {user_data['score']}\n"
                f"Coins: {user_data['coins']}\n"
                f"XP: {user_data['xp']}"
            )
        else:
            await message.reply_text("You have not scored any points yet.")
    except Exception as e:
        logging.error(f"Error in score_command: {e}")
        await message.reply_text("An error occurred while retrieving your score.")

# Top Command
@Client.on_message(filters.command("top", CMD) & filters.group)
async def top_command(client, message):
    """Command to show the top users based on their scores."""
    chat_id = message.chat.id

    try:
        # Fetch the top users from the database
        top_users = await db.get_top_users(chat_id)

        if top_users:
            top_users_text = "\n".join([f"User  ID: {user['user_id']}, Score: {user['score']}, Coins: {user['coins']}, XP: {user['xp']}" for user in top_users])
            await message.reply_text(f"Top Users:\n{top_users_text}")
        else:
            await message.reply_text("No scores available yet.")
    except Exception as e:
        logging.error(f"Error in top_command: {e}")
        await message.reply_text("An error occurred while retrieving the top users.")
