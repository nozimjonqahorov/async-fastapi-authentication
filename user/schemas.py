from datetime import datetime
from typing import Optional
from user.security import hash_password, verify_password
from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    username: str
    email: EmailStr
    is_active: bool
    is_superuser : bool
    created_at : datetime


class ChangeProfileSchema(BaseModel):
    username : Optional[str] = None
    email : Optional[EmailStr] = None
    is_active : Optional[bool] = None
    is_superuser : Optional[bool] = None

    model_config = {
        "from_attributes": True
    }


class PasswordChangeSchema(BaseModel):
    old_password : str
    new_password : str
    confirm_password : str 

    

class LogoutSchema(BaseModel):
    refresh : str