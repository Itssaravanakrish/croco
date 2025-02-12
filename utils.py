# utils.py

import logging
from script import messages_en, messages_ta, messages_hi  # Import your message dictionaries

async def get_message(language, key, **kwargs):
    """Fetch a message based on the language and key."""
    try:
        if language == "en":
            return messages_en[key].format(**kwargs)
        elif language == "ta":
            return messages_ta[key].format(**kwargs)
        elif language == "hi":
            return messages_hi[key].format(**kwargs)
        else:
            logging.error(f"Unsupported language: {language}.")
            return "Message not found."  # Fallback for unsupported languages
    except KeyError:
        logging.error(f"Message key '{key}' not found for language '{language}'.")
        return "Message not found."  # Fallback message
