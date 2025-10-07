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
last_run = {}        # guarda timestamps/flags por tarefa
_last_wait_log = {}  # throttle para mensagens "Aguardando janela"

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
    try:
        return parse(v1) < parse(v2)
    except Exception:
        return False

def executar_process(path):
    """Executa o path. Para scripts (.bat/.cmd) usa shell=True."""
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext in (".bat", ".cmd", ".ps1"):
            # shell para arquivos de lote/PowerShell
            return subprocess.Popen(path, cwd=os.path.dirname(path), shell=True)
        else:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            return subprocess.Popen([path], cwd=os.path.dirname(path), creationflags=flags)
    except Exception as e:
        log(f"❌ Erro ao executar {path}: {e}")
        return None

def start_process_by_path(path):
    """Executa um arquivo pelo caminho completo, com log."""
    if os.path.exists(path):
        log(f"▶️ Iniciando: {path}")
        return executar_process(path)
    else:
        log(f"⚠️ Arquivo não encontrado: {path}")
        return None

def resolve_executable_path(exe_info):
    """
    Resolve o caminho completo do executável a partir do exe_info:
    - se 'local' for um arquivo absoluto (ex: C:\pasta\arquivo.bat) -> usa direto
    - se 'local' for uma pasta absoluta -> junta com nome
    - se 'local' for relativo -> junta com BASE_DIR
    - se 'local' ausente -> usa BASE_DIR\nome
    """
    nome = exe_info.get("nome")
    local = exe_info.get("local")

    if local:
        # se local for um caminho absoluto para um arquivo existente ou com extensão
        if os.path.isabs(local):
            # se é diretório
            if os.path.isdir(local):
                return os.path.join(local, nome)
            # se parece ser um arquivo (tem extensão) -> usa direto
            if os.path.splitext(local)[1]:
                return local
            # senão, junta
            return os.path.join(local, nome)
        else:
            # local não absoluto — junta com BASE_DIR (suporta tanto "subpasta" quanto "nome completo")
            if os.path.splitext(local)[1]:
                # se tiver extensão trata como arquivo relativo -> junta com base
                return os.path.join(BASE_DIR, local)
            # se for pasta relativa
            return os.path.join(BASE_DIR, local, nome)
    else:
        return os.path.join(BASE_DIR, nome)

# -----------------------------
# Lógicas fixas
# -----------------------------
def rodar_valida():
    """Executa o valida_bkp.exe"""
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
    """Executa o updater e roda o valida depois"""
    updater_path = os.path.join(BASE_DIR, "updater.exe")
    if os.path.exists(updater_path):
        log(f"🔄 Nova versão detectada: {versao_remota} (local: {versao_local})")
        proc = executar_process(updater_path)
        if proc:
            proc.wait()
            log("✅ Atualização concluída.")
            try:
                with open(VERSION_FILE, "w", encoding="utf-8") as f:
                    f.write(versao_remota)
            except Exception as e:
                log(f"❌ Falha ao gravar versao.txt: {e}")
            # Após atualizar, executa o valida
            rodar_valida()
    else:
        log(f"⚠️ updater.exe não encontrado em {updater_path}")

# -----------------------------
# Função de tolerância (5 minutos) com log throttle
# -----------------------------
def dentro_da_janela(horarios, tolerancia_min=5):
    """
    Retorna (True, horario_str) se achou um horário dentro da janela [horario, horario + tolerancia_min].
    Se horarios for string única ou lista.
    """
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
            inicio = alvo
            fim = alvo + timedelta(minutes=tolerancia_min)
            if inicio <= agora <= fim:
                return (True, horario_str)
            else:
                # log de "aguardando" com throttle: só a cada 60s por tarefa+horário
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

        # atualiza se precisa
        if comparar_versoes(versao_local, versao_remota):
            rodar_updater(config, versao_local, versao_remota)
        else:
            log(f"✔️ Sistema já está na versão atual ({versao_local})")

        agora = datetime.now()

        # --- Execução fixa diária do valida_bkp às 12:00 (janela 12:00–12:05) ---
        ok, horario_encontrado = dentro_da_janela("12:00")
        if ok:
            chave_valida = f"valida_{agora.strftime('%Y-%m-%d')}"
            if last_run.get(chave_valida) != True:
                rodar_valida()
                last_run[chave_valida] = True

        # --- Execuções personalizadas via config ---
        for exe_info in config.get("executar", []):
            nome = exe_info.get("nome")
            if not nome:
                continue
            if not exe_info.get("ativo", True):
                continue

            horario = exe_info.get("horario")      # pode ser str ou list ou None
            intervalo = exe_info.get("intervalo", 0)
            # resolve caminho final do executável (suporta pasta ou caminho absoluto)
            caminho_exe = resolve_executable_path(exe_info)

            # --- HORÁRIOS (janela) ---
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
                # se não estiver na janela, dentro_da_janela já emitiu "Aguardando" com throttle

            # --- INTERVALO (minutos) ---
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
