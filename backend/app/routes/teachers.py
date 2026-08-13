import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.teacher import Teacher
from app.models.review import Review
from app.schemas.teacher import TeacherCreate, TeacherResponse


router = APIRouter(
    prefix="/teachers",
    tags=["Teachers"],
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
PHOTO_DIR = "app/static/photos"


@router.post("/", response_model=TeacherResponse)
def create_teacher(
    teacher_data: TeacherCreate,
    db: Session = Depends(get_db),
):
    teacher = Teacher(
        name=teacher_data.name,
        role=teacher_data.role,
        dept=teacher_data.dept,
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return TeacherResponse(
        id=teacher.id,
        name=teacher.name,
        role=teacher.role,
        dept=teacher.dept,
        photo_url=teacher.photo_url,
        average_rating=None,
        review_count=0,
    )


@router.get("/", response_model=list[TeacherResponse])
def get_teachers(
    search: str | None = Query(default=None),
    dept: str | None = Query(default=None),
    role: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Teacher)

    if search:
        query = query.filter(
            Teacher.name.ilike(f"%{search}%")
        )

    if dept:
        query = query.filter(
            Teacher.dept.ilike(f"%{dept}%")
        )

    if role:
        query = query.filter(
            Teacher.role.ilike(f"%{role}%")
        )

    teachers = (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []

    for teacher in teachers:
        avg = (
            db.query(func.avg(Review.rating))
            .filter(Review.teacher_id == teacher.id)
            .scalar()
        )

        count = (
            db.query(func.count(Review.id))
            .filter(Review.teacher_id == teacher.id)
            .scalar()
        )

        result.append(
            TeacherResponse(
                id=teacher.id,
                name=teacher.name,
                role=teacher.role,
                dept=teacher.dept,
                photo_url=teacher.photo_url,
                average_rating=float(avg) if avg else None,
                review_count=count or 0,
            )
        )

    return result


@router.get("/{teacher_id}", response_model=TeacherResponse)
def get_teacher(
    teacher_id: UUID,
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

    avg = (
        db.query(func.avg(Review.rating))
        .filter(Review.teacher_id == teacher.id)
        .scalar()
    )

    count = (
        db.query(func.count(Review.id))
        .filter(Review.teacher_id == teacher.id)
        .scalar()
    )

    return TeacherResponse(
        id=teacher.id,
        name=teacher.name,
        role=teacher.role,
        dept=teacher.dept,
        photo_url=teacher.photo_url,
        average_rating=float(avg) if avg else None,
        review_count=count or 0,
    )


@router.delete("/{teacher_id}")
def delete_teacher(
    teacher_id: UUID,
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

    db.delete(teacher)
    db.commit()

    return {
        "message": "Teacher deleted successfully"
    }


@router.post("/{teacher_id}/photo", response_model=TeacherResponse)
async def upload_teacher_photo(
    teacher_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    os.makedirs(PHOTO_DIR, exist_ok=True)
    filename = f"{teacher_id}{ext}"
    filepath = os.path.join(PHOTO_DIR, filename)

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    teacher.photo_url = f"/static/photos/{filename}"
    db.commit()
    db.refresh(teacher)

    avg = db.query(func.avg(Review.rating)).filter(Review.teacher_id == teacher.id).scalar()
    count = db.query(func.count(Review.id)).filter(Review.teacher_id == teacher.id).scalar()

    return TeacherResponse(
        id=teacher.id,
        name=teacher.name,
        role=teacher.role,
        dept=teacher.dept,
        photo_url=teacher.photo_url,
        average_rating=float(avg) if avg else None,
        review_count=count or 0,
    )