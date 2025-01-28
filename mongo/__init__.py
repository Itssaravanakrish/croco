import motor.motor_asyncio
from config import MONGO_URI, MONGO_DB_NAME

try:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    database = client[MONGO_DB_NAME]
except Exception as e:
    print(f"Error connecting to database: {e}")
