# vendor_profile/crud.py
from sqlalchemy.orm import Session
from vendor_profile import models, schemas


# ---------------- SERVICE CATEGORY ----------------
def get_service_categories(db: Session):
    return db.query(models.ServiceCategory).all()


# ---------------- VENDOR PROFILE ----------------
def create_vendor_profile(db: Session, vendor_id: str, profile: schemas.VendorProfileCreate):
    db_profile = models.VendorProfile(
        vendor_id=vendor_id,
        business_name=profile.business_name,
        service_category_id=profile.service_category_id,
        vendor_address=profile.vendor_address,
        vendor_phone=profile.vendor_phone,
        vendor_email=profile.vendor_email,
        logo_url=profile.logo_url,
        banner_url=profile.banner_url,
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def get_vendor_profile(db: Session, vendor_id: str):
    return db.query(models.VendorProfile).filter(models.VendorProfile.vendor_id == vendor_id).first()


def update_vendor_profile(db: Session, vendor_id: str, profile_update: schemas.VendorProfileUpdate):
    db_profile = get_vendor_profile(db, vendor_id)
    if not db_profile:
        return None

    for key, value in profile_update.dict(exclude_unset=True).items():
        setattr(db_profile, key, value)

    db.commit()
    db.refresh(db_profile)
    return db_profile


# ---------------- VENDOR ITEMS ----------------
def add_vendor_item(db: Session, vendor_id: str, item_data: schemas.VendorItemCreate):
    new_item = models.VendorItem(
        vendor_id=vendor_id,
        item_name=item_data.item_name,
        item_description=item_data.item_description,
        item_price=item_data.item_price,
        item_image_url=item_data.item_image_url,
        availability_status=item_data.availability_status,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


def get_vendor_items(db: Session, vendor_id: str):
    return db.query(models.VendorItem).filter(models.VendorItem.vendor_id == vendor_id).all()


def get_vendor_item(db: Session, item_id: str):
    return db.query(models.VendorItem).filter(models.VendorItem.id == item_id).first()


def delete_vendor_item(db: Session, item_id: str):
    item = get_vendor_item(db, item_id)
    if item:
        db.delete(item)
        db.commit()
        return True
    return False