import subprocess
import sys
import os
import json
import urllib.request
from datetime import datetime
import time

# -----------------------------
# Configurações
# -----------------------------
CONFIG_URL = "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config.json"
#URL de testes para produção: https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config.json
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"
# dirotório de testes para produção: C:\Program Files (x86)\MonitoramentoBKP
LOG_BASE_DIR = os.path.join(BASE_DIR, "logs")
VERSION_FILE = os.path.join(BASE_DIR, "versao.txt")
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
def baixar_config():
    try:
        with urllib.request.urlopen(CONFIG_URL, timeout=10) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except Exception as e:
        log(f"❌ Erro ao baixar config JSON: {e}")
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

def main():
    log("🚀 Iniciando processo de atualização")

    config = baixar_config()
    if not config:
        log("❌ Falha ao obter configuração remota. Abortando.")
        return

    versao_remota = config.get("versao", "0.0.0")
    log(f"🔎 Versão remota encontrada: {versao_remota}")

    for item in config.get("arquivos", []):
        nome = item.get("nome")
        url = item.get("url")
        destino_dir = item.get("destino", BASE_DIR)
        destino_path = os.path.join(destino_dir, nome)

        if not nome or not url:
            log("⚠️ Configuração de arquivo inválida (faltando nome ou url). Pulando...")
            continue

        log(f"⬇️ Atualizando '{nome}'")
        log(f"📁 Destino: {destino_path}")
        atualizar_software(destino_path, url, nome)

    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(versao_remota)
        log(f"💾 Versão local atualizada para {versao_remota}")
    except Exception as e:
        log(f"❌ Erro ao salvar versão local: {e}")

    log("🏁 Atualização concluída com sucesso!")

# -----------------------------
if __name__ == "__main__":
    main()
