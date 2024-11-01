import os
import requests
import json
from typing import Dict, List
from database import SessionLocal, Patient, Consultation, Exam
from sqlalchemy import desc
from datetime import datetime

class MedicalChat:
    def __init__(self):
        self.api_key = os.getenv('DEEPINFRA_API_KEY')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.db = SessionLocal()

    def get_exam_details(self, patient_id: int, exam_type: str = None) -> str:
        """Get specific exam details"""
        try:
            query = self.db.query(Exam).filter(Exam.patient_id == patient_id)
            if exam_type:
                query = query.filter(Exam.tipo_exame.ilike(f"%{exam_type}%"))
            exams = query.order_by(desc(Exam.data_exame)).all()

            if not exams:
                return "Nenhum exame encontrado com os critérios especificados."

            details = "DETALHES DOS EXAMES:\n\n"
            for exam in exams:
                details += f"Data: {exam.data_exame.strftime('%d/%m/%Y')}\n"
                details += f"Tipo: {exam.tipo_exame}\n"
                
                if exam.analise:
                    analysis = json.loads(exam.analise)
                    details += f"Resultados: {analysis.get('resultados', 'Não disponível')}\n"
                    details += f"Alterações: {analysis.get('alteracoes', 'Não disponível')}\n"
                    details += f"Interpretação: {analysis.get('interpretacao', 'Não disponível')}\n"
                details += "\n---\n\n"

            return details
        except Exception as e:
            print(f"Erro ao buscar detalhes dos exames: {e}")
            return "Erro ao buscar detalhes dos exames."

    def get_patient_history(self, patient_id: int) -> str:
        """Get patient's medical history as context"""
        try:
            patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return "Paciente não encontrado."

            # Get consultations
            consultations = self.db.query(Consultation)\
                .filter(Consultation.patient_id == patient_id)\
                .order_by(desc(Consultation.data_consulta))\
                .all()

            # Get exams
            exams = self.db.query(Exam)\
                .filter(Exam.patient_id == patient_id)\
                .order_by(desc(Exam.data_exame))\
                .all()

            context = f"DADOS DO PACIENTE:\n"
            context += f"Nome: {patient.nome}\n"
            context += f"Data de Nascimento: {patient.data_nascimento.strftime('%d/%m/%Y')}\n\n"
            
            # Add consultation history
            context += "HISTÓRICO DE CONSULTAS:\n"
            for consultation in consultations:
                context += f"\nConsulta em {consultation.data_consulta.strftime('%d/%m/%Y')}:\n"
                context += f"- Queixa Principal: {consultation.queixa_principal}\n"
                if consultation.diagnostico:
                    context += f"- Diagnóstico: {consultation.diagnostico}\n"
                if consultation.prescricoes:
                    context += f"- Prescrições: {consultation.prescricoes}\n"

            # Add exam history
            context += "\nHISTÓRICO DE EXAMES:\n"
            for exam in exams:
                context += f"\nExame em {exam.data_exame.strftime('%d/%m/%Y')}:\n"
                context += f"- Tipo: {exam.tipo_exame}\n"
                if exam.analise:
                    analysis = json.loads(exam.analise)
                    if analysis.get('resultados'):
                        context += f"- Resultados: {analysis['resultados']}\n"
                    if analysis.get('alteracoes'):
                        context += f"- Alterações: {analysis['alteracoes']}\n"

            return context
        except Exception as e:
            print(f"Erro ao buscar histórico: {e}")
            return "Erro ao buscar histórico do paciente."

    def query_history(self, patient_id: int, query: str) -> str:
        """Query patient's medical history"""
        try:
            # Check if query is about exams
            exam_keywords = ['exame', 'exames', 'sangue', 'laboratorial', 'resultado']
            is_exam_query = any(keyword in query.lower() for keyword in exam_keywords)

            # Get specific exam details if it's an exam query
            if is_exam_query:
                exam_types = ['sangue', 'urina', 'imagem']
                specific_type = next((type for type in exam_types if type in query.lower()), None)
                exam_details = self.get_exam_details(patient_id, specific_type)
                
                if "Nenhum exame encontrado" not in exam_details:
                    history = exam_details
                else:
                    history = self.get_patient_history(patient_id)
            else:
                history = self.get_patient_history(patient_id)
            
            prompt = f"""Como um assistente médico especializado, analise o histórico médico abaixo e responda à pergunta do médico.
            Forneça informações específicas e detalhadas, incluindo datas e valores quando disponíveis.
            Se a informação solicitada não estiver disponível, indique claramente e sugira próximos passos.
            
            HISTÓRICO MÉDICO:
            {history}

            PERGUNTA DO MÉDICO:
            {query}

            Por favor, forneça uma resposta profissional e detalhada, citando datas específicas quando relevante."""

            data = {
                "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": "Você é um assistente médico especializado em análise de prontuários e exames."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            response = requests.post(
                'https://api.deepinfra.com/v1/openai/chat/completions',
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            
            return response.json()['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"Erro na consulta: {e}")
            if hasattr(e, 'response'):
                print(f"Resposta da API: {e.response.text}")
            return "Desculpe, não foi possível processar sua consulta."

    def __del__(self):
        """Cleanup database session"""
        self.db.close()
