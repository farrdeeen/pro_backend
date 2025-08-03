from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from contextlib import asynccontextmanager
from .models import User, Post, Comment
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/proconnect")

@asynccontextmanager
async def lifespan(app):
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
