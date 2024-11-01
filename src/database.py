import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

def verify_login(username, password):
    """Verify user login credentials"""
    # For demo purposes, accept any non-empty credentials
    return bool(username and password)

# Import models after Base is defined
from .models import Patient, Consultation, Exam

# Create all tables
Base.metadata.create_all(bind=engine)

def get_patient_consultations(db, patient_id):
    """Get all consultations for a patient"""
    return db.query(Consultation).filter(Consultation.patient_id == patient_id).all()

def get_patient_exams(db, patient_id):
    """Get all exams for a patient"""
    return db.query(Exam).filter(Exam.patient_id == patient_id).all()

def create_exam(db, exam_data):
    """Create a new exam record"""
    exam = Exam(**exam_data)
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam

def delete_exam(db, exam_id):
    """Delete an exam record"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if exam:
        db.delete(exam)
        db.commit()
        return True
    return False
