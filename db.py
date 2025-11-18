"""
Database models and initialization for the proposal filler application.
This file defines the database schema and provides database connection utilities.
"""
import os
import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_URL = st.secrets["DATABASE_URL"]  # Supabase Postgres URL

engine = create_engine(DB_URL, echo=False, future=True)

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
    file_type = Column(Text, nullable=False)  # MIME type can be long (e.g., application/vnd.openxmlformats-officedocument.wordprocessingml.document)
    
    # Extracted/Form fields
    full_organization_name = Column(String(255), nullable=True)
    legal_designation = Column(String(255), nullable=True)
    mission_statement = Column(Text, nullable=True)
    ein = Column(String(100), nullable=True)  # Increased from 50 to handle formatted EINs
    year_founded = Column(String(10), nullable=True)
    location_served = Column(String(255), nullable=True)
    biggest_accomplishment = Column(Text, nullable=True)
    what_we_do_in_one_sentence = Column(Text, nullable=True)
    primary_cause_area = Column(JSON, nullable=True)  # List of strings
    populations = Column(JSON, nullable=True)  # List of strings
    geographic_focus = Column(String(255), nullable=True)  # Increased from 100 to 255
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Store raw extracted text for reference (can handle 10,000+ characters, not indexed)
    extracted_text = Column(Text, nullable=True, index=False)
    
    # Relationship to likes/passes
    actions = relationship("ProposalAction", back_populates="proposal", cascade="all, delete-orphan")


class ProposalAction(Base):
    """
    Table to store likes and passes on proposals.
    """
    __tablename__ = "proposal_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to proposal submission
    proposal_id = Column(Integer, ForeignKey("proposal_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Action type: like or pass
    action_type = Column(String(10), nullable=False, index=True)  # "like" or "pass"
    
    # Timestamp when action was taken
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Optional: session identifier to track which user/session made the action
    session_id = Column(String(255), nullable=True, index=True)
    
    # Relationship back to proposal
    proposal = relationship("ProposalSubmission", back_populates="actions")


def init_db():
    """
    Initialize the database by creating all tables.
    Call this once at application startup.
    """
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)

# unused thus far
def drop_and_recreate_tables():
    """
    Drop all tables and recreate them.
    WARNING: This will delete all data!
    Only use this during development or when you want to reset the database.
    """
    Base.metadata.drop_all(bind=engine)
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

