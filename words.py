import logging
from random import choice as choice_
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def process_word(word: str) -> str:
    """Process a word by replacing underscores with spaces and converting to lowercase."""
    return word.replace('_', ' ').lower()

# Get the directory where this script is located
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))

# Define the path to the word list files for different game modes using script_dir
easy_wordlist_path = script_dir / 'wordlists' / 'easy.txt'
hard_wordlist_path = script_dir / 'wordlists' / 'hard.txt'
adult_wordlist_path = script_dir / 'wordlists' / 'adult.txt'

# Initialize the list of words for each game mode
easy_words = []
hard_words = []
adult_words = []

# Load words for each game mode
def load_words(file_path):
    words = []
    try:
        with file_path.open(encoding='UTF-8') as file:
            words = [process_word(line.strip()) for line in file] #Process each line, striping the newline character.
        logging.info(f"Loaded {len(words)} words from {file_path.name}.")
    except FileNotFoundError:
        logging.error(f"Word list file {file_path.name} not found.")
        raise FileNotFoundError(f"Word list file {file_path.name} not found.")  # Raise FileNotFoundError.

    return words

try:
    easy_words = load_words(easy_wordlist_path)
    hard_words = load_words(hard_wordlist_path)
    adult_words = load_words(adult_wordlist_path)
except FileNotFoundError as e:
    logging.error(f"Failed to load word lists: {e}")
    # Handle the error appropriately, e.g., exit the program or use default words.
    # For now, let's keep the lists empty, so choice() will raise an exception.


def choice(game_mode: str) -> str:
    if game_mode == "easy":
        word_list = easy_words
    elif game_mode == "hard":
        word_list = hard_words
    elif game_mode == "adult":
        word_list = adult_words
    else:
        logging.warning(f"Invalid game mode: {game_mode}. Defaulting to easy.")  # Log the invalid mode
        word_list = easy_words  # Explicitly default to easy words

    if not word_list:
        raise ValueError("No words available for the specified game mode.")

    return choice_(word_list)
