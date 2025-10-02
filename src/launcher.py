import subprocess
import time
import os
import urllib.request
import json
from datetime import datetime

# -----------------------------
# Configurações
# -----------------------------
CONFIG_URL = "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config_atualizacao.json"
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"
CHECK_INTERVAL = 60  # intervalo em segundos
VERSION_FILE = os.path.join(BASE_DIR, "versao.txt")
LOG_FILE = os.path.join(BASE_DIR, "launcher.log")
MAX_LOG_LINES = 100  # mantém apenas as últimas 100 linhas do log

processes = {}
last_run = {}

# -----------------------------
# Funções de log
# -----------------------------
def log(msg):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    line = f"[{now}] {msg}\n"

    # Lê linhas antigas
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = []

    # Adiciona nova linha
    lines.append(line)

    # Mantém apenas as últimas MAX_LOG_LINES
    if len(lines) > MAX_LOG_LINES:
        lines = lines[-MAX_LOG_LINES:]

    # Escreve de volta
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(line.strip())

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

def ler_versao_local():
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "0.0.0"

def comparar_versoes(v1, v2):
    def parse(v): return [int(x) for x in v.strip().split(".")]
    return parse(v1) < parse(v2)

def executar(path):
    try:
        return subprocess.Popen([path], cwd=os.path.dirname(path), creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        log(f"❌ Erro ao executar {path}: {e}")
        return None

def start_process(exe_name):
    path = os.path.join(BASE_DIR, exe_name)
    if os.path.exists(path):
        log(f"▶️ Iniciando: {exe_name}")
        return executar(path)
    else:
        log(f"⚠️ Arquivo não encontrado: {path}")
        return None

# -----------------------------
# Lógicas fixas
# -----------------------------
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
    """Executa o updater e, se atualizar, roda o valida depois"""
    updater_path = os.path.join(BASE_DIR, "updater.exe")
    if os.path.exists(updater_path):
        log(f"🔄 Nova versão detectada: {versao_remota} (local: {versao_local})")
        proc = executar(updater_path)
        if proc:
            proc.wait()
            log("✅ Atualização concluída.")
            # Atualiza arquivo de versão local
            with open(VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(versao_remota)
            # Sempre roda o valida após atualizar
            rodar_valida()
    else:
        log(f"⚠️ updater.exe não encontrado em {updater_path}")

# -----------------------------
# Loop principal
# -----------------------------
if __name__ == "__main__":
    log("🚀 Launcher iniciado")
    while True:
        config = baixar_config()
        if not config:
            time.sleep(CHECK_INTERVAL)
            continue

        versao_remota = config.get("versao", "0.0.0")
        versao_local = ler_versao_local()

        # Atualização do updater
        if comparar_versoes(versao_local, versao_remota):
            rodar_updater(config, versao_local, versao_remota)
        else:
            log(f"✔️ Sistema já está na versão atual ({versao_local})")

        # Rodar valida às 12h
        agora_str = datetime.now().strftime("%H:%M")
        if agora_str == "12:00" and last_run.get("valida") != agora_str:
            rodar_valida()
            last_run["valida"] = agora_str

        # Executáveis futuros via config
        for exe_info in config.get("executar", []):
            nome = exe_info.get("nome")
            if not exe_info.get("ativo", True):
                continue

            horario = exe_info.get("horario")
            intervalo = exe_info.get("intervalo", 0)
            agora = datetime.now()

            # Horário fixo
            if horario:
                if agora.strftime("%H:%M") == horario and last_run.get(nome) != horario:
                    proc = start_process(nome)
                    if proc:
                        proc.wait()
                        log(f"✅ {nome} rodou no horário {horario}")
                    last_run[nome] = horario

            # Intervalo em minutos
            elif intervalo > 0:
                ultima_exec = last_run.get(nome)
                if not ultima_exec or (time.time() - ultima_exec) >= intervalo * 60:
                    proc = start_process(nome)
                    if proc:
                        proc.wait()
                        log(f"✅ {nome} rodou no intervalo de {intervalo} min")
                    last_run[nome] = time.time()

        time.sleep(CHECK_INTERVAL)
