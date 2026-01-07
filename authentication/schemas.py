from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
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
    phone_number: Optional[str] = None
    delivery_address: Optional[str] = None


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