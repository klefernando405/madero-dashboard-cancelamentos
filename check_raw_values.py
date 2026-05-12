import pandas as pd
df = pd.read_csv(r"\\172.24.0.80\arquivos3\Export_Cancelamentos\Export_Cancelamentos_Cupons.csv", sep=';', encoding='utf-8-sig', dtype=str)
df_day = df[df['DATA_C'] == '11/05/2026']
print("Distinct VRTOTAL values in Source:")
print(df_day['VRTOTAL'].unique().tolist())
