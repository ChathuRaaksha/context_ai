"""
Database connection management using Motor (async MongoDB driver).
Provides singleton database instance for the application.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    """
    MongoDB database connection manager.

    Attributes:
        client: Motor async MongoDB client
        db: MongoDB database instance
    """

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect_db(self) -> None:
        """
        Establish connection to MongoDB database.

        Raises:
            Exception: If connection fails
        """
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URI)
            self.db = self.client.get_database("ai_bug_hunter")

            # Test the connection
            await self.client.admin.command("ping")
            logger.info(f"Successfully connected to MongoDB at {settings.MONGODB_URI}")

            # Create indexes
            await self._create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def close_db(self) -> None:
        """
        Close MongoDB database connection.
        """
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def get_db(self) -> AsyncIOMotorDatabase:
        """
        Get the database instance.

        Returns:
            AsyncIOMotorDatabase: MongoDB database instance

        Raises:
            RuntimeError: If database is not connected
        """
        if self.db is None:
            raise RuntimeError("Database is not connected. Call connect_db() first.")
        return self.db

    async def _create_indexes(self) -> None:
        """
        Create database indexes for optimized queries.
        """
        try:
            # API Keys collection indexes
            await self.db.api_keys.create_index("key_hash", unique=True)
            await self.db.api_keys.create_index("is_active")

            # Bugs collection indexes
            await self.db.bugs.create_index("bug_id", unique=True)
            await self.db.bugs.create_index("detected_at")
            await self.db.bugs.create_index("severity")
            await self.db.bugs.create_index("category")
            await self.db.bugs.create_index("source_service")

            # Healing attempts collection indexes
            await self.db.healing_attempts.create_index("bug_id")
            await self.db.healing_attempts.create_index("attempted_at")

            # Predictions collection indexes
            await self.db.predictions.create_index("created_at")
            await self.db.predictions.create_index("prediction_type")

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.warning(f"Failed to create some indexes: {e}")


# Singleton instance
db_instance = Database()


async def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency function to get database instance.

    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
    """
    return db_instance.get_db()
