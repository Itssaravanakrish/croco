from typing import Callable, Any
from pyrogram import Client
from pyrogram.types import Message
import logging

def admin_only(handler: Callable[[Client, Message], Any]) -> Callable[[Client, Message], Any]:
    """Decorator to restrict access to admin-only commands.
    
    Args:
        handler (Callable): The function to decorate.
    
    Returns:
        Callable: The decorated function.
    """
    def wrapper(client: Client, message: Message):
        if message.chat.type == 'private':
            return handler(client, message)
        
        try:
            member = client.get_chat_member(message.chat.id, message.from_user.id)
            if member.status in ('creator', 'administrator'):
                return handler(client, message)
            else:
                message.reply_text("You do not have permission to use this command.")
        except Exception as e:
            logging.error(f"Failed to check member status: {e}")
            message.reply_text("An error occurred while checking permissions.")
    
    return wrapper

def nice_errors(handler: Callable) -> Callable:
    """Decorator to catch and handle exceptions.
    
    Args:
        handler (Callable): The function to decorate.
    
    Returns:
        Callable: The decorated function.
    """
    def wrapper(client: Client, message: Message, *args, **kwargs):
        try:
            return handler(client, message, *args, **kwargs)
        except Exception as e:
            logging.exception("An error occurred: %s", e)
            if message.chat.type == 'private':
                message.reply_text(f'Error: {e}')
            else:
                message.reply_text(f'Error: {e}')
    
    return wrapper
