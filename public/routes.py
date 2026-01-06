from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from cravings import crud as cravings_crud, schemas as cravings_schemas
from responses import crud as responses_crud, schemas as responses_schemas
from user_profile import crud as profile_crud
from notifications import crud as notifications_crud

router = APIRouter()


@router.get("/craving/{share_token}", response_model=cravings_schemas.CravingWithResponses)
def view_shared_craving(share_token: str, db: Session = Depends(get_db)):
    """View a craving via share link (no authentication required)"""
    craving = db.query(cravings_crud.models.Craving).filter(
        cravings_crud.models.Craving.share_token == share_token
    ).first()
    
    if not craving:
        raise HTTPException(status_code=404, detail="Craving not found")
    
    return craving


@router.post("/craving/{share_token}/respond", response_model=responses_schemas.ResponseOut)
def respond_to_shared_craving(
    share_token: str,
    response: responses_schemas.ResponseCreate,
    db: Session = Depends(get_db)
):
    """Respond to a craving anonymously (no authentication required)"""
    # Find craving by share token
    craving = db.query(cravings_crud.models.Craving).filter(
        cravings_crud.models.Craving.share_token == share_token
    ).first()
    
    if not craving:
        raise HTTPException(status_code=404, detail="Craving not found")
    
    # Check if craving is still open
    if craving.status != "open":
        raise HTTPException(status_code=400, detail="Craving is no longer accepting responses")
    
    # Validate anonymous response requirements
    if response.is_anonymous and not response.anonymous_name:
        response.anonymous_name = "Anonymous"
    
    # Create anonymous response (user_id is None)
    db_response = responses_crud.create_response(
        db=db,
        craving_id=craving.id,
        response=response,
        user_id=None  # Anonymous
    )
    
    # Create notification for craving owner
    responder_name = response.anonymous_name if response.is_anonymous else "Someone"
    notifications_crud.notify_craving_response(
        db=db,
        craving_owner_id=craving.user_id,
        craving_id=craving.id,
        response_id=db_response.id,
        responder_name=responder_name
    )
    
    return db_response


@router.get("/profile/{user_id}")
def view_public_profile(user_id: str, db: Session = Depends(get_db)):
    """View public profile (limited info, no authentication required)"""
    from authentication import crud as auth_crud
    
    user = auth_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = profile_crud.get_profile(db, user_id)
    
    # Return limited public info
    return {
        "username": user.username,
        "full_name": user.full_name,
        "bio": profile.bio if profile else None,
        "profile_image": profile.image_url if profile else None,
        "user_type": user.user_type.value,
        "created_at": user.created_at
    }