import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from a .env file into os.environ
load_dotenv()

# Read the DATABASE_URL environment variable. Docker Compose provides Postgres;
# the SQLite fallback keeps local development simple.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./booktracker.db")

# Create the SQLAlchemy engine using the configured database URL.
# For SQLite, SQLAlchemy requires check_same_thread=False when using it with FastAPI.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Create a SessionLocal factory that can be used to create new session objects.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all SQLAlchemy models to inherit from.
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
