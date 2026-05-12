import pandas as pd
import io
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive']
creds_path = r'c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\token_drive.json'

creds = Credentials.from_authorized_user_file(creds_path, SCOPES)
service = build('drive', 'v3', credentials=creds)

def get_id(name):
    res = service.files().list(q=f"name='{name}' and trashed=false", fields='files(id)').execute()
    files = res.get('files', [])
    return files[0]['id'] if files else None

def check_drive():
    for name in ['cancelamentos_cupons.csv', 'cancelamentos_itens.csv']:
        fid = get_id(name)
        if not fid:
            print(f"{name} not found")
            continue
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, service.files().get_media(fileId=fid))
        done = False
        while not done: _, done = downloader.next_chunk()
        buffer.seek(0)
        df = pd.read_csv(buffer, sep=';', decimal=',', encoding='utf-8-sig', dtype=str)
        print(f"{name}: {len(df)} rows total. 10/05/2026: {len(df[df['DATA_C'] == '10/05/2026'])} rows.")

check_drive()
