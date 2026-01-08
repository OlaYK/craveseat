from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from authentication.auth import get_current_active_user
from authentication import crud as auth_crud, models as auth_models
from database import get_db
from user_profile import crud, schemas
from cloudinary_setup import upload_image

router = APIRouter()


@router.get("/", response_model=schemas.UserProfile)
def get_profile(
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get current user's profile with all user details"""
    db_profile = crud.get_profile(db, current_user.id)
    
    # Build complete profile response
    profile_data = {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "user_type": current_user.user_type.value,
        "is_active": current_user.is_active,
        "bio": db_profile.bio if db_profile else None,
        "phone_number": db_profile.phone_number if db_profile else None,
        "delivery_address": db_profile.delivery_address if db_profile else None,
        "image_url": db_profile.image_url if db_profile else None,
        "created_at": db_profile.created_at if db_profile else current_user.created_at,
        "updated_at": db_profile.updated_at if db_profile else current_user.updated_at,
    }
    
    return profile_data


@router.patch("/", response_model=schemas.UserProfile)
def update_profile(
    profile_update: schemas.UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """
    Update user profile including:
    - username (must be unique)
    - phone_number (validated format)
    - bio
    - delivery_address
    - image_url
    """
    updated_profile = crud.update_profile(db, current_user.id, profile_update)
    
    # Refresh user to get updated username if it was changed
    db.refresh(current_user)
    
    # Return complete profile data
    profile_data = {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "user_type": current_user.user_type.value,
        "is_active": current_user.is_active,
        "bio": updated_profile.bio,
        "phone_number": updated_profile.phone_number,
        "delivery_address": updated_profile.delivery_address,
        "image_url": updated_profile.image_url,
        "created_at": updated_profile.created_at,
        "updated_at": updated_profile.updated_at,
    }
    
    return profile_data


@router.post("/upload-image", response_model=schemas.UserProfile)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Upload profile image"""
    try:
        # Upload to Cloudinary
        image_url = await upload_image(file, folder="user_profiles")

        if not image_url:
            raise HTTPException(status_code=500, detail="Image upload failed — no URL returned")

        # Update the user's profile with the new image URL
        updated_profile = crud.update_profile(
            db,
            current_user.id,
            schemas.UserProfileUpdate(image_url=image_url)
        )

        # Return complete profile data
        profile_data = {
            "user_id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "user_type": current_user.user_type.value,
            "is_active": current_user.is_active,
            "bio": updated_profile.bio,
            "phone_number": updated_profile.phone_number,
            "delivery_address": updated_profile.delivery_address,
            "image_url": updated_profile.image_url,
            "created_at": updated_profile.created_at,
            "updated_at": updated_profile.updated_at,
        }
        
        return profile_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


@router.post("/change-password")
def change_password(
    request: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Change user password"""
    user = auth_crud.get_user_by_username(db, current_user.username)

    if not auth_crud.verify_password(request.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    user.hashed_password = auth_crud.get_password_hash(request.new_password)
    db.commit()
    db.refresh(user)
    return {"msg": "Password updated successfully"}