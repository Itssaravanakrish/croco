# mongo/__init__.py

print("Initializing mongo package...")

try:
    from .mongo import MongoDB
    print("Successfully imported MongoDB.")
except ImportError as e:
    print(f"Error importing MongoDB: {e}")

try:
    from .users_and_chats import Users, Chats
    print("Successfully imported Users and Chats.")
except ImportError as e:
    print(f"Error importing Users and Chats: {e}")

__all__ = ["MongoDB", "Users", "Chats"]
