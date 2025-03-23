from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_game_keyboard():
    """Returns the inline keyboard for game actions."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("See Word 👀", callback_data="view"),
                InlineKeyboardButton("Next Word 🔄", callback_data="next")
            ],
            [
                InlineKeyboardButton("Settings ⚙️", callback_data="settings")
            ],
            [
                InlineKeyboardButton("I Don't Want To Be A Leader 🙅‍♂️", callback_data="end_game")
            ]
        ]
    )

def get_settings_keyboard():
    """Returns the inline keyboard for settings options."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Change Language 🌐", callback_data="change_language")],
            [InlineKeyboardButton("Change Game Mode 🎮", callback_data="change_game_mode")],
            [InlineKeyboardButton("Back to Game 🎮", callback_data="back_to_game")]
        ]
    )

def get_language_keyboard():
    """Returns the inline keyboard for language selection."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("English 🇬🇧", callback_data="set_language_en")],
            [InlineKeyboardButton("Tamil 🇮🇳", callback_data="set_language_ta")],
            [InlineKeyboardButton("Hindi 🇮🇳", callback_data="set_language_hi")],
            [InlineKeyboardButton("Back 🔙", callback_data="back_to_settings_language")]
        ]
    )

def get_game_mode_keyboard():
    """Returns the inline keyboard for game mode selection."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Easy 😌", callback_data="set_game_mode_easy")],
            [InlineKeyboardButton("Hard 😤", callback_data="set_game_mode_hard")],
            [InlineKeyboardButton("Adult 🔞", callback_data="set_game_mode_adult")],
            [InlineKeyboardButton("Back 🔙", callback_data="back_to_settings_game_mode")]
        ]
    )

def get_leader_keyboard():
    """Returns the inline keyboard for choosing a leader."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("I Want To Be A Leader 🙋‍♂️", callback_data="choose_leader")]
        ]
    )
