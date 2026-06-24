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


class ActivityActionEnum(str, enum.Enum):
    CARD_MOVED = "card_moved"
    CARD_ASSIGNED = "card_assigned"
    CARD_UNASSIGNED = "card_unassigned"
    CARD_EDITED = "card_edited"
    CARD_CREATED = "card_created"
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    BOARD_CREATED = "board_created"
    LIST_CREATED = "list_created"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    board_id = Column(
        Integer,
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    card_id = Column(
        Integer,
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    action = Column(SQLEnum(ActivityActionEnum), nullable=False, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    details = Column(Text, nullable=True)
    created_at = Column(
    DateTime,
    default=datetime.utcnow,
    nullable=False,
    index=True
)