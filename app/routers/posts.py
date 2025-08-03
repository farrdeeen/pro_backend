from fastapi import APIRouter, Body, HTTPException, status, Depends, Response
from beanie import PydanticObjectId
from typing import List
from app.models import Post, User, Comment
from app.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/posts", tags=["posts"])

@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(body: dict = Body(...), current_user: User = Depends(get_current_user)):
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=422, detail="Content cannot be empty.")
    post = Post(content=content, author_id=current_user.id)
    await post.insert()
    return post

@router.get("/", response_model=List[dict])
async def list_posts(skip: int = 0, limit: int = 20):
    posts = await Post.find_all().sort("-created_at").skip(skip).limit(limit).to_list()
    result = []
    for post in posts:
        author = await User.get(post.author_id)
        result.append({
            "_id": str(post.id),
            "content": post.content,
            "created_at": post.created_at.isoformat(),
            "likes": post.likes,
            "comments": post.comments,
            "author": {
                "name": author.name if author else "Unknown",
                "title": author.title if (author and author.title) else "Member",
                "avatar_url": author.avatar_url if author else None,
                "_id": str(author.id) if author else None,
            }
        })
    return result

@router.get("/{post_id}/", response_model=dict)
async def get_post(post_id: str):
    post = await Post.get(PydanticObjectId(post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    author = await User.get(post.author_id)
    return {
        "_id": str(post.id),
        "content": post.content,
        "created_at": post.created_at.isoformat(),
        "likes": post.likes,
        "comments": post.comments,
        "author": {
            "name": author.name if author else "Unknown",
            "title": author.title if (author and author.title) else "Member",
            "avatar_url": author.avatar_url if author else None,
            "_id": str(author.id) if author else None,
        }
    }

@router.post("/{post_id}/comments/", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def add_comment(
    post_id: str,
    body: dict = Body(...),
    current_user: User = Depends(get_current_user),
):
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=422, detail="Content cannot be empty.")
    post = await Post.get(PydanticObjectId(post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    comment = Comment(
        content=content,
        post_id=post.id,
        author_id=current_user.id,
    )
    await comment.insert()
    return comment

@router.get("/{post_id}/comments/", response_model=List[Comment])
async def list_comments(post_id: str, skip: int = 0, limit: int = 100):
    post = await Post.get(PydanticObjectId(post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return await Comment.find(Comment.post_id == post.id).sort("+created_at").skip(skip).limit(limit).to_list()

@router.post("/{post_id}/like/", status_code=status.HTTP_204_NO_CONTENT)
async def like_post(post_id: str, current_user: User = Depends(get_current_user)):
    post = await Post.get(PydanticObjectId(post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if current_user.id not in post.liked_by:
        post.liked_by.add(current_user.id)
        post.likes += 1
        await post.save()

@router.delete("/{post_id}/like/", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(post_id: str, current_user: User = Depends(get_current_user)):
    post = await Post.get(PydanticObjectId(post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if current_user.id in post.liked_by:
        post.liked_by.remove(current_user.id)
        post.likes = max(post.likes-1, 0)
        await post.save()

@router.delete("/{post_id}/", status_code=204)
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    post = await Post.get(PydanticObjectId(post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    # Only allow deletion by the author
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot delete this post.")
    await post.delete()
    return Response(status_code=204)
