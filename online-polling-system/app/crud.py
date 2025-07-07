from sqlalchemy.orm import Session
import models
import schemas
import random
import string

def generate_slug(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_poll(db: Session, poll: schemas.PollCreate):
    slug = generate_slug()
    db_poll = models.Poll(question=poll.question, options=poll.options, slug=slug)
    db.add(db_poll)
    db.commit()
    db.refresh(db_poll)
    return db_poll

def get_poll_by_slug(db: Session, slug: str):
    return db.query(models.Poll).filter(models.Poll.slug == slug).first()

def create_vote(db: Session, slug: str, vote: schemas.VoteCreate):
    poll = get_poll_by_slug(db, slug)
    if not poll:
        return None
    exists = db.query(models.Vote).filter_by(poll_id=poll.id, email=vote.email).first()
    if exists:
        return "exists"
    new_vote = models.Vote(poll_id=poll.id, email=vote.email, selected_option=vote.selected_option)
    db.add(new_vote)
    db.commit()
    return new_vote
