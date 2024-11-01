import streamlit as st
import pandas as pd
from datetime import datetime
import time
from pathlib import Path
import json
import io
import os
from dotenv import load_dotenv

# Initialize session state variables first
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'recording' not in st.session_state:
    st.session_state['recording'] = False
if 'recorder' not in st.session_state:
    st.session_state['recorder'] = None
if 'current_patient' not in st.session_state:
    st.session_state['current_patient'] = None
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []
if 'delete_confirmation' not in st.session_state:
    st.session_state['delete_confirmation'] = None
if 'view' not in st.session_state:
    st.session_state['view'] = 'search'
if 'search_cpf' not in st.session_state:
    st.session_state['search_cpf'] = ''
if 'search_name' not in st.session_state:
    st.session_state['search_name'] = ''

# Load environment variables
load_dotenv()

# Import components after session state initialization
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

# Rest of your existing code...
[Previous content of app.py from "# Custom CSS for theme" onwards]
