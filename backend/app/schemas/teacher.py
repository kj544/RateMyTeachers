from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeacherCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    role: str = Field(default="Teacher")
    dept: str = Field(default="General", max_length=150)


class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    role: str
    dept: str
    photo_url: str | None = None
    average_rating: float | None = None
    review_count: int = 0