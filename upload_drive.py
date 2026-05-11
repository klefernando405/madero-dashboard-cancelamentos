"""
MADERO | Upload Diário para Google Drive (OAuth2)
==================================================
Usa suas próprias credenciais Google (OAuth2) para fazer upload.
Na primeira execução abre o navegador para autorização.
Nas execuções seguintes usa o token salvo automaticamente.

Pré-requisito:
  - Arquivo 'oauth_credentials.json' na mesma pasta (baixado do Google Cloud Console)
  - Na primeira execução: autorizar no navegador que abrir
"""

import os
import io
import logging
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# =====================================================================
# CONFIGURAÇÕES
# =====================================================================
BASE_DIR = r"c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos"

CONFIGURACOES = {
    # Credenciais OAuth2
    "OAUTH_FILE": os.path.join(BASE_DIR, "oauth_credentials.json"),
    "TOKEN_FILE": os.path.join(BASE_DIR, "token_drive.json"),

    # ID da pasta no Google Drive
    "PASTA_DRIVE_ID": "1uex_JDIcqc1W_fT0u12T_NRSMdaRBFhJ",

    # ---------------------------------------------------------------
    # ARQUIVOS CSV — cancelamentos diários acumulados
    # Para adicionar um novo: inclua mais um dicionário na lista!
    # ---------------------------------------------------------------
    "ARQUIVOS_CSV": [
        {
            "origem": r"\\172.24.0.80\arquivos3\Export_Cancelamentos\Export_Cancelamentos_Cupons.csv",
            "nome_drive": "cancelamentos_cupons.csv",
        },
        {
            "origem": r"\\172.24.0.80\arquivos3\Export_Cancelamentos\Export_Cancelamentos_Itens.csv",
            "nome_drive": "cancelamentos_itens.csv",
        },
        # ------ ADICIONE NOVOS ARQUIVOS CSV AQUI ------
        # {
        #     "origem": r"\\servidor\pasta\NovoArquivo.csv",
        #     "nome_drive": "novo_arquivo.csv",
        # },
    ],

    # ---------------------------------------------------------------
    # ARQUIVOS EXCEL — planilhas atualizadas periodicamente
    # Para adicionar uma nova planilha: inclua mais um dicionário!
    # ---------------------------------------------------------------
    "ARQUIVOS_EXCEL": [
        {
            "origem": r"M:\Departamentos\Operacoes Matriz\MATRICIAL\13- REGIÕES CONTATOS\Regiões - Oficial\Planilha Divisão Regiões.xlsx",
            "nome_drive": "regioes.xlsx",
        },
        # ------ ADICIONE NOVAS PLANILHAS EXCEL AQUI ------
        # {
        #     "origem": r"M:\Caminho\NovaPlanilha.xlsx",
        #     "nome_drive": "nova_planilha.xlsx",
        # },
    ],
}

SCOPES = ["https://www.googleapis.com/auth/drive"]

# Log
LOG_PATH = os.path.join(BASE_DIR, "upload_drive.log")
logging.basicConfig(
    filename=LOG_PATH, level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger()


def conectar_drive():
    """Autentica via OAuth2 e retorna o serviço do Google Drive."""
    creds = None
    token_file  = CONFIGURACOES["TOKEN_FILE"]
    oauth_file  = CONFIGURACOES["OAUTH_FILE"]

    # Carrega token salvo se existir
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # Se não há token válido, faz autenticação
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            log.info("Token renovado automaticamente.")
        else:
            if not os.path.exists(oauth_file):
                raise FileNotFoundError(
                    f"Arquivo oauth_credentials.json não encontrado em:\n{oauth_file}\n"
                    "Baixe em: console.cloud.google.com → APIs e serviços → Credenciais → OAuth 2.0"
                )
            flow = InstalledAppFlow.from_client_secrets_file(oauth_file, SCOPES)
            creds = flow.run_local_server(port=0)
            log.info("Autenticação OAuth2 concluída e token salvo.")

        # Salva token para próximas execuções
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def buscar_arquivo_drive(service, nome, pasta_id):
    """Retorna o ID de um arquivo existente na pasta, ou None."""
    resultado = service.files().list(
        q=f"name='{nome}' and '{pasta_id}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
    arquivos = resultado.get("files", [])
    return arquivos[0]["id"] if arquivos else None


def upload_csv(service, df, nome_arquivo, pasta_id):
    """Faz upload de um DataFrame como CSV para o Google Drive."""
    conteudo = df.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")
    buffer = io.BytesIO(conteudo.encode("utf-8-sig"))
    media = MediaIoBaseUpload(buffer, mimetype="text/csv", resumable=True)

    arquivo_id = buscar_arquivo_drive(service, nome_arquivo, pasta_id)
    if arquivo_id:
        service.files().update(fileId=arquivo_id, media_body=media).execute()
        log.info(f"  ATUALIZADO: {nome_arquivo}")
    else:
        metadata = {"name": nome_arquivo, "parents": [pasta_id]}
        service.files().create(body=metadata, media_body=media, fields="id").execute()
        log.info(f"  CRIADO: {nome_arquivo}")
    print(f"  ✓ {nome_arquivo} enviado para o Drive.")


def upload_excel(service, caminho_local, nome_arquivo, pasta_id):
    """Faz upload de arquivo Excel para o Google Drive."""
    if not os.path.exists(caminho_local):
        log.warning(f"Arquivo não encontrado: {caminho_local}")
        print(f"  ⚠ Arquivo de regiões não encontrado em: {caminho_local}")
        return
    with open(caminho_local, "rb") as f:
        buffer = io.BytesIO(f.read())
    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    media = MediaIoBaseUpload(buffer, mimetype=mime, resumable=True)

    arquivo_id = buscar_arquivo_drive(service, nome_arquivo, pasta_id)
    if arquivo_id:
        service.files().update(fileId=arquivo_id, media_body=media).execute()
    else:
        metadata = {"name": nome_arquivo, "parents": [pasta_id]}
        service.files().create(body=metadata, media_body=media, fields="id").execute()
    log.info(f"  UPLOAD OK: {nome_arquivo}")
    print(f"  ✓ {nome_arquivo} enviado para o Drive.")


def baixar_csv_drive(service, nome_arquivo, pasta_id):
    """Baixa CSV do Drive e retorna DataFrame."""
    arquivo_id = buscar_arquivo_drive(service, nome_arquivo, pasta_id)
    if not arquivo_id:
        return pd.DataFrame()
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, service.files().get_media(fileId=arquivo_id))
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    try:
        return pd.read_csv(buffer, sep=";", decimal=",", encoding="utf-8-sig", dtype=str)
    except Exception:
        return pd.DataFrame()


def processar_e_acumular(service, csv_origem, nome_drive, pasta_id):
    """Lê CSV da rede, acumula com histórico do Drive usando drop_duplicates e faz upload."""
    print(f"\nProcessando: {os.path.basename(csv_origem)}...")
    log.info(f"Processando: {csv_origem}")

    if not os.path.exists(csv_origem):
        log.error(f"ARQUIVO NAO ENCONTRADO: {csv_origem}")
        print(f"  ⚠ Arquivo não encontrado: {csv_origem}")
        return

    try:
        # Lê tudo como string para evitar problemas de drop_duplicates com float de precisão diferente
        df_novo = pd.read_csv(csv_origem, sep=";", encoding="utf-8-sig", dtype=str, low_memory=False)
        df_novo.columns = [c.strip() for c in df_novo.columns]
        # Remove espaços vazios das extremidades das strings (importante para drop_duplicates)
        df_novo_limpo = df_novo.apply(lambda col: col.str.strip() if col.dtype == 'object' else col)
    except Exception as e:
        log.error(f"Erro ao ler CSV: {e}")
        return

    log.info(f"  Linhas no CSV da rede: {len(df_novo)}")
    print(f"  Linhas lidas da rede: {len(df_novo)}")

    # Acumula com histórico existente no Drive usando Upsert por Data
    df_historico = baixar_csv_drive(service, nome_drive, pasta_id)
    if not df_historico.empty:
        if 'DATA_C' in df_novo_limpo.columns and 'DATA_C' in df_historico.columns:
            # Converte datas para garantir comparação correta
            datas_novas = pd.to_datetime(df_novo_limpo['DATA_C'], format='%d/%m/%Y', errors='coerce').dropna().dt.date.unique()
            historico_dates = pd.to_datetime(df_historico['DATA_C'], format='%d/%m/%Y', errors='coerce').dt.date
            
            # Remove do histórico as datas exatas que vieram no arquivo novo (Overwrite diário)
            mask = historico_dates.isin(datas_novas)
            df_historico_filtrado = df_historico[~mask]
            
            # Concatena e aplica drop_duplicates final por precaução
            df_final = pd.concat([df_historico_filtrado, df_novo_limpo], ignore_index=True)
            df_final = df_final.drop_duplicates()
            log.info(f"  Upsert aplicado. Datas substituídas: {len(datas_novas)}")
        else:
            df_final = pd.concat([df_historico, df_novo_limpo], ignore_index=True).drop_duplicates()
            log.info(f"  Concatenação simples (Coluna DATA_C não encontrada).")
    else:
        df_final = df_novo_limpo  # Primeiro upload: envia tudo

    log.info(f"  Total para upload: {len(df_final)} linhas")
    print(f"  Total acumulado: {len(df_final)} linhas")
    upload_csv(service, df_final, nome_drive, pasta_id)


def run():
    print("=" * 55)
    print("  MADERO | Upload Diário para Google Drive")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)
    log.info("=" * 55)
    log.info(f"INICIO DO UPLOAD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        print("\nConectando ao Google Drive...")
        service = conectar_drive()
        print("✓ Conectado ao Google Drive!")
        log.info("Conexao com Google Drive: OK")
    except FileNotFoundError as e:
        print(f"\nERRO: {e}")
        log.error(str(e))
        return
    except Exception as e:
        log.error(f"Erro de conexao: {e}")
        print(f"\nERRO de conexão: {e}")
        return

    pasta_id = CONFIGURACOES["PASTA_DRIVE_ID"]
    hoje = datetime.now()

    # Processa todos os CSVs configurados
    for arq in CONFIGURACOES["ARQUIVOS_CSV"]:
        processar_e_acumular(service, arq["origem"], arq["nome_drive"], pasta_id)

    # Processa todos os Excels configurados
    for arq in CONFIGURACOES["ARQUIVOS_EXCEL"]:
        upload_excel(service, arq["origem"], arq["nome_drive"], pasta_id)

    print("\n✓ UPLOAD CONCLUÍDO COM SUCESSO!")
    print(f"  Log salvo em: {LOG_PATH}")
    log.info("UPLOAD CONCLUIDO COM SUCESSO!")


if __name__ == "__main__":
    run()
