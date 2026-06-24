from pydantic import BaseModel, Field
from typing import Optional


class ListCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    position: int = Field(default=0, ge=0)


class ListUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[int] = Field(None, ge=0)


class ListReorder(BaseModel):
    position: int = Field(..., ge=0)


class ListResponse(BaseModel):
    id: int
    board_id: int
    title: str
    position: int

    class Config:
        from_attributes = True
