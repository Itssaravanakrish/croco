import logging
from mongo.users_and_chats import db  # Import your database instance
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
            return messages_en[key].format(**kwargs)  # Fallback to English
    except KeyError:
        logging.error(f"Message key '{key}' not found for language '{language}'.")
        return messages_en.get("message_not_found", "Message not found.")  # Fallback message

class UserSettings:
    def __init__(self, user_id: str):
        self.user_id = user_id

    async def set_language(self, language: str) -> None:
        """Set the user's preferred language."""
        if language not in ["en", "ta", "hi"]:
            raise ValueError("Invalid language code. Must be 'en', 'ta', or 'hi'.")
        
        await db.set_user_language(self.user_id, language)  # Assuming you have this method in your db
        logging.info(f"User  {self.user_id} language set to {language}.")

    async def get_language(self) -> str:
        """Get the user's preferred language."""
        try:
            language = await db.get_user_language(self.user_id)  # Fetch the user's language preference
            return language
        except Exception as e:
            logging.error(f"Failed to get language for user {self.user_id}: {e}")
            return "en"  # Default to English if there's an error
