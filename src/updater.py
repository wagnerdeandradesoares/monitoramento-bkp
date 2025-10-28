import subprocess
import sys
import os
import json
import random
import urllib.request
from datetime import datetime
import time

# -----------------------------
# Configurações
# -----------------------------
CONFIG_URL = "https://github.com/wagnerdeandradesoares/monitoramento-bkp/releases/download/v1.0.2/config.json"
#URL de testes para produção: https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config.json
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"
# dirotório de testes para produção: C:\Program Files (x86)\MonitoramentoBKP
LOG_BASE_DIR = os.path.join(BASE_DIR, "logs")
VERSION_FILE = os.path.join(BASE_DIR, "versao.config")
MAX_LOG_LINES = 100


# Funções de log
def log(msg):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    line = f"[{now}] {msg}\n"
    garantir_diretorio_logs()

    LOG_FILE = os.path.join(LOG_BASE_DIR, "updater.log")  # Pode mudar o nome conforme necessário

    lines = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    lines.append(line)
    if len(lines) > MAX_LOG_LINES:
        lines = lines[-MAX_LOG_LINES:]

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(line.strip())

def garantir_diretorio_logs():
    if not os.path.exists(LOG_BASE_DIR):
        try:
            os.makedirs(LOG_BASE_DIR, exist_ok=True)
            print(f"✅ Pasta de logs criada: {LOG_BASE_DIR}")
        except Exception as e:
            print(f"❌ Erro ao criar a pasta de logs: {e}")
            raise

# Função para executar comandos como administrador
def run_as_admin(command):
    """Executa um comando como administrador."""
    if sys.platform == "win32":
        script = os.path.abspath(sys.argv[0])  # Obtém o caminho do script atual
        command = f'python "{script}" {command}'  # Comando a ser executado

        # Uso do runas para executar com privilégios elevados
        subprocess.run(['runas', '/user:Administrator', command], check=True)

# -----------------------------
# Funções de controle de serviço
# -----------------------------
def parar_servico():
    log("🛑 Parando o serviço BaseService...")
    try:
        # Executa o comando como administrador para parar o serviço
        subprocess.run(["sc", "stop", "BaseService"], check=True)
        time.sleep(5)  # Aguarda alguns segundos para garantir que o serviço foi realmente parado
        log("✔️ Serviço BaseService parado com sucesso.")
    except subprocess.CalledProcessError as e:
        log(f"⚠️ Erro ao parar o serviço BaseService: {e}")
        return False
    return True

def iniciar_servico():
    log("🚀 Iniciando o serviço BaseService...")
    try:
        # Executa o comando como administrador para iniciar o serviço
        subprocess.run(["sc", "start", "BaseService"], check=True)
        log("✔️ Serviço BaseService iniciado com sucesso.")
    except subprocess.CalledProcessError as e:
        log(f"⚠️ Erro ao iniciar o serviço BaseService: {e}")
        return False
    return True

# -----------------------------
# Funções utilitárias
# -----------------------------
def baixar_config_forcado():
    """Baixa config forçando evitar cache (adiciona query string aleatória)."""
    try:
        url = f"{CONFIG_URL}?nocache={random.randint(1000,999999)}"
        log(f"🌐 Baixando config (forçado): {url}")
        with urllib.request.urlopen(url, timeout=15) as resp:
            content = resp.read().decode()
            cfg = json.loads(content)
            log(f"✅ Config carregado. Versão remota no config: {cfg.get('versao')}")
            return cfg
    except Exception as e:
        log(f"❌ Falha ao baixar config: {e}")
        return None

def baixar_arquivo(url, destino):
    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        urllib.request.urlretrieve(url, destino)
        log(f"📦 Arquivo atualizado com sucesso: {destino}")
        return True
    except Exception as e:
        log(f"❌ Erro ao baixar {url}: {e}")
        return False

# -----------------------------
# Lógica principal
# -----------------------------
def atualizar_software(caminho_destino, arquivo_url, nome_arquivo):
    """
    Atualiza o arquivo apenas se o nome do arquivo for 'launcher.exe', 
    caso contrário, realiza a atualização sem parar o serviço.
    """
    if nome_arquivo.lower() == "launcher.exe":
        # Se for launcher.exe, para o serviço antes de atualizar
        if parar_servico():
            if substituir_arquivo(caminho_destino, arquivo_url):
                iniciar_servico()
    else:
        # Caso contrário, apenas substitui o arquivo sem parar o serviço
        if substituir_arquivo(caminho_destino, arquivo_url):
            log(f"✅ Atualização do {nome_arquivo} concluída sem parar o serviço.")

def substituir_arquivo(caminho_destino, arquivo_url):
    log("🔄 Iniciando atualização...")

    try:
        urllib.request.urlretrieve(arquivo_url, caminho_destino)
        log(f"📦 Arquivo atualizado com sucesso: {caminho_destino}")
        return True
    except Exception as e:
        log(f"❌ Erro ao baixar {arquivo_url}: {e}")
        return False
    
# -----------------------------
# Controle de versão local
# -----------------------------
def ler_versao_local_dict():
    """Lê o versao.config completo e retorna um dicionário."""
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                versao = str(dados.get("versao", "0.0.0")).strip()
                log(f"🔍 Versão local lida: {versao}")
                return dados  # retorna tudo, não só a versão
        except Exception as e:
            log(f"⚠️ Erro ao ler {VERSION_FILE}: {e} — recriando padrão")
    # cria arquivo padrão se não existir
    dados_padrao = {"versao": "0.0.0", "tipo": "CX1"}
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(dados_padrao, f, indent=2, ensure_ascii=False)
        log(f"♻️ Criado {VERSION_FILE} padrão: {dados_padrao}")
    except Exception as e:
        log(f"⚠️ Falha ao criar {VERSION_FILE}: {e}")
    return dados_padrao


def gravar_versao_local(versao_nova):
    """
    Atualiza apenas a chave 'versao' mantendo todas as outras existentes.
    Se o arquivo não existir, cria um novo com versão padrão.
    """
    try:
        # Lê o conteúdo existente (ou cria base vazia)
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
        else:
            dados = {}

        versao_antiga = dados.get("versao", "0.0.0")
        dados["versao"] = versao_nova.strip()

        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)

        log(f"💾 Versão atualizada: {versao_antiga} → {versao_nova}")
        return True
    except Exception as e:
        log(f"❌ Erro ao atualizar versão no {VERSION_FILE}: {e}")
        return False

    
def atualizar_item(item):
    """Atualiza um item do config: {nome, url, destino(optional)}"""
    nome = item.get("nome")
    url = item.get("url")
    destino_dir = item.get("destino", BASE_DIR)
    if not nome or not url:
        log("⚠️ Item inválido (sem nome ou URL). Pulando.")
        return False
    if os.path.isabs(destino_dir):
        destino = destino_dir if os.path.splitext(destino_dir)[1] else os.path.join(destino_dir, nome)
    else:
        destino = os.path.join(BASE_DIR, destino_dir, nome)
    log(f"📦 Atualizando item '{nome}' para {destino}")
      # Se for o launcher e existe serviço, parar antes (nome exato)
    if nome.lower() == "launcher.exe":
        if not parar_servico():
            log("⚠️ Não foi possível parar BaseService. Continuando tentativa de atualização.")
    ok = substituir_arquivo(destino, url)
    if not ok:
        log(f"❌ Falha ao atualizar {nome}")
        return False
    # se atualizou launcher, reinicia serviço
    if nome.lower() == "launcher.exe":
        iniciar_servico()
    return True

############################ Fluxo principal do updater ############################

def main():
    log("🚀 Iniciando processo de atualização")

    cfg = baixar_config_forcado()
    if not cfg:
        log("❌ Não foi possível baixar o config. Abortando.")
        return

    versao_remota = str(cfg.get("versao", "0.0.0")).strip()
    log(f"🔎 Versão remota (config): {versao_remota}")

    local = ler_versao_local_dict()
    versao_local = str(local.get("versao", "0.0.0")).strip()
    tipo_local = str(local.get("tipo", "CX1")).strip().upper()
        

 # Atualiza arquivos listados
    arquivos = cfg.get("arquivos", [])
    any_updated = False
    for item in arquivos:
        nome = item.get("nome")
        log(f"— processando item do config: {nome}")
        ok = atualizar_item(item)
        any_updated = any_updated or ok
        # sleeping curto para não sobrecarregar rede/IO em ambientes lentos
        time.sleep(0.2)

    # Se houve atualização de arquivos, ou versão remota diferente, grava versao.config
    if any_updated or versao_local != versao_remota:
        success = gravar_versao_local(versao_remota)
        if success:
            log(f"✅ Versão local atualizada para {versao_remota}")
        else:
            log("⚠️ Não foi possível gravar versão local.")
    else:
        log("ℹ️ Nada mudou (arquivos não alterados e versão igual).")


    log("🏁 Updater finalizado")


# -----------------------------
if __name__ == "__main__":
    main()
