import logging
from random import choice as choice_
from pathlib import Path

def process_word(word: str) -> str:
    """Process a word by replacing underscores with spaces and converting to lowercase."""
    return word.replace('_', ' ').lower()

# Define the path to the word list files for different game modes
easy_wordlist_path = Path('wordlists/easy.txt')
hard_wordlist_path = Path('wordlists/hard.txt')
adult_wordlist_path = Path('wordlists/adult.txt')

# Initialize the list of words for each game mode
easy_words = []
hard_words = []
adult_words = []

# Load words for each game mode
def load_words(file_path):
    words = []
    try:
        with file_path.open(encoding='UTF-8') as file:
            words = list(map(process_word, file.read().split()))
        logging.info(f"Loaded {len(words)} words from {file_path.name}.")
    except FileNotFoundError:
        logging.error(f"Word list file {file_path.name} not found.")
    return words

easy_words = load_words(easy_wordlist_path)
hard_words = load_words(hard_wordlist_path)
adult_words = load_words(adult_wordlist_path)

def choice(game_mode: str) -> str:
    """Select a random word from the word list based on the game mode. Returns None if the list is empty."""
    if game_mode == "easy":
        word_list = easy_words
    elif game_mode == "hard":
        word_list = hard_words
    elif game_mode == "adult":
        word_list = adult_words
    else:
        logging.warning("Invalid game mode. Defaulting to easy.")
        word_list = easy_words

    if not word_list:
        logging.warning("No words available to choose from.")
        return None  # Handle the case where the word list is empty
    return choice_(word_list)
