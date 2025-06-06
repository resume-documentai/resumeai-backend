from app.core.config import MONGO_URI
from pymongo import MongoClient
from typing import Optional

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        self._client = MongoClient(MONGO_URI)
        self._db = self._client.get_database("resume_reviewer")
        self._users_collection = self._db.get_collection("auth_collection")
        self._resume_collection = self._db.get_collection("resume_collection")
        
        # Initialize database if it doesn't exist
        if "resume_reviewer" not in self._client.list_database_names():
            self._db.create_collection("auth_collection")
            self._db.create_collection("resume_collection")
            print("Database and collections created successfully.")
        else:
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

# Create a global instance that can be imported
mongodb = Database()
