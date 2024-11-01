import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MedicalSummarizer:
    def __init__(self):
        self.api_key = os.getenv('DEEPINFRA_API_KEY')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        self.url = 'https://api.deepinfra.com/v1/openai/chat/completions'

    def summarize(self, text):
        """Generate medical summary from consultation text using LLaMA"""
        try:
            prompt = f"""Analise a seguinte transcrição de consulta médica e forneça um resumo estruturado:

            TRANSCRIÇÃO:
            {text}

            Forneça um resumo estruturado com os seguintes campos:
            1. Queixa Principal
            2. História Atual
            3. Exame Físico (se mencionado)
            4. Diagnóstico
            5. Prescrições
            6. Observações (se houver)

            Mantenha a linguagem técnica e profissional."""

            data = {
                "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": "Você é um especialista em análise de consultas médicas."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            response = requests.post(self.url, headers=self.headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            summary_text = result['choices'][0]['message']['content']
            
            # Parse the summary text into structured format
            summary = self._parse_summary(summary_text)
            
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return {
                'queixa_principal': 'Não identificado',
                'historia_atual': 'Não identificado',
                'exame_fisico': '',
                'diagnostico': 'Não identificado',
                'prescricoes': 'Não identificado',
                'observacoes': ''
            }

    def _parse_summary(self, summary_text):
        """Parse the LLaMA response into structured format"""
        sections = {
            'queixa_principal': '',
            'historia_atual': '',
            'exame_fisico': '',
            'diagnostico': '',
            'prescricoes': '',
            'observacoes': ''
        }
        
        current_section = None
        lines = summary_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            lower_line = line.lower()
            
            # Check for section headers
            if 'queixa principal' in lower_line:
                current_section = 'queixa_principal'
                continue
            elif 'história atual' in lower_line or 'historia atual' in lower_line:
                current_section = 'historia_atual'
                continue
            elif 'exame físico' in lower_line or 'exame fisico' in lower_line:
                current_section = 'exame_fisico'
                continue
            elif 'diagnóstico' in lower_line or 'diagnostico' in lower_line:
                current_section = 'diagnostico'
                continue
            elif 'prescrições' in lower_line or 'prescricoes' in lower_line:
                current_section = 'prescricoes'
                continue
            elif 'observações' in lower_line or 'observacoes' in lower_line:
                current_section = 'observacoes'
                continue
            
            # Add content to current section
            if current_section and current_section in sections:
                if sections[current_section]:
                    sections[current_section] += ' '
                sections[current_section] += line
        
        # Set default values for empty sections
        for key in sections:
            if not sections[key]:
                sections[key] = 'Não identificado' if key != 'exame_fisico' and key != 'observacoes' else ''
        
        return sections
