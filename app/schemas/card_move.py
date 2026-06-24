from pydantic import BaseModel, Field


class CardMove(BaseModel):
    list_id: int = Field(..., gt=0)
    position: int = Field(..., ge=0)
