from sqlalchemy.orm import Session
from passlib.context import CryptContext
from user_profile import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)


def get_profile(db: Session, user_id: str):
    """Get user profile - returns None if doesn't exist"""
    return db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()


def create_profile(db: Session, user_id: str, bio: str = None, phone_number: str = None, delivery_address: str = None, image_url: str = None):
    """Create a new profile - used internally during signup"""
    db_profile = models.UserProfile(
        user_id=user_id,
        bio=bio,
        phone_number=phone_number,
        delivery_address=delivery_address,
        image_url=image_url
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def update_profile(db: Session, user_id: str, profile_update: schemas.UserProfileUpdate):
    """Update profile - creates if doesn't exist. Also updates username if provided."""
    from authentication.models import User
    from fastapi import HTTPException
    
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get or create profile
    profile = get_profile(db, user_id)
    if not profile:
        # Create new profile if it doesn't exist
        profile = models.UserProfile(user_id=user_id)
        db.add(profile)
    
    # Extract update data (only fields that were explicitly set)
    update_data = profile_update.dict(exclude_unset=True)
    
    # Handle username update separately (it's in the User table, not UserProfile)
    if 'username' in update_data:
        new_username = update_data.pop('username')
        if new_username and new_username != user.username:
            # Check if username is already taken
            existing_user = db.query(User).filter(
                User.username == new_username.lower(),
                User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already taken")
            
            # Update username
            user.username = new_username.lower()
    
    # Update profile fields (bio, phone_number, delivery_address, image_url)
    for field, value in update_data.items():
        if hasattr(profile, field):
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    db.refresh(user)
    return profile


def change_user_password(db: Session, user_id: str, old_password: str, new_password: str):
    """Change user password"""
    from authentication.models import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    if not verify_password(old_password, user.hashed_password):
        return False

    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True