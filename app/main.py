from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import create_db_and_tables
from app.modules.auth.router import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables on startup
    await create_db_and_tables()
    yield

app = FastAPI(
    title="DevOps-RAG API",
    description="An AI-driven DevOps management agent for bare-metal servers.",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
