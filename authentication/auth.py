import os
import re
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, APIRouter, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import shortuuid

try:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token
except ImportError:  # pragma: no cover - handled at runtime if optional dependency missing
    google_requests = None
    google_id_token = None

from authentication import schemas, models, crud
from database import get_db, engine
from vendor_profile.models import VendorProfile
from user_profile.models import UserProfile


router = APIRouter()

models.Base.metadata.create_all(bind=engine)


SECRET_KEY = os.getenv("SECRET_KEY", "e5a50e37f6c8c6733b341610b468e5a5f53e164c12f4eac4069586a544497d1e")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")) 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, identifier: str, password: str):
    # Convert to lowercase for case-insensitive login
    identifier = identifier.lower().strip()
    
    # Try username first
    user = crud.get_user_by_username(db, identifier)
    
    # If not found, try email
    if not user:
        user = crud.get_user_by_email(db, identifier)
        
    if not user:
        return None
    if not crud.verify_password(password, user.hashed_password):
        return None
    return user


def _build_user_data(user: models.User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "user_type": user.user_type.value,
        "is_active": user.is_active,
        "disabled": user.disabled,
        "active_role": user.active_role.value if user.active_role else user.user_type.value,
        "bio": user.profile.bio if user.profile else None,
        "phone_number": user.profile.phone_number if user.profile else None,
        "delivery_address": user.profile.delivery_address if user.profile else None,
        "image_url": user.profile.image_url if user.profile else None,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def _generate_unique_username(db: Session, email: str) -> str:
    base_username = re.sub(r"[^a-z0-9_]", "", email.split("@")[0].lower()) or "user"
    candidate = base_username
    suffix = 1

    while crud.get_user_by_username(db, candidate):
        candidate = f"{base_username}{suffix}"
        suffix += 1

    return candidate


def _verify_google_id_token(id_token: str) -> dict:
    if google_id_token is None or google_requests is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google auth dependency missing. Install `google-auth`."
        )

    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID is not configured"
        )

    try:
        payload = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            google_client_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )

    issuer = payload.get("iss")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token issuer"
        )

    return payload


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
            "user": _build_user_data(created_user)
        }
    }


@router.post("/login", response_model=schemas.GenericResponse)
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Log in with email/username and password (JSON format)
    
    Returns success message with access token
    """
    user = authenticate_user(db, login_data.email_or_username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
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
            "user": _build_user_data(user)
        }
    }


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Hybrid token endpoint. Supports both JSON (app) and Form Data (Swagger UI).
    """
    content_type = request.headers.get("Content-Type", "")
    username = None
    password = None

    if "application/json" in content_type:
        try:
            data = await request.json()
            username = data.get("email_or_username") or data.get("username")
            password = data.get("password")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
    else:
        # Fallback to form data (Standard for Swagger UI)
        try:
            form_data = await request.form()
            username = form_data.get("username")
            password = form_data.get("password")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid form data")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username/Email and password are required"
        )

    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
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


@router.post("/google", response_model=schemas.GenericResponse)
def google_auth(
    request: schemas.GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Sign up or sign in with Google ID token.
    """
    payload = _verify_google_id_token(request.id_token)

    email = payload.get("email")
    email_verified = payload.get("email_verified")
    full_name = payload.get("name")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email is required"
        )

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google email is not verified"
        )

    email = email.lower().strip()
    user = crud.get_user_by_email(db, email)
    is_new_user = False

    if user and user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact support."
        )

    if not user:
        if not request.phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required for first-time Google signup"
            )

        username = _generate_unique_username(db, email)
        user = models.User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=crud.get_password_hash(shortuuid.uuid()),
            user_type=models.UserType.user,
            disabled=False,
        )
        db.add(user)
        db.flush()

        db_profile = UserProfile(
            user_id=user.id,
            phone_number=request.phone_number,
        )
        db.add(db_profile)
        is_new_user = True
    else:
        if full_name and not user.full_name:
            user.full_name = full_name

        if not user.profile:
            if not request.phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number is required to complete your profile"
                )

            db_profile = UserProfile(
                user_id=user.id,
                phone_number=request.phone_number,
            )
            db.add(db_profile)

    db.commit()
    db.refresh(user)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {
        "success": True,
        "message": "Google authentication successful",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "is_new_user": is_new_user,
            "user": _build_user_data(user)
        }
    }


@router.get("/users/me", response_model=schemas.GenericResponse)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    """
    Get current user information
    
    Returns user profile with success message
    """
    return {
        "success": True,
        "message": "User retrieved successfully",
        "data": _build_user_data(current_user)
    }


@router.put("/users/me/change-password", response_model=schemas.GenericResponse)
def change_password(
    request: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Change user password
    
    Returns success message
    """
    if not crud.verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    hashed_new_pw = crud.get_password_hash(request.new_password)
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
        "data": _build_user_data(db_user)
    }


@router.post("/switch-role", response_model=schemas.GenericResponse)
def switch_role(
    request: schemas.SwitchRoleRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Switch between user and vendor roles
    
    Returns success message with new active role
    """
    target_role = request.target_role

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
        "message": "Current role retrieved successfully",
        "data": {
            "active_role": current_user.active_role.value if current_user.active_role else current_user.user_type.value,
            "user_type": current_user.user_type.value,
            "has_user_profile": bool(current_user.profile),
            "has_vendor_profile": bool(current_user.vendor_profile),
            "can_switch_to_vendor": bool(current_user.vendor_profile),
            "can_switch_to_user": bool(current_user.profile)
        }
    }
