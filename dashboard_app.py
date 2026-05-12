import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import locale
import io
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# Configuração da Página
st.set_page_config(
    page_title="Madero | Cancelamentos",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# AUTENTICAÇÃO — lê de st.secrets (Streamlit Cloud) ou arquivo local
# =====================================================================
def _carregar_config_auth():
    # Streamlit Cloud: lê dos Secrets
    try:
        if 'auth' in st.secrets and 'config' in st.secrets['auth']:
            return yaml.safe_load(st.secrets['auth']['config'])
    except Exception:
        pass
    # Local: lê do arquivo yaml
    import os
    local = r'c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\config_auth.yaml'
    if os.path.exists(local):
        with open(local, encoding='utf-8') as f:
            return yaml.safe_load(f)
    st.error('Configuração de autenticação não encontrada.')
    st.stop()

config = _carregar_config_auth()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

if not st.session_state.get('authentication_status'):
    st.markdown("""
        <style>
        /* Fundo escuro premium para a tela de login */
        .stApp { background-color: #0f0f0f; }
        
        /* Ocultar barra superior na tela de login */
        header { visibility: hidden; }

        /* Remover espaços excessivos do Streamlit para evitar barra de rolagem */
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 0rem !important;
        }

        /* Estilizar a caixa do formulário de login */
        div[data-testid="stForm"] {
            background-color: #1a1a1a;
            border: 1px solid #C5A059;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.8);
        }
        
        /* Corrigir cores dentro do formulário */
        div[data-testid="stForm"] p, div[data-testid="stForm"] label {
            color: #ffffff !important;
            font-weight: 600;
        }

        /* Botão de login dourado (apenas o botão principal) */
        div[data-testid="stFormSubmitButton"] button {
            background-color: #C5A059 !important;
            color: #ffffff !important;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            text-transform: uppercase;
            width: 100%;
            margin-top: 10px;
            transition: 0.3s;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            background-color: #b38e4a !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Layout centralizado usando colunas (mais finas para diminuir o tamanho da caixa)
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        # Logo Branco do Madero (Tamanho Controlado)
        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 10px;'>
                <img src="https://cdn-sites-assets.mziq.com/wp-content/uploads/sites/858/2021/09/logo-branco.png" width="220">
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.markdown("<div style='text-align: center; color: #C5A059; font-size: 18px; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 25px;'>MONITORAMENTO DE CANCELAMENTOS</div>", unsafe_allow_html=True)
        
        # O formulário de login renderizado aqui será capturado pelo CSS acima
        authenticator.login(location='main')

        if st.session_state.get('authentication_status') is False:
            st.error('❌ Usuário ou senha incorretos.')
    
    # Bloqueia o carregamento do resto do painel enquanto não logar
    st.stop()

_username = st.session_state.get('username', '')
_user_profile = config.get('user_profiles', {}).get(_username, {})
_user_perfil = _user_profile.get('perfil', 'GERENTE')
_user_escopo = _user_profile.get('escopo', None)
_user_nome   = _user_profile.get('nome', st.session_state.get('name', ''))

# Estilo CSS Premium
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #000000 !important; }
    .stApp { background-color: #f0f2f6; }
    h1, h2, h3, .section-title { color: #000000 !important; font-weight: 700 !important; margin-bottom: 10px !important; }
    .header-bar { background-color: #1a1a1a; padding: 20px; border-radius: 15px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; color: #ffffff !important; }
    .header-bar span { color: #ffffff !important; }
    .metric-container { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border-bottom: 4px solid #C5A059; text-align: center; height: 120px; display: flex; flex-direction: column; justify-content: center; }
    .metric-label { font-size: 13px; color: #333 !important; text-transform: uppercase; font-weight: 700; margin-bottom: 5px; }
    .metric-value { font-size: 22px; color: #000000 !important; font-weight: 700; }
    .chart-card { background-color: #ffffff !important; padding: 20px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #eeeeee; margin-bottom: 20px; }
    section[data-testid="stSidebar"] { background-color: #1a1a1a !important; }
    section[data-testid="stSidebar"] * { color: #ffffff !important; }
    .stButton>button, .stDownloadButton>button { width: 100%; background-color: #C5A059 !important; color: white !important; border-radius: 10px; font-weight: 700; border: none; text-transform: uppercase; padding: 12px; }
    [data-testid="stDataFrame"] * { color: #000000 !important; }
    /* Labels dos filtros em preto negrito */
    .stMultiSelect label, .stDateInput label { color: #000000 !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# Formatação Moeda BRL — apenas para valores numéricos
def format_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =====================================================================
# GOOGLE DRIVE — leitura de dados
# =====================================================================
def _get_drive_service():
    """Conecta ao Drive via Service Account (Secrets) ou arquivo local."""
    import os
    
    try:
        if 'gcp_service_account' in st.secrets:
            creds = service_account.Credentials.from_service_account_info(
                st.secrets['gcp_service_account'],
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            return build('drive', 'v3', credentials=creds)
    except Exception:
        pass

    # Fallback local
    local_sa = r'c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\service_account.json'
    creds = service_account.Credentials.from_service_account_file(
        local_sa, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    return build('drive', 'v3', credentials=creds)

def _drive_folder_id():
    try:
        if 'drive' in st.secrets:
            return st.secrets['drive']['folder_id']
    except Exception:
        pass
    return '1uex_JDIcqc1W_fT0u12T_NRSMdaRBFhJ'

def _baixar_arquivo_drive(service, nome_arquivo, folder_id):
    """Baixa um arquivo do Drive e retorna BytesIO."""
    resultado = service.files().list(
        q=f"name='{nome_arquivo}' and '{folder_id}' in parents and trashed=false",
        fields='files(id)'
    ).execute()
    arquivos = resultado.get('files', [])
    if not arquivos:
        return None
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(
        buffer, service.files().get_media(fileId=arquivos[0]['id'])
    )
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    return buffer

@st.cache_data(ttl=1800)  # Cache de 30 min
def load_data(tipo):
    """Baixa CSV do Drive e retorna DataFrame processado."""
    nomes = {
        'cupons': 'cancelamentos_cupons.csv',
        'itens':  'cancelamentos_itens.csv',
    }
    nome_regioes = 'regioes.xlsx'
    nome_arquivo = nomes.get(tipo, 'cancelamentos_cupons.csv')

    service   = _get_drive_service()
    folder_id = _drive_folder_id()

    # Baixa CSV principal
    buf = _baixar_arquivo_drive(service, nome_arquivo, folder_id)
    if buf is None:
        return pd.DataFrame()
    df = pd.read_csv(buf, sep=';', decimal=',', encoding='utf-8-sig', dtype=str, low_memory=False)
    df.columns = [c.strip() for c in df.columns]

    # Baixa planilha de regiões e faz JOIN
    buf_reg = _baixar_arquivo_drive(service, nome_regioes, folder_id)
    if buf_reg:
        df_reg = pd.read_excel(buf_reg)
        # Detecta colunas de região
        col_map = {}
        for col in df_reg.columns:
            c = str(col).upper()
            if 'COD' in c and 'FILIAL' in c and 'CDFILIAL_C' not in col_map: col_map[col] = 'CDFILIAL_C'
            elif 'DIRETOR' in c and 'DIRETOR' not in col_map.values(): col_map[col] = 'DIRETOR'
            elif 'GEOP' in c and 'GEOP' not in col_map.values(): col_map[col] = 'GEOP'
            elif 'GERENTE' in c and 'REGIONAL' in c and 'GERENTE_REGIONAL' not in col_map.values(): col_map[col] = 'GERENTE_REGIONAL'
        df_reg = df_reg.rename(columns=col_map)[[v for v in col_map.values()]].drop_duplicates(subset=['CDFILIAL_C'])
        df_reg['CDFILIAL_C'] = df_reg['CDFILIAL_C'].astype(str).str.replace('.0','',regex=False).str.strip().str.lstrip('0')
        df['CDFILIAL_C'] = df['CDFILIAL_C'].astype(str).str.replace('.0','',regex=False).str.strip().str.lstrip('0')
        df = df.merge(df_reg, on='CDFILIAL_C', how='left')

    # Conversões
    df['DATA_C']  = pd.to_datetime(df['DATA_C'], format='%d/%m/%Y', errors='coerce')
    df['VRTOTAL'] = pd.to_numeric(df['VRTOTAL'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    df['HORA_INT'] = pd.to_numeric(df['HORA_C'].astype(str).str[:2], errors='coerce').fillna(0).astype(int)
    df['DIA_SEMANA'] = df['DATA_C'].dt.day_name().map({
        'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
        'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    })
    if 'DSOBSCANITE' in df.columns:
        df['MOTIVO_LIMPO'] = df['DSOBSCANITE'].fillna('NÃO INFORMADO').astype(str).str.split(';').str[0].str.strip().str.upper()
        df['MOTIVO_LIMPO'] = df['MOTIVO_LIMPO'].replace(['NAN', 'NONE', ''], 'NÃO INFORMADO')
    for col in ['DIRETOR', 'GEOP', 'GERENTE_REGIONAL', 'NMOPERADOR', 'CANAL_DE_VENDA_C', 'PRODUTO_C', 'NMFILIAL_C']:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(['nan', 'None', 'NAT', ''], 'NÃO MAPEADO').str.strip()
    return df


def update_fig_layout(fig, title=None):
    """Layout padrão: texto preto em fundo branco, sem prefixo R$ nos eixos."""
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>" if title else "", font=dict(color="#000000", size=15)),
        font=dict(color="#000000", family="Inter"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            title_text="",
            tickfont=dict(color="#000000", size=10),
            showgrid=False,
            linecolor='#cccccc'
        ),
        yaxis=dict(
            title_text="",
            tickfont=dict(color="#000000", size=10),
            showgrid=True,
            gridcolor="#eeeeee",
            linecolor='#cccccc'
        ),
        margin=dict(l=10, r=30, t=50, b=10),
        autosize=True,
        legend=dict(font=dict(color="#000000"))
    )
    return fig


# Gráfico de barras horizontal (categoria no Y, valor no X)
# NÃO aplica tickprefix no eixo Y pois ele exibe nomes/categorias
def plot_bar_h(df_in, cat_col, title, color='#C5A059', top_n=None):
    df_plot = df_in.groupby(cat_col)['VRTOTAL'].sum().reset_index()
    df_plot = df_plot.sort_values('VRTOTAL', ascending=True)  # ascending=True → maior fica em cima
    if top_n:
        df_plot = df_plot.tail(top_n)
    df_plot['TEXTO'] = df_plot['VRTOTAL'].apply(format_brl)

    fig = px.bar(df_plot, x='VRTOTAL', y=cat_col, orientation='h',
                 color_discrete_sequence=[color], text='TEXTO')
    fig.update_traces(textposition='outside')
    fig = update_fig_layout(fig, title)
    # Apenas o eixo X recebe prefixo de valor (é o eixo de valor numérico)
    max_val = df_plot['VRTOTAL'].max() if not df_plot.empty else 1
    fig.update_xaxes(tickprefix="R$ ", tickformat=",", range=[0, max_val * 1.3])
    return fig


# Gráfico de barras vertical (categoria no X, valor no Y)
def plot_bar_v(df_in, cat_col, title, color='#1a1a1a', top_n=None):
    df_plot = df_in.groupby(cat_col)['VRTOTAL'].sum().reset_index()
    df_plot = df_plot.sort_values('VRTOTAL', ascending=False)
    if top_n:
        df_plot = df_plot.head(top_n)
    df_plot['TEXTO'] = df_plot['VRTOTAL'].apply(format_brl)

    fig = px.bar(df_plot, x=cat_col, y='VRTOTAL', orientation='v',
                 color_discrete_sequence=[color], text='TEXTO')
    fig.update_traces(textposition='outside')
    fig = update_fig_layout(fig, title)
    # Apenas o eixo Y recebe prefixo de valor
    max_val = df_plot['VRTOTAL'].max() if not df_plot.empty else 1
    fig.update_yaxes(tickprefix="R$ ", tickformat=",", range=[0, max_val * 1.2])
    return fig


# --- SIDEBAR ---
with st.sidebar:
    st.image("https://www.grupomadero.com.br/wp-content/themes/madero/assets/images/logo-madero.png", width=180)
    st.markdown("<br>", unsafe_allow_html=True)

    # Info do usuário logado
    perfil_icons = {"ADMIN": "👑", "DIRETOR": "🎯", "GERENTE": "📊", "GESTOR": "🏪"}
    icone = perfil_icons.get(_user_perfil, "👤")
    st.markdown(f"""
    <div style='background:#2a2a2a;padding:12px;border-radius:10px;border-left:3px solid #C5A059;margin-bottom:10px;'>
        <div style='color:#C5A059;font-size:11px;font-weight:700;text-transform:uppercase;'>Usuário Conectado</div>
        <div style='color:#ffffff;font-size:14px;font-weight:700;margin-top:4px;'>{icone} {_user_nome}</div>
        <div style='color:#aaaaaa;font-size:11px;margin-top:2px;'>Perfil: {_user_perfil}</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("🛡️ PAINEL CANCELAMENTOS", ["Cancelamento de Cupons", "Cancelamento de Itens"])
    # Botão de atualizar cache
    if st.button("🔄 ATUALIZAR DADOS"):
        load_data.clear()
        st.rerun()

    st.markdown("---")

    # Logout
    authenticator.logout("🚪 SAIR", location="sidebar")

# Carregar Dados
tipo = "cupons" if page == "Cancelamento de Cupons" else "itens"
df_raw = load_data(tipo)

# --- HEADER ---
st.markdown(f"""
<div class="header-bar">
  <div>
    <span style="font-size: 22px; font-weight: 700;">{page.upper()}</span><br>
    <span style="font-size: 13px; opacity: 0.7;">Monitoramento de Cancelamentos</span>
  </div>
  <div style="text-align: right;"><span style="color: #00ff00;">●</span> MONITORAMENTO ATIVO</div>
</div>""", unsafe_allow_html=True)

# =====================================================================
# PRÉ-FILTRO POR PERFIL (aplicado ANTES dos filtros manuais)
# =====================================================================
def aplicar_prefiltro(df_in, perfil, escopo):
    """Restringe o DataFrame ao escopo do usuário logado."""
    if perfil == "ADMIN" or not escopo:
        return df_in  # Vê tudo
    elif perfil == "DIRETOR":
        return df_in[df_in['DIRETOR'].str.upper() == escopo.upper()]
    elif perfil == "GERENTE":
        return df_in[df_in['GEOP'].str.upper() == escopo.upper()]
    elif perfil == "GESTOR":
        return df_in[df_in['NMFILIAL_C'].str.upper() == escopo.upper()]
    return df_in

# Aplicar pré-filtro invisível baseado no perfil do usuário
df_scoped = aplicar_prefiltro(df_raw, _user_perfil, _user_escopo)

# --- FILTROS VISUAIS ---
st.markdown("<h3 style='font-size: 17px;'>🎛️ Filtros</h3>", unsafe_allow_html=True)

# Badge de escopo — mostra ao usuário não-ADMIN o que está travado
if _user_perfil != "ADMIN" and _user_escopo:
    escopo_label = {"DIRETOR": "🎯 Diretor", "GERENTE": "📊 Gerente Regional", "GESTOR": "🏪 Filial"}.get(_user_perfil, "")
    st.markdown(f"""
    <div style='background:#fff8e7;border:1px solid #C5A059;border-radius:8px;padding:8px 14px;margin-bottom:10px;font-size:13px;'>
        🔒 <b>Visualização restrita ao seu escopo:</b> {escopo_label} — <b>{_user_escopo}</b>
    </div>""", unsafe_allow_html=True)

f_col1, f_col2, f_col3, f_col4 = st.columns(4)

with f_col1:
    start_d = df_scoped['DATA_C'].min() if not df_scoped.empty else datetime.now()
    end_d   = df_scoped['DATA_C'].max() if not df_scoped.empty else datetime.now()
    f_date  = st.date_input("PERÍODO", value=(start_d, end_d), format="DD/MM/YYYY")

with f_col2:
    # DIRETOR: travado para o próprio nome; GERENTE/GESTOR: travado
    if _user_perfil in ("DIRETOR", "GERENTE", "GESTOR") and _user_escopo:
        st.markdown(f"**DIRETOR REGIONAL**")
        st.markdown(f"<div style='color:#C5A059;font-weight:700;padding:6px 0;'>🔒 {_user_escopo if _user_perfil=='DIRETOR' else df_scoped['DIRETOR'].iloc[0] if not df_scoped.empty else '—'}</div>", unsafe_allow_html=True)
        f_diretor = []
    else:
        f_diretor = st.multiselect("DIRETOR REGIONAL", options=sorted([str(x) for x in df_scoped['DIRETOR'].unique() if x]))

with f_col3:
    if _user_perfil in ("GERENTE", "GESTOR") and _user_escopo:
        st.markdown(f"**GERENTE REGIONAL (GEOP)**")
        st.markdown(f"<div style='color:#C5A059;font-weight:700;padding:6px 0;'>🔒 {_user_escopo if _user_perfil=='GERENTE' else df_scoped['GEOP'].iloc[0] if not df_scoped.empty else '—'}</div>", unsafe_allow_html=True)
        f_gerente = []
    else:
        df_temp_ger = df_scoped[df_scoped['DIRETOR'].isin(f_diretor)] if f_diretor else df_scoped
        f_gerente = st.multiselect("GERENTE REGIONAL (GEOP)", options=sorted([str(x) for x in df_temp_ger['GEOP'].unique() if x]))

with f_col4:
    if _user_perfil == "GESTOR" and _user_escopo:
        st.markdown(f"**FILIAL**")
        st.markdown(f"<div style='color:#C5A059;font-weight:700;padding:6px 0;'>🔒 {_user_escopo}</div>", unsafe_allow_html=True)
        f_filial = []
    else:
        df_temp_fil = df_scoped
        if f_diretor:  df_temp_fil = df_temp_fil[df_temp_fil['DIRETOR'].isin(f_diretor)]
        if f_gerente:  df_temp_fil = df_temp_fil[df_temp_fil['GEOP'].isin(f_gerente)]
        f_filial = st.multiselect("FILIAL", options=sorted([str(x) for x in df_temp_fil['NMFILIAL_C'].unique() if x]))

f_operador = st.multiselect("👤 FILTRAR POR OPERADOR", options=sorted([str(x) for x in df_scoped['NMOPERADOR'].unique() if x]))

# Aplicar Filtros Manuais sobre o df já com pré-filtro de perfil
df = df_scoped.copy()
if len(f_date) == 2:
    df = df[(df['DATA_C'] >= pd.Timestamp(f_date[0])) & (df['DATA_C'] <= pd.Timestamp(f_date[1]))]
if f_diretor:  df = df[df['DIRETOR'].isin(f_diretor)]
if f_gerente:  df = df[df['GEOP'].isin(f_gerente)]
if f_filial:   df = df[df['NMFILIAL_C'].isin(f_filial)]
if f_operador: df = df[df['NMOPERADOR'].isin(f_operador)]

# KPIs
st.markdown("<br>", unsafe_allow_html=True)
ck1, ck2, ck3, ck4 = st.columns(4)
with ck1:
    st.markdown(f'<div class="metric-container"><div class="metric-label">Total Cancelado</div><div class="metric-value">{format_brl(df["VRTOTAL"].sum())}</div></div>', unsafe_allow_html=True)
with ck2:
    st.markdown(f'<div class="metric-container"><div class="metric-label">Operações</div><div class="metric-value">{len(df):,}</div></div>', unsafe_allow_html=True)
with ck3:
    filial_ofensora = df.groupby("NMFILIAL_C")["VRTOTAL"].sum().idxmax() if not df.empty else "---"
    st.markdown(f'<div class="metric-container"><div class="metric-label">Filial Ofensora</div><div class="metric-value" style="font-size: 15px;">{filial_ofensora}</div></div>', unsafe_allow_html=True)
with ck4:
    geop_ofensor = df.groupby("GEOP")["VRTOTAL"].sum().idxmax() if not df.empty else "---"
    st.markdown(f'<div class="metric-container"><div class="metric-label">GEOP Ofensor</div><div class="metric-value" style="font-size: 15px;">{geop_ofensor}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =====================================================================
# PÁGINA: CANCELAMENTO DE CUPONS
# =====================================================================
if page == "Cancelamento de Cupons":
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(plot_bar_h(df, 'DIRETOR', "Cancelamentos por DIRETOR"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r1c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        df_can = df.groupby('CANAL_DE_VENDA_C')['VRTOTAL'].sum().reset_index()
        fig_can = px.pie(df_can, values='VRTOTAL', names='CANAL_DE_VENDA_C', hole=0.5,
                         color_discrete_sequence=['#1a1a1a', '#C5A059', '#4D8093'])
        fig_can = update_fig_layout(fig_can, "Cancelamentos por CANAL DE VENDA")
        st.plotly_chart(fig_can, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(plot_bar_v(df, 'GEOP', "Cancelamentos por GEOP", color='#1a1a1a'), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r2c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        df_top_prod = df.groupby('PRODUTO_C')['VRTOTAL'].sum().nlargest(10).reset_index()
        st.plotly_chart(plot_bar_h(df_top_prod, 'PRODUTO_C', "Top 10 Produtos Cancelados"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        df_top_op = df.groupby('NMOPERADOR')['VRTOTAL'].sum().nlargest(15).reset_index()
        st.plotly_chart(plot_bar_h(df_top_op, 'NMOPERADOR', "Cancelamentos por Operador (Top 15)"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r3c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        df_hr = df.groupby('HORA_INT')['VRTOTAL'].sum().reset_index()
        df_hr['TEXTO'] = df_hr['VRTOTAL'].apply(format_brl)
        # Identificar horário mais ofensor para destacar em vermelho
        hora_max = df_hr.loc[df_hr['VRTOTAL'].idxmax(), 'HORA_INT'] if not df_hr.empty else -1
        df_hr['COR'] = df_hr['HORA_INT'].apply(lambda h: '#DC2626' if h == hora_max else '#1a1a1a')
        fig_hr = go.Figure()
        fig_hr.add_trace(go.Scatter(
            x=df_hr['HORA_INT'], y=df_hr['VRTOTAL'], mode='lines+markers+text',
            text=df_hr['TEXTO'], textposition='top center',
            line=dict(color='#1a1a1a', width=2),
            marker=dict(color=df_hr['COR'], size=10),
            textfont=dict(size=10)
        ))
        fig_hr = update_fig_layout(fig_hr, "Evolução por Horário")
        fig_hr.update_xaxes(dtick=1, title_text="Hora do Dia")
        fig_hr.update_yaxes(tickprefix="R$ ", tickformat=",")
        # Anotação no pico
        if not df_hr.empty:
            row_max = df_hr[df_hr['HORA_INT'] == hora_max].iloc[0]
            fig_hr.add_annotation(x=hora_max, y=row_max['VRTOTAL'],
                text=f"⚠ PICO: {int(hora_max)}h", showarrow=True,
                arrowhead=2, arrowcolor='#DC2626', font=dict(color='#DC2626', size=11, family='Inter'),
                ax=0, ay=-35)
        st.plotly_chart(fig_hr, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Treemap — Dia da Semana (Cupons)
    r4c1, r4c2 = st.columns(2)
    with r4c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        df_dia_c = df.groupby('DIA_SEMANA')['VRTOTAL'].sum().reindex(ordem_dias).reset_index().fillna(0)
        df_dia_c['TEXTO'] = df_dia_c['VRTOTAL'].apply(format_brl)
        fig_tree_c = px.treemap(
            df_dia_c, path=['DIA_SEMANA'], values='VRTOTAL',
            color='VRTOTAL',
            color_continuous_scale=['#f0f2f6', '#C5A059', '#1a1a1a'],
            custom_data=['TEXTO']
        )
        fig_tree_c.update_traces(
            texttemplate='<b>%{label}</b><br>%{customdata[0]}',
            textfont=dict(size=14)
        )
        fig_tree_c.update_layout(
            title=dict(text='<b>Cancelamentos por Dia da Semana (Treemap)</b>', font=dict(color='#000000', size=15)),
            font=dict(family='Inter', color='#000000'),
            paper_bgcolor='white',
            margin=dict(l=10, r=10, t=50, b=10),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_tree_c, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# =====================================================================
# PÁGINA: CANCELAMENTO DE ITENS
# =====================================================================
else:
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(plot_bar_h(df, 'DIRETOR', "Itens: Por DIRETOR"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r1c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(plot_bar_h(df, 'GEOP', "Itens: Por Gerente Regional (GEOP)", color='#1a1a1a'), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        # Gráfico por Filial (Top 15 mais ofensoras)
        df_fil_i = df.groupby('NMFILIAL_C')['VRTOTAL'].sum().nlargest(15).reset_index()
        st.plotly_chart(plot_bar_h(df_fil_i, 'NMFILIAL_C', "Itens: Por Filial (Top 15)", color='#C5A059'), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r2c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        # Motivos de Cancelamento — Gráfico de Barras (Top 10)
        if 'MOTIVO_LIMPO' in df.columns:
            df_mot = df.groupby('MOTIVO_LIMPO')['VRTOTAL'].sum().nlargest(10).reset_index()
            st.plotly_chart(plot_bar_h(df_mot, 'MOTIVO_LIMPO', "Itens: Principais Motivos (Top 10)", color='#1E3A5F'), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        df_hr_i = df.groupby('HORA_INT')['VRTOTAL'].sum().reset_index()
        df_hr_i['TEXTO'] = df_hr_i['VRTOTAL'].apply(format_brl)
        
        # Identificar horário mais ofensor para destacar em vermelho
        hora_max_i = df_hr_i.loc[df_hr_i['VRTOTAL'].idxmax(), 'HORA_INT'] if not df_hr_i.empty else -1
        df_hr_i['COR'] = df_hr_i['HORA_INT'].apply(lambda h: '#DC2626' if h == hora_max_i else '#1a1a1a')
        
        fig_hr = go.Figure()
        fig_hr.add_trace(go.Scatter(
            x=df_hr_i['HORA_INT'], y=df_hr_i['VRTOTAL'], mode='lines+markers+text',
            text=df_hr_i['TEXTO'], textposition='top center',
            line=dict(color='#1a1a1a', width=2),
            marker=dict(color=df_hr_i['COR'], size=10),
            textfont=dict(size=10)
        ))
        
        fig_hr = update_fig_layout(fig_hr, "Itens: Evolução por Hora")
        fig_hr.update_xaxes(dtick=1, title_text="Hora do Dia")
        fig_hr.update_yaxes(tickprefix="R$ ", tickformat=",")
        
        # Anotação no pico
        if not df_hr_i.empty:
            row_max_i = df_hr_i[df_hr_i['HORA_INT'] == hora_max_i].iloc[0]
            fig_hr.add_annotation(x=hora_max_i, y=row_max_i['VRTOTAL'],
                text=f"⚠ PICO: {int(hora_max_i)}h", showarrow=True,
                arrowhead=2, arrowcolor='#DC2626', font=dict(color='#DC2626', size=11, family='Inter'),
                ax=0, ay=-35)
                
        st.plotly_chart(fig_hr, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r3c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        df_p_i = df.groupby('PRODUTO_C')['VRTOTAL'].sum().nlargest(10).reset_index()
        st.plotly_chart(plot_bar_h(df_p_i, 'PRODUTO_C', "Itens: Por Produto (Top 10)"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    r4c1, r4c2 = st.columns(2)
    with r4c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        df_op_i = df.groupby('NMOPERADOR')['VRTOTAL'].sum().nlargest(10).reset_index()
        st.plotly_chart(plot_bar_h(df_op_i, 'NMOPERADOR', "Itens: Por Operador (Top 10)", color='#1a1a1a'), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r4c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        # Dia da Semana — TREEMAP (Mapa de Árvore)
        ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        df_dia = df.groupby('DIA_SEMANA')['VRTOTAL'].sum().reindex(ordem_dias).reset_index().fillna(0)
        df_dia['TEXTO'] = df_dia['VRTOTAL'].apply(format_brl)
        fig_tree = px.treemap(
            df_dia, path=['DIA_SEMANA'], values='VRTOTAL',
            color='VRTOTAL',
            color_continuous_scale=['#f0f2f6', '#C5A059', '#1a1a1a'],
            custom_data=['TEXTO']
        )
        fig_tree.update_traces(
            texttemplate='<b>%{label}</b><br>%{customdata[0]}',
            textfont=dict(size=14)
        )
        fig_tree.update_layout(
            title=dict(text='<b>Itens: Por Dia da Semana (Treemap)</b>', font=dict(color='#000000', size=15)),
            font=dict(family='Inter', color='#000000'),
            paper_bgcolor='white',
            margin=dict(l=10, r=10, t=50, b=10),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_tree, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# =====================================================================
# GRÁFICO DE LINHA — CANCELAMENTOS POR DIA (ambas as páginas)
# =====================================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
df_diario = df.groupby(df['DATA_C'].dt.date)['VRTOTAL'].sum().reset_index()
df_diario.columns = ['DIA', 'TOTAL']
df_diario = df_diario.sort_values('DIA')
df_diario['TEXTO'] = df_diario['TOTAL'].apply(format_brl)

# Identificar dia com maior volume
dia_max = df_diario.loc[df_diario['TOTAL'].idxmax(), 'DIA'] if not df_diario.empty else None
df_diario['COR'] = df_diario['DIA'].apply(lambda d: '#DC2626' if d == dia_max else '#1a1a1a')

fig_diario = go.Figure()
fig_diario.add_trace(go.Scatter(
    x=df_diario['DIA'], y=df_diario['TOTAL'], mode='lines+markers+text',
    text=df_diario['TEXTO'], textposition='top center',
    line=dict(color='#C5A059', width=2),
    marker=dict(color=df_diario['COR'], size=8),
    textfont=dict(size=9, color='#333333')
))
fig_diario = update_fig_layout(fig_diario, f"Evolução Diária — {page}")
fig_diario.update_xaxes(
    title_text="Data",
    tickformat="%d/%m",
    dtick=86400000,
    tickangle=-45
)
max_d_val = df_diario['TOTAL'].max() if not df_diario.empty else 1
fig_diario.update_yaxes(tickprefix="R$ ", tickformat=",", range=[0, max_d_val * 1.2])

# Anotação no pico
if not df_diario.empty and dia_max:
    row_max = df_diario[df_diario['DIA'] == dia_max].iloc[0]
    fig_diario.add_annotation(x=dia_max, y=row_max['TOTAL'],
        text=f"⚠ PICO", showarrow=True,
        arrowhead=2, arrowcolor='#DC2626', font=dict(color='#DC2626', size=11, family='Inter'),
        ax=0, ay=-35)

fig_diario.update_layout(height=350)
st.plotly_chart(fig_diario, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# =====================================================================
# TABELA E DOWNLOAD (ambas as páginas)
# =====================================================================
st.markdown(f"<h3 class='section-title'>📋 Detalhamento: {page}</h3>", unsafe_allow_html=True)
st.markdown('<div class="chart-card">', unsafe_allow_html=True)

cols_view = ['DATA_C', 'HORA_C', 'NMFILIAL_C', 'DIRETOR', 'GEOP', 'NMOPERADOR', 'PRODUTO_C', 'VRTOTAL', 'CANAL_DE_VENDA_C']
if page == "Cancelamento de Itens":
    cols_view.append('DSOBSCANITE')

df_table = df[cols_view].sort_values('VRTOTAL', ascending=False)
df_table_show = df_table.copy()
df_table_show['VRTOTAL'] = df_table_show['VRTOTAL'].apply(format_brl)
st.dataframe(df_table_show, use_container_width=True, hide_index=True)

output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    df_table.to_excel(writer, index=False, sheet_name='Relatorio')
st.download_button(
    label="📥 BAIXAR BASE FILTRADA EM EXCEL",
    data=output.getvalue(),
    file_name=f"auditoria_{page.lower().replace(' ','_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="dl_final"
)
st.markdown('</div>', unsafe_allow_html=True)
