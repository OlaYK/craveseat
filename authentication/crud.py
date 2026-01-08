from sqlalchemy.orm import Session
from passlib.context import CryptContext
from authentication import models, schemas


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_username(db: Session, username: str):
    # Case-insensitive username lookup
    return db.query(models.User).filter(models.User.username == username.lower()).first()

def get_user_by_id(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    # Case-insensitive email lookup
    return db.query(models.User).filter(models.User.email == email.lower()).first()

def create_user(db: Session, user: schemas.UserCreate):
    """Create user without profile - deprecated, use create_user_with_profile"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username.lower(),
        email=user.email.lower(),
        full_name=user.full_name,
        hashed_password=hashed_password,
        user_type=user.user_type,
        disabled=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_user_with_profile(db: Session, user: schemas.UserCreate):
    """Create user and profile together during signup"""
    from user_profile.models import UserProfile
    
    hashed_password = get_password_hash(user.password)
    
    # Create user
    db_user = models.User(
        username=user.username.lower(),
        email=user.email.lower(),
        full_name=user.full_name,
        hashed_password=hashed_password,
        user_type=user.user_type,
        disabled=False,
    )
    db.add(db_user)
    db.flush()  # Get the user ID without committing
    
    # Create profile with signup data
    db_profile = UserProfile(
        user_id=db_user.id,
        bio=user.bio,
        phone_number=user.phone_number,
        delivery_address=user.delivery_address,
    )
    db.add(db_profile)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user