from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from authentication.auth import get_current_active_user
from authentication import models as auth_models, schemas as auth_schemas
from database import get_db
from notifications import crud, schemas

router = APIRouter()


@router.get("/", response_model=auth_schemas.StandardResponse[List[schemas.NotificationResponse]])
def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get current user's notifications"""
    notifications = crud.get_user_notifications(
        db, 
        current_user.id, 
        skip=skip, 
        limit=limit, 
        unread_only=unread_only
    )
    return {
        "success": True,
        "message": "Notifications retrieved successfully",
        "data": notifications
    }


@router.get("/unread-count", response_model=auth_schemas.GenericResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Get count of unread notifications"""
    count = crud.get_unread_count(db, current_user.id)
    return {
        "success": True,
        "message": "Unread count retrieved",
        "data": {"unread_count": count}
    }


@router.post("/mark-read", response_model=auth_schemas.GenericResponse)
def mark_notifications_read(
    notification_data: schemas.NotificationMarkRead,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Mark specific notifications as read"""
    count = crud.mark_notifications_as_read(
        db, 
        notification_data.notification_ids, 
        current_user.id
    )
    return {
        "success": True,
        "message": f"{count} notifications marked as read",
        "data": {"marked_read": count}
    }


@router.post("/mark-all-read", response_model=auth_schemas.GenericResponse)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Mark all notifications as read"""
    count = crud.mark_all_as_read(db, current_user.id)
    return {
        "success": True,
        "message": "All notifications marked as read",
        "data": {"marked_read": count}
    }


@router.delete("/{notification_id}", response_model=auth_schemas.GenericResponse)
def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_active_user),
):
    """Delete a notification"""
    success = crud.delete_notification(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {
        "success": True,
        "message": "Notification deleted"
    }