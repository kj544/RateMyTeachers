from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=10)
    text: str = Field(min_length=1)
    reviewer_name: str | None = Field(
        default=None,
        max_length=150,
    )


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    teacher_id: UUID
    rating: int
    text: str
    reviewer_name: str | None
    created_at: datetime