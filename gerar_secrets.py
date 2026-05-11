import json, yaml, os

# Lê service account
with open(r'c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\service_account.json') as f:
    sa = json.load(f)

# Lê config_auth
with open(r'c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\config_auth.yaml', encoding='utf-8') as f:
    auth_content = f.read()

lines = [
    "# ==============================================",
    "# STREAMLIT CLOUD SECRETS",
    "# Cole este conteudo em: share.streamlit.io",
    "# App > Settings > Secrets",
    "# ==============================================",
    "",
    "[drive]",
    'folder_id = "1uex_JDIcqc1W_fT0u12T_NRSMdaRBFhJ"',
    'nome_cupons = "cancelamentos_cupons.csv"',
    'nome_itens = "cancelamentos_itens.csv"',
    'nome_regioes = "regioes.xlsx"',
    "",
    "[gcp_service_account]",
]
for k, v in sa.items():
    if k == 'private_key':
        lines.append(f'{k} = """{v}"""')
    else:
        lines.append(f'{k} = "{v}"')

lines += [
    "",
    "[auth]",
    'config = """',
    auth_content,
    '"""',
]

output = '\n'.join(lines)
out_path = r'c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\secrets_template.toml'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(output)
print('Gerado com sucesso:', out_path)
