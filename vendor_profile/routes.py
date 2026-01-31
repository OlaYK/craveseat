from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from authentication.auth import get_current_active_user
from authentication import models as auth_models, schemas as auth_schemas
from authentication.models import UserType
from authentication.role_helpers import require_vendor_role, can_access_vendor_features
from database import get_db
from vendor_profile import crud, schemas
from cloudinary_setup import upload_image

router = APIRouter()


# ---------------- SERVICE CATEGORIES ----------------
@router.get("/categories", response_model=auth_schemas.StandardResponse[list[schemas.ServiceCategoryResponse]])
def list_service_categories(db: Session = Depends(get_db)):
    """Get all service categories"""
    categories = crud.get_service_categories(db)
    return {
        "success": True,
        "message": "Categories retrieved successfully",
        "data": categories
    }


# ---------------- VENDOR PROFILE ----------------
@router.post("/", response_model=auth_schemas.StandardResponse[schemas.VendorProfileResponse])
def create_vendor_profile(
    profile: schemas.VendorProfileCreate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Create vendor profile - any user can become a vendor"""
    # Check if vendor profile already exists
    existing_profile = crud.get_vendor_profile(db, current_user.id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Vendor profile already exists.")

    # Create the vendor profile
    # First, verify if the category exists to avoid FK error (500)
    category = db.query(crud.models.ServiceCategory).filter(crud.models.ServiceCategory.id == profile.service_category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail=f"Service category with ID {profile.service_category_id} does not exist. Check GET /vendor/categories for valid IDs.")

    new_profile = crud.create_vendor_profile(db, current_user.id, profile)
    
    # Update user to have both roles if they only had user role
    if current_user.user_type == UserType.user:
        current_user.user_type = UserType.both
        current_user.active_role = UserType.vendor
        db.commit()
    
    return {
        "success": True,
        "message": "Vendor profile created successfully",
        "data": new_profile
    }


@router.get("/", response_model=auth_schemas.StandardResponse[schemas.VendorProfileResponse])
def get_vendor_profile(
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get current vendor's profile"""
    require_vendor_role(current_user)

    profile = crud.get_vendor_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Vendor profile not found.")
    return {
        "success": True,
        "message": "Vendor profile retrieved successfully",
        "data": profile
    }


@router.put("/", response_model=auth_schemas.StandardResponse[schemas.VendorProfileResponse])
def update_vendor_profile(
    profile_update: schemas.VendorProfileUpdate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Update vendor profile"""
    require_vendor_role(current_user)

    updated_profile = crud.update_vendor_profile(db, current_user.id, profile_update)
    if not updated_profile:
        raise HTTPException(status_code=404, detail="Vendor profile not found.")
    return {
        "success": True,
        "message": "Vendor profile updated successfully",
        "data": updated_profile
    }


# ---------------- IMAGE UPLOADS ----------------
@router.post("/upload-logo", response_model=auth_schemas.StandardResponse[schemas.VendorProfileResponse])
async def upload_vendor_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Upload vendor logo"""
    require_vendor_role(current_user)
    
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
        return {
            "success": True,
            "message": "Vendor logo uploaded successfully",
            "data": updated_profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logo upload failed: {str(e)}")


@router.post("/upload-banner", response_model=auth_schemas.StandardResponse[schemas.VendorProfileResponse])
async def upload_vendor_banner(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Upload vendor banner"""
    require_vendor_role(current_user)
    
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
        return {
            "success": True,
            "message": "Vendor banner uploaded successfully",
            "data": updated_profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Banner upload failed: {str(e)}")


# ---------------- VENDOR ITEMS ----------------
@router.post("/items", response_model=auth_schemas.StandardResponse[schemas.VendorItemResponse])
def add_item(
    item: schemas.VendorItemCreate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Add item (requires vendor profile first)"""
    require_vendor_role(current_user)
    
    # Check if vendor profile exists
    profile = crud.get_vendor_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=400, detail="Create vendor profile before adding items.")
    
    new_item = crud.add_vendor_item(db, current_user.id, item)
    return {
        "success": True,
        "message": "Item added successfully",
        "data": new_item
    }


@router.get("/items", response_model=auth_schemas.StandardResponse[list[schemas.VendorItemResponse]])
def list_vendor_items(
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get all items for current vendor"""
    require_vendor_role(current_user)
    items = crud.get_vendor_items(db, current_user.id)
    return {
        "success": True,
        "message": "Vendor items retrieved successfully",
        "data": items
    }


@router.post("/items/{item_id}/upload-image", response_model=auth_schemas.StandardResponse[schemas.VendorItemResponse])
async def upload_item_image(
    item_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Upload image for a specific item"""
    require_vendor_role(current_user)
    
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
        return {
            "success": True,
            "message": "Item image uploaded successfully",
            "data": item
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


@router.delete("/items/{item_id}", response_model=auth_schemas.GenericResponse)
def delete_vendor_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Delete an item"""
    require_vendor_role(current_user)
    
    item = crud.get_vendor_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    
    if item.vendor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this item.")
    
    success = crud.delete_vendor_item(db, item_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete item")
    return {
        "success": True,
        "message": "Item deleted successfully"
    }