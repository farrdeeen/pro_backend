from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import lifespan
from app.routers import auth, users, posts  # adjust for your routers

app = FastAPI(
    title="ProConnect API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in prod!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)

@app.get("/status", tags=["health"])
async def health_check():
    from datetime import datetime, timezone
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
