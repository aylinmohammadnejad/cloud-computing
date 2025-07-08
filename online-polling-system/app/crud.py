import os
import json
import random
import string
from uuid import uuid4
from sqlalchemy.orm import Session
import redis

import models
import schemas
from worker import analyze_votes  # ✅ Celery task

# Redis setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)

# تولید slug برای Poll
def generate_slug(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# ایجاد نظرسنجی
def create_poll(db: Session, poll: schemas.PollCreate):
    slug = generate_slug()
    db_poll = models.Poll(
        question=poll.question,
        options=poll.options,
        slug=slug
    )
    db.add(db_poll)
    db.commit()
    db.refresh(db_poll)
    return db_poll

# گرفتن Poll با slug
def get_poll_by_slug(db: Session, slug: str):
    return db.query(models.Poll).filter(models.Poll.slug == slug).first()

# ذخیره رأی جدید
def create_vote(db: Session, slug: str, vote: schemas.VoteCreate):
    poll = get_poll_by_slug(db, slug)
    if not poll:
        return None

    # چک تکراری بودن رأی
    exists = db.query(models.Vote).filter_by(poll_id=poll.id, email=vote.email).first()
    if exists:
        return "exists"

    # چک اعتبار گزینه انتخاب‌شده
    if vote.selected_option not in poll.options:
        raise ValueError("Invalid option selected")

    # ذخیره رأی
    new_vote = models.Vote(
        id=str(uuid4()),
        poll_id=poll.id,
        email=vote.email,
        selected_option=vote.selected_option
    )
    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)

    #  ارسال به Celery برای تحلیل
    analyze_votes.delay(str(poll.id))

    return new_vote

# گرفتن نتایج رأی‌گیری
def get_results(db: Session, slug: str):
    redis_key = f"poll:{slug}:results"

    # اول چک کش Redis
    cached = redis_client.get(redis_key)
    if cached:
        print("📦 نتیجه از کش خوانده شد")
        return json.loads(cached)

    poll = get_poll_by_slug(db, slug)
    if not poll:
        return {"detail": "Poll not found"}

    votes = db.query(models.Vote).filter_by(poll_id=poll.id).all()
    total_votes = len(votes)

    results = []
    for option in poll.options:
        count = sum(1 for vote in votes if vote.selected_option == option)
        percentage = (count / total_votes * 100) if total_votes > 0 else 0
        results.append({
            "option": option,
            "count": count,
            "percentage": round(percentage, 2)
        })

    result_data = {
        "question": poll.question,
        "total_votes": total_votes,
        "results": results
    }

    redis_client.set(redis_key, json.dumps(result_data), ex=300)

    return result_data
