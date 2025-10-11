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

# -----------------------------
# Execuções fixas
# -----------------------------
def rodar_valida():
    valida_path = os.path.join(BASE_DIR, "valida_bkp.exe")
    if os.path.exists(valida_path):
        log("▶️ Rodando valida_bkp.exe")
        proc = executar_process(valida_path)
        if proc:
            log("✅ valida_bkp concluído")
    else:
        log("⚠️ valida_bkp.exe não encontrado")

def rodar_updater():
    """Atualiza arquivos conforme config['arquivos'] respeitando 'local'"""
    log(f"🔄 Nova versão detectada: {versao_remota} (local: {versao_local})")

    updater_path = os.path.join(BASE_DIR, "updater.exe")
    if os.path.exists(updater_path):
        log("▶️ Rodando updater.exe")
        proc = executar_process(updater_path)
        if proc:
            proc.wait()
            log("✅ updater.exe concluído")
            rodar_valida()  # Executa valida_bkp após atualização
    else:
        log("⚠️ updater.exe não encontrado")

    

def start_process_by_path(path):
    """Verifica existência e executa o arquivo"""
    if os.path.exists(path):
        log(f"▶️ Iniciando: {path}")
        return executar_process(path)
    else:
        log(f"⚠️ Arquivo não encontrado: {path}")
        return None

def dentro_da_janela(horarios, tolerancia_min=5):
    """Verifica se o horário atual está dentro da janela"""
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
                log(f"✅ Dentro da janela de {horario_str}")
                return (True, horario_str)
            else:
                log(f"🕒 Fora da janela: {horario_str} (agora {agora.strftime('%H:%M')})")
        except Exception as e:
            log(f"⚠️ Horário inválido em config: {horario_str} ({e})")

    return (False, None)

def executar_process(path):
    """Executa arquivos .exe ou .bat mesmo em contexto de serviço."""
    try:
        if not os.path.exists(path):
            log(f"⚠️ Arquivo não encontrado: {path}")
            return None

        nome = os.path.basename(path)
        log(f"🚀 Executando {nome} via subprocess.Popen()...")

        # Executa em modo oculto e independente da sessão
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # sem janela
        subprocess.Popen(
            ["cmd.exe", "/c", path],
            cwd=os.path.dirname(path),
            startupinfo=si,
            shell=True
        )

        log(f"🟢 {nome} executado com sucesso (modo serviço).")
        return True
    except Exception as e:
        log(f"❌ Erro ao executar {path}: {e}")
        return None


def resolve_executable_path(exe_info):
    """Resolve o caminho absoluto do executável com base no config"""
    nome = exe_info.get("nome")
    local = exe_info.get("local")

    if not nome:
        log("⚠️ Nenhum nome de arquivo especificado no config.")
        return None

    if local:
        if os.path.isabs(local):
            caminho = os.path.join(local, nome) if os.path.isdir(local) else local
            log(f"🔍 Caminho absoluto resolvido: {caminho}")
            return caminho
        else:
            caminho = os.path.join(BASE_DIR, local, nome)
            log(f"🔍 Caminho relativo resolvido: {caminho}")
            return caminho

    caminho = os.path.join(BASE_DIR, nome)
    log(f"🔍 Caminho padrão resolvido: {caminho}")
    return caminho

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
            rodar_updater()
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
                        start_process_by_path(caminho_exe)
                        last_run[chave_hor] = True

            # Intervalo
            elif intervalo and intervalo > 0:
                chave_int = f"{nome}__interval"
                ultima = last_run.get(chave_int)
                now_ts = time.time()
                if not ultima or (now_ts - ultima) >= (intervalo * 60):
                    start_process_by_path(caminho_exe)
                    last_run[chave_int] = now_ts

        time.sleep(CHECK_INTERVAL)
