from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)        # "receita" | "despesa"
    category = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String, default="pendente")  # "pago" | "pendente" | "atrasado"
    calendar_event_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
