from app.core.config import MONGO_URI
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from threading import Lock
import os

class Database:
    _instance = None
    _lock = Lock()

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
            uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017/")
            self._client = MongoClient(uri)
            self._db = self._client.get_database("resume_reviewer")
            self._users_collection = self._db.get_collection("auth_collection")
            self._resume_collection = self._db.get_collection("resume_collection")
            # Test connection
            self._client.admin.command('ping')
            print(f"Successfully connected to MongoDB at {uri}")
        except ConnectionFailure as e:
            raise ConnectionError(f"Could not connect to MongoDB: {str(e)}")

        # Initialize database if it doesn't exist
        if "resume_reviewer" not in self._client.list_database_names():
            self._db.create_collection("auth_collection")
            self._db.create_collection("resume_collection")
            print("Database and collections created successfully.")
            print("Database already exists.")

    @property
    def client(self) -> MongoClient:
        return self._client

    @property
    def db(self):
        return self._db

    @property
    def users_collection(self):
        return self._users_collection

    @property
    def resume_collection(self):
        return self._resume_collection


