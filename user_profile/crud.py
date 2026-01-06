from sqlalchemy.orm import Session
from passlib.context import CryptContext
from user_profile import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)


def get_profile(db: Session, user_id: str):
    return db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()


def create_profile(db: Session, user_id: str, profile: schemas.UserProfileCreate, image_url: str = None):
    db_profile = models.UserProfile(
        user_id=user_id,
        bio=profile.bio,
        phone_number=profile.phone_number,
        delivery_address=profile.delivery_address,
        image_url=image_url
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def update_profile(db: Session, user_id: str, profile_update: schemas.UserProfileUpdate):
    profile = get_profile(db, user_id)
    if not profile:
        profile = models.UserProfile(user_id=user_id)
        db.add(profile)

    # Update only fields that were provided
    for field, value in profile_update.dict(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


def change_user_password(db: Session, user_id: str, old_password: str, new_password: str):
    from authentication.models import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    if not verify_password(old_password, user.hashed_password):
        return False

    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True