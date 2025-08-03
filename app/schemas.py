from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    title: Optional[str] = None
    bio: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    email: EmailStr
    title: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime

    model_config = {
        "populate_by_name": True,
        "alias_priority": 2,
    }

class AuthOut(BaseModel):
    access_token: str
    user: UserOut
