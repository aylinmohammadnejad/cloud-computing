# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal
from database import engine  # این خط رو اضافه کن


# جداول را (تنها بار اول) بساز
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Online Polling System")

# اجازه CORS برای فرانت ساده
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# وابستگی گرفتن سشن دیتابیس
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- Endpoints ----
@app.post("/polls/", response_model=schemas.PollResponse)
def create_poll(poll: schemas.PollCreate, db: Session = Depends(get_db)):
    return crud.create_poll(db, poll)

@app.get("/polls/{slug}/", response_model=schemas.PollResponse)
def get_poll(slug: str, db: Session = Depends(get_db)):
    poll = crud.get_poll_by_slug(db, slug)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return poll

@app.post("/polls/{slug}/vote")
def vote(slug: str, vote: schemas.VoteCreate, db: Session = Depends(get_db)):
    result = crud.create_vote(db, slug, vote)
    if result == "exists":
        raise HTTPException(status_code=403, detail="You have already voted")
    if result is None:
        raise HTTPException(status_code=404, detail="Poll not found")
    return {"message": "Vote submitted"}

@app.get("/polls/{slug}/results")
def poll_results(slug: str, db: Session = Depends(get_db)):
    return crud.get_results(db, slug)          # این تابع را در crud پیاده‌سازی کن
