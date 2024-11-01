# Medical Solutions - Sistema de Prontuário Eletrônico

Sistema de gravação, transcrição e gerenciamento de prontuários médicos.

## Estrutura do Projeto

```
V1/
├── src/                    # Código fonte
│   ├── medical_recorder.py # Sistema de gravação
│   ├── database.py        # Gerenciamento do banco de dados
│   ├── medical_summarizer.py # Geração de resumos médicos
│   └── patient_manager.py  # Gerenciamento de pacientes
├── data/                   # Dados do sistema
│   ├── database/          # Banco de dados SQLite
│   ├── recordings/        # Gravações temporárias
│   └── transcriptions/    # Transcrições JSON
├── .env                   # Variáveis de ambiente
└── requirements.txt       # Dependências do projeto
```

## Configuração

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente no arquivo `.env`:
```
OPENAI_API_KEY=sua_chave_api_aqui
```

## Uso

1. Execute o programa:
```bash
python src/medical_recorder.py
```

2. Digite o CPF do paciente
   - Se o paciente não estiver cadastrado, você será solicitado a registrá-lo

3. Inicie a gravação da consulta
   - Fale normalmente durante a consulta
   - Pressione Enter para finalizar a gravação

4. O sistema irá:
   - Transcrever o áudio automaticamente
   - Gerar um resumo profissional da consulta
   - Salvar no banco de dados
   - Criar um arquivo JSON com o registro completo

## Funcionalidades

- Cadastro e gerenciamento de pacientes
- Gravação e transcrição automática de consultas
- Geração de resumos médicos profissionais
- Banco de dados SQLite para armazenamento
- Histórico completo de consultas por paciente
- Exportação de prontuários em JSON

## Banco de Dados

O sistema utiliza SQLite para armazenar:
- Dados dos pacientes
- Histórico de consultas
- Transcrições completas
- Resumos médicos estruturados
