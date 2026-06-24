from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class AddMember(BaseModel):
    user_id: int = Field(..., gt=0)


class UpdateRole(BaseModel):
    role: Literal["owner", "manager", "member"] = Field(...)


class WorkspaceMemberResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class WorkspaceMemberDetailResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    name: str
    email: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True

