from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, LargeBinary
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False)
    data_nascimento = Column(String(10), nullable=False)
    sexo = Column(String(10), nullable=False)
    telefone = Column(String(20), nullable=False)
    email = Column(String(100))
    endereco = Column(String(200))
    
    consultations = relationship("Consultation", back_populates="patient")
    exams = relationship("Exam", back_populates="patient")

class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    data_consulta = Column(DateTime, default=datetime.now)
    queixa_principal = Column(Text)
    historia_atual = Column(Text)
    exame_fisico = Column(Text)
    diagnostico = Column(Text)
    prescricoes = Column(Text)
    observacoes = Column(Text)
    transcricao_completa = Column(Text)
    resumo_clinico = Column(Text)
    segmentos_detalhados = Column(Text)
    
    patient = relationship("Patient", back_populates="consultations")

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    data_exame = Column(DateTime, default=datetime.now)
    tipo_exame = Column(String(100))
    arquivo_pdf = Column(LargeBinary)
    analise = Column(Text)
    
    patient = relationship("Patient", back_populates="exams")
