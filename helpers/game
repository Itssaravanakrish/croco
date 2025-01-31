from time import time
from pyrogram import Client, filters
from pyrogram.types import Message
from words import choice

def make_sure_in_game(client: Client, message: Message) -> bool:
    """ Check if a game is in progress. If a game is in progress, return True. Otherwise, raise an exception. """
    game = client.db.get(message.chat.id, 'game')
    if game:
        if (time() - game['start']) >= 300:
            end_game(client, message)
        return True
    raise Exception('There is no game going on.')

def make_sure_not_in_game(client: Client, message: Message) -> bool:
    """ Check if a game is not in progress. If a game is not in progress, return True. Otherwise, raise an exception. """
    game = client.db.get(message.chat.id, 'game')
    if game:
        if (time() - game['start']) >= 300:
            end_game(client, message)
        raise Exception('There is a game going on.')
    return True

def requires_game_running(func):
    """ Decorator to check if a game is in progress. If a game is in progress, call the decorated function. Otherwise, raise an exception. """
    def wrapper(client: Client, message: Message, *args, **kwargs):
        make_sure_in_game(client, message)
        return func(client, message, *args, **kwargs)
    return wrapper

def requires_game_not_running(func):
    """ Decorator to check if a game is not in progress. If a game is not in progress, call the decorated function. Otherwise, raise an exception. """
    def wrapper(client: Client, message: Message, *args, **kwargs):
        make_sure_not_in_game(client, message)
        return func(client, message, *args, **kwargs)
    return wrapper

@requires_game_not_running
def new_game(client: Client, message: Message) -> bool:
    """ Start a new game. Initialize the game data and return True. """
    client.db.set(message.chat.id, 'game', {
        'start': time(),
        'host': message.from_user,
        'word': choice(),
    })
    return True

@requires_game_running
def get_game(client: Client, message: Message) -> dict:
    """ Get the current game data. Return the game data. """
    return client.db.get(message.chat.id, 'game')

@requires_game_running
def next_word(client: Client, message: Message) -> str:
    """ Get the next word. Update the game data with the next word and return it. """
    game = get_game(client, message)
    game['word'] = choice()
    client.db.set(message.chat.id, 'game', game)
    return game['word']

@requires_game_running
def is_true(client: Client, message: Message, word: str) -> bool:
    """ Check if the given word is correct. If the word is correct, end the game and return True. Otherwise, return False. """
    game = get_game(client, message)
    if game['word'] == word.lower():
        end_game(client, message)
        return True
    return False

def end_game(client: Client, message: Message) -> bool:
    """ End the current game. Remove the game data and return True. """
    if client.db.get(message.chat.id, 'game'):
        try:
            client.db.delete(message.chat.id, 'game')
            return True
        except Exception as e:
            raise e
    return False
