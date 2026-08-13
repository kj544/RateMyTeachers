import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.review import Review


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Teacher",
    )

    dept: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="General",
    )

    photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )

    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="teacher",
        cascade="all, delete-orphan",
    ) 