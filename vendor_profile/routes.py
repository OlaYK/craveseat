from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from authentication.auth import get_current_active_user
from authentication import models as auth_models
from authentication.models import UserType
from database import get_db
from vendor_profile import crud, schemas
from cloudinary_setup import upload_image

router = APIRouter()


# ---------------- SERVICE CATEGORIES ----------------
@router.get("/categories", response_model=list[schemas.ServiceCategoryResponse])
def list_service_categories(db: Session = Depends(get_db)):
    """Get all service categories"""
    return crud.get_service_categories(db)


# ---------------- VENDOR PROFILE ----------------
@router.post("/", response_model=schemas.VendorProfileResponse)
def create_vendor_profile(
    profile: schemas.VendorProfileCreate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Create vendor profile (vendors only)"""
    if current_user.user_type != UserType.vendor:
        raise HTTPException(status_code=403, detail="Only vendors can create a vendor profile.")

    existing_profile = crud.get_vendor_profile(db, current_user.id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Vendor profile already exists.")

    return crud.create_vendor_profile(db, current_user.id, profile)


@router.get("/", response_model=schemas.VendorProfileResponse)
def get_vendor_profile(
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get current vendor's profile"""
    if current_user.user_type != UserType.vendor:
        raise HTTPException(status_code=403, detail="Only vendors can access this route.")

    profile = crud.get_vendor_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Vendor profile not found.")
    return profile


@router.put("/", response_model=schemas.VendorProfileResponse)
def update_vendor_profile(
    profile_update: schemas.VendorProfileUpdate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Update vendor profile"""
    if current_user.user_type != UserType.vendor:
        raise HTTPException(status_code=403, detail="Only vendors can update their profile.")

    updated_profile = crud.update_vendor_profile(db, current_user.id, profile_update)
    if not updated_profile:
        raise HTTPException(status_code=404, detail="Vendor profile not found.")
    return updated_profile


# ---------------- IMAGE UPLOADS ----------------
@router.post("/upload-logo", response_model=schemas.VendorProfileResponse)
async def upload_vendor_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Upload vendor logo"""
    if current_user.user_type != UserType.vendor:
        raise HTTPException(status_code=403, detail="Only vendors can upload logos.")
    
    profile = crud.get_vendor_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Vendor profile not found. Create profile first.")
    
    try:
        logo_url = await upload_image(file, folder="vendor_logos")
        if not logo_url:
            raise HTTPException(status_code=500, detail="Logo upload failed")
        
        updated_profile = crud.update_vendor_profile(
            db,
            current_user.id,
            schemas.VendorProfileUpdate(logo_url=logo_url)
        )
        return updated_profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logo upload failed: {str(e)}")


@router.post("/upload-banner", response_model=schemas.VendorProfileResponse)
async def upload_vendor_banner(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Upload vendor banner"""
    if current_user.user_type != UserType.vendor:
        raise HTTPException(status_code=403, detail="Only vendors can upload banners.")
    
    profile = crud.get_vendor_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Vendor profile not found. Create profile first.")
    
    try:
        banner_url = await upload_image(file, folder="vendor_banners")
        if not banner_url:
            raise HTTPException(status_code=500, detail="Banner upload failed")
        
        updated_profile = crud.update_vendor_profile(
            db,
            current_user.id,
            schemas.VendorProfileUpdate(banner_url=banner_url)
        )
        return updated_profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Banner upload failed: {str(e)}")


# ---------------- VENDOR ITEMS ----------------
@router.post("/items", response_model=schemas.VendorItemResponse)
def add_item(
    item: schemas.VendorItemCreate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Add item (requires vendor profile first)"""
    if current_user.user_type != UserType.vendor:
        raise HTTPException(status_code=403, detail="Only vendors can add items.")
    
    # Check if vendor profile exists
    profile = crud.get_vendor_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=400, detail="Create vendor profile before adding items.")
    
    return crud.add_vendor_item(db, current_user.id, item)


@router.get("/items", response_model=list[schemas.VendorItemResponse])
def list_vendor_items(
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get all items for current vendor"""
    if current_user.user_type != UserType.vendor:
        raise HTTPException(status_code=403, detail="Only vendors can view their items.")
    return crud.get_vendor_items(db, current_user.id)


@router.post("/items/{item_id}/upload-image", response_model=schemas.VendorItemResponse)
async def upload_item_image(
    item_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Upload image for a specific item"""
    if current_user.user_type != UserType.vendor:
        raise HTTPException(status_code=403, detail="Only vendors can upload item images.")
    
    item = crud.get_vendor_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    
    if item.vendor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this item.")
    
    try:
        image_url = await upload_image(file, folder="vendor_items")
        if not image_url:
            raise HTTPException(status_code=500, detail="Image upload failed")
        
        item.item_image_url = image_url
        db.commit()
        db.refresh(item)
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Delete an item"""
    if current_user.user_type != UserType.vendor:
        raise HTTPException(status_code=403, detail="Only vendors can delete their items.")
    
    item = crud.get_vendor_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    
    if item.vendor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this item.")
    
    success = crud.delete_vendor_item(db, item_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete item")
    return None