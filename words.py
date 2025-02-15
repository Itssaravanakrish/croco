# words.py
import logging
from random import choice as choice_
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def process_word(word: str) -> str:
    return word.replace('_', ' ').lower()

script_dir = Path(os.path.dirname(os.path.abspath(__file__)))

easy_wordlist_path = script_dir / 'wordlists' / 'easy.txt'
hard_wordlist_path = script_dir / 'wordlists' / 'hard.txt'
adult_wordlist_path = script_dir / 'wordlists' / 'adult.txt'

easy_words = []
hard_words = []
adult_words = []

def load_words(file_path):
    words = []
    try:
        with file_path.open(encoding='UTF-8') as file:
            words = [process_word(line.strip()) for line in file]
        logging.info(f"Loaded {len(words)} words from {file_path.name}.")
    except FileNotFoundError:
        logging.error(f"Word list file {file_path.name} not found.")
        raise  # Re-raise the FileNotFoundError to be handled elsewhere

    return words

try:
    easy_words = load_words(easy_wordlist_path)
    hard_words = load_words(hard_wordlist_path)
    adult_words = load_words(adult_wordlist_path)
except FileNotFoundError as e:
    logging.error(f"Failed to load word lists: {e}")
    # Consider a more graceful exit here if word lists are critical.  For example:
    # exit(1)  # Or provide default words if possible.

word_lists = {
    "easy": easy_words,
    "hard": hard_words,
    "adult": adult_words,
    # "normal": easy_words + hard_words,  # Example combined mode (optional)
}

def choice(game_mode: str) -> str:
    word_list = word_lists.get(game_mode.lower())  # Case-insensitive lookup

    if word_list is None:
        logging.warning(f"Invalid game mode: {game_mode}. Defaulting to easy.")
        word_list = word_lists["easy"]

    if not word_list:
        logging.error(f"No words available for game mode: {game_mode}!")
        return "No words available"  # Or another default message

    return choice_(word_list)
