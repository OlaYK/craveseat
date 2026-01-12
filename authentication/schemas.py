from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re
from .models import UserType    


#user schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr  # Changed to EmailStr for validation
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    user_type: Optional[UserType] = UserType.user
    
    @field_validator('username')
    @classmethod
    def username_to_lowercase(cls, v: str) -> str:
        """Convert username to lowercase for case-insensitive handling"""
        return v.lower().strip()
    
    @field_validator('email')
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        """Convert email to lowercase"""
        return v.lower().strip()


class UserCreate(UserBase):
    password: str
    confirm_password: str
    # Profile fields during signup
    bio: Optional[str] = None
    phone_number: str  # Now required
    delivery_address: Optional[str] = None
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format"""
        if not v or not v.strip():
            raise ValueError('Phone number is required')
        
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


class User(UserBase):
    id: str
    class Config:
        from_attributes = True


class UserOut(UserBase):
    id: str
    is_active: bool
    class Config:
        from_attributes = True


class UserInDB(UserOut):
    hashed_password: str


#token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class SignupResponse(BaseModel):
    message: str
    success: bool
    user: User