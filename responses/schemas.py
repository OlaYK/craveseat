from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"


class ResponseBase(BaseModel):
    message: str


class ResponseCreate(ResponseBase):
    # For anonymous responses
    is_anonymous: Optional[bool] = False
    anonymous_name: Optional[str] = None
    anonymous_contact: Optional[str] = None


class ResponseUpdate(BaseModel):
    message: Optional[str] = None
    status: Optional[ResponseStatus] = None


class ResponseOut(ResponseBase):
    id: str
    craving_id: str
    user_id: Optional[str] = None  # None if anonymous
    status: ResponseStatus
    is_anonymous: bool
    anonymous_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# For nested display in cravings
class ResponseInCraving(BaseModel):
    id: str
    user_id: Optional[str] = None  # None if anonymous
    message: str
    status: ResponseStatus
    is_anonymous: bool
    anonymous_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True