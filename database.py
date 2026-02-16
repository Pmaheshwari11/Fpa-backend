import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# For Production (Postgres on Render), we need to handle connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # How many connections to keep open
    max_overflow=20,       # How many extra to open if busy
    pool_pre_ping=True,    # Check if connection is alive before using it
    connect_args={"check_same_thread": False} if "sqlite" in (DATABASE_URL or "") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()