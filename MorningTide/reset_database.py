import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine

def reset_database():
    response = input("⚠️  WARNING: This will DELETE ALL DATA. Continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    print("🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("🔄 Creating tables from SQLAlchemy models...")
    # Import models to register them
    from app.models.user import User
    from app.models.journal_entry import JournalEntry
    
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database reset complete!")
    print("📋 Tables created:")
    print("   - users")
    print("   - journal_entries")

if __name__ == '__main__':
    reset_database()