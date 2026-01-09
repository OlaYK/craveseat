from sqlalchemy.orm import Session
from passlib.context import CryptContext
import hashlib
from user_profile import models, schemas


# Configure password hashing with SHA256 pre-hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _prepare_password(password: str) -> str:
    """
    Pre-hash long passwords with SHA256 to ensure they fit bcrypt's 72-byte limit.
    """
    if len(password.encode('utf-8')) > 72:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    return password


def verify_password(plain_password: str, hashed_password: str):
    prepared_password = _prepare_password(plain_password)
    return pwd_context.verify(prepared_password, hashed_password)


def get_password_hash(password: str):
    prepared_password = _prepare_password(password)
    return pwd_context.hash(prepared_password)


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
    """Update profile - creates if doesn't exist"""
    profile = get_profile(db, user_id)
    
    if not profile:
        # Create new profile if it doesn't exist
        profile = models.UserProfile(user_id=user_id)
        db.add(profile)

    # Update only fields that were provided
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


def change_user_password(db: Session, user_id: str, old_password: str, new_password: str):
    """Change user password with proper long password handling"""
    from authentication.models import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    if not verify_password(old_password, user.hashed_password):
        return False

    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True