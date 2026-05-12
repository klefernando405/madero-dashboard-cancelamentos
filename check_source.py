import pandas as pd
import os

path_cupons = r"\\172.24.0.80\arquivos3\Export_Cancelamentos\Export_Cancelamentos_Cupons.csv"
path_itens = r"\\172.24.0.80\arquivos3\Export_Cancelamentos\Export_Cancelamentos_Itens.csv"

def check_source(path, name):
    print(f"--- Checking Source {name} ---")
    if not os.path.exists(path):
        print(f"Path not found: {path}")
        return
    df = pd.read_csv(path, sep=';', encoding='utf-8-sig', dtype=str, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    print(f"Total rows: {len(df)}")
    if 'DATA_C' in df.columns:
        print(f"Count for 10/05/2026: {len(df[df['DATA_C'] == '10/05/2026'])}")

check_source(path_cupons, "Cupons")
check_source(path_itens, "Itens")
