from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ActivityLogResponse(BaseModel):
    id: int
    workspace_id: int
    board_id: Optional[int] = None
    card_id: Optional[int] = None
    action: str
    user_id: int
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityLogDetailResponse(BaseModel):
    id: int
    workspace_id: int
    board_id: Optional[int] = None
    card_id: Optional[int] = None
    action: str
    user_id: int
    user_name: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
