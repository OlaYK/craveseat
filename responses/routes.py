from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from authentication.auth import get_current_active_user
from authentication import models as auth_models
from database import get_db
from responses import crud, schemas
from cravings import crud as cravings_crud

router = APIRouter()


@router.post("/", response_model=schemas.ResponseOut, status_code=status.HTTP_201_CREATED)
def create_response(
    craving_id: str,
    response: schemas.ResponseCreate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Create a response to a craving (authenticated user, optionally anonymous)"""
    # Check if craving exists
    db_craving = cravings_crud.get_craving(db, craving_id)
    if not db_craving:
        raise HTTPException(status_code=404, detail="Craving not found")
    
    # Don't allow users to respond to their own cravings
    if db_craving.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot respond to your own craving")
    
    # Check if craving is still open
    if db_craving.status != "open":
        raise HTTPException(status_code=400, detail="Craving is no longer accepting responses")
    
    # Create response (user_id is provided but can be hidden if is_anonymous=True)
    db_response = crud.create_response(db, craving_id, response, current_user.id)
    
    # Create notification
    from notifications import crud as notifications_crud
    responder_name = response.anonymous_name if response.is_anonymous else current_user.username
    notifications_crud.notify_craving_response(
        db=db,
        craving_owner_id=db_craving.user_id,
        craving_id=craving_id,
        response_id=db_response.id,
        responder_name=responder_name
    )
    
    return db_response


@router.get("/craving/{craving_id}", response_model=List[schemas.ResponseOut])
def list_craving_responses(
    craving_id: str,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get all responses for a specific craving"""
    # Check if craving exists
    db_craving = cravings_crud.get_craving(db, craving_id)
    if not db_craving:
        raise HTTPException(status_code=404, detail="Craving not found")
    
    return crud.get_craving_responses(db, craving_id)


@router.get("/my-responses", response_model=List[schemas.ResponseOut])
def list_my_responses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get current user's responses"""
    return crud.get_user_responses(db, current_user.id, skip=skip, limit=limit)


@router.get("/{response_id}", response_model=schemas.ResponseOut)
def get_response(
    response_id: str,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get a specific response"""
    db_response = crud.get_response(db, response_id)
    if not db_response:
        raise HTTPException(status_code=404, detail="Response not found")
    return db_response


@router.put("/{response_id}", response_model=schemas.ResponseOut)
def update_response(
    response_id: str,
    response_update: schemas.ResponseUpdate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Update a response (only the responder or craving owner can update)"""
    db_response = crud.get_response(db, response_id)
    if not db_response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Get the craving to check ownership
    db_craving = cravings_crud.get_craving(db, db_response.craving_id)
    
    # Only the response creator can edit message, craving owner can change status
    if response_update.message and db_response.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this response message")
    
    if response_update.status and db_craving.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only craving owner can change response status")
    
    updated_response = crud.update_response(db, response_id, response_update)
    return updated_response


@router.delete("/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_response(
    response_id: str,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Delete a response (only the responder can delete)"""
    db_response = crud.get_response(db, response_id)
    if not db_response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    if db_response.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this response")
    
    success = crud.delete_response(db, response_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete response")
    return None