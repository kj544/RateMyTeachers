from uuid import UUID
from app.core.admin import verify_admin


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.teacher import Teacher
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewResponse


router = APIRouter(
    tags=["Reviews"],
)


@router.post(
    "/teachers/{teacher_id}/reviews",
    response_model=ReviewResponse,
)
def create_review(
    teacher_id: UUID,
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
):
    teacher = (
        db.query(Teacher)
        .filter(Teacher.id == teacher_id)
        .first()
    )

    if teacher is None:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found",
        )

    review = Review(
        teacher_id=teacher_id,
        rating=review_data.rating,
        text=review_data.text,
        reviewer_name=review_data.reviewer_name,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review

@router.get(
    "/teachers/{teacher_id}/reviews",
    response_model=list[ReviewResponse],
)
def get_teacher_reviews(
    teacher_id: UUID,
    sort: str = Query(
        default="newest",
        pattern="^(newest|oldest|highest|lowest)$",
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    teacher = (
        db.query(Teacher)
        .filter(Teacher.id == teacher_id)
        .first()
    )

    if teacher is None:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found",
        )

    query = (
        db.query(Review)
        .filter(Review.teacher_id == teacher_id)
    )

    if sort == "newest":
        query = query.order_by(Review.created_at.desc())

    elif sort == "oldest":
        query = query.order_by(Review.created_at.asc())

    elif sort == "highest":
        query = query.order_by(Review.rating.desc())

    elif sort == "lowest":
        query = query.order_by(Review.rating.asc())

    reviews = (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )

    return reviews


@router.delete(
    "/reviews/{review_id}",
    dependencies=[Depends(verify_admin)],
)
def delete_review(
    review_id: UUID,
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

    db.delete(review)
    db.commit()

    return {
        "message": "Review deleted successfully"
    }
