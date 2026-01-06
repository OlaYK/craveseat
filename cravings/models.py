from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import relationship
from database import Base
import shortuuid
from enum import Enum as PyEnum


class CravingStatus(PyEnum):
    open = "open"
    in_progress = "in_progress"
    fulfilled = "fulfilled"
    cancelled = "cancelled"


class CravingCategory(PyEnum):
    food = "food"
    beverages = "beverages"
    snacks = "snacks"
    groceries = "groceries"
    bakery = "bakery"
    fast_food = "fast_food"
    other = "other"


class Craving(Base):
    __tablename__ = "cravings"

    id = Column(String, primary_key=True, default=shortuuid.uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SAEnum(CravingCategory), nullable=False)
    status = Column(SAEnum(CravingStatus), default=CravingStatus.open, nullable=False)
    
    anonymous = Column(Boolean, default=False)
    image_url = Column(String, nullable=True)
    delivery_address = Column(Text, nullable=True)
    
    recommended_vendor = Column(String, nullable=True)
    vendor_contact = Column(String, nullable=True)
    share_token = Column(String, unique=True, nullable=False, default=shortuuid.uuid, index=True)  # For share URLs
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="cravings")
    responses = relationship("Response", back_populates="craving", cascade="all, delete-orphan")