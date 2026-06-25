from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app.models.board import Board
from app.schemas.board import BoardResponse # 🌟 Your schema file

router = APIRouter()

# 🌟 Make sure response_model matches your List[BoardResponse] structure!
@router.get("/workspace/{workspace_id}", response_model=List[BoardResponse])
def get_workspace_boards(workspace_id: int, db: Session = Depends(get_db)):
    
    # 🌟 CRITICAL: joinedload(Board.owner) tells SQLAlchemy to fetch the 
    # creator data in the same query so Pydantic can map 'UserMinResponse' cleanly.
    boards = db.query(Board)\
               .filter(Board.workspace_id == workspace_id)\
               .options(joinedload(Board.owner))\
               .all()
               
    return boards