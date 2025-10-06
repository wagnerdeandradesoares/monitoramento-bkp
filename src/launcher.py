import subprocess
import time
import os
import urllib.request
import json
from datetime import datetime, timedelta

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

def start_process(exe_name, custom_local=None):
    path = os.path.join(custom_local or BASE_DIR, exe_name)
    if os.path.exists(path):
        log(f"▶️ Iniciando: {path}")
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
    """Executa o updater e roda o valida depois"""
    updater_path = os.path.join(BASE_DIR, "updater.exe")
    if os.path.exists(updater_path):
        log(f"🔄 Nova versão detectada: {versao_remota} (local: {versao_local})")
        proc = executar(updater_path)
        if proc:
            proc.wait()
            log("✅ Atualização concluída.")
            with open(VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(versao_remota)
            # Após atualizar, executa o valida
            rodar_valida()
    else:
        log(f"⚠️ updater.exe não encontrado em {updater_path}")

# -----------------------------
# Função de tolerância (5 minutos)
# -----------------------------
def dentro_da_tolerancia(horarios, tolerancia_min=5):
    agora = datetime.now()
    if isinstance(horarios, str):
        horarios = [horarios]

    for horario_str in horarios:
        try:
            alvo = datetime.strptime(horario_str, "%H:%M").replace(
                year=agora.year, month=agora.month, day=agora.day
            )
            inicio = alvo
            fim = alvo + timedelta(minutes=tolerancia_min)
            if inicio <= agora <= fim:
                return True
            else:
                hora_fim = fim.strftime("%H:%M")
                log(f"⏳ Aguardando horário {horario_str}–{hora_fim}...")
        except Exception as e:
            log(f"⚠️ Horário inválido em config: {horario_str} ({e})")
    return False

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

        # Atualização automática
        if comparar_versoes(versao_local, versao_remota):
            rodar_updater(config, versao_local, versao_remota)
        else:
            log(f"✔️ Sistema já está na versão atual ({versao_local})")

        agora = datetime.now()

        # --- Execução fixa diária do valida_bkp às 12:00 (uma vez por dia) ---
        if dentro_da_tolerancia("12:00") and last_run.get("valida") != agora.strftime("%d/%m"):
            rodar_valida()
            last_run["valida"] = agora.strftime("%d/%m")

        # --- Execuções personalizadas via config ---
        for exe_info in config.get("executar", []):
            nome = exe_info.get("nome")
            if not exe_info.get("ativo", True):
                continue

            horario = exe_info.get("horario")
            intervalo = exe_info.get("intervalo", 0)
            local = exe_info.get("local", BASE_DIR)

            # Execução por horário (com tolerância de 5 min)
            if horario:
                if dentro_da_tolerancia(horario) and last_run.get(nome) != agora.strftime("%d/%m %H"):
                    proc = start_process(nome, custom_local=local)
                    if proc:
                        proc.wait()
                        log(f"✅ {nome} rodou próximo do horário definido ({horario})")
                    last_run[nome] = agora.strftime("%d/%m %H")

            # Execução por intervalo
            elif intervalo > 0:
                ultima_exec = last_run.get(nome)
                if not ultima_exec or (time.time() - ultima_exec) >= intervalo * 60:
                    proc = start_process(nome, custom_local=local)
                    if proc:
                        proc.wait()
                        log(f"✅ {nome} rodou no intervalo de {intervalo} min")
                    last_run[nome] = time.time()

        time.sleep(CHECK_INTERVAL)
