from sqlalchemy import Column, Integer, String, ForeignKey

from app.database import Base


class List(Base):
    __tablename__ = "lists"

    id = Column(Integer, primary_key=True, index=True)

    board_id = Column(
        Integer,
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    title = Column(
        String(100),
        nullable=False,
        index=True
    )

    position = Column(
        Integer,
        nullable=False,
        default=0
    )