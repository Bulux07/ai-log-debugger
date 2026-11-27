"""Database connection setup: one engine and a session factory for the whole app."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Fail loudly at startup if the URL is missing, instead of at the first query.
DATABASE_URL = os.environ["DATABASE_URL"]

# pool_pre_ping checks a connection is alive before using it, so a restarted
# database doesn't cause one failed request.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Each request will open its own session (a short-lived conversation with the DB).
SessionLocal = sessionmaker(bind=engine, autoflush=False)