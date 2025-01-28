from typing import Callable
from pyrogram import Client, Message, CallbackQuery
import logging

def admin_only(handler: Callable):
    """ Decorator to restrict access to admin-only commands.
    
    Args:
        handler (Callable): The function to decorate.
    
    Returns:
        Callable: The decorated function.
    """
    def wrapper(client: Client, message: Message):
        if message.chat.type == 'private':
            return handler(client, message)
        member = message.chat.get_member(message.from_user.id)
        if member.status in ('creator', 'administrator'):
            return handler(client, message)
    return wrapper

def nice_errors(handler: Callable):
    """ Decorator to catch and handle exceptions.
    
    Args:
        handler (Callable): The function to decorate.
    
    Returns:
        Callable: The decorated function.
    """
    def wrapper(client: Client, message: Message, *args, **kwargs):
        try:
            return handler(client, message, *args, **kwargs)
        except Exception as e:
            logging.error(f"Error: {e}")
            if message.chat.type == 'private':
                message.reply_text(f'Error: {e}')
            else:
                message.reply_text(f'Error: {e}')
    return wrapper
