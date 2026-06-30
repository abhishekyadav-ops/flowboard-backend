from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.card import Card
from app.models.list import List
from app.models.board import Board
from app.models.user import User
from app.models.card_assignment import CardAssignment
from app.models.comment import Comment
from app.models.workspace_member import WorkspaceMember
from app.schemas.card import CardCreate, CardUpdate, CardMoveRequest, CardResponse
from app.schemas.card_assignment import AssignCard
from app.core.dependencies import (
    get_current_user,
    get_db,
    get_current_workspace
)

router = APIRouter()


# Fix 4: Schema for Comment Creation
class CommentCreate(BaseModel):
    message: str


# Fix 1: Changed route from "/{board_id}" to "/" to match frontend behavior
@router.post("/", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(
    card: CardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new card"""
    # 1. Fetch task list and validate existence
    task_list = db.query(List).filter(List.id == card.list_id).first()
    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )

    # 2. Fetch board linked to this list
    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )

    # 3. Check workspace permissions
    get_current_workspace(board.workspace_id, current_user, db)

    # 4. Handle auto-positioning
    max_position = (
        db.query(Card.position)
        .filter(Card.list_id == card.list_id)
        .order_by(Card.position.desc())
        .first()
    )
    new_position = (max_position[0] + 1) if max_position and max_position[0] is not None else 0

    new_card = Card(
        list_id=card.list_id,
        title=card.title,
        description=card.description,
        priority=card.priority,
        due_date=card.due_date,
        position=new_position,
        created_by=current_user.id,
        links=card.links or []
    )

    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return new_card


@router.get("/{card_id}", response_model=CardResponse)
def get_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get card details"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    task_list = db.query(List).filter(List.id == card.list_id).first()
    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    return card


@router.put("/{card_id}", response_model=CardResponse)
def update_card(
    card_id: int,
    card_data: CardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update card"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    task_list = db.query(List).filter(List.id == card.list_id).first()
    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    if card_data.title:
        card.title = card_data.title
    if card_data.description is not None:
        card.description = card_data.description
    if card_data.priority:
        card.priority = card_data.priority
    if card_data.due_date is not None:
        card.due_date = card_data.due_date
    if card_data.links is not None:
        card.links = card_data.links

    db.commit()
    db.refresh(card)

    return card


@router.put("/{card_id}/move")
def move_card(
    card_id: int,
    move_data: CardMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Move card to different list and/or position"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    old_list = db.query(List).filter(List.id == card.list_id).first()
    board = db.query(Board).filter(Board.id == old_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    new_list = db.query(List).filter(List.id == move_data.list_id).first()
    if not new_list or new_list.board_id != board.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target list not found"
        )

    card.list_id = move_data.list_id
    card.position = move_data.position

    db.commit()
    db.refresh(card)

    return {"message": "Card moved successfully"}


# Fixed Error 1: Safe cascading manual deletions to prevent ForeignKeyViolation drops
@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete card along with child dependencies"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    task_list = db.query(List).filter(List.id == card.list_id).first()
    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    # Clean out user card assignments
    assignments = (
        db.query(CardAssignment)
        .filter(CardAssignment.card_id == card_id)
        .all()
    )
    for assignment in assignments:
        db.delete(assignment)

    # Clean out card messaging comments
    comments = (
        db.query(Comment)
        .filter(Comment.card_id == card_id)
        .all()
    )
    for comment in comments:
        db.delete(comment)

    # Safely commit parent drop execution tracking
    db.delete(card)
    db.commit()


@router.post("/{card_id}/assign", status_code=status.HTTP_201_CREATED)
def assign_card(
    card_id: int,
    assignment: AssignCard,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign user to card"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    task_list = db.query(List).filter(List.id == card.list_id).first()
    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    user = db.query(User).filter(User.id == assignment.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Fix 3: Security vulnerability fixed. Verifies assignee is part of the workspace.
    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == board.workspace_id,
            WorkspaceMember.user_id == assignment.user_id
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this workspace"
        )

    existing = (
        db.query(CardAssignment)
        .filter(
            CardAssignment.card_id == card_id,
            CardAssignment.user_id == assignment.user_id
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already assigned to this card"
        )

    new_assignment = CardAssignment(
        card_id=card_id,
        user_id=assignment.user_id,
        assigned_by=current_user.id
    )

    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    return {"message": "User assigned successfully"}


# Fix 2: Changed route name from '/assign/{user_id}' to '/unassign/{user_id}' to sync with frontend
@router.delete("/{card_id}/unassign/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_card(
    card_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unassign user from card"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    task_list = db.query(List).filter(List.id == card.list_id).first()
    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    assignment = (
        db.query(CardAssignment)
        .filter(
            CardAssignment.card_id == card_id,
            CardAssignment.user_id == user_id
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    db.delete(assignment)
    db.commit()


@router.get("/{card_id}/assignees")
def get_card_assignees(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assigned users for card"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    task_list = db.query(List).filter(List.id == card.list_id).first()
    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    assignments = (
        db.query(CardAssignment)
        .filter(CardAssignment.card_id == card_id)
        .all()
    )

    assignees = []
    for assignment in assignments:
        user = db.query(User).filter(User.id == assignment.user_id).first()
        if user:
            assignees.append({
                "id": user.id,
                "name": user.name,
                "email": user.email
            })

    return {"card_id": card_id, "assignees": assignees}


# Fix 4: Removed raw dict mapping and swapped with CommentCreate model
@router.post("/{card_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(
    card_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add comment to card"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    task_list = db.query(List).filter(List.id == card.list_id).first()
    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    new_comment = Comment(
        card_id=card_id,
        user_id=current_user.id,
        message=comment_data.message
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {"message": "Comment added successfully"}


@router.get("/{card_id}/comments")
def get_card_comments(
    card_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all comments on card"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    task_list = db.query(List).filter(List.id == card.list_id).first()
    board = db.query(Board).filter(Board.id == task_list.board_id).first()
    get_current_workspace(board.workspace_id, current_user, db)

    comments = (
        db.query(Comment)
        .filter(Comment.card_id == card_id)
        .offset(skip)
        .limit(limit)
        .order_by(Comment.created_at.desc())
        .all()
    )

    result = []
    for comment in comments:
        user = db.query(User).filter(User.id == comment.user_id).first()
        if user:
            result.append({
                "id": comment.id,
                "card_id": comment.card_id,
                "user_id": comment.user_id,
                "user_name": user.name,
                "user_email": user.email,
                "message": comment.message,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at
            })

    return result