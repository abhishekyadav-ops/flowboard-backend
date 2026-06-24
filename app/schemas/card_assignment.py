from pydantic import BaseModel, Field
from datetime import datetime


class AssignCard(BaseModel):
    user_id: int = Field(..., gt=0)


class CardAssignmentResponse(BaseModel):
    id: int
    card_id: int
    user_id: int
    assigned_by: int
    assigned_at: datetime

    class Config:
        from_attributes = True
