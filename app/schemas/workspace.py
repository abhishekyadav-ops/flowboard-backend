from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkspaceDetailResponse(WorkspaceResponse):
    pass


# 🌟 Added: A minimal sub-schema to cleanly hold the user profile details
class UserMinResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


# Inside app/schemas/workspace.py

class WorkspaceMemberResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    role: str
    # 🌟 Explicitly typed with typing.Optional and defaulted to None
    joined_at: Optional[datetime] = None  

    class Config:
        from_attributes = True


# 🌟 Updated: Explicitly redeclare fields if your sub-classing layer is dropping properties
class WorkspaceMemberDetailResponse(WorkspaceMemberResponse):
    user: Optional[UserMinResponse] = None
    # 🌟 Re-enforcing this field here completely guarantees Pydantic allows None values
    joined_at: Optional[datetime] = None  

    class Config:
        from_attributes = True