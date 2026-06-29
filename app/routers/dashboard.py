from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.board import Board
from app.models.list import List
from app.models.card import Card
from app.models.card_assignment import CardAssignment
from app.models.user import User
from app.core.dependencies import get_current_user, get_db

router = APIRouter()


@router.get("/workspace/{workspace_id}")
def workspace_dashboard(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify the current user is a member of this workspace
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

    # Fetch workspace to know the owner (needed for board visibility)
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id)
        .first()
    )

    # Bug 2 fixed: only return boards the current user is allowed to see.
    # Owner's boards are visible to everyone; member-created boards
    # are only visible to the workspace owner and the creator themselves.
    boards = (
        db.query(Board)
        .filter(
            Board.workspace_id == workspace_id,
            (Board.created_by == workspace.owner_id) |
            (Board.created_by == current_user.id)
        )
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

            # Normalize: lowercase and strip spaces before matching
            title = lst.title.lower().replace(" ", "")

            # Bug 1 fixed: "to do" → "todo" after .replace(), so one check is enough.
            # The original ["todo", "todo"] never actually caught the "to do" variation.
            if title == "todo":
                stats["todo"] += card_count
            elif title == "inprogress":
                stats["in_progress"] += card_count
            elif title == "review":
                stats["review"] += card_count
            elif title == "done":
                stats["done"] += card_count

    # Bug 3 fixed: use joinedload to fetch all users in one query instead of
    # firing a separate SELECT per member inside the loop.
    workspace_members = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .options(joinedload(WorkspaceMember.user))
        .all()
    )

    members = []

    for member in workspace_members:
        user = member.user  # already loaded — no extra query

        if not user:
            continue

        # Bug 4 fixed: scope the assigned_tasks count to this workspace only,
        # not the user's total assignments across every workspace in the database.
        assigned_tasks = (
            db.query(CardAssignment)
            .join(Card, Card.id == CardAssignment.card_id)
            .join(List, List.id == Card.list_id)
            .join(Board, Board.id == List.board_id)
            .filter(
                CardAssignment.user_id == member.user_id,
                Board.workspace_id == workspace_id
            )
            .count()
        )

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