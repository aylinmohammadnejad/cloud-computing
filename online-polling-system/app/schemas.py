from pydantic import BaseModel, EmailStr
from typing import List
from uuid import UUID
from datetime import datetime

class PollCreate(BaseModel):
    question: str
    options: List[str]

class PollResponse(BaseModel):
    id: UUID
    question: str
    options: List[str]
    slug: str
    created_at: datetime

    class Config:
        orm_mode = True

class VoteCreate(BaseModel):
    email: EmailStr
    selected_option: str
