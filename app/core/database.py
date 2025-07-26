from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from threading import Lock
import os



class Database:
    _instance = None
    _lock = Lock()
    _initialized = False
    _engine = None
    _sessionmaker = None
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """ Initialize the database connection """
        self._session = None
        
    def initialize(self, uri: str = None):
        """ Initialize the database connection """
        if self._initialized:
            return
        
        try:
            db_url = uri or os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL environment variable is required")
        
            self._engine = create_engine(db_url)
            self._sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
            self._initialized = True
            
            with self._engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()

            
        except Exception as e:
            self._initialized = False
            raise Exception(f"Failed to initialize database: {str(e)}")
        
        
    def get_session(self):
        """ Get a database session """
        if not self._initialized:
            raise Exception("Database is not initialized")
        return self._sessionmaker()
        
    def close(self):
        """ Close the database connection """
        if self._engine:
            self._engine.dispose()
            self._initialized = False
            
database = Database()