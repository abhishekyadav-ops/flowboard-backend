from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint
)
from datetime import datetime

from app.database import Base


class CardAssignment(Base):
    __tablename__ = "card_assignments"
    __table_args__ = (
        UniqueConstraint('card_id', 'user_id', name='_card_user_uc'),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    card_id = Column(
        Integer,
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    assigned_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    assigned_at = Column(
    DateTime,
    default=datetime.utcnow,
    nullable=False,
    index=True
)