"""
Database Connection and Session Management for NELIA Suite.
Connects to PostgreSQL (Docker container scriptor_postgres or local instance).
Provides transparent automatic SQLite fallback if PostgreSQL is not available,
ensuring zero configuration issues for any end-user cloning from GitHub.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

POSTGRES_USER = os.getenv("POSTGRES_USER", "scriptor")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "scriptor_password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "scriptor_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

IS_SQLITE_FALLBACK = False
Base = declarative_base()


def _create_engine_with_fallback():
    global IS_SQLITE_FALLBACK
    if DATABASE_URL.startswith("sqlite"):
        IS_SQLITE_FALLBACK = True
        return create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)

    try:
        # Probar conexión con timeout corto para no congelar si PostgreSQL no está disponible
        pg_engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 2} if "psycopg" in DATABASE_URL else {},
            echo=False
        )
        with pg_engine.connect() as conn:
            pass
        return pg_engine
    except Exception as e:
        print(f"⚠️  [Aviso DB] PostgreSQL no detectado en {POSTGRES_HOST}:{POSTGRES_PORT} ({e}).")
        print("💡 [Aviso DB] Activando almacenamiento local SQLite ('nelia_local.db') automáticamente.")
        IS_SQLITE_FALLBACK = True
        return create_engine(
            "sqlite:///nelia_local.db",
            connect_args={"check_same_thread": False},
            echo=False
        )


engine = _create_engine_with_fallback()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from db import models
    Base.metadata.create_all(bind=engine)
