from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional


class TransactionCreate(BaseModel):
    description: str
    amount: float
    type: str           # "receita" | "despesa"
    category: str
    due_date: date
    status: str = "pendente"
    sync_calendar: bool = False


class StatusUpdate(BaseModel):
    status: str


class Transaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    amount: float
    type: str
    category: str
    due_date: date
    status: str
    calendar_event_id: Optional[str] = None
    created_at: datetime
