import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime

def fix_database():
    """Add missing date column to journal_entries table"""
    
    print("🔍 Checking database...")
    
    conn = sqlite3.connect('morningtide.db')
    cursor = conn.cursor()

    try:
        # Check if journal_entries table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_entries'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ journal_entries table doesn't exist!")
            print("📝 Creating journal_entries table...")
            cursor.execute('''
                CREATE TABLE journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    emotion TEXT,
                    emotion_confidence REAL,
                    emotional_intensity REAL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()
            print("✅ journal_entries table created!")
            return
        
        # Check if date column exists
        cursor.execute("PRAGMA table_info(journal_entries)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Existing columns: {', '.join(columns)}")

        if 'date' not in columns:
            print("📝 Adding date column...")
            
            # Add the date column
            cursor.execute("ALTER TABLE journal_entries ADD COLUMN date DATE")
            
            # Update existing entries with date from created_at or today
            cursor.execute("""
                UPDATE journal_entries 
                SET date = COALESCE(DATE(created_at), DATE('now'))
                WHERE date IS NULL
            """)
            
            conn.commit()
            print("✅ Date column added successfully!")
            print("✅ Existing entries updated with dates")
        else:
            print("✅ Date column already exists!")
        
        # Verify the fix
        cursor.execute("PRAGMA table_info(journal_entries)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"\n✅ Final columns: {', '.join(columns)}")
        
        # Check data
        cursor.execute("SELECT COUNT(*) FROM journal_entries")
        count = cursor.fetchone()[0]
        print(f"📊 Total entries in database: {count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("="*60)
    print("🔧 MorningTide Database Fix Script")
    print("="*60)
    print()
    
    fix_database()
    
    print()
    print("="*60)
    print("✅ Database fix complete!")
    print("="*60)