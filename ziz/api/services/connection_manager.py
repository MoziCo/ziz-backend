"""MongoDB connection manager with lazy initialization and idle cleanup."""

import asyncio
import os
import time
from typing import Optional

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


class MongoConnectionManager:
    """Manages MongoDB connections with lazy initialization and automatic cleanup."""

    def __init__(self, mongo_url: str, idle_timeout: int = 30):
        self.mongo_url = mongo_url
        self.idle_timeout = idle_timeout
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._last_activity: float = 0
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance, creating connection if needed."""
        async with self._lock:
            if self._client is None:
                await self._create_connection()

            self._last_activity = time.time()
            assert self._database is not None, (
                "Database should be initialized after connection creation"
            )
            return self._database

    async def _create_connection(self):
        """Create new MongoDB connection with optimized settings."""
        logger.info("Creating new MongoDB connection")
        self._client = AsyncIOMotorClient(
            self.mongo_url,
            maxIdleTimeMS=30000,  # Close idle connections after 30 seconds
            minPoolSize=0,  # No minimum connections maintained
            maxPoolSize=1,  # Single connection for Railway optimization
        )
        db_name = os.getenv("MONGODB_DB_NAME", "ziz_db")
        self._database = self._client.get_database(db_name)
        self._last_activity = time.time()

        # Start cleanup task if not already running
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def close_connection(self):
        """Explicitly close the MongoDB connection."""
        async with self._lock:
            if self._client is not None:
                logger.info("Closing MongoDB connection")
                self._client.close()
                self._client = None
                self._database = None

            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
                self._cleanup_task = None

    async def _cleanup_loop(self):
        """Background task to check for idle connections and clean them up."""
        try:
            while True:
                await asyncio.sleep(10)  # Check every 10 seconds

                current_time = time.time()
                if (current_time - self._last_activity) > self.idle_timeout:
                    async with self._lock:
                        if self._client is not None:
                            logger.info("Closing idle MongoDB connection")
                            self._client.close()
                            self._client = None
                            self._database = None
                            break  # Exit cleanup loop
        except asyncio.CancelledError:
            logger.info("MongoDB cleanup task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in MongoDB cleanup loop: {e}")


# Global connection manager instance
mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
connection_manager = MongoConnectionManager(mongo_url)


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency function to get database instance."""
    return await connection_manager.get_database()


async def close_connections():
    """Close all MongoDB connections."""
    await connection_manager.close_connection()
