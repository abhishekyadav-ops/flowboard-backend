import os
from contextlib import asynccontextmanager
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware

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

# 🌟 FIX 1: Safe production lifespan startup handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on application startup safely
    Base.metadata.create_all(bind=engine)
    yield

# 🌟 FIX 2: Added redirect_slashes=False to stop 307 redirect CORS drops
app = FastAPI(
    title="FlowBoard API", 
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False  
)

# 3. CORS Configuration
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