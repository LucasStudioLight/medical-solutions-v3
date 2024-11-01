import streamlit as st
import sys
import os

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

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set environment variable to indicate cloud deployment
os.environ['DEPLOYMENT_ENV'] = 'cloud'

# Import the main app
from src.app import main

if __name__ == '__main__':
    main()
