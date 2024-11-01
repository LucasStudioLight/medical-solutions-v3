import PyPDF2
import json
import requests
import re
from datetime import datetime
from database import create_exam, SessionLocal
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class ExamAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('DEEPINFRA_API_KEY')
        
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return ""

    def extract_date_from_text(self, text):
        """Extract date from exam text"""
        try:
            # Common date patterns in Brazilian format
            date_patterns = [
                r'Data\s*(?:do\s*(?:exame|resultado))?\s*:\s*(\d{2}\/\d{2}\/\d{4})',
                r'Realizado\s*em\s*:\s*(\d{2}\/\d{2}\/\d{4})',
                r'Data\s*:\s*(\d{2}\/\d{2}\/\d{4})',
                r'(\d{2}\/\d{2}\/\d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    date_str = match.group(1)
                    return datetime.strptime(date_str, '%d/%m/%Y')
            
            return datetime.now()  # Default to current date if no date found
            
        except Exception as e:
            print(f"Error extracting date: {str(e)}")
            return datetime.now()

    def extract_exam_type(self, text):
        """Extract exam type from text"""
        try:
            # Common exam type patterns
            type_patterns = [
                r'(?:EXAME|Exame)\s*(?:DE|de)?\s*([A-Za-zÀ-ÿ\s]{3,50}?)(?:\s*:|\s*\n|$)',
                r'(?:RESULTADO|Resultado)\s*(?:DE|de)?\s*([A-Za-zÀ-ÿ\s]{3,50}?)(?:\s*:|\s*\n|$)',
                r'(?:LAUDO|Laudo)\s*(?:DE|de)?\s*([A-Za-zÀ-ÿ\s]{3,50}?)(?:\s*:|\s*\n|$)'
            ]
            
            for pattern in type_patterns:
                match = re.search(pattern, text)
                if match:
                    exam_type = match.group(1).strip()
                    return exam_type
            
            return "Exame Médico"  # Default type if no type found
            
        except Exception as e:
            print(f"Error extracting exam type: {str(e)}")
            return "Exame Médico"

    def analyze_exam(self, text):
        """Analyze exam text using LLaMA API"""
        try:
            url = 'https://api.deepinfra.com/v1/openai/chat/completions'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            prompt = f"""Analise o seguinte texto de exame médico e forneça um resumo estruturado:

            TEXTO DO EXAME:
            {text}

            Forneça uma análise com os seguintes campos:
            1. Tipo de Exame
            2. Principais Resultados
            3. Alterações Significativas
            4. Interpretação Clínica
            5. Recomendações

            Mantenha a linguagem técnica e profissional."""

            data = {
                "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": "Você é um especialista em análise de exames médicos."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            analysis_text = result['choices'][0]['message']['content']
            
            # Parse the analysis text into structured format
            analysis = self._parse_analysis(analysis_text)
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing exam: {str(e)}")
            return {
                'tipo_exame': 'Não identificado',
                'resultados': 'Erro na análise',
                'alteracoes': 'Erro na análise',
                'interpretacao': 'Erro na análise',
                'recomendacoes': 'Erro na análise'
            }

    def _parse_analysis(self, analysis_text):
        """Parse the analysis text into structured format"""
        sections = {
            'tipo_exame': '',
            'resultados': '',
            'alteracoes': '',
            'interpretacao': '',
            'recomendacoes': ''
        }
        
        current_section = None
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            lower_line = line.lower()
            
            # Check for section headers
            if 'tipo de exame' in lower_line:
                current_section = 'tipo_exame'
                continue
            elif 'principais resultados' in lower_line:
                current_section = 'resultados'
                continue
            elif 'alterações' in lower_line:
                current_section = 'alteracoes'
                continue
            elif 'interpretação' in lower_line:
                current_section = 'interpretacao'
                continue
            elif 'recomendações' in lower_line:
                current_section = 'recomendacoes'
                continue
            
            # Add content to current section
            if current_section and current_section in sections:
                if sections[current_section]:
                    sections[current_section] += ' '
                sections[current_section] += line
        
        # Set default values for empty sections
        for key in sections:
            if not sections[key]:
                sections[key] = 'Não identificado'
        
        return sections

def process_exam(pdf_file, patient_id, exam_date=None):
    """Process exam PDF file and save to database"""
    try:
        # Initialize analyzer
        analyzer = ExamAnalyzer()
        
        # Read PDF content
        pdf_content = pdf_file.read()
        
        # Extract text from PDF
        pdf_file.seek(0)  # Reset file pointer
        text = analyzer.extract_text_from_pdf(pdf_file)
        
        # Extract exam type and date from text
        extracted_type = analyzer.extract_exam_type(text)
        extracted_date = analyzer.extract_date_from_text(text)
        
        # Use extracted date if no date provided
        if exam_date is None:
            exam_date = extracted_date
        
        # Analyze exam text
        analysis = analyzer.analyze_exam(text)
        
        # Update exam type if not found in analysis
        if analysis['tipo_exame'] == 'Não identificado':
            analysis['tipo_exame'] = extracted_type
        
        # Create exam data
        exam_data = {
            'patient_id': patient_id,
            'data_exame': exam_date,
            'tipo_exame': analysis['tipo_exame'],
            'arquivo_pdf': pdf_content,
            'texto_exame': text,
            'analise': json.dumps(analysis)
        }
        
        # Save to database
        db = SessionLocal()
        exam = create_exam(db, exam_data)
        db.close()
        
        return analysis
        
    except Exception as e:
        print(f"Error processing exam: {str(e)}")
        return None
