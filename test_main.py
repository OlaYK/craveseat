# test_main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from user_profile import crud, schemas

from cloudinary_setup import upload_image

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Test User Profile API")


# --- CRUD Endpoints for Testing --- #

@app.post("/profile/", response_model=schemas.UserProfile)
def create_profile(profile: schemas.UserProfileCreate, db: Session = Depends(get_db)):
    # Simulate user_id=1 for testing
    db_profile = crud.get_profile_by_user_id(db, user_id=1)
    if db_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
    return crud.create_profile(db, user_id=1, profile=profile)


@app.get("/profile/{user_id}", response_model=schemas.UserProfile)
def read_profile(user_id: int, db: Session = Depends(get_db)):
    db_profile = crud.get_profile_by_user_id(db, user_id=user_id)
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db_profile


@app.put("/profile/{user_id}", response_model=schemas.UserProfile)
def update_profile(user_id: int, profile_update: schemas.UserProfileUpdate, db: Session = Depends(get_db)):
    return crud.update_profile(db, user_id=user_id, profile_update=profile_update)


@app.post("/profile/{user_id}/upload-image", response_model=schemas.UserProfile)
async def upload_profile_image(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    image_url = upload_image(file)
    return crud.update_profile(db, user_id=user_id, profile_update=schemas.UserProfileUpdate(profile_image=image_url))