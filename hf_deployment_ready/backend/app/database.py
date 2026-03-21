"""
Database connection manager
Handles MongoDB connection with fallback to JSON file storage
"""
import logging
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """MongoDB connection manager (optional)"""
    
    def __init__(self):
        self.client = None
        self.db = None
        
        if settings.USE_MONGODB and settings.MONGODB_URL:
            try:
                from pymongo import MongoClient
                self.client = MongoClient(settings.MONGODB_URL)
                self.db = self.client[settings.MONGODB_DB_NAME]
                
                # Test connection
                self.client.server_info()
                logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
                
            except Exception as e:
                logger.warning(
                    f"Could not connect to MongoDB: {e}. "
                    f"Will use JSON file storage instead."
                )
                self.client = None
                self.db = None
        else:
            logger.info("MongoDB disabled. Using JSON file storage.")
    
    def is_connected(self) -> bool:
        """Check if connected to MongoDB"""
        return self.db is not None
    
    def get_collection(self, name: str):
        """Get a MongoDB collection"""
        if self.db is not None:
            return self.db[name]
        return None
    
    def close(self):
        """Close MongoDB connection"""
        if self.client is not None:
            self.client.close()
            logger.info("MongoDB connection closed")


# Global database manager instance
db_manager = DatabaseManager()
