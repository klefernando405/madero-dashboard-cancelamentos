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

def load_and_debug(tipo, date_str):
    print(f"--- Debugging {tipo} for {date_str} ---")
    nome_arquivo = 'cancelamentos_cupons.csv' if tipo == 'cupons' else 'cancelamentos_itens.csv'
    
    res = service.files().list(q=f"name='{nome_arquivo}' and trashed=false").execute()
    fid = res['files'][0]['id']
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, service.files().get_media(fileId=fid))
    done = False
    while not done: _, done = downloader.next_chunk()
    buffer.seek(0)
    
    df = pd.read_csv(buffer, sep=';', decimal=',', encoding='utf-8-sig', dtype=str, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    
    print(f"Rows in CSV: {len(df)}")
    
    # Check rows for the specific date BEFORE any processing
    df_day_raw = df[df['DATA_C'] == date_str]
    print(f"Rows for {date_str} in CSV: {len(df_day_raw)}")

    # Reproduce processing logic
    df['DATA_C_DT'] = pd.to_datetime(df['DATA_C'], format='%d/%m/%Y', errors='coerce')
    df['VRTOTAL_NUM'] = pd.to_numeric(df['VRTOTAL'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    
    # Check for NaT in DATA_C
    nat_rows = df[df['DATA_C_DT'].isna() & df['DATA_C'].notna()]
    if not nat_rows.empty:
        print(f"WARNING: {len(nat_rows)} rows have invalid date format!")
        print(f"Sample invalid dates: {nat_rows['DATA_C'].unique()[:5]}")
    
    # Filter by date as the dashboard does
    df_day = df[df['DATA_C_DT'] == pd.Timestamp(date_str)]
    print(f"Rows for {date_str} after processing: {len(df_day)}")
    print(f"Sum VRTOTAL for {date_str}: {df_day['VRTOTAL_NUM'].sum()}")
    
    # Save the processed day to Excel for user inspection
    output_name = f"debug_dashboard_{tipo}_{date_str.replace('/','-')}.xlsx"
    df_day.to_excel(output_name, index=False)
    print(f"Data for {date_str} saved to {output_name}")

load_and_debug('cupons', '11/05/2026')
load_and_debug('itens', '11/05/2026')
