from telegram.ext import filters
from config import SUDO_USERS

sudo_only = filters.User(SUDO_USERS)
