from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal, List


class CardCreate(BaseModel):
    list_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    due_date: Optional[datetime] = None
    links: Optional[List[str]] = []


class CardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    due_date: Optional[datetime] = None
    links: Optional[List[str]] = None


class CardMoveRequest(BaseModel):
    list_id: int = Field(..., gt=0)
    position: int = Field(..., ge=0)


class CardResponse(BaseModel):
    id: int
    list_id: int
    title: str
    description: Optional[str] = None
    priority: Literal[
        "low",
        "medium",
        "high",
        "critical"
    ]
    due_date: Optional[datetime] = None
    links: Optional[List[str]] = []
    position: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True