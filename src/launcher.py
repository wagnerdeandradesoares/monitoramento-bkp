import os
import subprocess
import time
import json
from datetime import datetime
import urllib.request

# -----------------------------
# Configurações
# -----------------------------
CONFIG_URL = "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config_atualizacao.json"  # URL para o arquivo de configuração remota
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"
CHECK_INTERVAL = 60  # intervalo em segundos
VERSION_FILE = os.path.join(BASE_DIR, "versao.txt")
LOG_FILE = os.path.join(BASE_DIR, "launcher.log")
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
def ler_versao_local():
    """Lê a versão local a partir do arquivo versao.txt"""
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "0.0.0"

def comparar_versoes(v1, v2):
    """Compara duas versões no formato x.y.z"""
    def parse(v): return [int(x) for x in v.strip().split(".")]
    return parse(v1) < parse(v2)

def executar(path):
    """Executa um arquivo no caminho especificado"""
    try:
        return subprocess.Popen([path], cwd=os.path.dirname(path), creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        log(f"❌ Erro ao executar {path}: {e}")
        return None

def rodar_valida():
    """Executa o valida_bkp.exe"""
    valida_path = os.path.join(BASE_DIR, "valida_bkp.exe")
    if os.path.exists(valida_path):
        log("▶️ Rodando valida_bkp.exe")
        proc = executar(valida_path)
        if proc:
            proc.wait()
            log("✅ valida_bkp concluído")
    else:
        log("⚠️ valida_bkp.exe não encontrado")

def rodar_updater(config, versao_local, versao_remota):
    """Verifica e executa o updater caso necessário"""
    download_necessario = config.get("download", False)

    # Verifica se a versão local é diferente da remota ou se o download é necessário
    if versao_local == versao_remota:
        # Se a versão for a mesma, verifica o campo "download"
        if download_necessario:
            log(f"Versão local ({versao_local}) já está atualizada, mas 'download' está habilitado. Chamando o updater para baixar os arquivos...")
            subprocess.Popen([os.path.join(BASE_DIR, "updater.exe")])
        else:
            log(f"✔️ A versão local já está atualizada e não há necessidade de download ({versao_local}).")
    else:
        # Se a versão local for diferente da remota, realiza a atualização
        log(f"🔄 Nova versão detectada: {versao_remota} (local: {versao_local})")
        subprocess.Popen([os.path.join(BASE_DIR, "updater.exe")])

def baixar_config():
    """Baixa o arquivo de configuração JSON"""
    try:
        with urllib.request.urlopen(CONFIG_URL, timeout=10) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except Exception as e:
        log(f"❌ Erro ao baixar config JSON: {e}")
    return None

# -----------------------------
# Loop principal
# -----------------------------
if __name__ == "__main__":
    log("🚀 Launcher iniciado")
    while True:
        # Baixando a configuração remotamente
        config = baixar_config()
        if not config:
            log("❌ Erro ao carregar arquivo de configuração remoto")
            time.sleep(CHECK_INTERVAL)
            continue

        versao_remota = config.get("versao", "0.0.0")
        versao_local = ler_versao_local()

        # Atualização do launcher (compara versões e verifica download)
        rodar_updater(config, versao_local, versao_remota)

        time.sleep(CHECK_INTERVAL)
