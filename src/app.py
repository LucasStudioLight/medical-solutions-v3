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
try:
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
except ImportError:
    try:
        from src.patient_manager import PatientManager
        from src.medical_recorder import MedicalRecorder
        from src.medical_chat import MedicalChat
        from src.exam_analyzer import ExamAnalyzer, process_exam
        from src.database import (
            SessionLocal, 
            get_patient_consultations, 
            create_exam,
            get_patient_exams,
            verify_login,
            delete_exam
        )
    except ImportError as e:
        st.error(f"⚠️ Erro ao importar módulos: {str(e)}")
        st.stop()

[Rest of your existing app.py code...]
