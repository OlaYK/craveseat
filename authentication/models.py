from sqlalchemy import Column, String, Boolean, Enum, TIMESTAMP, text
from sqlalchemy.orm import relationship
from database import Base
import shortuuid
from enum import Enum as PyEnum

class UserType(PyEnum):
    user = "user"
    vendor = "vendor"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=shortuuid.uuid, unique=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    user_type = Column(Enum(UserType), default=UserType.user, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=text("now()"), onupdate=text("now()"))
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    vendor_profile = relationship("VendorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    cravings = relationship("Craving", back_populates="user", cascade="all, delete-orphan")
    responses = relationship("Response", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")