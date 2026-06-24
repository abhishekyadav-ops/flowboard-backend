from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query
)
from sqlalchemy.orm import Session

from app.models.board import Board
from app.models.list import List
from app.models.user import User
from app.models.card import Card
# Fix 3: Removed unused WorkspaceMember import

from app.schemas.board import BoardCreate, BoardUpdate, BoardResponse
from app.schemas.list import ListResponse

from app.core.dependencies import (
    get_current_user,
    get_db,
    get_current_workspace
)

router = APIRouter()


@router.post(
    "/",
    response_model=BoardResponse,
    status_code=status.HTTP_201_CREATED
)
def create_board(
    board: BoardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new board"""
    # Fix 2: Validation added to block whitespace-only or empty board names
    cleaned_name = board.name.strip() if board.name else ""
    if not cleaned_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Board name cannot be empty"
        )

    get_current_workspace(
        board.workspace_id,
        current_user,
        db
    )

    new_board = Board(
        workspace_id=board.workspace_id,
        name=cleaned_name,
        description=board.description,
        created_by=current_user.id
    )

    db.add(new_board)
    db.commit()
    db.refresh(new_board)

    default_lists = [
        ("To Do", 0),
        ("In Progress", 1),
        ("Review", 2),
        ("Done", 3),
    ]

    for title, position in default_lists:
        db.add(
            List(
                board_id=new_board.id,
                title=title,
                position=position,
            )
        )

    db.commit()

    return new_board


@router.get("/workspace/{workspace_id}", response_model=list[BoardResponse])
def get_workspace_boards(
    workspace_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all boards in a workspace"""
    get_current_workspace(workspace_id, current_user, db)

    boards = (
        db.query(Board)
        .filter(Board.workspace_id == workspace_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return boards


@router.get("/{board_id}/details", response_model=BoardResponse)
def get_board(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get board details"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )

    get_current_workspace(board.workspace_id, current_user, db)
    return board


@router.put("/{board_id}", response_model=BoardResponse)
def update_board(
    board_id: int,
    board_data: BoardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update board"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )

    get_current_workspace(board.workspace_id, current_user, db)

    if board_data.name:
        board.name = board_data.name
    if board_data.description is not None:
        board.description = board_data.description

    db.commit()
    db.refresh(board)

    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete board"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )

    get_current_workspace(board.workspace_id, current_user, db)

    # Fix 1: Manual cascade fallback handling to safeguard database integrity across child associations
    lists = (
        db.query(List)
        .filter(List.board_id == board_id)
        .all()
    )
    for lst in lists:
        db.delete(lst)

    db.delete(board)
    db.commit()


@router.get("/{board_id}/lists", response_model=list[ListResponse])
def get_board_lists(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all lists in board"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )

    get_current_workspace(board.workspace_id, current_user, db)

    lists = (
        db.query(List)
        .filter(List.board_id == board_id)
        .order_by(List.position)
        .all()
    )

    return lists


@router.get("/{board_id}/stats")
def get_board_stats(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get board statistics"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )

    get_current_workspace(board.workspace_id, current_user, db)

    list_count = db.query(List).filter(List.board_id == board_id).count()
    card_count = (
        db.query(Card)
        .join(List, Card.list_id == List.id)
        .filter(List.board_id == board_id)
        .count()
    )

    return {
        "board_id": board_id,
        "list_count": list_count,
        "card_count": card_count
    }