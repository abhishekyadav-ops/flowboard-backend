from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CommentCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)


class CommentUpdate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: int
    card_id: int
    user_id: int
    message: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentDetailResponse(BaseModel):
    id: int
    card_id: int
    user_id: int
    user_name: str
    user_email: str
    message: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
