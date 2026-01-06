from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum as SAEnum, Boolean, func
from sqlalchemy.orm import relationship
from database import Base
import shortuuid
from enum import Enum as PyEnum


class NotificationType(PyEnum):
    craving_response = "craving_response"  # Someone responded to your craving
    response_accepted = "response_accepted"  # Your response was accepted
    response_rejected = "response_rejected"  # Your response was rejected
    craving_fulfilled = "craving_fulfilled"  # Craving marked as fulfilled
    new_message = "new_message"  # New message in chat (future)
    system = "system"  # System notifications


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=shortuuid.uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    notification_type = Column(SAEnum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Related entities (optional)
    craving_id = Column(String, ForeignKey("cravings.id"), nullable=True)
    response_id = Column(String, ForeignKey("responses.id"), nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    craving = relationship("Craving")
    response = relationship("Response")