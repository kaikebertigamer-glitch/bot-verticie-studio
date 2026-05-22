import os
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import uvicorn

import database
import models
import schemas
import calendar_service

app = FastAPI(title="Finanças Empresariais", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=database.engine)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("frontend/index.html", encoding="utf-8") as f:
        return f.read()


# ── helpers ───────────────────────────────────────────────────────────────────

def _auto_overdue(db: Session) -> None:
    db.query(models.Transaction).filter(
        models.Transaction.status == "pendente",
        models.Transaction.due_date < date.today(),
    ).update({"status": "atrasado"})
    db.commit()


def _month_at_offset(now: datetime, offset: int) -> tuple[int, int]:
    month = now.month - offset
    year = now.year
    while month <= 0:
        month += 12
        year -= 1
    return month, year


def _tx_to_dict(t: models.Transaction) -> dict:
    return {
        "id": t.id,
        "description": t.description,
        "amount": t.amount,
        "type": t.type,
        "category": t.category,
        "due_date": t.due_date.isoformat(),
        "status": t.status,
        "calendar_event_id": t.calendar_event_id,
        "created_at": t.created_at.isoformat(),
    }


# ── dashboard ─────────────────────────────────────────────────────────────────

@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(database.get_db)):
    _auto_overdue(db)
    now = datetime.now()
    all_tx = db.query(models.Transaction).all()

    month_tx = [t for t in all_tx if t.due_date.month == now.month and t.due_date.year == now.year]
    total_income   = sum(t.amount for t in month_tx if t.type == "receita" and t.status == "pago")
    total_expenses = sum(t.amount for t in month_tx if t.type == "despesa" and t.status == "pago")

    pending_amount = sum(t.amount for t in all_tx if t.status == "pendente"  and t.type == "despesa")
    overdue_count  = sum(1         for t in all_tx if t.status == "atrasado")

    recent = (
        db.query(models.Transaction)
        .order_by(models.Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    chart_labels, chart_income, chart_expenses = [], [], []
    for i in range(5, -1, -1):
        m, y = _month_at_offset(now, i)
        chunk = [t for t in all_tx if t.due_date.month == m and t.due_date.year == y]
        chart_labels.append(f"{m:02d}/{str(y)[-2:]}")
        chart_income.append(  sum(t.amount for t in chunk if t.type == "receita" and t.status == "pago"))
        chart_expenses.append(sum(t.amount for t in chunk if t.type == "despesa" and t.status == "pago"))

    return {
        "balance": total_income - total_expenses,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "pending_amount": pending_amount,
        "overdue_count": overdue_count,
        "recent_transactions": [_tx_to_dict(t) for t in recent],
        "chart": {"labels": chart_labels, "income": chart_income, "expenses": chart_expenses},
    }


# ── transactions ──────────────────────────────────────────────────────────────

@app.get("/api/transactions", response_model=List[schemas.Transaction])
def list_transactions(
    db: Session = Depends(database.get_db),
    type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, le=500),
):
    _auto_overdue(db)
    q = db.query(models.Transaction)
    if type:   q = q.filter(models.Transaction.type   == type)
    if status: q = q.filter(models.Transaction.status == status)
    return q.order_by(models.Transaction.due_date.desc()).limit(limit).all()


@app.post("/api/transactions", response_model=schemas.Transaction, status_code=201)
def create_transaction(data: schemas.TransactionCreate, db: Session = Depends(database.get_db)):
    tx = models.Transaction(**data.model_dump(exclude={"sync_calendar"}))
    db.add(tx)
    db.commit()
    db.refresh(tx)

    if data.sync_calendar:
        try:
            tx.calendar_event_id = calendar_service.create_event(tx)
            db.commit()
        except Exception:
            pass  # Transaction saved; calendar sync is best-effort

    return tx


@app.patch("/api/transactions/{tx_id}/status", response_model=schemas.Transaction)
def update_status(tx_id: int, data: schemas.StatusUpdate, db: Session = Depends(database.get_db)):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(404, "Transação não encontrada")
    tx.status = data.status
    db.commit()
    db.refresh(tx)
    return tx


@app.delete("/api/transactions/{tx_id}")
def delete_transaction(tx_id: int, db: Session = Depends(database.get_db)):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(404, "Transação não encontrada")
    if tx.calendar_event_id:
        try:
            calendar_service.delete_event(tx.calendar_event_id)
        except Exception:
            pass
    db.delete(tx)
    db.commit()
    return {"ok": True}


# ── google oauth ──────────────────────────────────────────────────────────────

@app.get("/api/auth/google")
def google_auth():
    if not calendar_service.credentials_file_exists():
        raise HTTPException(400, "Arquivo credentials.json não encontrado. Veja as instruções de configuração.")
    return RedirectResponse(calendar_service.get_auth_url())


@app.get("/api/auth/callback")
def google_callback(code: str, state: Optional[str] = None):
    try:
        calendar_service.exchange_code(code, state or "")
        return RedirectResponse("/?auth=success")
    except Exception:
        return RedirectResponse("/?auth=error")


@app.get("/api/auth/status")
def auth_status():
    return {"authenticated": calendar_service.is_authenticated()}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
