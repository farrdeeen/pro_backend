from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Header, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Set, Optional
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr, Field
from beanie import Document, Indexed, PydanticObjectId, init_beanie
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

# === Load environment variables ===
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/proconnect")
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

# ========== Models ==========
class User(Document):
    name: str = Field(..., min_length=2, max_length=80)
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    title: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    class Settings:
        name = "user"

class Post(Document):
    author_id: Indexed(PydanticObjectId)
    content: str = Field(..., min_length=1, max_length=5000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    liked_by: Set[PydanticObjectId] = Field(default_factory=set)
    likes: int = 0
    comments: int = 0
    class Settings:
        name = "post"

class Comment(Document):
    post_id: Indexed(PydanticObjectId)
    author_id: Indexed(PydanticObjectId)
    content: str = Field(..., min_length=1, max_length=2000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    class Settings:
        name = "comment"

# ========== Auth & Security ==========
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_pw(password: str) -> str:
    return pwd_context.hash(password)
def verify_pw(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
def create_jwt(sub: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": sub, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)
def decode_jwt(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user(authorization: str = Header(None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing credentials")
    user_id = decode_jwt(authorization.split()[1])
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ========== Schemas ==========
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

# ========== Helpers ==========
def user_to_out(user: User, id: Optional[str] = None) -> UserOut:
    return UserOut(
        id=id if id is not None else str(user.id),
        name=user.name,
        email=user.email,
        title=user.title,
        bio=user.bio,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )

# ========== Routers ==========
auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/register/", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterIn):
    if await User.find_one(User.email == payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_pw(payload.password),
        title=payload.title,
        bio=payload.bio,
    )
    await user.insert()
    token = create_jwt(str(user.id))
    return {
        "access_token": token,
        "user": user_to_out(user, str(user.id))
    }

@auth_router.post("/login/", response_model=AuthOut)
async def login(payload: LoginIn):
    user = await User.find_one(User.email == payload.email)
    if not user or not verify_pw(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_jwt(str(user.id))
    return {
        "access_token": token,
        "user": user_to_out(user, str(user.id))
    }

@auth_router.get("/id/by_email", response_model=str)
async def get_user_id_by_email(email: str = Query(..., example="user@example.com")):
    user = await User.find_one(User.email == email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return str(user.id)

@auth_router.get("/me/", response_model=UserOut)
async def read_me(current_user: User = Depends(get_current_user)):
    return user_to_out(current_user, str(current_user.id))

users_router = APIRouter(prefix="/users", tags=["users"])

@users_router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_out(user, str(user.id))

@users_router.get("/{user_id}/posts/", response_model=List[dict])
async def get_user_posts(user_id: str):
    posts = await Post.find(Post.author_id == PydanticObjectId(user_id)).sort("-created_at").to_list()
    result = []
    author = await User.get(PydanticObjectId(user_id))
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
                "avatar_url": author.avatar_url if author else None
            }
        })
    return result

posts_router = APIRouter(prefix="/posts", tags=["posts"])

@posts_router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(body: dict = Body(...), current_user: User = Depends(get_current_user)):
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=422, detail="Content cannot be empty.")
    post = Post(content=content, author_id=current_user.id)
    await post.insert()
    return post

@posts_router.get("/", response_model=List[dict])
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
                "avatar_url": author.avatar_url if author else None
            }
        })
    return result

@posts_router.get("/{post_id}/", response_model=dict)
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
            "avatar_url": author.avatar_url if author else None
        }
    }

@posts_router.post("/{post_id}/comments/", response_model=Comment, status_code=status.HTTP_201_CREATED)
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

@posts_router.get("/{post_id}/comments/", response_model=List[Comment])
async def list_comments(post_id: str, skip: int = 0, limit: int = 100):
    post = await Post.get(PydanticObjectId(post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return await Comment.find(Comment.post_id == post.id).sort("+created_at").skip(skip).limit(limit).to_list()

@posts_router.post("/{post_id}/like/", status_code=status.HTTP_204_NO_CONTENT)
async def like_post(post_id: str, current_user: User = Depends(get_current_user)):
    post = await Post.get(PydanticObjectId(post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if current_user.id not in post.liked_by:
        post.liked_by.add(current_user.id)
        post.likes += 1
        await post.save()

@posts_router.delete("/{post_id}/like/", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(post_id: str, current_user: User = Depends(get_current_user)):
    post = await Post.get(PydanticObjectId(post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if current_user.id in post.liked_by:
        post.liked_by.remove(current_user.id)
        post.likes = max(post.likes-1, 0)
        await post.save()

# === Database & Application Startup ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client.get_default_database()
    await init_beanie(database=db, document_models=[User, Post, Comment])
    app.state.mongo_client = mongo_client
    app.state.db = db
    print("✅ MongoDB & Beanie initialized")
    try:
        yield
    finally:
        mongo_client.close()
        print("🛑 MongoDB connection closed")

app = FastAPI(
    title="ProConnect API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev; restrict in prod!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(posts_router)

@app.get("/status", tags=["health"])
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
