from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from enum import Enum


class CravingStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    fulfilled = "fulfilled"
    cancelled = "cancelled"


class CravingCategory(str, Enum):
    food = "food"
    snacks = "snacks"
    drinks = "drinks"
    gadgets = "gadgets"
    furniture = "furniture"
    electronics = "electronics"
    clothing = "clothing"
    beauty_health = "beauty_health"
    books = "books"
    other = "other"


class CravingBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        validation_alias=AliasChoices("name", "title"),
        serialization_alias="name",
    )
    description: Optional[str] = None
    category: CravingCategory
    price_estimate: Optional[Decimal] = None
    delivery_address: Optional[str] = None
    recommended_vendor: Optional[str] = None
    vendor_link: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("vendor_link", "vendor_contact"),
        serialization_alias="vendor_link",
    )
    notes: Optional[str] = None


class CravingCreate(CravingBase):
    """Create craving with optional image URL."""
    image_url: Optional[str] = None


class CravingUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("name", "title"),
        serialization_alias="name",
    )
    description: Optional[str] = None
    category: Optional[CravingCategory] = None
    status: Optional[CravingStatus] = None
    price_estimate: Optional[Decimal] = None
    delivery_address: Optional[str] = None
    recommended_vendor: Optional[str] = None
    vendor_link: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("vendor_link", "vendor_contact"),
        serialization_alias="vendor_link",
    )
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
