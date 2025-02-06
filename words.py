import logging
from random import choice as choice_
from pathlib import Path

def process_word(word: str) -> str:
    """Process a word by replacing underscores with spaces and converting to lowercase."""
    return word.replace('_', ' ').lower()

# Define the path to the word list file
wordlist_path = Path('wordlists/en.txt')

# Initialize the list of words
all_words = []

try:
    with wordlist_path.open(encoding='UTF-8') as file:
        all_words = list(map(process_word, file.read().split()))
    logging.info(f"Loaded {len(all_words)} words from the word list.")
except FileNotFoundError:
    logging.error("Word list file not found.")

def choice() -> str:
    """Select a random word from the word list. Returns None if the list is empty."""
    if not all_words:
        logging.warning("No words available to choose from.")
        return None  # Handle the case where the word list is empty
    return choice_(all_words)
