import pandas as pd
import io
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive']
creds_path = r'c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\token_drive.json'

path_cupons_net = r"\\172.24.0.80\arquivos3\Export_Cancelamentos\Export_Cancelamentos_Cupons.csv"

creds = Credentials.from_authorized_user_file(creds_path, SCOPES)
service = build('drive', 'v3', credentials=creds)

def get_id(name):
    res = service.files().list(q=f"name='{name}' and trashed=false", fields='files(id)').execute()
    files = res.get('files', [])
    return files[0]['id'] if files else None

def compare_counts(date_str):
    print(f"--- Detailed Comparison for {date_str} ---")
    df_net = pd.read_csv(path_cupons_net, sep=';', encoding='utf-8-sig', dtype=str)
    df_net.columns = [c.strip() for c in df_net.columns]
    df_net = df_net[df_net['DATA_C'] == date_str].apply(lambda col: col.str.strip() if col.dtype == 'object' else col)
    
    fid = get_id('cancelamentos_cupons.csv')
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, service.files().get_media(fileId=fid))
    done = False
    while not done: _, done = downloader.next_chunk()
    buffer.seek(0)
    df_drive = pd.read_csv(buffer, sep=';', encoding='utf-8-sig', dtype=str)
    df_drive = df_drive[df_drive['DATA_C'] == date_str].apply(lambda col: col.str.strip() if col.dtype == 'object' else col)

    print(f"Total Rows Net: {len(df_net)}")
    print(f"Total Rows Drive: {len(df_drive)}")

    # Group by all columns and count occurrences
    net_counts = df_net.groupby(list(df_net.columns)).size().reset_index(name='count_net')
    drive_counts = df_drive.groupby(list(df_drive.columns)).size().reset_index(name='count_drive')
    
    merged = pd.merge(net_counts, drive_counts, on=list(df_net.columns), how='outer').fillna(0)
    diff = merged[merged['count_net'] != merged['count_drive']]
    
    print(f"Divergent groups: {len(diff)}")
    
    if not diff.empty:
        diff.to_excel('divergencia_detalhada.xlsx', index=False)
        print("Divergence saved to divergencia_detalhada.xlsx")
    else:
        print("No divergences found (counts match for all unique rows).")

compare_counts('11/05/2026')
