from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "user_id",
            name="uq_workspace_user"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    
    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False
    )
    
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    role = Column(
        String(20),
        nullable=False,
        default="member"
    )
    
    joined_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Optional: Add ORM relationships to make your queries cleaner down the line
    # workspace = relationship("Workspace", back_populates="members")
    # user = relationship("User", back_populates="workspaces")