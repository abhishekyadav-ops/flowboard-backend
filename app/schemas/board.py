from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.schemas.workspace import UserMinResponse

# 🌟 CLEANED UP: Self-referencing import removed from here!

class BoardCreate(BaseModel):
    workspace_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class BoardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class BoardResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    owner: Optional[UserMinResponse] = None

    class Config:
        from_attributes = True