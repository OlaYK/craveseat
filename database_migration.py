"""
Migration script to convert existing usernames and emails to lowercase
Run this ONCE after updating the code

Usage: python migrate_lowercase.py
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def migrate_to_lowercase():
    """Convert all existing usernames and emails to lowercase"""
    db = SessionLocal()
    
    try:
        print("🔄 Starting migration to lowercase usernames and emails...")
        
        # Update usernames to lowercase
        result = db.execute(
            text("UPDATE users SET username = LOWER(username), email = LOWER(email)")
        )
        
        db.commit()
        print(f"✅ Migration complete! Updated {result.rowcount} users")
        print("✅ All usernames and emails are now lowercase")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
    finally:
        db.close()


def check_duplicates():
    """Check for potential duplicate usernames/emails after lowercase conversion"""
    db = SessionLocal()
    
    try:
        print("\n🔍 Checking for duplicates...")
        
        # Check duplicate usernames
        result = db.execute(
            text("""
                SELECT LOWER(username) as username, COUNT(*) as count
                FROM users
                GROUP BY LOWER(username)
                HAVING COUNT(*) > 1
            """)
        )
        
        duplicates = result.fetchall()
        if duplicates:
            print("⚠️  WARNING: Found duplicate usernames:")
            for dup in duplicates:
                print(f"   - {dup[0]}: {dup[1]} occurrences")
        else:
            print("✅ No duplicate usernames found")
        
        # Check duplicate emails
        result = db.execute(
            text("""
                SELECT LOWER(email) as email, COUNT(*) as count
                FROM users
                GROUP BY LOWER(email)
                HAVING COUNT(*) > 1
            """)
        )
        
        duplicates = result.fetchall()
        if duplicates:
            print("⚠️  WARNING: Found duplicate emails:")
            for dup in duplicates:
                print(f"   - {dup[0]}: {dup[1]} occurrences")
        else:
            print("✅ No duplicate emails found")
            
    except Exception as e:
        print(f"❌ Check failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION: Convert to Lowercase")
    print("=" * 60)
    
    # First check for potential issues
    check_duplicates()
    
    # Ask for confirmation
    print("\n⚠️  This will convert ALL usernames and emails to lowercase.")
    response = input("Continue? (yes/no): ")
    
    if response.lower() == 'yes':
        migrate_to_lowercase()
        print("\n" + "=" * 60)
        print("Migration complete! You can now use the updated code.")
        print("=" * 60)
    else:
        print("❌ Migration cancelled")