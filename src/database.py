import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Create base class for declarative models
Base = declarative_base()

# Import models after Base is defined
from .models import Patient, Consultation, Exam

def init_database():
    """Initialize database connection"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        st.error("⚠️ DATABASE_URL não está configurado. Por favor, configure as variáveis de ambiente no Streamlit Cloud.")
        st.info("Para configurar:")
        st.code("""
1. Vá para Configurações do App no Streamlit Cloud
2. Encontre a seção "Secrets"
3. Adicione:
[database]
DATABASE_URL = "sua-url-do-banco-de-dados"
        """)
        return None
    
    try:
        # Create SQLAlchemy engine
        engine = create_engine(database_url)
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        return SessionLocal
    except Exception as e:
        st.error(f"⚠️ Erro ao conectar ao banco de dados: {str(e)}")
        return None

# Initialize session factory
SessionLocal = init_database()

def verify_login(username, password):
    """Verify user login credentials"""
    if not SessionLocal:
        return False
    return bool(username and password)

def get_patient_consultations(db, patient_id):
    """Get all consultations for a patient"""
    if not db:
        return []
    return db.query(Consultation).filter(Consultation.patient_id == patient_id).all()

def get_patient_exams(db, patient_id):
    """Get all exams for a patient"""
    if not db:
        return []
    return db.query(Exam).filter(Exam.patient_id == patient_id).all()

def create_exam(db, exam_data):
    """Create a new exam record"""
    if not db:
        return None
    exam = Exam(**exam_data)
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam

def delete_exam(db, exam_id):
    """Delete an exam record"""
    if not db:
        return False
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if exam:
        db.delete(exam)
        db.commit()
        return True
    return False
