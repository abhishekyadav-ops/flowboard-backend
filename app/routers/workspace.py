from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func 

from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.user import User
from app.models.board import Board
from app.models.list import List 
from app.models.card import Card 
from app.models.card_assignment import CardAssignment 
from app.models.comment import Comment 

# 🌟 Strict schema mapping out of workspace to avoid namespace masking
from app.schemas.workspace import (
    WorkspaceCreate, 
    WorkspaceUpdate, 
    WorkspaceResponse, 
    WorkspaceDetailResponse,
    WorkspaceMemberDetailResponse,
    UserMinResponse
)
from app.schemas.workspace_member import AddMember, UpdateRole

from app.core.dependencies import (
    get_current_user,
    get_db,
    get_current_workspace,
    require_workspace_manager,
    require_workspace_owner
)

router = APIRouter()

# --- WORKSPACE CRUD ENPOINTS ---




@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new workspace and establish initial owner permissions"""
    cleaned_name = workspace.name.strip()

    # 🌟 1. Case-Insensitive Duplicate Check for this owner
    existing_workspace = db.query(Workspace).filter(
        func.lower(Workspace.name) == func.lower(cleaned_name),
        Workspace.owner_id == current_user.id
    ).first()

    if existing_workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A workspace named '{cleaned_name}' already exists."
        )

    # 2. Proceed with creation if everything is unique
    new_workspace = Workspace(
        name=cleaned_name,  # Saves the cleaned string version without accidental spaces
        description=workspace.description,
        owner_id=current_user.id
    )

    db.add(new_workspace)
    db.commit()
    db.refresh(new_workspace)

    membership = WorkspaceMember(
        workspace_id=new_workspace.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(membership)
    db.commit()

    return new_workspace


@router.get("/", response_model=list[WorkspaceResponse])
def get_workspaces(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all workspaces the current user has access to"""
    memberships = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    workspace_ids = [member.workspace_id for member in memberships]

    workspaces = (
        db.query(Workspace)
        .filter(Workspace.id.in_(workspace_ids))
        .all()
    ) if workspace_ids else []

    return workspaces


@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get standalone workspace description details"""
    get_current_workspace(workspace_id, current_user, db)

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceDetailResponse)
def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update general configuration metadata (Workspace Owners Only)"""
    require_workspace_owner(workspace_id, current_user, db)

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    if workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the workspace owner can perform this action."
        )

    if workspace_data.name:
        workspace.name = workspace_data.name
    if workspace_data.description is not None:
        workspace.description = workspace_data.description

    db.commit()
    db.refresh(workspace)

    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Purge a workspace along with its complete relational task-board structures.
    Enforces real, verified OG user ownership before wiping any rows.
    """
    # 1. Fetch the target workspace and verify existence
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # 2. 🌟 CRUCIAL SECURE FIX: Force verification against your dynamic dependencies file!
    # This reads the logged-in user's true membership record and blocks them if they aren't the OG owner.
    require_workspace_owner(workspace_id, current_user, db)

    # 3. Deep-Purge Cascades: Boards -> Lists -> Cards -> Assignments & Comments
    # Keep your manual purge loops here for safety if you don't have ON DELETE CASCADE configured in DB models yet.
    boards = db.query(Board).filter(Board.workspace_id == workspace_id).all()
    board_ids = [board.id for board in boards]

    if board_ids:
        lists = db.query(List).filter(List.board_id.in_(board_ids)).all()
        list_ids = [lst.id for lst in lists]

        if list_ids:
            cards = db.query(Card).filter(Card.list_id.in_(list_ids)).all()
            card_ids = [card.id for card in cards]

            if card_ids:
                db.query(CardAssignment).filter(CardAssignment.card_id.in_(card_ids)).delete(synchronize_session=False)
                db.query(Comment).filter(Comment.card_id.in_(card_ids)).delete(synchronize_session=False)
                db.query(Card).filter(Card.id.in_(card_ids)).delete(synchronize_session=False)

            db.query(List).filter(List.id.in_(list_ids)).delete(synchronize_session=False)

        db.query(Board).filter(Board.id.in_(board_ids)).delete(synchronize_session=False)

    # 4. Clean up Workspace Members
    db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id).delete(synchronize_session=False)

    # 5. Safe to drop the workspace row now
    db.delete(workspace)
    db.commit()

# --- WORKSPACE MEMBERSHIP & DROPDOWN ENDPOINTS ---

@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberDetailResponse])
def get_workspace_members(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get structured workspace members for card assignment dropdown lists"""
    get_current_workspace(workspace_id, current_user, db)

    memberships = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .all()
    )

    result = []
    for membership in memberships:
        user = db.query(User).filter(User.id == membership.user_id).first()
        if user:
            result.append({
                "id": membership.id,
                "workspace_id": membership.workspace_id,
                "user_id": membership.user_id,
                "role": membership.role,
                "joined_at": membership.joined_at,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email
                }
            })

    return result


@router.post("/{workspace_id}/members", status_code=status.HTTP_201_CREATED)
def add_workspace_member(
    workspace_id: int,
    member_data: AddMember,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a registered user to the workspace team (Managers/Owners Only)"""
    require_workspace_manager(workspace_id, current_user, db)

    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    existing_member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == member_data.user_id
        )
        .first()
    )

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already a member of this workspace"
        )

    new_member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=member_data.user_id,
        role="member"
    )

    db.add(new_member)
    db.commit()

    return {"message": "Member added successfully"}


@router.put("/{workspace_id}/members/{user_id}/role")
def update_member_role(
    workspace_id: int,
    user_id: int,
    role_data: UpdateRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modify workspace access permissions (Workspace Owners Only)"""
    require_workspace_owner(workspace_id, current_user, db)

    membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    if membership.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner role cannot be changed"
        )

    membership.role = role_data.role
    db.commit()

    return {"message": "Member role updated successfully"}


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_workspace_member(
    workspace_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke user access from workspace scope (Workspace Owners Only)"""
    require_workspace_owner(workspace_id, current_user, db)

    membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    if membership.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot be removed"
        )

    db.delete(membership)
    db.commit()

@router.get("/{workspace_id}/stats")
def get_workspace_stats(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve operational high-level counts for dashboards"""
    get_current_workspace(workspace_id, current_user, db)

    # 1. Count boards in this workspace
    active_boards = db.query(Board).filter(Board.workspace_id == workspace_id).count()
    
    # 2. 🌟 FIX: Count ONLY unique users inside this workspace
    unique_member_count = (
        db.query(func.count(WorkspaceMember.user_id.distinct()))
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .scalar()
    )

    # 3. 🌟 FIX: Return the precise keys your React frontend state needs
    return {
        "activeBoards": active_boards,
        "teamMembers": unique_member_count
    }


# 🌟 NEW ADDITION: User Directory Search for "Invite/Add Member" Form Dropdowns
@router.get("/{workspace_id}/search-users", response_model=list[UserMinResponse])
def search_assignable_users(
    workspace_id: int,
    q: str = Query("", min_length=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Find platform users who are NOT yet part of this workspace.
    Feeds your global search autocomplete dropdowns seamlessly.
    """
    get_current_workspace(workspace_id, current_user, db)

    # Find existing workspace member IDs so we don't list them again
    existing_member_ids = [
        m.user_id for m in db.query(WorkspaceMember.user_id).filter(
            WorkspaceMember.workspace_id == workspace_id
        ).all()
    ]

    query = db.query(User).filter(User.id.not_in(existing_member_ids))
    if q:
        query = query.filter((User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%")))

    return query.limit(20).all()