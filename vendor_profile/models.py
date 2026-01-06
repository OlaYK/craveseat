# vendor_profile/models.py
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    DateTime,
    Text,
    Numeric,
    Boolean,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import relationship
import shortuuid
from enum import Enum as PyEnum

from database import Base


# --- Python enums for status/verification/availability ---
class VendorStatus(PyEnum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class VerificationStatus(PyEnum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class AvailabilityStatus(PyEnum):
    available = "available"
    out_of_stock = "out_of_stock"


# --- Service categories (table-driven) ---
class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    vendors = relationship("VendorProfile", back_populates="category")


# --- Vendor profile (1-to-1 with user) ---
class VendorProfile(Base):
    __tablename__ = "vendor_profiles"  # Fixed: was "vendor_profile"

    vendor_id = Column(String, ForeignKey("users.id"), primary_key=True, nullable=False, index=True)

    business_name = Column(String(200), nullable=True)
    service_category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=True)

    vendor_address = Column(Text, nullable=True)
    vendor_phone = Column(String(50), nullable=True)
    vendor_email = Column(String(120), nullable=True)

    logo_url = Column(String, nullable=True)
    banner_url = Column(String, nullable=True)

    rating = Column(Numeric(3, 2), nullable=True, default=0.0)
    is_verified = Column(Boolean, default=False)

    status = Column(SAEnum(VendorStatus), default=VendorStatus.active, nullable=False)
    verification_status = Column(SAEnum(VerificationStatus), default=VerificationStatus.pending, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="vendor_profile")
    category = relationship("ServiceCategory", back_populates="vendors")
    items = relationship("VendorItem", back_populates="vendor", cascade="all, delete-orphan")


# --- Items sold by vendors (1 vendor -> many items) ---
class VendorItem(Base):
    __tablename__ = "vendor_items"

    id = Column(String, primary_key=True, default=shortuuid.uuid, index=True)
    vendor_id = Column(String, ForeignKey("vendor_profiles.vendor_id"), nullable=False, index=True)

    item_name = Column(String(200), nullable=False)
    item_description = Column(Text, nullable=True)
    item_price = Column(Numeric(12, 2), nullable=False)
    item_image_url = Column(String, nullable=True)

    availability_status = Column(SAEnum(AvailabilityStatus), default=AvailabilityStatus.available, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    vendor = relationship("VendorProfile", back_populates="items")