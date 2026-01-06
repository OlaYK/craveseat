from sqlalchemy.orm import Session
from responses import models, schemas


def create_response(
    db: Session, 
    craving_id: str, 
    response: schemas.ResponseCreate,
    user_id: str = None  # Now optional
):
    """Create a response (authenticated or anonymous)"""
    db_response = models.Response(
        craving_id=craving_id,
        user_id=user_id,  # Will be None for anonymous
        message=response.message,
        is_anonymous=response.is_anonymous,
        anonymous_name=response.anonymous_name,
        anonymous_contact=response.anonymous_contact
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response


def get_response(db: Session, response_id: str):
    return db.query(models.Response).filter(models.Response.id == response_id).first()


def get_craving_responses(db: Session, craving_id: str):
    return db.query(models.Response).filter(
        models.Response.craving_id == craving_id
    ).order_by(models.Response.created_at.desc()).all()


def get_user_responses(db: Session, user_id: str, skip: int = 0, limit: int = 50):
    return db.query(models.Response).filter(
        models.Response.user_id == user_id
    ).order_by(models.Response.created_at.desc()).offset(skip).limit(limit).all()


def update_response(db: Session, response_id: str, response_update: schemas.ResponseUpdate):
    db_response = get_response(db, response_id)
    if not db_response:
        return None
    
    for key, value in response_update.dict(exclude_unset=True).items():
        setattr(db_response, key, value)
    
    db.commit()
    db.refresh(db_response)
    return db_response


def delete_response(db: Session, response_id: str):
    db_response = get_response(db, response_id)
    if db_response:
        db.delete(db_response)
        db.commit()
        return True
    return False