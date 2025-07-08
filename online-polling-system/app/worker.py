# app/worker.py
from celery import Celery
from sqlalchemy.orm import sessionmaker
from database import engine
from models import Vote, Poll
import os
import redis
import json

# تنظیم اتصال Redis و Celery
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("worker", broker=REDIS_URL)

# اتصال Redis برای کش کردن نتایج
redis_client = redis.Redis.from_url(REDIS_URL)

# اتصال به دیتابیس
SessionLocal = sessionmaker(bind=engine)

@celery_app.task
def analyze_votes(poll_id):
    db = SessionLocal()
    try:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return

        votes = db.query(Vote).filter_by(poll_id=poll_id).all()
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

        # کش کردن در Redis با کلید poll:{slug}:results
        redis_key = f"poll:{poll.slug}:results"
        redis_client.set(redis_key, json.dumps(result_data), ex=300)  
        print(f"✅ کش نتایج انجام شد برای poll: {poll.slug}")

    finally:
        db.close()
