from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from pydantic import BaseModel

from authentication import schemas, models, crud
from database import get_db, engine, SessionLocal
from vendor_profile.models import VendorProfile
from user_profile.models import UserProfile


router = APIRouter()

models.Base.metadata.create_all(bind=engine)


SECRET_KEY = "e5a50e37f6c8c6733b341610b468e5a5f53e164c12f4eac4069586a544497d1e" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# JSON Login Schema
class LoginRequest(BaseModel):
    username: str
    password: str


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str):
    # Convert to lowercase for case-insensitive login
    user = crud.get_user_by_username(db, username.lower())
    if not user:
        return None
    if not crud.verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Account is disabled. Please contact support."
        )
    return current_user


@router.post("/signup", response_model=schemas.GenericResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Sign up a new user (JSON format)
    
    Returns success message with auto-login token
    """
    # Validate passwords match
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Check if username already exists
    db_user = crud.get_user_by_username(db, username=user.username.lower())
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    db_user = crud.get_user_by_email(db, email=user.email.lower())
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user with profile
    created_user = crud.create_user_with_profile(db=db, user=user)
    
    # Auto-login: Generate token immediately
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": created_user.username}, 
        expires_delta=access_token_expires
    )
    
    return {
        "success": True,
        "message": "Sign up successful",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": created_user.id,
                "username": created_user.username,
                "email": created_user.email,
                "full_name": created_user.full_name,
                "user_type": created_user.user_type.value,
                "is_active": created_user.is_active,
                "active_role": created_user.active_role.value if created_user.active_role else created_user.user_type.value,
                "bio": created_user.profile.bio if created_user.profile else None,
                "phone_number": created_user.profile.phone_number if created_user.profile else None,
                "delivery_address": created_user.profile.delivery_address if created_user.profile else None,
                "image_url": created_user.profile.image_url if created_user.profile else None,
            }
        }
    }


@router.post("/login", response_model=schemas.GenericResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Log in with username and password (JSON format)
    
    Returns success message with access token
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is disabled
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact support."
        )
    
    # Generate access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    
    return {
        "success": True,
        "message": "Log in successful",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "user_type": user.user_type.value,
                "is_active": user.is_active,
                "active_role": user.active_role.value if user.active_role else user.user_type.value,
                "bio": user.profile.bio if user.profile else None,
                "phone_number": user.profile.phone_number if user.profile else None,
                "delivery_address": user.profile.delivery_address if user.profile else None,
                "image_url": user.profile.image_url if user.profile else None,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
        }
    }


# Keep OAuth2 endpoint for compatibility (optional)
@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token endpoint (form-urlencoded)
    
    For API documentation and OAuth2 clients
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=schemas.GenericResponse)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    """
    Get current user information
    
    Returns user profile with success message
    """
    return {
        "success": True,
        "message": "User retrieved successfully",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "user_type": current_user.user_type.value,
            "is_active": current_user.is_active,
            "active_role": current_user.active_role.value if current_user.active_role else current_user.user_type.value,
            "bio": current_user.profile.bio if current_user.profile else None,
            "phone_number": current_user.profile.phone_number if current_user.profile else None,
            "delivery_address": current_user.profile.delivery_address if current_user.profile else None,
            "image_url": current_user.profile.image_url if current_user.profile else None,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at,
        }
    }


@router.put("/users/me/change-password", response_model=schemas.GenericResponse)
def change_password(
    old_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Change user password
    
    Returns success message
    """
    if not crud.verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    hashed_new_pw = crud.get_password_hash(new_password)
    current_user.hashed_password = hashed_new_pw

    db.commit()
    db.refresh(current_user)
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }


@router.get("/users/{user_id}", response_model=schemas.GenericResponse)
def read_user(
    user_id: str, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get user by ID
    
    Returns user information with success message
    """
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "success": True,
        "message": "User retrieved successfully",
        "data": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "user_type": db_user.user_type.value,
            "is_active": db_user.is_active,
            "active_role": db_user.active_role.value if db_user.active_role else db_user.user_type.value,
            "bio": db_user.profile.bio if db_user.profile else None,
            "phone_number": db_user.profile.phone_number if db_user.profile else None,
            "delivery_address": db_user.profile.delivery_address if db_user.profile else None,
            "image_url": db_user.profile.image_url if db_user.profile else None,
            "created_at": db_user.created_at,
            "updated_at": db_user.updated_at,
        }
    }


# Add to authentication/auth.py

@router.post("/switch-role", response_model=schemas.GenericResponse)
def switch_role(
    target_role: str,  # "user" or "vendor"
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Switch between user and vendor roles
    
    Returns success message with new active role
    """
    # Validate target role
    if target_role not in ["user", "vendor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'user' or 'vendor'"
        )
    
    # Check if user has the necessary profile
    if target_role == "vendor":
        vendor_profile = db.query(VendorProfile).filter(
            VendorProfile.vendor_id == current_user.id
        ).first()
        
        if not vendor_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must create a vendor profile before switching to vendor mode. Visit /vendor to set up your vendor profile."
            )
    
    if target_role == "user":
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User profile not found"
            )
    
    # Update user type and active role
    if current_user.user_type != models.UserType.both:
        current_user.user_type = models.UserType.both
    
    current_user.active_role = models.UserType.vendor if target_role == "vendor" else models.UserType.user
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "success": True,
        "message": f"Successfully switched to {target_role} mode",
        "data": {
            "active_role": current_user.active_role.value,
            "user_type": current_user.user_type.value,
            "has_user_profile": bool(current_user.profile),
            "has_vendor_profile": bool(current_user.vendor_profile)
        }
    }


@router.get("/current-role", response_model=schemas.GenericResponse)
def get_current_role(
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get current active role and available roles
    """
    return {
        "success": True,
        "data": {
            "active_role": current_user.active_role.value if current_user.active_role else current_user.user_type.value,
            "user_type": current_user.user_type.value,
            "has_user_profile": bool(current_user.profile),
            "has_vendor_profile": bool(current_user.vendor_profile),
            "can_switch_to_vendor": bool(current_user.vendor_profile),
            "can_switch_to_user": bool(current_user.profile)
        }
    }