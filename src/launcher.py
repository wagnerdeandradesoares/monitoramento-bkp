import subprocess
import time
import os
import urllib.request
import json
from datetime import datetime, timedelta

# -----------------------------
# Configurações
# -----------------------------
CONFIG_URL = "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config.json"
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"
CHECK_INTERVAL = 60  # intervalo em segundos
VERSION_FILE = os.path.join(BASE_DIR, "versao.txt")
LOG_FILE = os.path.join(BASE_DIR, "launcher.log")
MAX_LOG_LINES = 100  # mantém apenas as últimas 100 linhas do log

processes = {}
last_run = {}
_last_wait_log = {}

# -----------------------------
# Funções de log
# -----------------------------
def log(msg):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    line = f"[{now}] {msg}\n"
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

# -----------------------------
# Utilitários
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
    try:
        return [int(x) for x in v1.split(".")] < [int(x) for x in v2.split(".")]
    except:
        return False

def baixar_arquivo(url, destino):
    """Baixa um arquivo para o destino especificado."""
    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        urllib.request.urlretrieve(url, destino)
        log(f"⬇️ Arquivo baixado: {destino}")
        return True
    except Exception as e:
        log(f"❌ Erro ao baixar {url}: {e}")
        return False

def executar_process(path):
    """Executa arquivos .exe, .bat, .cmd e .ps1"""
    try:
        ext = os.path.splitext(path)[1].lower()
        logs_dir = os.path.join(BASE_DIR, "bat_logs")
        os.makedirs(logs_dir, exist_ok=True)

        if ext in (".bat", ".cmd"):
            log_path = os.path.join(logs_dir, f"{os.path.basename(path)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            cmd = ['cmd.exe', '/c', f'"{path}" > "{log_path}" 2>&1']
            proc = subprocess.Popen(cmd, cwd=os.path.dirname(path))
            log(f"🟢 BAT iniciado: {path} (log: {log_path})")
            return proc

        elif ext == ".ps1":
            log_path = os.path.join(logs_dir, f"{os.path.basename(path)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            cmd_line = f'powershell -ExecutionPolicy Bypass -File "{path}" > "{log_path}" 2>&1'
            proc = subprocess.Popen(["cmd.exe", "/c", cmd_line], cwd=os.path.dirname(path))
            log(f"🟢 PS1 iniciado: {path} (log: {log_path})")
            return proc

        else:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.Popen([path], cwd=os.path.dirname(path), creationflags=flags)
            log(f"🟢 EXE iniciado: {path}")
            return proc
    except Exception as e:
        log(f"❌ Erro ao executar {path}: {e}")
        return None

def start_process_by_path(path):
    if os.path.exists(path):
        log(f"▶️ Iniciando: {path}")
        return executar_process(path)
    else:
        log(f"⚠️ Arquivo não encontrado: {path}")
        return None

def resolve_executable_path(exe_info):
    nome = exe_info.get("nome")
    local = exe_info.get("local")
    if local:
        if os.path.isabs(local):
            if os.path.isdir(local):
                return os.path.join(local, nome)
            if os.path.splitext(local)[1]:
                return local
            return os.path.join(local, nome)
        else:
            if os.path.splitext(local)[1]:
                return os.path.join(BASE_DIR, local)
            return os.path.join(BASE_DIR, local, nome)
    return os.path.join(BASE_DIR, nome)

# -----------------------------
# Execuções fixas
# -----------------------------
def rodar_valida():
    valida_path = os.path.join(BASE_DIR, "valida_bkp.exe")
    if os.path.exists(valida_path):
        log("▶️ Rodando valida_bkp.exe")
        proc = executar_process(valida_path)
        if proc:
            proc.wait()
            log("✅ valida_bkp concluído")
    else:
        log("⚠️ valida_bkp.exe não encontrado")

def rodar_updater(config, versao_local, versao_remota):
    """Atualiza arquivos conforme config['arquivos'] respeitando 'local'"""
    log(f"🔄 Nova versão detectada: {versao_remota} (local: {versao_local})")

    for arq in config.get("arquivos", []):
        nome = arq.get("nome")
        url = arq.get("url")
        local = arq.get("local")
        if not nome or not url:
            continue

        if local:
            if os.path.isabs(local):
                destino = local if os.path.splitext(local)[1] else os.path.join(local, nome)
            else:
                destino = os.path.join(BASE_DIR, local, nome)
        else:
            destino = os.path.join(BASE_DIR, nome)

        if baixar_arquivo(url, destino):
            log(f"✅ {nome} atualizado em {destino}")

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(versao_remota)

    rodar_valida()

# -----------------------------
# Função de janela (5 min)
# -----------------------------
def dentro_da_janela(horarios, tolerancia_min=5):
    agora = datetime.now()
    if horarios is None:
        return (False, None)
    if isinstance(horarios, str):
        horarios = [horarios]

    for horario_str in horarios:
        if not horario_str:
            continue
        try:
            alvo = datetime.strptime(horario_str, "%H:%M").replace(
                year=agora.year, month=agora.month, day=agora.day
            )
            fim = alvo + timedelta(minutes=tolerancia_min)
            if alvo <= agora <= fim:
                return (True, horario_str)
            chave_wait = f"wait_{horario_str}"
            ultima = _last_wait_log.get(chave_wait, 0)
            if time.time() - ultima >= 60:
                _last_wait_log[chave_wait] = time.time()
                log(f"⏳ Aguardando horário {horario_str}–{fim.strftime('%H:%M')}...")
        except Exception as e:
            log(f"⚠️ Horário inválido em config: {horario_str} ({e})")
    return (False, None)

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

        if comparar_versoes(versao_local, versao_remota):
            rodar_updater(config, versao_local, versao_remota)
        else:
            log(f"✔️ Sistema já está na versão atual ({versao_local})")

        agora = datetime.now()

        # --- Execução fixa diária do valida_bkp às 12:00 (janela 12:00–12:05) ---
        ok, horario_encontrado = dentro_da_janela("12:00")
        if ok:
            chave_valida = f"valida_{agora.strftime('%Y-%m-%d')}"
            if not last_run.get(chave_valida):
                rodar_valida()
                last_run[chave_valida] = True

        # --- Execuções personalizadas via config ---
        for exe_info in config.get("executar", []):
            nome = exe_info.get("nome")
            if not nome or not exe_info.get("ativo", True):
                continue

            horario = exe_info.get("horario")
            intervalo = exe_info.get("intervalo", 0)
            caminho_exe = resolve_executable_path(exe_info)

            # Horário fixo
            if horario:
                dentro, horario_str = dentro_da_janela(horario)
                if dentro and horario_str:
                    chave_hor = f"{nome}__hor__{horario_str}__{agora.strftime('%Y-%m-%d')}"
                    if not last_run.get(chave_hor):
                        proc = start_process_by_path(caminho_exe)
                        if proc:
                            proc.wait()
                            log(f"✅ {nome} executado na janela {horario_str} (+5min)")
                        last_run[chave_hor] = True

            # Intervalo
            elif intervalo and intervalo > 0:
                chave_int = f"{nome}__interval"
                ultima = last_run.get(chave_int)
                now_ts = time.time()
                if not ultima or (now_ts - ultima) >= (intervalo * 60):
                    proc = start_process_by_path(caminho_exe)
                    if proc:
                        proc.wait()
                        log(f"✅ {nome} executou por intervalo ({intervalo} min)")
                    last_run[chave_int] = now_ts

        time.sleep(CHECK_INTERVAL)
