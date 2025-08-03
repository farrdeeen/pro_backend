from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.models import User
from app.schemas import RegisterIn, LoginIn, UserOut, AuthOut
from app.auth import hash_pw, verify_pw, create_jwt, get_current_user
from app.schemas import UserOut
from beanie import PydanticObjectId

router = APIRouter(prefix="/auth", tags=["auth"])

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

@router.post("/register/", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
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
        "user": user_to_out(user)
    }

@router.post("/login/", response_model=AuthOut)
async def login(payload: LoginIn):
    user = await User.find_one(User.email == payload.email)
    if not user or not verify_pw(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_jwt(str(user.id))
    return {
        "access_token": token,
        "user": user_to_out(user)
    }

@router.get("/id/by_email", response_model=str)
async def get_user_id_by_email(email: str = Query(..., example="user@example.com")):
    user = await User.find_one(User.email == email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return str(user.id)

@router.get("/me/", response_model=UserOut)
async def read_me(current_user: User = Depends(get_current_user)):
    return user_to_out(current_user)
