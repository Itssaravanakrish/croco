import logging
from random import choice as choice_
from pathlib import Path
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def process_word(word: str) -> str:
    """Process the word by replacing underscores with spaces and converting to lowercase."""
    return word.replace('_', ' ').lower()

# Define the script directory
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))

# Define paths to word lists
easy_wordlist_path = script_dir / 'wordlists' / 'easy.txt'
hard_wordlist_path = script_dir / 'wordlists' / 'hard.txt'
adult_wordlist_path = script_dir / 'wordlists' / 'adult.txt'

# Initialize word lists
easy_words = []
hard_words = []
adult_words = []

def load_words(file_path):
    """Load words from a given file path."""
    words = []
    try:
        with file_path.open(encoding='UTF-8') as file:
            words = [process_word(line.strip()) for line in file]
        logging.info(f"Loaded {len(words)} words from {file_path.name}.")
    except FileNotFoundError:
        logging.error(f"Word list file {file_path.name} not found.")
        raise  # Re-raise the FileNotFoundError to be handled elsewhere

    return words

# Load words from files
try:
    easy_words = load_words(easy_wordlist_path)
    hard_words = load_words(hard_wordlist_path)
    adult_words = load_words(adult_wordlist_path)
except FileNotFoundError as e:
    logging.error(f"Failed to load word lists: {e}")
    # Consider a more graceful exit here if word lists are critical. For example:
    # exit(1)  # Or provide default words if possible.

# Dictionary to hold word lists
word_lists = {
    "easy": easy_words,
    "hard": hard_words,
    "adult": adult_words,
    # "normal": easy_words + hard_words,  # Example combined mode (optional)
}

def choice(game_mode: str) -> str:
    """Select a random word from the specified game mode."""
    if not isinstance(game_mode, str):
        logging.error(f"Expected game_mode to be a string, got {type(game_mode).__name__}.")
        game_mode = "easy"  # Default to easy if not a string

    word_list = word_lists.get(game_mode.lower())  # Case-insensitive lookup

    if word_list is None:
        logging.warning(f"Invalid game mode: {game_mode}. Defaulting to easy.")
        word_list = word_lists["easy"]

    if not word_list:
        logging.error(f"No words available for game mode: {game_mode}!")
        return "No words available"  # Or another default message

    return choice_(word_list)

def get_word_list(game_mode: str):
    """Return a list of words based on the specified game mode."""
    return word_lists.get(game_mode.lower(), word_lists["easy"])  # Default to easy if mode is invalid
