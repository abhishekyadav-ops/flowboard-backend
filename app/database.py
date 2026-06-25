import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load local .env file settings if running locally
load_dotenv()

# 1. Fetch the raw environment variable string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/flowboard")

# 🌟 2. CRUCIAL PRODUCTION FIX: Convert 'postgres://' to 'postgresql://' for Render compatibility
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False, # manually have to commit 
    autoflush=False,  # till the time we are not commiting, the changes will not be flushed to the database
    bind=engine       # the engine that we created above
)

Base = declarative_base()

def get_db():
    """
    Creates a fresh database session for a request, 
    and automatically closes it when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()