import os
import shortuuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

from database import Base, SessionLocal
from authentication.models import User
from user_profile.models import UserProfile
from vendor_profile.models import VendorProfile
from cravings.models import Craving
from responses.models import Response
from notifications.models import Notification

from cravings import crud, schemas, models

# Get a user
db = SessionLocal()
user = db.query(User).first()
if not user:
    print("No user found in DB")
    exit(1)

print(f"Testing with user: {user.username} ({user.id})")

# Create a test craving object
test_craving = schemas.CravingCreate(
    name="Test Craving Numeric",
    description="Test Description",
    category=schemas.CravingCategory.food,
    price_estimate=1000.50,
    delivery_address="Test Address",
    notes="Test notes"
)

try:
    print("Attempting to create craving...")
    db_craving = crud.create_craving(db, user.id, test_craving)
    print(f"Successfully created craving with ID: {db_craving.id}")
    print(f"Share token: {db_craving.share_token}")
    print(f"Category: {db_craving.category}")
except Exception as e:
    print(f"\nFAILED to create craving!")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
