import pandas as pd
import io
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive']
creds_path = r'c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\token_drive.json'

path_cupons_net = r"\\172.24.0.80\arquivos3\Export_Cancelamentos\Export_Cancelamentos_Cupons.csv"
path_regioes_net = r"M:\Departamentos\Operacoes Matriz\MATRICIAL\13- REGIÕES CONTATOS\Regiões - Oficial\Planilha Divisão Regiões.xlsx"

creds = Credentials.from_authorized_user_file(creds_path, SCOPES)
service = build('drive', 'v3', credentials=creds)

def export_divergence_base(date_str):
    print(f"--- Generating Divergence Base for {date_str} ---")
    
    # 1. Load Source
    df_net = pd.read_csv(path_cupons_net, sep=';', encoding='utf-8-sig', dtype=str)
    df_net.columns = [c.strip() for c in df_net.columns]
    df_net = df_net[df_net['DATA_C'] == date_str].copy()
    df_net = df_net.apply(lambda col: col.str.strip() if col.dtype == 'object' else col)
    
    # 2. Replicate Dashboard Logic
    # Load Regioes from network (since it's the source)
    df_reg = pd.read_excel(path_regioes_net)
    col_map = {}
    for col in df_reg.columns:
        c = str(col).upper()
        if 'COD' in c and 'FILIAL' in c and 'CDFILIAL_C' not in col_map: col_map[col] = 'CDFILIAL_C'
        elif 'DIRETOR' in c and 'DIRETOR' not in col_map.values(): col_map[col] = 'DIRETOR'
        elif 'GEOP' in c and 'GEOP' not in col_map.values(): col_map[col] = 'GEOP'
    
    df_reg = df_reg.rename(columns=col_map)[[v for v in col_map.values()]].drop_duplicates(subset=['CDFILIAL_C'])
    df_reg['CDFILIAL_C'] = df_reg['CDFILIAL_C'].astype(str).str.replace('.0','',regex=False).str.strip().str.lstrip('0')
    
    df_dash = df_net.copy()
    df_dash['CDFILIAL_C_PROC'] = df_dash['CDFILIAL_C'].astype(str).str.replace('.0','',regex=False).str.strip().str.lstrip('0')
    df_dash = df_dash.merge(df_reg, left_on='CDFILIAL_C_PROC', right_on='CDFILIAL_C', how='left', suffixes=('', '_REG'))
    
    # Numeric conversion
    df_dash['VRTOTAL_PROC'] = pd.to_numeric(df_dash['VRTOTAL'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    
    # Identify rows that would be lost if filtered by Director/GEOP (if they become NaN)
    df_dash['STATUS_MAPEAMENTO'] = df_dash['DIRETOR'].apply(lambda x: 'MAPEADO' if pd.notnull(x) else 'NÃO MAPEADO')
    
    # Save comparison base
    df_dash.to_excel('BASE_DIVERGENCIA_DASHBOARD.xlsx', index=False)
    print("Divergence base saved to BASE_DIVERGENCIA_DASHBOARD.xlsx")
    
    # Summary
    print(f"Total rows in Source: {len(df_net)}")
    print(f"Total rows Mapped: {len(df_dash[df_dash['STATUS_MAPEAMENTO'] == 'MAPEADO'])}")
    print(f"Total rows Unmapped: {len(df_dash[df_dash['STATUS_MAPEAMENTO'] == 'NÃO MAPEADO'])}")
    print(f"Sum of VRTOTAL: {df_dash['VRTOTAL_PROC'].sum()}")

export_divergence_base('11/05/2026')
