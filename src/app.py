import streamlit as st
import pandas as pd
from datetime import datetime
import time
from pathlib import Path
import json
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import components
from patient_manager import PatientManager
from medical_recorder import MedicalRecorder
from medical_chat import MedicalChat
from exam_analyzer import ExamAnalyzer, process_exam
from database import (
    SessionLocal, 
    get_patient_consultations, 
    create_exam,
    get_patient_exams,
    verify_login,
    delete_exam
)

# Configure Streamlit page with medical theme
st.set_page_config(
    page_title="Anamnese.AI - Medical Solutions",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check if database is configured
if not SessionLocal:
    st.error("⚠️ Banco de dados não configurado")
    st.info("""
    Para usar este aplicativo, você precisa configurar a conexão com o banco de dados:
    1. Vá para Configurações do App no Streamlit Cloud
    2. Encontre a seção "Secrets"
    3. Adicione suas configurações:
    ```toml
    [database]
    DATABASE_URL = "sua-url-do-banco-de-dados"
    ```
    """)
    st.stop()

[Rest of your existing app.py code...]
