import pandas as pd
import io
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive']
creds_path = r'c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\token_drive.json'

path_cupons_net = r"\\172.24.0.80\arquivos3\Export_Cancelamentos\Export_Cancelamentos_Cupons.csv"
path_itens_net = r"\\172.24.0.80\arquivos3\Export_Cancelamentos\Export_Cancelamentos_Itens.csv"

creds = Credentials.from_authorized_user_file(creds_path, SCOPES)
service = build('drive', 'v3', credentials=creds)

def get_id(name):
    res = service.files().list(q=f"name='{name}' and trashed=false", fields='files(id)').execute()
    files = res.get('files', [])
    return files[0]['id'] if files else None

def compare_and_save_missing(name_net, name_drive, output_name):
    print(f"--- Comparing {name_net} ---")
    df_net = pd.read_csv(name_net, sep=';', encoding='utf-8-sig', dtype=str)
    df_net.columns = [c.strip() for c in df_net.columns]
    df_net = df_net.apply(lambda col: col.str.strip() if col.dtype == 'object' else col)
    
    fid = get_id(name_drive)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, service.files().get_media(fileId=fid))
    done = False
    while not done: _, done = downloader.next_chunk()
    buffer.seek(0)
    df_drive = pd.read_csv(buffer, sep=';', encoding='utf-8-sig', dtype=str)
    df_drive = df_drive.apply(lambda col: col.str.strip() if col.dtype == 'object' else col)

    # Convert to set of tuples for comparison (excluding the index)
    # We use all columns to identify a row
    net_tuples = set(map(tuple, df_net.values))
    drive_tuples = set(map(tuple, df_drive.values))
    
    missing_tuples = net_tuples - drive_tuples
    print(f"Rows in Net: {len(df_net)}")
    print(f"Rows in Drive: {len(df_drive)}")
    print(f"Rows in Net but not in Drive: {len(missing_tuples)}")
    
    if missing_tuples:
        df_missing = pd.DataFrame(list(missing_tuples), columns=df_net.columns)
        df_missing.to_excel(output_name, index=False)
        print(f"Missing rows saved to {output_name}")
    else:
        print("No missing rows found between Source and Drive.")

compare_and_save_missing(path_cupons_net, 'cancelamentos_cupons.csv', 'cupons_faltantes.xlsx')
compare_and_save_missing(path_itens_net, 'cancelamentos_itens.csv', 'itens_faltantes.xlsx')
