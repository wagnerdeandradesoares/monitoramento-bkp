import os
import subprocess
import json
from datetime import datetime
import urllib.request
import shutil

# -----------------------------
# Configurações
# -----------------------------
CONFIG_URL = "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config_atualizacao.json"
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"
VERSION_FILE = os.path.join(BASE_DIR, "versao.txt")
LOG_FILE = os.path.join(BASE_DIR, "updater.log")
MAX_LOG_LINES = 100  # mantém apenas as últimas 100 linhas do log

# -----------------------------
# Funções de log
# -----------------------------
def log(msg):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    line = f"[{now}] {msg}\n"

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = []

    lines.append(line)
    if len(lines) > MAX_LOG_LINES:
        lines = lines[-MAX_LOG_LINES:]

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(line.strip())

# -----------------------------
# Funções utilitárias
# -----------------------------
def baixar_config():
    """Baixa o arquivo de configuração JSON"""
    try:
        with urllib.request.urlopen(CONFIG_URL, timeout=10) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except Exception as e:
        log(f"❌ Erro ao baixar config JSON: {e}")
    return None

def ler_versao_local():
    """Lê a versão local a partir do arquivo versao.txt"""
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "0.0.0"

def baixar_arquivos(config):
    """Baixa os arquivos necessários do repositório remoto"""
    try:
        for file_info in config.get("arquivos", []):
            file_url = file_info.get("url")
            destino = file_info.get("destino")
            if file_url and destino:
                file_path = os.path.join(destino, file_info.get("nome"))
                log(f"🔄 Baixando arquivo {file_path} de {file_url} para o destino {destino}")
                with urllib.request.urlopen(file_url) as response:
                    with open(file_path, "wb") as f:
                        shutil.copyfileobj(response, f)
                log(f"✅ Arquivo baixado: {file_path}")
    except Exception as e:
        log(f"❌ Erro ao baixar arquivos: {e}")

def rodar_updater(config):
    """Baixa os arquivos e atualiza a versão local"""
    log(f"🔄 Iniciando o processo de atualização...")
    
    # Baixa os arquivos necessários
    baixar_arquivos(config)
    log("✅ Arquivos baixados com sucesso.")
    
    # Atualizar a versão local com a versão remota
    versao_remota = config.get("versao", "0.0.0")
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(versao_remota)
    log(f"✅ Atualização concluída. Versão local atualizada para {versao_remota}.")

# -----------------------------
# Execução principal
# -----------------------------
if __name__ == "__main__":
    log("🚀 Updater iniciado")

    # Baixa a configuração
    config = baixar_config()
    if config:
        # Chama o updater para baixar os arquivos e atualizar
        rodar_updater(config)
    else:
        log("❌ Não foi possível carregar a configuração!")

    # O programa termina após a execução do updater.
