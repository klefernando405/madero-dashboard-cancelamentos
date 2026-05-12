import pandas as pd
import os

path_itens_net = r"\\172.24.0.80\arquivos3\Export_Cancelamentos\Export_Cancelamentos_Itens.csv"
path_regioes_net = r"M:\Departamentos\Operacoes Matriz\MATRICIAL\13- REGIÕES CONTATOS\Regiões - Oficial\Planilha Divisão Regiões.xlsx"

def export_itens_divergence(date_str):
    df_net = pd.read_csv(path_itens_net, sep=';', encoding='utf-8-sig', dtype=str)
    df_net.columns = [c.strip() for c in df_net.columns]
    df_net = df_net[df_net['DATA_C'] == date_str].copy()
    
    # Process numeric
    df_net['VRTOTAL_PROC'] = pd.to_numeric(df_net['VRTOTAL'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    
    # Save
    df_net.to_excel('BASE_DIVERGENCIA_ITENS.xlsx', index=False)
    print(f"Itens divergence base saved. Rows: {len(df_net)}, Sum: {df_net['VRTOTAL_PROC'].sum()}")

export_itens_divergence('11/05/2026')
