from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent / "chores.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    from app import models

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if inspector.has_table("team_members"):
        existing = {col["name"] for col in inspector.get_columns("team_members")}
        if "color" not in existing:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE team_members ADD COLUMN color VARCHAR(7) "
                        f"NOT NULL DEFAULT '{models.DEFAULT_MEMBER_COLOR}'"
                    )
                )
