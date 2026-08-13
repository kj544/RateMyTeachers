# app/schemas/review_report.py
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


ReportReason = Literal["inappropriate", "spam", "harassment", "off_topic", "other"]
ReportStatus = Literal["pending", "reviewed", "dismissed"]


class ReviewReportCreate(BaseModel):
    reason: ReportReason
    details: str | None = None


class ReviewReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    review_id: UUID
    reason: str
    details: str | None
    status: str
    created_at: datetime


class ReviewReportStatusUpdate(BaseModel):
    status: ReportStatus