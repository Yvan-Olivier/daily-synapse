"""SQLAlchemy engine & session factory.

Reads Postgres connection details from environment variables (.env).
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "daily_synapse")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


engine = create_engine(get_database_url(), echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    return SessionLocal()
