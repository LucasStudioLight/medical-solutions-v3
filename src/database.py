from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, LargeBinary, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from datetime import datetime
from pathlib import Path
import hashlib
import enum

# Create database directory
db_dir = Path(__file__).parent.parent / 'data' / 'database'
db_dir.mkdir(parents=True, exist_ok=True)

# Create database engine with connection pooling and timeout settings
DATABASE_URL = f"sqlite:///{db_dir}/medical_records.db?timeout=30"
engine = create_engine(
    DATABASE_URL,
    connect_args={
        'timeout': 30,
        'check_same_thread': False
    },
    pool_size=20,
    max_overflow=0
)

# Create declarative base
Base = declarative_base()

# Create scoped session factory
session_factory = sessionmaker(bind=engine)
SessionLocal = scoped_session(session_factory)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password):
        return self.password_hash == self.hash_password(password)

class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    data_nascimento = Column(DateTime)
    cpf = Column(String(14), unique=True)
    telefone = Column(String(20))
    email = Column(String(100))
    endereco = Column(String(200))
    sexo = Column(String(20))
    
    # Relationships
    consultas = relationship("Consultation", back_populates="patient", cascade="all, delete-orphan")
    exames = relationship("Exam", back_populates="patient", cascade="all, delete-orphan")

class Consultation(Base):
    __tablename__ = 'consultations'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id', ondelete='CASCADE'))
    data_consulta = Column(DateTime, default=datetime.now)
    transcricao_completa = Column(Text)
    resumo_clinico = Column(Text)
    segmentos_detalhados = Column(Text)  # JSON string of all segments with timing
    
    # Metadata
    duracao_segundos = Column(Integer)
    quantidade_segmentos = Column(Integer)
    
    # Medical summary fields
    queixa_principal = Column(Text)
    historia_atual = Column(Text)
    exame_fisico = Column(Text)
    diagnostico = Column(Text)
    prescricoes = Column(Text)
    observacoes = Column(Text)
    
    # Relationships
    patient = relationship("Patient", back_populates="consultas")
    exames = relationship("Exam", back_populates="consultation")

class Exam(Base):
    __tablename__ = 'exams'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id', ondelete='CASCADE'))
    consultation_id = Column(Integer, ForeignKey('consultations.id', ondelete='SET NULL'), nullable=True)
    data_exame = Column(DateTime, default=datetime.now)
    tipo_exame = Column(String(100))
    arquivo_pdf = Column(LargeBinary)  # PDF file content
    texto_exame = Column(Text)  # Extracted text from PDF
    analise = Column(Text)  # JSON string of exam analysis
    
    # Relationships
    patient = relationship("Patient", back_populates="exames")
    consultation = relationship("Consultation", back_populates="exames")

# Create all tables
Base.metadata.create_all(engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database with default user"""
    db = SessionLocal()
    try:
        # Create default user if not exists
        if not db.query(User).filter_by(username='medico').first():
            default_user = User(
                username='medico',
                password_hash=User.hash_password('adm')
            )
            db.add(default_user)
            db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def verify_login(username, password):
    """Verify user login"""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username=username).first()
        return user and user.verify_password(password)
    finally:
        db.close()

def create_patient(db, patient_data):
    """Create a new patient"""
    try:
        patient = Patient(**patient_data)
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient
    except Exception as e:
        db.rollback()
        raise e

def get_patient(db, cpf):
    """Get patient by CPF"""
    return db.query(Patient).filter(Patient.cpf == cpf).first()

def get_patients_by_name(db, nome):
    """Get patients by name (partial match)"""
    try:
        return db.query(Patient).filter(Patient.nome.ilike(f"%{nome}%")).all()
    except Exception as e:
        print(f"Error in get_patients_by_name: {str(e)}")
        return []

def create_consultation(db, consultation_data):
    """Create a new consultation"""
    try:
        consultation = Consultation(**consultation_data)
        db.add(consultation)
        db.commit()
        db.refresh(consultation)
        return consultation
    except Exception as e:
        db.rollback()
        raise e

def get_patient_consultations(db, patient_id):
    """Get all consultations for a patient"""
    return db.query(Consultation).filter(Consultation.patient_id == patient_id).all()

def create_exam(db, exam_data):
    """Create a new exam"""
    try:
        exam = Exam(**exam_data)
        db.add(exam)
        db.commit()
        db.refresh(exam)
        return exam
    except Exception as e:
        db.rollback()
        raise e

def get_patient_exams(db, patient_id):
    """Get all exams for a patient"""
    return db.query(Exam).filter(Exam.patient_id == patient_id).order_by(Exam.data_exame.desc()).all()

def delete_exam(db, exam_id):
    """Delete an exam by ID"""
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if exam:
            db.delete(exam)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e

# Initialize database with default user
init_db()
