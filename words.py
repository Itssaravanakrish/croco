from random import choice as choice_
import logging

def process_word(word: str) -> str:
    """Process a word by replacing underscores with spaces and converting to lowercase."""
    return word.replace('_', ' ').lower()

try:
    with open('wordlists/en.txt', encoding='UTF-8') as file:
        all_words = list(map(process_word, file.read().split()))
except FileNotFoundError:
    logging.error("Word list file not found.")
    all_words = []

def choice() -> str:
    """Select a random word from the word list."""
    return choice_(all_words)
