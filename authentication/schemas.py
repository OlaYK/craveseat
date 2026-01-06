from pydantic import BaseModel
from typing import Optional
from .models import UserType    


#user schemas
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    user_type:Optional[UserType] = UserType.user

class UserCreate(UserBase):
    password: str
    confirm_password: str

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



