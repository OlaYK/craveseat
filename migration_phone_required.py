"""
Migration script to make phone_number required in user_profiles table.
This script:
1. Updates any existing NULL phone_number values to a placeholder
2. Alters the column to be NOT NULL
"""

from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL

def migrate_phone_number_to_required():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        
        try:
            # Step 1: Update any NULL phone numbers to a placeholder
            # This ensures existing users won't break
            result = conn.execute(
                text("""
                    UPDATE user_profiles 
                    SET phone_number = 'NOT_PROVIDED' 
                    WHERE phone_number IS NULL OR phone_number = ''
                """)
            )
            print(f"Updated {result.rowcount} records with placeholder phone numbers")
            
            # Step 2: Alter the column to be NOT NULL
            # Note: SQLite doesn't support ALTER COLUMN directly, so we need to recreate the table
            # Check if we're using SQLite
            if 'sqlite' in SQLALCHEMY_DATABASE_URL:
                print("Detected SQLite database - recreating table with new schema")
                
                # For SQLite, we need to:
                # 1. Create a new table with the correct schema
                # 2. Copy data from old table
                # 3. Drop old table
                # 4. Rename new table
                
                conn.execute(text("""
                    CREATE TABLE user_profiles_new (
                        user_id VARCHAR NOT NULL,
                        bio VARCHAR,
                        phone_number VARCHAR NOT NULL,
                        delivery_address VARCHAR,
                        image_url VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        PRIMARY KEY (user_id),
                        FOREIGN KEY(user_id) REFERENCES users (id)
                    )
                """))
                
                conn.execute(text("""
                    INSERT INTO user_profiles_new 
                    (user_id, bio, phone_number, delivery_address, image_url, created_at, updated_at)
                    SELECT user_id, bio, phone_number, delivery_address, image_url, created_at, updated_at
                    FROM user_profiles
                """))
                
                conn.execute(text("DROP TABLE user_profiles"))
                conn.execute(text("ALTER TABLE user_profiles_new RENAME TO user_profiles"))
                
                print("Table recreated successfully")
            else:
                # For PostgreSQL/MySQL
                conn.execute(text("""
                    ALTER TABLE user_profiles 
                    ALTER COLUMN phone_number SET NOT NULL
                """))
                print("Column altered successfully")
            
            # Commit the transaction
            trans.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"Migration failed: {e}")
            raise

if __name__ == "__main__":
    print("Starting migration to make phone_number required...")
    migrate_phone_number_to_required()
