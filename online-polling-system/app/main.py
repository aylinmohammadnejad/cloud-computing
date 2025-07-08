# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal
from database import engine  

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Online Polling System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return crud.get_results(db, slug)        

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/vote/{slug}")
def vote_page(slug: str):
    # مسیر فایل vote.html
    file_path = os.path.join("frontend", "vote.html")
    return FileResponse(file_path)
