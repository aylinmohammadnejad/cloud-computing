# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from uuid import uuid4
from typing import List
import uvicorn

app = FastAPI()

# مدل‌ها
class PollCreate(BaseModel):
    question: str
    options: List[str]

class VoteRequest(BaseModel):
    email: EmailStr
    selected_option: str

polls = {}
votes = {}

@app.post("/polls/")
def create_poll(data: PollCreate):
    poll_id = str(uuid4())
    slug = poll_id[:6]
    polls[slug] = {"question": data.question, "options": data.options, "votes": []}
    return {"slug": slug}

@app.get("/polls/{slug}/")
def get_poll(slug: str):
    if slug not in polls:
        raise HTTPException(status_code=404, detail="Poll not found")
    return polls[slug]

@app.post("/polls/{slug}/vote")
def vote(slug: str, vote_data: VoteRequest):
    if slug not in polls:
        raise HTTPException(status_code=404, detail="Poll not found")

    for v in polls[slug]["votes"]:
        if v["email"] == vote_data.email:
            raise HTTPException(status_code=403, detail="Already voted")
    if vote_data.selected_option not in polls[slug]["options"]:
        raise HTTPException(status_code=400, detail="Invalid option")

    polls[slug]["votes"].append({
        "email": vote_data.email,
        "selected_option": vote_data.selected_option
    })
    return {"message": "Vote recorded"}

@app.get("/polls/{slug}/results")
def get_results(slug: str):
    if slug not in polls:
        raise HTTPException(status_code=404, detail="Poll not found")

    total_votes = len(polls[slug]["votes"])
    option_counts = {opt: 0 for opt in polls[slug]["options"]}
    for v in polls[slug]["votes"]:
        option_counts[v["selected_option"]] += 1
    results = {
        opt: f"{(count / total_votes * 100):.1f}%" for opt, count in option_counts.items()
    }
    return {"total": total_votes, "results": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
