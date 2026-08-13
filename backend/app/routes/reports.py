from uuid import UUID
from app.core.admin import verify_admin

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.review import Review
from app.models.review_report import ReviewReport
from app.schemas.review_report import (
    ReviewReportCreate,
    ReviewReportResponse,
    ReviewReportStatusUpdate,
)


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


# Report a review
@router.post(
    "/reviews/{review_id}",
    response_model=ReviewReportResponse,
)
def report_review(
    review_id: UUID,
    report_data: ReviewReportCreate,
    db: Session = Depends(get_db),
):
    review = (
        db.query(Review)
        .filter(Review.id == review_id)
        .first()
    )

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Review not found",
        )

    report = ReviewReport(
        review_id=review_id,
        reason=report_data.reason,
        details=report_data.details,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report


# Get all reported reviews
@router.get(
    "/",
    dependencies=[Depends(verify_admin)],
)
def get_reports(
    db: Session = Depends(get_db),
):
    reports = (
        db.query(ReviewReport)
        .order_by(ReviewReport.created_at.desc())
        .all()
    )

    result = []

    for report in reports:
        review = (
            db.query(Review)
            .filter(Review.id == report.review_id)
            .first()
        )

        result.append(
            {
                "report_id": report.id,
                "review_id": report.review_id,
                "reason": report.reason,
                "details": report.details,
                "status": report.status,
                "reported_at": report.created_at,
                "review": (
                    {
                        "rating": review.rating,
                        "text": review.text,
                        "reviewer_name": review.reviewer_name,
                        "teacher_id": review.teacher_id,
                        "created_at": review.created_at,
                    }
                    if review
                    else None
                ),
            }
        )

    return result


# Update a report's status (admin only)
@router.patch(
    "/{report_id}",
    response_model=ReviewReportResponse,
    dependencies=[Depends(verify_admin)],
)
def update_report_status(
    report_id: UUID,
    update: ReviewReportStatusUpdate,
    db: Session = Depends(get_db),
):
    report = (
        db.query(ReviewReport)
        .filter(ReviewReport.id == report_id)
        .first()
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    report.status = update.status
    db.commit()
    db.refresh(report)

    return report