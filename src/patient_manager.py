from datetime import datetime
from typing import Optional, Dict, List
from database import SessionLocal, Patient, get_patient, create_patient, get_patients_by_name

class PatientManager:
    def __init__(self):
        self.db = SessionLocal()

    def register_patient(self, patient_data: Dict) -> Patient:
        """Register a new patient"""
        try:
            # Format and validate date string
            if 'data_nascimento' in patient_data and isinstance(patient_data['data_nascimento'], str):
                try:
                    # Remove any extra spaces
                    date_str = patient_data['data_nascimento'].strip()
                    
                    # Try different date formats
                    try:
                        # Try dd/mm/yyyy format
                        patient_data['data_nascimento'] = datetime.strptime(date_str, '%d/%m/%Y')
                    except ValueError:
                        try:
                            # Try ddmmyyyy format
                            if len(date_str) == 8 and date_str.isdigit():
                                patient_data['data_nascimento'] = datetime.strptime(date_str, '%d%m%Y')
                            else:
                                raise ValueError()
                        except ValueError:
                            raise ValueError(
                                "Data de nascimento inválida. Use o formato dd/mm/aaaa (exemplo: 06/01/1986) "
                                "ou ddmmaaaa (exemplo: 06011986)"
                            )
                except ValueError as e:
                    raise ValueError(str(e))

            # Validate CPF
            if 'cpf' in patient_data:
                # Remove any non-digit characters
                patient_data['cpf'] = ''.join(filter(str.isdigit, patient_data['cpf']))
                if len(patient_data['cpf']) != 11:
                    raise ValueError("CPF deve conter 11 dígitos")

            # Clean up email
            if 'email' in patient_data:
                patient_data['email'] = patient_data['email'].strip().lower()

            # Clean up phone
            if 'telefone' in patient_data:
                # Remove any non-digit characters
                patient_data['telefone'] = ''.join(filter(str.isdigit, patient_data['telefone']))
                if len(patient_data['telefone']) < 10:
                    raise ValueError("Telefone deve conter pelo menos 10 dígitos (DDD + número)")

            # Validate sexo
            if 'sexo' not in patient_data:
                raise ValueError("Sexo é obrigatório")
            
            # Capitalize first letter of sexo
            patient_data['sexo'] = patient_data['sexo'].capitalize()
            if patient_data['sexo'] not in ['Masculino', 'Feminino']:
                raise ValueError("Sexo deve ser 'masculino' ou 'feminino'")

            # Check if patient already exists
            existing_patient = get_patient(self.db, patient_data.get('cpf'))
            if existing_patient:
                raise ValueError("Paciente já cadastrado com este CPF")

            # Create new patient
            return create_patient(self.db, patient_data)
        except Exception as e:
            raise ValueError(str(e))

    def get_patient_by_cpf(self, cpf: str) -> Optional[Patient]:
        """Get patient by CPF"""
        try:
            # Clean CPF input
            cpf = ''.join(filter(str.isdigit, cpf))
            if len(cpf) != 11:
                raise ValueError("CPF deve conter 11 dígitos")
            return get_patient(self.db, cpf)
        except Exception as e:
            raise ValueError(str(e))

    def search_patients_by_name(self, nome: str) -> List[Patient]:
        """Search patients by name"""
        try:
            return get_patients_by_name(self.db, nome)
        except Exception as e:
            print(f"Error searching patients by name: {str(e)}")
            return []

    def format_patient_info(self, patient: Patient) -> Dict:
        """Format patient information for display"""
        try:
            return {
                "id": patient.id,
                "nome": patient.nome,
                "data_nascimento": patient.data_nascimento.strftime('%d/%m/%Y') if patient.data_nascimento else None,
                "cpf": f"{patient.cpf[:3]}.{patient.cpf[3:6]}.{patient.cpf[6:9]}-{patient.cpf[9:]}" if patient.cpf else None,
                "telefone": self._format_phone(patient.telefone) if patient.telefone else None,
                "email": patient.email,
                "endereco": patient.endereco,
                "sexo": patient.sexo
            }
        except Exception as e:
            print(f"Error formatting patient info: {str(e)}")
            return {}

    def _format_phone(self, phone: str) -> str:
        """Format phone number for display"""
        if not phone:
            return ""
        
        try:
            # Remove any non-digit characters
            phone = ''.join(filter(str.isdigit, phone))
            
            if len(phone) == 11:  # Mobile with DDD
                return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
            elif len(phone) == 10:  # Landline with DDD
                return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
            else:
                return phone
        except Exception:
            return phone

    def __del__(self):
        """Close database session"""
        try:
            self.db.close()
        except:
            pass
