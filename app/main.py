from fastapi import FastAPI 
from app.database import Base, engine
from app.models.list import List
from app.models.card import Card
from app.models.workspace_member import WorkspaceMember
from app.models.card_assignment import CardAssignment
from app.models.comment import Comment
from app.models.activity_log import ActivityLog
from app.routers import user, workspace, board, card, list 
from app.routers import dashboard    
from app.routers import auth  # Successfully imported here!
from fastapi.middleware.cors import CORSMiddleware
from app.models.user import User
from app.models.workspace import Workspace
from app.models.board import Board

# Initialize database tables
Base.metadata.create_all(bind=engine) 

app = FastAPI(
    title="FlowBoard API", 
    version="1.0.0"
)

# CORS configuration allowing clean React communication
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

# 🌟 ADDED: Included the Google Authentication router endpoint mapping structure
# Since the auth.py file already prefixes '/users/auth' internally, we pass it directly here
app.include_router(auth.router)

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

@app.get("/") 
def root(): 
    return {
        "message": "FlowBoard API Running"
    }