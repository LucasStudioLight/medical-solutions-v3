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

# Custom CSS for theme
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #00BFFF;
        --secondary-color: #0066CC;
        --background-color: #001F3F;
        --text-color: #FFFFFF;
    }
    
    /* Global styles */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--primary-color) !important;
    }
    
    /* Buttons */
    .stButton button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: var(--secondary-color);
    }
    
    /* Logout button */
    .logout-button {
        position: fixed;
        top: 14px;
        right: 14px;
        z-index: 999999;
    }
    
    .logout-button button {
        background-color: #ff4b4b;
        color: white;
    }
    
    /* Cards and containers */
    .patient-header {
        background-color: rgba(0, 191, 255, 0.1);
        border: 1px solid var(--primary-color);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: var(--text-color);
        border: 1px solid var(--primary-color);
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: var(--primary-color);
    }
    
    /* Footer */
    footer {
        visibility: hidden;
    }
    
    footer:after {
        content: 'Powered by TIWANG A.I.';
        visibility: visible;
        display: block;
        position: relative;
        padding: 5px;
        top: 2px;
        color: var(--primary-color);
    }
    
    /* Input fields */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.1);
        color: var(--text-color);
        border: 1px solid var(--primary-color);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: rgba(0, 191, 255, 0.1);
        border: 1px solid var(--primary-color);
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background-color: var(--primary-color);
    }
    
    /* Success/Info/Warning messages */
    .stSuccess, .stInfo {
        background-color: rgba(0, 191, 255, 0.1);
        border: 1px solid var(--primary-color);
        color: var(--text-color);
    }
    
    .stWarning {
        background-color: rgba(255, 191, 0, 0.1);
        border: 1px solid #FFB300;
        color: var(--text-color);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: var(--background-color);
    }
    
    /* Hexagonal elements */
    .hex-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 20px;
    }
    
    .hex-item {
        width: 100px;
        height: 115px;
        background-color: rgba(0, 191, 255, 0.1);
        clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--primary-color);
        transition: all 0.3s ease;
    }
    
    .hex-item:hover {
        background-color: var(--primary-color);
        transform: scale(1.1);
    }
</style>
""", unsafe_allow_html=True)

# Error message mapping
ERROR_MESSAGES = {
    "CPF deve conter 11 dígitos": "CPF Incompleto",
    "Paciente já cadastrado com este CPF": "CPF já cadastrado",
    "Data de nascimento inválida": "Data de nascimento inválida",
    "Telefone deve conter pelo menos 10 dígitos": "Telefone incompleto",
    "default": "Erro na gravação"
}

def logout():
    """Handle user logout"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def get_friendly_error_message(error_msg):
    """Convert technical error messages to user-friendly ones"""
    for key in ERROR_MESSAGES:
        if key in str(error_msg):
            return ERROR_MESSAGES[key]
    return ERROR_MESSAGES["default"]

def login():
    """Handle user login"""
    st.title('Medical Solutions')
    
    with st.form('login_form'):
        username = st.text_input('Usuário')
        password = st.text_input('Senha', type='password')
        submitted = st.form_submit_button('Entrar')
        
        if submitted:
            if verify_login(username, password):
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error('Usuário ou senha incorretos')

def return_to_home():
    """Clear current patient and return to search view"""
    st.session_state['view'] = 'search'
    st.session_state['search_cpf'] = ''
    st.session_state['search_name'] = ''
    st.rerun()

def show_registration_form(cpf, patient_manager):
    """Show the patient registration form"""
    st.warning('Paciente não encontrado. Preencha os dados para registro:')
    with st.form('patient_form'):
        nome = st.text_input('Nome completo:')
        data_nascimento = st.text_input('Data de nascimento (dd/mm/aaaa):')
        sexo = st.selectbox('Sexo:', ['masculino', 'feminino'])
        telefone = st.text_input('Telefone:')
        email = st.text_input('Email:')
        endereco = st.text_input('Endereço:')
        
        if st.form_submit_button('Registrar'):
            try:
                patient = patient_manager.register_patient({
                    'nome': nome,
                    'cpf': cpf,
                    'data_nascimento': data_nascimento,
                    'sexo': sexo,
                    'telefone': telefone,
                    'email': email,
                    'endereco': endereco
                })
                st.success('Paciente registrado com sucesso!')
                st.session_state['current_patient'] = patient
                st.session_state['view'] = 'patient_data'
                st.rerun()
            except ValueError as e:
                st.error(get_friendly_error_message(str(e)))

def show_patient_preview(patient, patient_manager):
    """Show patient preview with access button"""
    patient_info = patient_manager.format_patient_info(patient)
    st.success('Paciente encontrado!')
    st.write('**Dados do Paciente:**')
    st.write(f"ID: {patient_info['id']}")
    st.write(f"Nome: {patient_info['nome']}")
    st.write(f"CPF: {patient_info['cpf']}")
    st.write(f"Data de Nascimento: {patient_info['data_nascimento']}")
    st.write(f"Sexo: {patient_info['sexo']}")
    st.write(f"Telefone: {patient_info['telefone']}")
    st.write(f"Email: {patient_info['email']}")
    st.write(f"Endereço: {patient_info['endereco']}")
    
    if st.button('Acessar Dados do Paciente'):
        st.session_state['current_patient'] = patient
        st.session_state['view'] = 'patient_data'
        st.rerun()

def show_delete_confirmation():
    """Show delete confirmation dialog"""
    st.warning("Deseja realmente excluir esse documento?")
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Sim"):
            db = SessionLocal()
            if delete_exam(db, st.session_state['delete_confirmation']):
                st.success('Exame excluído com sucesso!')
                db.close()
                st.session_state['delete_confirmation'] = None
                st.rerun()
            else:
                st.error('Erro ao excluir exame')
                db.close()
    with col2:
        if st.button("Não"):
            st.session_state['delete_confirmation'] = None
            st.rerun()

def show_search_screen():
    """Show the patient search screen"""
    st.title('Medical Solutions')
    
    with st.container():
        st.markdown("""
        <div class="search-container">
            <h2>Pesquisar Paciente</h2>
            <p>Digite o CPF ou nome do paciente para acessar seus dados</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize components
        patient_manager = PatientManager()
        
        # Search tabs
        search_tab1, search_tab2 = st.tabs(['Buscar por CPF', 'Buscar por Nome'])
        
        with search_tab1:
            # CPF search
            cpf = st.text_input('CPF:', value=st.session_state['search_cpf'], help='Digite o CPF do paciente')
            
            if cpf:
                st.session_state['search_cpf'] = cpf
                try:
                    patient = patient_manager.get_patient_by_cpf(cpf)
                    if patient:
                        show_patient_preview(patient, patient_manager)
                    else:
                        show_registration_form(cpf, patient_manager)
                except ValueError as e:
                    st.error(get_friendly_error_message(str(e)))
        
        with search_tab2:
            # Name search
            nome = st.text_input('Nome:', value=st.session_state['search_name'], help='Digite o nome do paciente')
            
            if nome and len(nome) >= 3:
                st.session_state['search_name'] = nome
                patients = patient_manager.search_patients_by_name(nome)
                if patients:
                    st.success(f'Encontrado(s) {len(patients)} paciente(s)')
                    for patient in patients:
                        with st.expander(f"{patient.nome} (CPF: {patient.cpf})"):
                            show_patient_preview(patient, patient_manager)
                else:
                    st.warning('Nenhum paciente encontrado com este nome')
            elif nome:
                st.info('Digite pelo menos 3 caracteres para buscar')

def show_patient_data():
    """Show patient data and content"""
    st.title('Medical Solutions')
    
    # Initialize components
    patient_manager = PatientManager()
    medical_chat = MedicalChat()
    
    # Show current patient header with return button
    patient_info = patient_manager.format_patient_info(st.session_state['current_patient'])
    st.markdown(
        f"""
        <div class="patient-header">
            <h3>Área do Paciente</h3>
            <div class="patient-info">
                <div>
                    <p><strong>ID:</strong> {patient_info['id']}</p>
                    <p><strong>Nome:</strong> {patient_info['nome']}</p>
                    <p><strong>CPF:</strong> {patient_info['cpf']}</p>
                </div>
                <div>
                    <p><strong>Data de Nascimento:</strong> {patient_info['data_nascimento']}</p>
                    <p><strong>Sexo:</strong> {patient_info['sexo']}</p>
                    <p><strong>Telefone:</strong> {patient_info['telefone']}</p>
                </div>
                <div>
                    <p><strong>Email:</strong> {patient_info['email']}</p>
                    <p><strong>Endereço:</strong> {patient_info['endereco']}</p>
                </div>
            </div>
            <button class="home-button" onclick="parent.window.document.querySelector('button[kind=secondary]').click()">🏠 Voltar</button>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Add return to home button
    if st.button("🏠 Voltar para Pesquisa"):
        return_to_home()

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(['Nova Consulta', 'Histórico', 'Exames', 'Chat Médico'])
    
    # New Consultation Tab
    with tab1:
        st.header('Nova Consulta')
        
        if not st.session_state['recording']:
            if st.button('Iniciar Gravação'):
                st.session_state['recording'] = True
                st.session_state['recorder'] = MedicalRecorder(st.session_state['current_patient'].id)
                if not st.session_state['recorder'].start_recording():
                    st.session_state['recording'] = False
                    st.session_state['recorder'] = None
                st.rerun()
        else:
            st.warning('Gravação em andamento...')
            
            if st.button('Finalizar Gravação'):
                with st.spinner('Processando...'):
                    consultation_data = st.session_state['recorder'].save_consultation()
                    if consultation_data:
                        st.success('Consulta processada com sucesso!')
                        st.subheader('Resumo da Consulta:')
                        st.write(f"**Queixa Principal:** {consultation_data['queixa_principal']}")
                        st.write(f"**Diagnóstico:** {consultation_data['diagnostico']}")
                        st.write(f"**Prescrições:** {consultation_data['prescricoes']}")
                        st.session_state['recording'] = False
                        st.session_state['recorder'] = None
                        st.rerun()
    
    # History Tab
    with tab2:
        st.header('Histórico de Consultas')
        
        # Get patient's consultations
        db = SessionLocal()
        consultations = get_patient_consultations(db, st.session_state['current_patient'].id)
        
        if consultations:
            for i, consultation in enumerate(consultations):
                with st.expander(f"Consulta {consultation.data_consulta.strftime('%d/%m/%Y %H:%M')}"):
                    st.write(f"**Queixa Principal:** {consultation.queixa_principal}")
                    st.write(f"**História Atual:** {consultation.historia_atual}")
                    if consultation.exame_fisico:
                        st.write(f"**Exame Físico:** {consultation.exame_fisico}")
                    st.write(f"**Diagnóstico:** {consultation.diagnostico}")
                    st.write(f"**Prescrições:** {consultation.prescricoes}")
                    if consultation.observacoes:
                        st.write(f"**Observações:** {consultation.observacoes}")
                    
                    # Option to download full consultation data
                    consultation_data = {
                        'data_consulta': consultation.data_consulta.isoformat(),
                        'transcricao_completa': consultation.transcricao_completa,
                        'resumo_clinico': json.loads(consultation.resumo_clinico) if consultation.resumo_clinico else {},
                        'segmentos_detalhados': json.loads(consultation.segmentos_detalhados) if consultation.segmentos_detalhados else []
                    }
                    st.download_button(
                        'Baixar JSON completo',
                        data=json.dumps(consultation_data, ensure_ascii=False, indent=2),
                        file_name=f'consulta_{consultation.data_consulta.strftime("%Y%m%d_%H%M%S")}.json',
                        mime='application/json',
                        key=f'download_consultation_{i}'
                    )
        else:
            st.info('Nenhuma consulta encontrada para este paciente.')
        
        db.close()
    
    # Exams Tab
    with tab3:
        st.header('Exames')
        
        # Show delete confirmation if needed
        if st.session_state['delete_confirmation']:
            show_delete_confirmation()
        
        # Upload new exam
        uploaded_file = st.file_uploader("Carregar novo exame (PDF)", type=['pdf'])
        if uploaded_file:
            # Add date input for exam date
            exam_date = st.date_input(
                "Data do Exame",
                datetime.now(),
                help="Selecione a data em que o exame foi realizado",
                format="DD/MM/YYYY"  # Format date input in Brazilian format
            )
            
            if st.button('Processar Exame'):
                with st.spinner('Analisando exame...'):
                    # Convert date to datetime
                    exam_datetime = datetime.combine(exam_date, datetime.min.time())
                    analysis = process_exam(uploaded_file, st.session_state['current_patient'].id, exam_datetime)
                    if analysis:
                        st.success('Exame processado com sucesso!')
                        st.subheader('Análise do Exame:')
                        st.write(f"**Tipo de Exame:** {analysis['tipo_exame']}")
                        st.write(f"**Principais Resultados:** {analysis['resultados']}")
                        st.write(f"**Alterações Significativas:** {analysis['alteracoes']}")
                        st.write(f"**Interpretação Clínica:** {analysis['interpretacao']}")
                        st.write(f"**Recomendações:** {analysis['recomendacoes']}")
        
        # Show existing exams
        st.subheader('Exames Anteriores')
        db = SessionLocal()
        exams = get_patient_exams(db, st.session_state['current_patient'].id)
        
        if exams:
            for i, exam in enumerate(exams):
                # Format exam date in Brazilian format
                exam_date_str = exam.data_exame.strftime('%d/%m/%Y')
                with st.expander(f"Exame {exam_date_str} - {exam.tipo_exame}"):
                    analysis = json.loads(exam.analise) if exam.analise else {}
                    st.write(f"**Data do Exame:** {exam_date_str}")
                    st.write(f"**Principais Resultados:** {analysis.get('resultados', '')}")
                    st.write(f"**Alterações:** {analysis.get('alteracoes', '')}")
                    st.write(f"**Interpretação:** {analysis.get('interpretacao', '')}")
                    st.write(f"**Recomendações:** {analysis.get('recomendacoes', '')}")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # Option to download PDF with formatted date
                        if exam.arquivo_pdf:
                            filename = f"{exam.tipo_exame} - {exam_date_str}.pdf"
                            st.download_button(
                                'Baixar PDF original',
                                data=exam.arquivo_pdf,
                                file_name=filename,
                                mime='application/pdf',
                                key=f'download_exam_{i}'
                            )
                    with col2:
                        # Delete button
                        if st.button('🗑️ Excluir', key=f'delete_exam_{i}'):
                            st.session_state['delete_confirmation'] = exam.id
                            st.rerun()
        else:
            st.info('Nenhum exame encontrado para este paciente.')
        
        db.close()
    
    # Chat Tab
    with tab4:
        st.header('Chat Médico')
        st.write('Faça perguntas sobre o histórico do paciente:')
        
        # Chat interface
        query = st.text_input('Sua pergunta:')
        if st.button('Enviar'):
            if query:
                with st.spinner('Processando...'):
                    response = medical_chat.query_history(st.session_state['current_patient'].id, query)
                    st.session_state['chat_messages'].append(('user', query))
                    st.session_state['chat_messages'].append(('assistant', response))
        
        # Display chat history
        for role, message in st.session_state['chat_messages']:
            if role == 'user':
                st.write(f"👨‍⚕️ **Médico:** {message}")
            else:
                st.write(f"🤖 **Assistente:** {message}")

def main():
    # Add logout button if logged in
    if st.session_state['logged_in']:
        col1, col2 = st.columns([11, 1])
        with col2:
            if st.button('🚪 Sair', key='logout_button'):
                logout()
    
    if not st.session_state['logged_in']:
        login()
    else:
        if st.session_state['view'] == 'search':
            show_search_screen()
        elif st.session_state['current_patient']:
            show_patient_data()
        else:
            show_search_screen()

if __name__ == '__main__':
    main()
