from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CravingStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    fulfilled = "fulfilled"
    cancelled = "cancelled"


class CravingCategory(str, Enum):
    food = "food"
    beverages = "beverages"
    snacks = "snacks"
    groceries = "groceries"
    bakery = "bakery"
    fast_food = "fast_food"
    other = "other"


class CravingBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: CravingCategory
    anonymous: Optional[bool] = False
    delivery_address: Optional[str] = None
    recommended_vendor: Optional[str] = None
    vendor_contact: Optional[str] = None
    notes: Optional[str] = None


class CravingCreate(CravingBase):
    pass


class CravingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[CravingCategory] = None
    status: Optional[CravingStatus] = None
    anonymous: Optional[bool] = None
    delivery_address: Optional[str] = None
    recommended_vendor: Optional[str] = None
    vendor_contact: Optional[str] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None


class CravingResponse(CravingBase):
    id: str
    user_id: str
    status: CravingStatus
    image_url: Optional[str] = None
    share_token: str  # Token for sharing
    created_at: datetime
    updated_at: datetime
    fulfilled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CravingWithResponses(CravingResponse):
    responses: List["ResponseInCraving"] = []

    class Config:
        from_attributes = True


# Import for forward reference
from responses.schemas import ResponseInCraving
CravingWithResponses.model_rebuild()