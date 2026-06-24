from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query
)
from sqlalchemy.orm import Session

from app.models.list import List
from app.models.card import Card
from app.models.board import Board
from app.models.user import User
# Fix 1: Removed unused WorkspaceMember import

from app.schemas.list import ListCreate, ListUpdate, ListResponse, ListReorder
from app.schemas.card import CardResponse

from app.core.dependencies import (
    get_current_user,
    get_db,
    get_current_workspace
)

router = APIRouter()


@router.post("/{board_id}", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
def create_list(
    board_id: int,
    list_data: ListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new list in board"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )

    get_current_workspace(board.workspace_id, current_user, db)

    # Fix 2: Auto-calculate position if not provided, ensuring seamless positioning
    if list_data.position is None:
        max_position = (
            db.query(List.position)
            .filter(List.board_id == board_id)
            .order_by(List.position.desc())
            .first()
        )
        new_position = (max_position[0] + 1) if max_position and max_position[0] is not None else 0
    else:
        new_position = list_data.position

    new_list = List(
        board_id=board_id,
        title=list_data.title,
        position=new_position
    )

    db.add(new_list)
    db.commit()
    db.refresh(new_list)

    return new_list


@router.get("/{list_id}", response_model=ListResponse)
def get_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list details"""
    task_list = db.query(List).filter(List.id == list_id).first()
    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )

    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    return task_list


@router.put("/{list_id}", response_model=ListResponse)
def update_list(
    list_id: int,
    list_data: ListUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update list"""
    task_list = db.query(List).filter(List.id == list_id).first()
    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )

    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    if list_data.title:
        task_list.title = list_data.title
    if list_data.position is not None:
        task_list.position = list_data.position

    db.commit()
    db.refresh(task_list)

    return task_list


@router.put("/{list_id}/reorder")
def reorder_list(
    list_id: int,
    reorder_data: ListReorder,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reorder a list"""
    task_list = db.query(List).filter(List.id == list_id).first()
    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )

    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    task_list.position = reorder_data.position
    db.commit()
    db.refresh(task_list)

    return {"message": "List reordered successfully"}


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete list (and all its cards)"""
    task_list = db.query(List).filter(List.id == list_id).first()
    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )

    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    db.delete(task_list)
    db.commit()


@router.get("/{list_id}/cards", response_model=list[CardResponse])
def get_list_cards(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all cards in list"""
    task_list = db.query(List).filter(List.id == list_id).first()
    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )

    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    cards = (
        db.query(Card)
        .filter(Card.list_id == list_id)
        .order_by(Card.position)
        .all()
    )

    return cards