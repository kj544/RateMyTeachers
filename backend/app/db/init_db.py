from app.db.database import engine
from app.db.base import Base

from app.models.teacher import Teacher
from app.models.review import Review
from app.models.review_report import ReviewReport


def init_db():
    Base.metadata.create_all(bind=engine)