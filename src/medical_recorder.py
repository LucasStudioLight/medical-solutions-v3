import sounddevice as sd
import numpy as np
import wave
import time
from datetime import datetime
import json
import requests
import os
from database import SessionLocal, create_consultation
from medical_summarizer import MedicalSummarizer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MedicalRecorder:
    def __init__(self, patient_id):
        self.patient_id = patient_id
        self.recording = False
        self.audio_data = []
        self.sample_rate = 44100
        self.channels = 1
        self.api_key = os.getenv('DEEPINFRA_API_KEY')
        self.summarizer = MedicalSummarizer()

    def audio_callback(self, indata, frames, time, status):
        """Callback function to process audio data"""
        if status:
            print(status)
        self.audio_data.append(indata.copy())

    def start_recording(self):
        """Start recording audio"""
        self.recording = True
        self.audio_data = []
        
        try:
            self.stream = sd.InputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=self.audio_callback
            )
            self.stream.start()
        except Exception as e:
            print(f"Error starting recording: {str(e)}")
            self.recording = False
            raise e

    def stop_recording(self):
        """Stop recording audio"""
        if not hasattr(self, 'stream') or not self.recording:
            return None
            
        try:
            self.stream.stop()
            self.stream.close()
            self.recording = False
            
            if not self.audio_data:
                return None
            
            # Combine all audio chunks
            audio_array = np.concatenate(self.audio_data)
            
            # Convert to int16
            audio_array = (audio_array * 32767).astype(np.int16)
            
            # Save to WAV file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consultation_{timestamp}.wav"
            
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 2 bytes per sample
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_array.tobytes())
            
            return filename
            
        except Exception as e:
            print(f"Error stopping recording: {str(e)}")
            return None

    def transcribe_audio(self, filename):
        """Transcribe audio file using DeepInfra Whisper API"""
        try:
            url = 'https://api.deepinfra.com/v1/inference/openai/whisper-large-v3'
            headers = {
                'Authorization': f'bearer {self.api_key}'
            }
            
            with open(filename, 'rb') as f:
                files = {'audio': f}
                response = requests.post(url, headers=headers, files=files)
                response.raise_for_status()
                
                result = response.json()
                
                # Combine all segments into full text
                full_text = ""
                segments = result.get('segments', [])
                for segment in sorted(segments, key=lambda x: x.get('start', 0)):
                    full_text += segment.get('text', '') + " "
                
                return full_text.strip(), segments
                
        except Exception as e:
            print(f"Error transcribing audio: {str(e)}")
            return "Erro na transcrição do áudio", []

    def save_consultation(self):
        """Save consultation data to database"""
        try:
            # Save audio file
            filename = self.stop_recording()
            if not filename:
                return None
            
            # Transcribe audio
            transcription, segments = self.transcribe_audio(filename)
            
            # Generate summary using medical summarizer
            summary = self.summarizer.summarize(transcription)
            
            # Create consultation data
            consultation_data = {
                'patient_id': self.patient_id,
                'data_consulta': datetime.now(),
                'transcricao_completa': transcription,
                'resumo_clinico': json.dumps(summary),
                'segmentos_detalhados': json.dumps(segments),
                'duracao_segundos': len(self.audio_data) // self.sample_rate,
                'quantidade_segmentos': len(segments),
                'queixa_principal': summary.get('queixa_principal', 'Não identificado'),
                'historia_atual': summary.get('historia_atual', 'Não identificado'),
                'exame_fisico': summary.get('exame_fisico', ''),
                'diagnostico': summary.get('diagnostico', 'Não identificado'),
                'prescricoes': summary.get('prescricoes', 'Não identificado'),
                'observacoes': summary.get('observacoes', '')
            }
            
            # Save to database
            db = SessionLocal()
            consultation = create_consultation(db, consultation_data)
            db.close()
            
            # Clean up audio file
            try:
                os.remove(filename)
            except:
                pass
            
            return {
                'queixa_principal': consultation_data['queixa_principal'],
                'diagnostico': consultation_data['diagnostico'],
                'prescricoes': consultation_data['prescricoes']
            }
            
        except Exception as e:
            print(f"Error saving consultation: {str(e)}")
            raise e
