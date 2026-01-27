"""
Database Configuration with SQLAlchemy
"""

import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy. orm import sessionmaker

DATABASE_PATH = 'morningtide.db'

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(f'sqlite:///{DATABASE_PATH}')
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """Get database connection (raw SQLite)"""
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    return db

def get_session():
    """Get SQLAlchemy session"""
    return SessionLocal()

def init_db():
    """Initialize database with required tables"""
    db = get_db()
    cursor = db.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create journal entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create analysis results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            emotion_score INTEGER NOT NULL,
            top_emotions TEXT NOT NULL,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entry_id) REFERENCES journal_entries(id)
        )
    ''')
    
    db.commit()
    db.close()
    
    # Create SQLAlchemy tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialized successfully")