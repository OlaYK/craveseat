from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from authentication.auth import get_current_active_user
from authentication import models as auth_models
from database import get_db
from cravings import crud, schemas
from cloudinary_setup import upload_image

router = APIRouter()


@router.post("/", response_model=schemas.CravingResponse, status_code=status.HTTP_201_CREATED)
async def create_craving(
    craving: schemas.CravingCreate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Create a new craving with auto-generated share token"""
    db_craving = crud.create_craving(db, current_user.id, craving)
    return db_craving


@router.get("/{craving_id}/share-url")
def get_share_url(
    craving_id: str,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get shareable URL for a craving"""
    db_craving = crud.get_craving(db, craving_id)
    if not db_craving:
        raise HTTPException(status_code=404, detail="Craving not found")
    
    if db_craving.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to share this craving")
    
    # Generate full share URL (you can customize the domain)
    base_url = "https://craveseat.com/share"  # Replace with your actual domain
    share_url = f"{base_url}/{db_craving.share_token}"
    
    return {
        "share_token": db_craving.share_token,
        "share_url": share_url,
        "message": "Share this link with anyone to let them view and respond to your craving!"
    }


@router.post("/{craving_id}/upload-image", response_model=schemas.CravingResponse)
async def upload_craving_image(
    craving_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Upload an image for a craving"""
    db_craving = crud.get_craving(db, craving_id)
    if not db_craving:
        raise HTTPException(status_code=404, detail="Craving not found")
    
    if db_craving.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this craving")
    
    try:
        image_url = await upload_image(file, folder="cravings")
        if not image_url:
            raise HTTPException(status_code=500, detail="Image upload failed")
        
        updated_craving = crud.update_craving(
            db, craving_id, schemas.CravingUpdate(image_url=image_url)
        )
        return updated_craving
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


@router.get("/", response_model=List[schemas.CravingResponse])
def list_cravings(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get all cravings with optional filters"""
    return crud.get_cravings(db, skip=skip, limit=limit, status=status, category=category)


@router.get("/my-cravings", response_model=List[schemas.CravingResponse])
def list_my_cravings(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get current user's cravings"""
    return crud.get_user_cravings(db, current_user.id, skip=skip, limit=limit)


@router.get("/{craving_id}", response_model=schemas.CravingWithResponses)
def get_craving(
    craving_id: str,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get a specific craving with its responses"""
    db_craving = crud.get_craving(db, craving_id)
    if not db_craving:
        raise HTTPException(status_code=404, detail="Craving not found")
    return db_craving


@router.put("/{craving_id}", response_model=schemas.CravingResponse)
def update_craving(
    craving_id: str,
    craving_update: schemas.CravingUpdate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Update a craving"""
    db_craving = crud.get_craving(db, craving_id)
    if not db_craving:
        raise HTTPException(status_code=404, detail="Craving not found")
    
    if db_craving.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this craving")
    
    updated_craving = crud.update_craving(db, craving_id, craving_update)
    return updated_craving


@router.delete("/{craving_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_craving(
    craving_id: str,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Delete a craving"""
    db_craving = crud.get_craving(db, craving_id)
    if not db_craving:
        raise HTTPException(status_code=404, detail="Craving not found")
    
    if db_craving.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this craving")
    
    success = crud.delete_craving(db, craving_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete craving")
    return None