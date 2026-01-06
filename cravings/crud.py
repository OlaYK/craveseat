from sqlalchemy.orm import Session
from cravings import models, schemas
from datetime import datetime


def create_craving(db: Session, user_id: str, craving: schemas.CravingCreate, image_url: str = None):
    db_craving = models.Craving(
        user_id=user_id,
        title=craving.title,
        description=craving.description,
        category=craving.category,
        anonymous=craving.anonymous,
        delivery_address=craving.delivery_address,
        recommended_vendor=craving.recommended_vendor,
        vendor_contact=craving.vendor_contact,
        notes=craving.notes,
        image_url=image_url
    )
    db.add(db_craving)
    db.commit()
    db.refresh(db_craving)
    return db_craving


def get_craving(db: Session, craving_id: str):
    return db.query(models.Craving).filter(models.Craving.id == craving_id).first()


def get_cravings(db: Session, skip: int = 0, limit: int = 50, status: str = None, category: str = None):
    query = db.query(models.Craving)
    
    if status:
        query = query.filter(models.Craving.status == status)
    if category:
        query = query.filter(models.Craving.category == category)
    
    return query.order_by(models.Craving.created_at.desc()).offset(skip).limit(limit).all()


def get_user_cravings(db: Session, user_id: str, skip: int = 0, limit: int = 50):
    return db.query(models.Craving).filter(
        models.Craving.user_id == user_id
    ).order_by(models.Craving.created_at.desc()).offset(skip).limit(limit).all()


def update_craving(db: Session, craving_id: str, craving_update: schemas.CravingUpdate):
    db_craving = get_craving(db, craving_id)
    if not db_craving:
        return None
    
    for key, value in craving_update.dict(exclude_unset=True).items():
        setattr(db_craving, key, value)
    
    # If status is being changed to fulfilled, set fulfilled_at
    if craving_update.status == schemas.CravingStatus.fulfilled and not db_craving.fulfilled_at:
        db_craving.fulfilled_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_craving)
    return db_craving


def delete_craving(db: Session, craving_id: str):
    db_craving = get_craving(db, craving_id)
    if db_craving:
        db.delete(db_craving)
        db.commit()
        return True
    return False