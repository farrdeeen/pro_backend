from beanie import Document, Indexed, PydanticObjectId
from datetime import datetime
from typing import Set, Optional
from pydantic import EmailStr, Field

class User(Document):
    name: str = Field(..., min_length=2, max_length=80)
    email: EmailStr = Indexed(unique=True)
    password_hash: str
    title: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    class Settings:
        name = "user"

class Post(Document):
    author_id: PydanticObjectId = Indexed()
    content: str = Field(..., min_length=1, max_length=5000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    liked_by: Set[PydanticObjectId] = Field(default_factory=set)
    likes: int = 0
    comments: int = 0
    class Settings:
        name = "post"

class Comment(Document):
    post_id: PydanticObjectId = Indexed()
    author_id: PydanticObjectId = Indexed()
    content: str = Field(..., min_length=1, max_length=2000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    class Settings:
        name = "comment"
