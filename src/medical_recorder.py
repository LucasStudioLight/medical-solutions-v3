import os
import json
import time
from datetime import datetime
from pathlib import Path

class MedicalRecorder:
    def __init__(self, patient_id):
        self.patient_id = patient_id
        self.is_cloud = os.getenv('DEPLOYMENT_ENV') == 'cloud'
        
    def start_recording(self):
        if self.is_cloud:
            st.warning("Gravação de áudio não está disponível na versão cloud. Por favor, use a versão local para esta funcionalidade.")
            return False
        return True
        
    def save_consultation(self):
        if self.is_cloud:
            st.error("Funcionalidade não disponível na versão cloud")
            return None
            
        # Rest of the code would go here for local version
        return None
