from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import create_db_and_tables
from app.modules.auth.router import router as auth_router
from app.modules.servers.router import router as servers_router
from app.modules.guardrails.service import init_and_seed_db
from app.modules.chat.router import router as chat_router

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.modules.chat.agent import build_graph

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables on startup
    await create_db_and_tables()
    # Initialize and seed ChromaDB local vector store
    await init_and_seed_db()
    
    # Initialize SQLite checkpointer for LangGraph
    async with AsyncSqliteSaver.from_conn_string("data/devops_rag.db") as checkpointer:
        app.state.graph = build_graph(checkpointer=checkpointer)
        yield

app = FastAPI(
    title="DevOps-Copilot API",
    description="An AI-driven DevOps management copilot for bare-metal servers.",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(servers_router, prefix="/api/v1/servers", tags=["Servers"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat & Agent"])

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
