from app.core.config import MONGO_URI
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from threading import Lock
from app.core.config import TEST_MODE
import os

class Database:
    _instance = None
    _lock = Lock()
    _initialized = False

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Database with empty collections"""
        self._client = None
        self._db = None
        self._users_collection = None
        self._resume_collection = None

    def initialize(self, uri: str = None):
        """
        Initialize the database connection
        
        Args:
            uri (str, optional): MongoDB connection URI. Defaults to None (uses MONGO_URI env var)
        """
        if self._client is not None:
            return

        try:
            if TEST_MODE:
                # In test mode, just set up mock collections
                self._db = type('MockDB', (), {})()
                self._users_collection = type('MockCollection', (), {})()
                self._resume_collection = type('MockCollection', (), {})()
                self._initialized = True
                return

            uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017/")
            # Configure connection pooling with optimized settings

            self._client = MongoClient(
                uri,
                maxPoolSize=50,  # Reduced from 100 to prevent excessive connections
                minPoolSize=5,   # Reduced from 10 to allow for graceful scaling
                waitQueueTimeoutMS=30000,  # Increased to 30s to handle bursts
                socketTimeoutMS=60000,     # Increased to 1 minute
                serverSelectionTimeoutMS=10000,  # Increased to 10s
                connectTimeoutMS=10000,    # Added connection timeout
                heartbeatFrequencyMS=10000, # Reduced heartbeat frequency
                appname="resumeai-backend"  # Added app name for better monitoring
            )
            
            # Get the database name from the URI
            uri_parts = uri.split('/')
            db_name = uri_parts[-1].split('?')[0]
            
            self._db = self._client.get_database(db_name)
            
            # Ensure collections exist
            if "auth_collection" not in self._db.list_collection_names():
                self._db.create_collection("auth_collection")
            if "resume_collection" not in self._db.list_collection_names():
                self._db.create_collection("resume_collection")
            
            self._users_collection = self._db.get_collection("auth_collection")
            self._resume_collection = self._db.get_collection("resume_collection")
            
            # Test connection
            self._client.admin.command('ping')
            
            self._initialized = True
            
        except ConnectionFailure as e:
            raise ConnectionError(f"Could not connect to MongoDB: {str(e)}")

    def close(self):
        """Close the database connection"""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            self._users_collection = None
            self._resume_collection = None
            self._initialized = False

    @property
    def client(self) -> MongoClient:
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        return self._client

    @property
    def db(self):
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        return self._db

    @property
    def users_collection(self):
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        return self._users_collection

    @property
    def resume_collection(self):
        if not self._initialized:
            raise RuntimeError("Database not initialized")


