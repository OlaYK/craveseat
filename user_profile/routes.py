from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from authentication.auth import get_current_active_user
from authentication import crud as auth_crud, models as auth_models
from database import get_db
from user_profile import crud, schemas
from cloudinary_setup import upload_image

router = APIRouter()


@router.post("/", response_model=schemas.UserProfile)
def create_profile(
    profile: schemas.UserProfileCreate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    # Check if profile already exists
    existing_profile = crud.get_profile(db, current_user.id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    return crud.create_profile(
        db=db,
        user_id=current_user.id,
        profile=profile
    )


@router.get("/", response_model=schemas.UserProfile)
def read_profile(
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    db_profile = crud.get_profile(db, current_user.id)
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db_profile


@router.put("/", response_model=schemas.UserProfile)
def update_profile(
    profile_update: schemas.UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    return crud.update_profile(db, current_user.id, profile_update)


@router.post("/upload-image", response_model=schemas.UserProfile)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    try:
        # Upload to Cloudinary
        image_url = await upload_image(file)

        if not image_url:
            raise HTTPException(status_code=500, detail="Image upload failed — no URL returned")

        # Update the user's profile with the new image URL
        updated_profile = crud.update_profile(
            db,
            current_user.id,
            schemas.UserProfileUpdate(image_url=image_url)
        )

        return updated_profile

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


@router.post("/change-password")
def change_password(
    request: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    user = auth_crud.get_user_by_username(db, current_user.username)

    if not auth_crud.verify_password(request.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    user.hashed_password = auth_crud.get_password_hash(request.new_password)
    db.commit()
    db.refresh(user)
    return {"msg": "Password updated successfully"}