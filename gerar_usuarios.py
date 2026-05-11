"""
Script auxiliar para gerenciar usuários do Dashboard de Auditoria.
Execute este script para:
  - Gerar hashes de senha
  - Adicionar novos usuários ao config.yaml
  - Redefinir senha de um usuário existente

Uso:
  python gerar_usuarios.py
"""
import bcrypt
import yaml
import os

CONFIG_PATH = r"c:\Users\M27812\Desktop\Antigravity\Projetos\madero-cancelamentos\config_auth.yaml"

def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

def criar_config_inicial():
    """Cria o arquivo de configuração com usuários iniciais."""
    
    # Defina os usuários iniciais aqui
    # Formato: (username, nome_completo, email, senha_inicial, perfil, escopo)
    # perfil: ADMIN, DIRETOR, GERENTE, GESTOR
    # escopo: nome do diretor/geop/filial para filtrar dados (None = vê tudo)
    usuarios = [
        # ADMIN — vê tudo
        ("admin",                "Administrador",     "admin@grupomadero.com.br",           "Madero@2025", "ADMIN",   None),

        # DIRETORES — vê todas as regiões sob sua gestão
        ("andretrevisani",       "Andre Trevisani",   "andre.trevisani@grupomadero.com.br", "Madero@2025", "DIRETOR", "ANDRE TREVISANI"),
        ("grazianibarreto",      "Graziani Barreto",  "graziani.barreto@grupomadero.com.br","Madero@2025", "DIRETOR", "GRAZIANI BARRETO"),
        ("kleberriquelme",       "Kleber Riquelme",   "kleber.riquelme@grupomadero.com.br", "Madero@2025", "DIRETOR", "KLEBER RIQUELME"),
        ("gustavodireito",       "Gustavo Direito",   "gustavo.direito@grupomadero.com.br", "Madero@2025", "DIRETOR", "GUSTAVO DIREITO"),
        ("breinerpena",          "Breiner Pena",      "breiner.pena@grupomadero.com.br",    "Madero@2025", "DIRETOR", "BREINER PENA"),
        ("franqueado",           "Franqueado",        "franqueado@grupomadero.com.br",      "Madero@2025", "DIRETOR", "FRANQUEADO"),

        # GERENTES REGIONAIS — vê apenas as filiais do seu GEOP
        ("joselinares",          "Jose Linares",      "jose.linares@grupomadero.com.br",    "Madero@2025", "GERENTE", "JOSE LINARES"),
        ("luanaoliveira",        "Luana Oliveira",    "luana.oliveira@grupomadero.com.br",  "Madero@2025", "GERENTE", "LUANA OLIVEIRA"),
        ("ranierisilva",         "Ranieri Silva",     "ranieri.silva@grupomadero.com.br",   "Madero@2025", "GERENTE", "RANIERI SILVA"),
        ("rafaelbarbosa",        "Rafael Barbosa",    "rafael.barbosa@grupomadero.com.br",  "Madero@2025", "GERENTE", "RAFAEL BARBOSA"),
        ("rodrigopurcina",       "Rodrigo Purcina",   "rodrigo.purcina@grupomadero.com.br", "Madero@2025", "GERENTE", "RODRIGO PURCINA"),
        ("diegocamerino",        "Diego Camerino",    "diego.camerino@grupomadero.com.br",  "Madero@2025", "GERENTE", "DIEGO CAMERINO"),
        ("andersoncruz",         "Anderson Cruz",     "anderson.cruz@grupomadero.com.br",   "Madero@2025", "GERENTE", "ANDERSON CRUZ"),
        ("danieljunior",         "Daniel Junior",     "daniel.junior@grupomadero.com.br",   "Madero@2025", "GERENTE", "DANIEL JUNIOR"),
        ("igornobre",            "Igor Nobre",        "igor.nobre@grupomadero.com.br",      "Madero@2025", "GERENTE", "IGOR NOBRE"),
        ("cristianojesus",       "Cristiano Jesus",   "cristiano.jesus@grupomadero.com.br", "Madero@2025", "GERENTE", "CRISTIANO JESUS"),
    ]

    credentials = {"usernames": {}}
    user_profiles = {}

    for username, nome, email, senha, perfil, escopo in usuarios:
        credentials["usernames"][username] = {
            "name":     nome,
            "email":    email,
            "password": hash_senha(senha),
        }
        user_profiles[username] = {
            "perfil": perfil,
            "escopo": escopo,
            "nome":   nome,
        }

    config = {
        "credentials": credentials,
        "cookie": {
            "expiry_days": 1,
            "key":         "madero_auditoria_secret_key_2025",
            "name":        "madero_auth_cookie",
        },
        "preauthorized": {"emails": []},
        "user_profiles": user_profiles,
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    print(f"\nConfig gerado em: {CONFIG_PATH}")
    print(f"Total de usuarios: {len(usuarios)}")
    print("\nUsuarios criados:")
    for u, n, e, s, p, _ in usuarios:
        print(f"  [{p:8}] Login: {u:15} | Senha inicial: {s} | {n}")
    print("\nATENCAO: Solicite que cada usuario troque sua senha no primeiro acesso!")

def adicionar_usuario():
    """Adiciona um novo usuário ao config existente."""
    if not os.path.exists(CONFIG_PATH):
        print("Config nao encontrado. Execute primeiro para criar o config inicial.")
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    username = input("Username (sem espacos): ").strip().lower()
    if username in config["credentials"]["usernames"]:
        print(f"Usuario '{username}' ja existe!")
        return

    nome   = input("Nome completo: ").strip()
    email  = input("Email: ").strip()
    senha  = input("Senha inicial: ").strip()
    perfil = input("Perfil (ADMIN/DIRETOR/GERENTE/GESTOR): ").strip().upper()
    escopo = input("Escopo (nome do diretor/geop/filial, ou deixe em branco para ADMIN): ").strip() or None

    config["credentials"]["usernames"][username] = {
        "name":     nome,
        "email":    email,
        "password": hash_senha(senha),
    }
    config["user_profiles"][username] = {
        "perfil": perfil,
        "escopo": escopo,
        "nome":   nome,
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    print(f"\nUsuario '{username}' adicionado com sucesso!")

if __name__ == "__main__":
    print("=" * 50)
    print("  GERENCIADOR DE USUARIOS — MADERO AUDITORIA")
    print("=" * 50)
    print("\n1. Criar/Recriar config inicial (todos os usuarios)")
    print("2. Adicionar novo usuario")
    opcao = input("\nEscolha (1 ou 2): ").strip()

    if opcao == "1":
        criar_config_inicial()
    elif opcao == "2":
        adicionar_usuario()
    else:
        print("Opcao invalida.")
