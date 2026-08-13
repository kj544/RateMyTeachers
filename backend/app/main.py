import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db.init_db import init_db
from app.routes.teachers import router as teacher_router
from app.routes.reviews import router as review_router
from app.routes.reports import router as reports_router


app = FastAPI(
    title="RateMyTeachers API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # dev only — restrict to your real frontend origin before going live
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("app/static/photos", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def startup():
    init_db()


app.include_router(teacher_router)
app.include_router(review_router)
app.include_router(reports_router)


@app.get("/")
def root():
    return {
        "message": "RateMyTeachers API is running"
    }