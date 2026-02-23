import os
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found")
    exit(1)

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

# Check actual Postgres column types
with engine.connect() as conn:
    print("\nDetailed column types (Postgres):")
    result = conn.execute(text("""
        SELECT column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'cravings'
    """))
    for row in result:
        print(f"- {row[0]}: {row[1]} ({row[2]})")
with engine.connect() as conn:
    try:
        result = conn.execute(text("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE pg_type.typname = 'cravingcategory'"))
        print("\nEnum values for 'cravingcategory':")
        for row in result:
            print(f"- {row[0]}")
    except Exception as e:
        print(f"\nCould not fetch enum values: {e}")
