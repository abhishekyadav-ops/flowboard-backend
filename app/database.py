# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:root@localhost:5432/flowboard"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False, # manually have to commit 
    autoflush=False,  # till the time we are not commiting, the changes will not be flushed to the database
    bind=engine # the engine that we created above
)

Base = declarative_base()

# 🌟 ADD THIS NEW CODE HERE:
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