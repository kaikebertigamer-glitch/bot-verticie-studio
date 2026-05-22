import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_data_dir = Path(os.getenv("DATA_DIR", "."))
_data_dir.mkdir(parents=True, exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{_data_dir / 'fintech.db'}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
