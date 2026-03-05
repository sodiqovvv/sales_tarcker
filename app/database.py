from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./sales.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# WAL rejimi
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL;"))
    conn.execute(text("PRAGMA synchronous=FULL;"))
    conn.commit()

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass