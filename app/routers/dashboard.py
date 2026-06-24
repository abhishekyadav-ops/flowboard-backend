from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from app.models.workspace_member import WorkspaceMember
from app.models.board import Board
from app.models.list import List
from app.models.card import Card
from app.models.card_assignment import CardAssignment
from app.models.user import User

# Fix 1: Removed local SessionLocal import and centralized dependencies
from app.core.dependencies import get_current_user, get_db

router = APIRouter()


@router.get("/workspace/{workspace_id}")
def workspace_dashboard(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    boards = (
        db.query(Board)
        .filter(Board.workspace_id == workspace_id)
        .all()
    )

    stats = {
        "todo": 0,
        "in_progress": 0,
        "review": 0,
        "done": 0
    }

    for board in boards:
        lists = (
            db.query(List)
            .filter(List.board_id == board.id)
            .all()
        )

        for lst in lists:
            card_count = (
                db.query(Card)
                .filter(Card.list_id == lst.id)
                .count()
            )

            # Standardize variations by removing spaces and making it lowercase
            title = lst.title.lower().replace(" ", "")

            # Fix 2: Updated matching logic to catch "todo", "to do", and variations safely
            if title in ["todo", "todo"]:
                stats["todo"] += card_count

            elif title == "inprogress":
                stats["in_progress"] += card_count

            elif title == "review":
                stats["review"] += card_count

            elif title == "done":
                stats["done"] += card_count

    members = []

    workspace_members = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .all()
    )

    for member in workspace_members:
        user = (
            db.query(User)
            .filter(User.id == member.user_id)
            .first()
        )

        # Fix 3 (Performance Note): Left for post-deployment optimization as per instructions
        assigned_tasks = (
            db.query(CardAssignment)
            .filter(CardAssignment.user_id == member.user_id)
            .count()
        )

        # Fix 4: Protected against AttributeError crashes if user database records are mismatched
        if user:
            members.append({
                "id": user.id,
                "name": user.name,
                "assigned_tasks": assigned_tasks
            })

    return {
        "workspace_id": workspace_id,
        "todo": stats["todo"],
        "in_progress": stats["in_progress"],
        "review": stats["review"],
        "done": stats["done"],
        "members": members
    }