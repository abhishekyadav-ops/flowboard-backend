import os
from contextlib import asynccontextmanager
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text # 🌟 Imported text for executing raw SQL updates

# Database and Core Engine Imports
from app.database import Base, engine

# Explicit Model Imports to prevent production startup handshake issues
from app.models.user import User
from app.models.workspace import Workspace
from app.models.board import Board
from app.models.list import List
from app.models.card import Card
from app.models.workspace_member import WorkspaceMember
from app.models.card_assignment import CardAssignment
from app.models.comment import Comment
from app.models.activity_log import ActivityLog

# API Router Imports
from app.routers import user, workspace, board, card, list, dashboard, auth

# Safe production lifespan startup handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize database tables on application startup safely
    Base.metadata.create_all(bind=engine)
    
    # 2. 🌟 FORCE SCHEMA PATCH: Ensure missing columns exist in Render PostgreSQL
    with engine.connect() as connection:
        try:
            print("🚀 Checking database columns for 'cards' table...")
            
            # Add updated_at if missing
            connection.execute(text(
                "ALTER TABLE cards ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;"
            ))
            
            # Add important_link if missing
            connection.execute(text(
                "ALTER TABLE cards ADD COLUMN IF NOT EXISTS important_link TEXT;"
            ))
            
            connection.commit()
            print("✅ Database schema patched successfully!")
        except Exception as e:
            print(f"⚠️ Column patch note: {e}")
            
    yield

# Added redirect_slashes=False to stop 307 redirect CORS drops
app = FastAPI(
    title="FlowBoard API", 
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False  
)

# 🌟 STEP 1: Define Proxy Header Middleware first
class ProxyHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        proto = request.headers.get("x-forwarded-proto")
        if proto:
            request.scope["scheme"] = proto
        return await call_next(request)

# 🌟 STEP 2: Register Proxy Header Middleware FIRST
app.add_middleware(ProxyHeaderMiddleware)

# 🌟 STEP 3: Register CORSMiddleware SECOND
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://flowboard-ui-laxd.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Include API Route Endpoints
app.include_router(auth.router)  # Handles its own /users/auth path internally

app.include_router(
    user.router,
    prefix="/users",
    tags=["Users"]
)

app.include_router(
    workspace.router,
    prefix="/workspaces",
    tags=["Workspaces"]
)

app.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"]
)

app.include_router(
    board.router,
    prefix="/boards",
    tags=["Boards"]
)

app.include_router(
    card.router,
    prefix="/cards",
    tags=["Cards"]
)

app.include_router(
    list.router,
    prefix="/lists",    
    tags=["Lists"]
)

# 5. Root Status Check Endpoint
@app.get("/") 
def root(): 
    return {
        "message": "FlowBoard API Running Successfully"
    }