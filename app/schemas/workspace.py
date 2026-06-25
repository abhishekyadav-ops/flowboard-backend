from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# 🌟 STEP 1: Define UserMinResponse FIRST so the workspace models can see it
class UserMinResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


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
    
    # 🌟 STEP 2: Add the nested owner field to your core response
    owner: Optional[UserMinResponse] = None

    class Config:
        from_attributes = True


class WorkspaceDetailResponse(WorkspaceResponse):
    # This automatically inherits the 'owner' field from WorkspaceResponse!
    pass


class WorkspaceMemberResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    role: str
    joined_at: Optional[datetime] = None  

    class Config:
        from_attributes = True


class WorkspaceMemberDetailResponse(WorkspaceMemberResponse):
    user: Optional[UserMinResponse] = None
    joined_at: Optional[datetime] = None  

    class Config:
        from_attributes = True