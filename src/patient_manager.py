import streamlit as st
from datetime import datetime
try:
    from database import SessionLocal, Patient, get_patient, create_patient, get_patients_by_name
except ImportError:
    try:
        from src.database import SessionLocal, Patient, get_patient, create_patient, get_patients_by_name
    except ImportError:
        st.error("⚠️ Erro ao importar módulos do banco de dados")

class PatientManager:
    def __init__(self):
        self.db = SessionLocal() if SessionLocal else None

    def get_patient_by_cpf(self, cpf):
        """Get patient by CPF"""
        if not self.db:
            return None
        return self.db.query(Patient).filter(Patient.cpf == cpf).first()

    def search_patients_by_name(self, name):
        """Search patients by name"""
        if not self.db:
            return []
        return self.db.query(Patient).filter(Patient.nome.ilike(f"%{name}%")).all()

    def register_patient(self, patient_data):
        """Register a new patient"""
        if not self.db:
            st.error("⚠️ Banco de dados não está configurado")
            return None
        
        try:
            patient = Patient(**patient_data)
            self.db.add(patient)
            self.db.commit()
            self.db.refresh(patient)
            return patient
        except Exception as e:
            self.db.rollback()
            raise ValueError(str(e))

    def format_patient_info(self, patient):
        """Format patient info for display"""
        if not patient:
            return {}
        
        return {
            'id': patient.id,
            'nome': patient.nome,
            'cpf': patient.cpf,
            'data_nascimento': patient.data_nascimento,
            'sexo': patient.sexo,
            'telefone': patient.telefone,
            'email': patient.email,
            'endereco': patient.endereco
        }
