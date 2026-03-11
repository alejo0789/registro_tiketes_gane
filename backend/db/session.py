from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Get the absolute path to the project root (where .env should be)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Default to SQLite for easy testing, but configurable via .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./acertemos.db")
print(f"--- DATABASE CONNECTED TO: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL} ---")

# Dialect-specific engine arguments
engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
