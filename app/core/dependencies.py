from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

# 🌟 FIX: Import the master driver-patched get_db instead of rewriting a broken copy
from app.database import get_db 
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.core.config import (
    SECRET_KEY,
    ALGORITHM
)

# Keeps OAuth2 scheme matched against your real login endpoint path
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)  # 🌟 This now correctly uses your master session!
) -> User:
    """
    Validates incoming signed JWT tickets.
    Blocks fake, modified, or missing authorization tokens completely.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


def get_current_workspace(
    workspace_id: int,
    current_user: User,
    db: Session
) -> WorkspaceMember:
    """Get workspace membership validation profile context"""
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
            detail="Access denied. You are not a member of this workspace."
        )

    return membership


def require_workspace_manager(
    workspace_id: int,
    current_user: User,
    db: Session
) -> WorkspaceMember:
    """Verify user has Manager or Owner authorization status context overrides"""
    membership = get_current_workspace(workspace_id, current_user, db)

    if membership.role not in ["owner", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access privileges required"
        )

    return membership


def require_workspace_owner(
    workspace_id: int,
    current_user: User,
    db: Session
) -> WorkspaceMember:
    """Verify user matches primary Owner criteria profiles"""
    membership = get_current_workspace(workspace_id, current_user, db)

    if membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access privileges required"
        )

    return membership