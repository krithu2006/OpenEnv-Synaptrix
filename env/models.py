from pydantic import BaseModel
from typing import Optional, Literal

class EmailObservation(BaseModel):
    email_id: str
    subject: str
    body: str
    sender: str
    timestamp: str

class TriageAction(BaseModel):
    category: Literal["Work", "Spam", "Personal"]
    priority: Optional[Literal["High", "Medium", "Low"]] = None
    tone: Optional[Literal["Formal", "Casual", "Urgent"]] = None

class StepResult(BaseModel):
    observation: EmailObservation
    reward: float
    done: bool
    info: dict
