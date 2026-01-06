# seed_categories.py
from database import SessionLocal
from vendor_profile.models import ServiceCategory

db = SessionLocal()

categories = [
    {"name": "Food & Beverages", "description": "Restaurants, cafes, food delivery"},
    {"name": "Groceries", "description": "Grocery stores, supermarkets"},
    {"name": "Bakery", "description": "Bakeries, pastries, bread"},
    {"name": "Catering", "description": "Event catering services"},
    {"name": "Fast Food", "description": "Quick service restaurants"},
]

for cat in categories:
    existing = db.query(ServiceCategory).filter(ServiceCategory.name == cat["name"]).first()
    if not existing:
        new_cat = ServiceCategory(**cat)
        db.add(new_cat)

db.commit()
db.close()
print("Service categories seeded successfully!")