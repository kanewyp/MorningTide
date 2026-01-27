# test_database.py
from app.database import engine, SessionLocal, Base
from sqlalchemy import text

def test_database_connection():
    """Test database connectivity."""
    print("\nTesting database connection...")
    
    try:
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"  ✓ Database connection successful")
            return True
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        return False

def test_create_tables():
    """Test table creation."""
    print("\nTesting table creation...")
    
    try:
        Base.metadata. create_all(bind=engine)
        print(f"  ✓ Tables created successfully")
        return True
    except Exception as e:
        print(f"  ✗ Table creation failed: {e}")
        return False

def test_session():
    """Test database session."""
    print("\nTesting database session...")
    
    try:
        db = SessionLocal()
        # Try a simple query
        result = db. execute(text("SELECT 1")).scalar()
        db.close()
        print(f"  ✓ Database session works")
        return True
    except Exception as e:
        print(f"  ✗ Database session failed: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()
    test_create_tables()
    test_session()