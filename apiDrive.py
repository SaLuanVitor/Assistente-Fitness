from googleapiclient.discovery import build # type: ignore
from googleapiclient.http import MediaFileUpload # type: ignore
from google.auth.transport.requests import Request # type: ignore
from google.oauth2.credentials import Credentials # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
import os
import json

SCOPES = ['https://www.googleapis.com/auth/drive']

def load_config(file_path):
    """
    Carrega as configurações do arquivo JSON.
    """
    with open(file_path, 'r') as file:
        return json.load(file)

def authenticate_google_drive(config):
    """
    Autentica com o Google Drive usando OAuth2 e retorna as credenciais.
    """
    creds = None
    TOKEN_FILE = 'token.json'

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config({
                "installed": {
                    "client_id": config['client_id'],
                    "client_secret": config['client_secret'],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": config['redirect_uris']
                }
            }, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token_file:
                token_file.write(creds.to_json())

    return creds

def upload_file_to_drive(config, file_name):
    """
    Atualiza ou envia um novo arquivo para o Google Drive.
    """
    creds = authenticate_google_drive(config)
    service = build('drive', 'v3', credentials=creds)
    folder_id = config['folder_id']
    file_path = os.path.join(config['file_path'], file_name)

    # Verificar se o arquivo já existe no Google Drive
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    media = MediaFileUpload(file_path, resumable=True)

    if items:
        # Atualizar arquivo existente
        file_id = items[0]['id']
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        print(f"Arquivo atualizado no Google Drive. ID: {updated_file.get('id')}")
    else:
        # Fazer upload de novo arquivo
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f"Novo arquivo enviado para o Google Drive. ID: {uploaded_file.get('id')}")
