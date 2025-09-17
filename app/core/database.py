from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

class Database:
    client: AsyncIOMotorClient = None
    
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URI)
        print("Connected to MongoDB")

    @classmethod
    async def connect_db(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance

    @classmethod
    async def close_db(cls):
        try:
            if hasattr(cls, '_instance') and cls._instance and cls._instance.client:
                await cls._instance.client.close()
                print("Closed MongoDB connection")
        except Exception as e:
            print(f"Error closing MongoDB connection: {e}")

    @classmethod
    def get_db(cls):
        if not hasattr(cls, '_instance'):
            raise RuntimeError("Database not initialized. Call connect_db() first.")
        return cls._instance.client.context_management

db = Database()
