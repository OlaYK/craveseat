from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re


class UserProfileBase(BaseModel):
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    delivery_address: Optional[str] = None


class UserProfileUpdate(UserProfileBase):
    """Update profile - all fields optional"""
    username: Optional[str] = None
    image_url: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    delivery_address: Optional[str] = None
    
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format if provided"""
        if v is None or v.strip() == "":
            return None
        
        # Remove common formatting characters for validation
        cleaned = re.sub(r'[\s\-\(\)\.]', '', v)
        
        # Check if it starts with + (international format)
        if cleaned.startswith('+'):
            cleaned = cleaned[1:]
        
        # Validate that remaining characters are digits
        if not cleaned.isdigit():
            raise ValueError('Phone number must contain only digits, spaces, hyphens, parentheses, or start with +')
        
        # Check length (typically 10-15 digits for most phone numbers)
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
        
        return v.strip()
    
    @field_validator('username')
    @classmethod
    def username_to_lowercase(cls, v: Optional[str]) -> Optional[str]:
        """Convert username to lowercase for case-insensitive handling"""
        if v is None:
            return None
        return v.lower().strip()


class UserProfile(UserProfileBase):
    """Complete user profile response with user details"""
    user_id: str
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # User details from User table
    username: str
    email: str
    full_name: Optional[str] = None
    user_type: str
    is_active: bool

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str