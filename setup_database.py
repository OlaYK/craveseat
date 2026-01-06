"""
Run this script to set up your database properly
"""
from database import SessionLocal, engine, Base
from vendor_profile.models import ServiceCategory, VendorProfile, VendorItem
from authentication.models import User
from user_profile.models import UserProfile
from cravings.models import Craving
from responses.models import Response

def setup_database():
    print("🔧 Setting up database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created")
    
    # Seed service categories
    db = SessionLocal()
    try:
        categories = [
            {"name": "Food & Beverages", "description": "Restaurants, cafes, food delivery"},
            {"name": "Groceries", "description": "Grocery stores, supermarkets"},
            {"name": "Bakery", "description": "Bakeries, pastries, bread"},
            {"name": "Catering", "description": "Event catering services"},
            {"name": "Fast Food", "description": "Quick service restaurants"},
            {"name": "Snacks & Treats", "description": "Snack shops, candy stores"},
            {"name": "Beverages Only", "description": "Juice bars, coffee shops, smoothie bars"},
        ]
        
        added_count = 0
        for cat_data in categories:
            existing = db.query(ServiceCategory).filter(
                ServiceCategory.name == cat_data["name"]
            ).first()
            
            if not existing:
                new_cat = ServiceCategory(**cat_data)
                db.add(new_cat)
                added_count += 1
        
        db.commit()
        print(f"✅ Service categories seeded ({added_count} new categories added)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n🎉 Database setup complete!")
    print("\nNext steps:")
    print("1. Delete vendor_media.py file")
    print("2. Run: alembic revision --autogenerate -m 'fix vendor tables'")
    print("3. Run: alembic upgrade head")
    print("4. Start server: uvicorn main:app --reload")

if __name__ == "__main__":
    setup_database()