from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    craving_response = "craving_response"
    response_accepted = "response_accepted"
    response_rejected = "response_rejected"
    craving_fulfilled = "craving_fulfilled"
    new_message = "new_message"
    system = "system"


class NotificationBase(BaseModel):
    notification_type: NotificationType
    title: str
    message: str
    craving_id: Optional[str] = None
    response_id: Optional[str] = None


class NotificationCreate(NotificationBase):
    user_id: str


class NotificationResponse(NotificationBase):
    id: str
    user_id: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationMarkRead(BaseModel):
    notification_ids: list[str]