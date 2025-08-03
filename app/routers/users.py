from fastapi import APIRouter, HTTPException
from app.models import User, Post
from app.schemas import UserOut
from beanie import PydanticObjectId
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

def user_to_out(user: User) -> UserOut:
    return UserOut(
        id=str(user.id),
        name=user.name,
        email=user.email,
        title=user.title,
        bio=user.bio,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_out(user)

@router.get("/{user_id}/posts/", response_model=List[dict])
async def get_user_posts(user_id: str):
    posts = await Post.find(Post.author_id == PydanticObjectId(user_id)).sort("-created_at").to_list()
    author = await User.get(PydanticObjectId(user_id))
    result = []
    for post in posts:
        result.append({
            "_id": str(post.id),
            "content": post.content,
            "created_at": post.created_at.isoformat(),
            "likes": post.likes,
            "comments": post.comments,
            "author": {
                "name": author.name if author else "Unknown",
                "title": author.title if author and author.title else "Member",
                "avatar_url": author.avatar_url if author else None,
                "_id": str(author.id) if author else None,
            }
        })
    return result
