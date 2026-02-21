from sqlalchemy.orm import Session
from passlib.context import CryptContext
import hashlib
from user_profile import models, schemas
from authentication import models as auth_models


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
    """Update profile and username (stored on User table)."""
    user = db.query(auth_models.User).filter(auth_models.User.id == user_id).first()
    if not user:
        return None

    profile = get_profile(db, user_id)

    update_data = profile_update.model_dump(exclude_unset=True)

    # Username and full_name live on auth_models.User, not UserProfile.
    new_username = update_data.pop("username", None)
    new_full_name = update_data.pop("full_name", None)

    if new_username is not None:
        normalized_username = new_username.lower().strip()
        existing_user = db.query(auth_models.User).filter(
            auth_models.User.username == normalized_username,
            auth_models.User.id != user_id
        ).first()
        if existing_user:
            raise ValueError("Username already taken")
        user.username = normalized_username
        
    if new_full_name is not None:
        user.full_name = new_full_name.strip() if new_full_name else None

    if not profile:
        phone_number = update_data.get("phone_number")
        if not phone_number:
            raise ValueError("Phone number is required to create a profile")
        profile = models.UserProfile(user_id=user_id, phone_number=phone_number)
        db.add(profile)

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
