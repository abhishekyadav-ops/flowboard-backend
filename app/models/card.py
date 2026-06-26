from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Enum as SQLEnum
)
from datetime import datetime
import enum

from app.database import Base


class PriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer,ForeignKey("lists.id", ondelete="CASCADE"),nullable=False,index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.MEDIUM, index=True)
    due_date = Column(DateTime, nullable=True, index=True)
    position = Column(Integer, nullable=False, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False)
    important_link = Column(Text, nullable=True)