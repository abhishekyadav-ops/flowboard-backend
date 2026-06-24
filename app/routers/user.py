from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import re

from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserSearchResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user, get_db

router = APIRouter()


def validate_password(password: str) -> None:
    """Validate password meets security requirements"""
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )
    
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )
    
    if not re.search(r"[0-9]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one digit"
        )
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one special character"
        )


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    validate_password(user.password)
    
    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }


@router.post("/login", status_code=status.HTTP_200_OK)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user and return access token"""
    db_user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if not db_user or not verify_password(form_data.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token({"sub": str(db_user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


# Fix 3: Standardized user query string routing for seamless integration with frontend select/dropdown bars
@router.get("/search", response_model=list[UserSearchResponse])
def search_users(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search active users dynamically by name or email"""
    users = (
        db.query(User)
        .filter(
            User.is_active == True,
            (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
        )
        .limit(limit)
        .all()
    )
    return users


# Fix 2: Retained temporarily for member population fallbacks, added protection for active states
@router.get("", response_model=list[UserResponse])
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all active users (Paginated)"""
    users = (
        db.query(User)
        .filter(User.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return users