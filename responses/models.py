from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum as SAEnum, Boolean, func
from sqlalchemy.orm import relationship
from database import Base
import shortuuid
from enum import Enum as PyEnum


class ResponseStatus(PyEnum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"


class Response(Base):
    __tablename__ = "responses"

    id = Column(String, primary_key=True, default=shortuuid.uuid, index=True)
    craving_id = Column(String, ForeignKey("cravings.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)  # Now NULLABLE for anonymous
    
    message = Column(Text, nullable=False)
    status = Column(SAEnum(ResponseStatus), default=ResponseStatus.pending, nullable=False)
    
    # Anonymous response fields
    is_anonymous = Column(Boolean, default=False, nullable=False)
    anonymous_name = Column(String(100), nullable=True)  # Optional name like "Anonymous Friend"
    anonymous_contact = Column(String(200), nullable=True)  # Optional contact (email/phone)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    craving = relationship("Craving", back_populates="responses")
    user = relationship("User", back_populates="responses")  # Will be None for anonymous responses