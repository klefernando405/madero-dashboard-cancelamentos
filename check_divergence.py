import pandas as pd
import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials

path_cupons_net = r"\\172.24.0.80\arquivos3\Export_Cancelamentos\Export_Cancelamentos_Cupons.csv"
creds_path = r'c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\token_drive.json'

def check_value_divergence(date_str):
    print(f"--- Checking Divergence for {date_str} ---")
    
    # 1. Source Network
    df_net = pd.read_csv(path_cupons_net, sep=';', decimal=',', encoding='utf-8-sig', dtype=str)
    df_net.columns = [c.strip() for c in df_net.columns]
    df_net_day = df_net[df_net['DATA_C'] == date_str].copy()
    df_net_day['VRTOTAL_NUM'] = pd.to_numeric(df_net_day['VRTOTAL'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce')
    
    print(f"Network Source - Rows: {len(df_net_day)}")
    print(f"Network Source - Sum VRTOTAL: {df_net_day['VRTOTAL_NUM'].sum()}")
    
    # 2. Google Drive
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = Credentials.from_authorized_user_file(creds_path, SCOPES)
    service = build('drive', 'v3', credentials=creds)
    
    res = service.files().list(q="name='cancelamentos_cupons.csv' and trashed=false").execute()
    fid = res['files'][0]['id']
    
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, service.files().get_media(fileId=fid))
    done = False
    while not done: _, done = downloader.next_chunk()
    buffer.seek(0)
    
    df_drive = pd.read_csv(buffer, sep=';', decimal=',', encoding='utf-8-sig', dtype=str)
    df_drive_day = df_drive[df_drive['DATA_C'] == date_str].copy()
    # Note: dashboard_app logic for numeric conversion
    df_drive_day['VRTOTAL_NUM'] = pd.to_numeric(df_drive_day['VRTOTAL'], errors='coerce').fillna(0)
    
    print(f"Drive Storage - Rows: {len(df_drive_day)}")
    print(f"Drive Storage - Sum VRTOTAL: {df_drive_day['VRTOTAL_NUM'].sum()}")
    
    # Check for duplicates in Drive for that day
    dupes = df_drive_day.duplicated().sum()
    print(f"Drive Storage - Duplicates for that day: {dupes}")

check_value_divergence('11/05/2026')
