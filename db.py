"""
Database models and initialization for the proposal filler application.
This file defines the database schema and provides database connection utilities.
"""
import os
import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = st.secrets["DATABASE_URL"]  # Supabase Postgres URL

engine = create_engine(DB_URL, echo=False, future=True)

# Database URL - can be easily changed to cloud database later
# DB_URL = os.getenv("DATABASE_URL", "sqlite:///data/app.db")

# Create engine
# engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class ProposalSubmission(Base):
    """
    Main table to store proposal submissions with extracted and form data.
    """
    __tablename__ = "proposal_submissions"

    id = Column(Integer, primary_key=True, index=True)
    # File information
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Local path or S3 key
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    
    # Extracted/Form fields
    full_organization_name = Column(String(255), nullable=True)
    legal_designation = Column(String(255), nullable=True)
    mission_statement = Column(Text, nullable=True)
    ein = Column(String(50), nullable=True)
    year_founded = Column(String(10), nullable=True)
    location_served = Column(String(255), nullable=True)
    biggest_accomplishment = Column(Text, nullable=True)
    what_we_do_in_one_sentence = Column(Text, nullable=True)
    primary_cause_area = Column(JSON, nullable=True)  # List of strings
    populations = Column(JSON, nullable=True)  # List of strings
    geographic_focus = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Store raw extracted text for reference
    extracted_text = Column(Text, nullable=True)


def init_db():
    """
    Initialize the database by creating all tables.
    Call this once at application startup.
    """
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency function to get database session.
    Use this in a context manager or with try/finally.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

