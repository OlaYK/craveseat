from sqlalchemy.orm import Session
from notifications import models, schemas
from datetime import datetime


def create_notification(db: Session, notification: schemas.NotificationCreate):
    """Create a new notification"""
    db_notification = models.Notification(
        user_id=notification.user_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        craving_id=notification.craving_id,
        response_id=notification.response_id,
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def get_user_notifications(db: Session, user_id: str, skip: int = 0, limit: int = 50, unread_only: bool = False):
    """Get notifications for a user"""
    query = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(models.Notification.is_read == False)
    
    return query.order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()


def mark_notifications_as_read(db: Session, notification_ids: list[str], user_id: str):
    """Mark notifications as read"""
    notifications = db.query(models.Notification).filter(
        models.Notification.id.in_(notification_ids),
        models.Notification.user_id == user_id
    ).all()
    
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    
    db.commit()
    return len(notifications)


def mark_all_as_read(db: Session, user_id: str):
    """Mark all notifications as read for a user"""
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).all()
    
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    
    db.commit()
    return len(notifications)


def get_unread_count(db: Session, user_id: str):
    """Get count of unread notifications"""
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).count()


def delete_notification(db: Session, notification_id: str, user_id: str):
    """Delete a notification"""
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == user_id
    ).first()
    
    if notification:
        db.delete(notification)
        db.commit()
        return True
    return False


# Helper function to create common notifications
def notify_craving_response(db: Session, craving_owner_id: str, craving_id: str, response_id: str, responder_name: str = "Someone"):
    """Notify craving owner that someone responded"""
    return create_notification(db, schemas.NotificationCreate(
        user_id=craving_owner_id,
        notification_type=schemas.NotificationType.craving_response,
        title="New Response to Your Craving",
        message=f"{responder_name} responded to your craving!",
        craving_id=craving_id,
        response_id=response_id
    ))


def notify_response_status_change(db: Session, responder_id: str, craving_id: str, response_id: str, new_status: str):
    """Notify responder that their response status changed"""
    title_map = {
        "accepted": "Response Accepted",
        "rejected": "Response Declined",
        "completed": "Response Completed"
    }
    
    message_map = {
        "accepted": "Your response to a craving was accepted!",
        "rejected": "Your response to a craving was declined.",
        "completed": "The craving you responded to has been completed!"
    }
    
    notification_type_map = {
        "accepted": schemas.NotificationType.response_accepted,
        "rejected": schemas.NotificationType.response_rejected,
        "completed": schemas.NotificationType.craving_fulfilled
    }
    
    return create_notification(db, schemas.NotificationCreate(
        user_id=responder_id,
        notification_type=notification_type_map.get(new_status, schemas.NotificationType.system),
        title=title_map.get(new_status, "Response Status Updated"),
        message=message_map.get(new_status, "Your response status has been updated."),
        craving_id=craving_id,
        response_id=response_id
    ))