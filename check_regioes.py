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

def check_regioes():
    res = service.files().list(q="name='regioes.xlsx' and trashed=false", fields='files(id)').execute()
    if not res.get('files'):
        print("regioes.xlsx not found")
        return
    fid = res['files'][0]['id']
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, service.files().get_media(fileId=fid))
    done = False
    while not done: _, done = downloader.next_chunk()
    buffer.seek(0)
    
    df_reg = pd.read_excel(buffer)
    # Process as in dashboard_app
    col_map = {}
    for col in df_reg.columns:
        c = str(col).upper()
        if 'COD' in c and 'FILIAL' in c and 'CDFILIAL_C' not in col_map: 
            col_map[col] = 'CDFILIAL_C'
    
    df_reg = df_reg.rename(columns=col_map)
    df_reg['CDFILIAL_C'] = df_reg['CDFILIAL_C'].astype(str).str.replace('.0','',regex=False).str.strip().str.lstrip('0')
    
    dupes = df_reg['CDFILIAL_C'].duplicated().sum()
    print(f"Duplicate Filiais in regioes.xlsx: {dupes}")
    if dupes > 0:
        print("\nExamples of duplicates in regioes.xlsx:")
        print(df_reg[df_reg['CDFILIAL_C'].duplicated(keep=False)].sort_values('CDFILIAL_C').head(10))

check_regioes()
