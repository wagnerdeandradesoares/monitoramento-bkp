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

def start_process(exe_name, custom_dir=None):
    """Executa um arquivo no diretório base ou no caminho customizado"""
    path = os.path.join(custom_dir or BASE_DIR, exe_name)
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
    updater_path = os.path.join(BASE_DIR, "updater.exe")
    if os.path.exists(updater_path):
        log(f"🔄 Nova versão detectada: {versao_remota} (local: {versao_local})")
        proc = executar(updater_path)
        if proc:
            proc.wait()
            log("✅ Atualização concluída.")
            with open(VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(versao_remota)
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

        agora = datetime.now()
        agora_str = agora.strftime("%H:%M")

        # Rodar valida às 12h (fixo)
        if agora_str == "12:00" and last_run.get("valida") != agora.date():
            rodar_valida()
            last_run["valida"] = agora.date()

        # Executáveis via config
        for exe_info in config.get("executar", []):
            nome = exe_info.get("nome")
            if not exe_info.get("ativo", True):
                continue

            local_exec = exe_info.get("local")  # novo campo customizado
            horario = exe_info.get("horario")
            intervalo = exe_info.get("intervalo", 0)

            # --- HORÁRIOS FIXOS ---
            if horario:
                try:
                    # permite lista ou único horário
                    horarios = horario if isinstance(horario, list) else [horario]
                    hora_atual, minuto_atual = agora.hour, agora.minute
                    minutos_atuais = hora_atual * 60 + minuto_atual

                    for h in horarios:
                        hora_cfg, min_cfg = map(int, h.split(":"))
                        minutos_cfg = hora_cfg * 60 + min_cfg
                        diff = minutos_atuais - minutos_cfg
                        chave_exec = f"{nome}_{h}"

                        # executa apenas se dentro de 5 min e não rodou ainda hoje
                        if 0 <= diff <= 5 and last_run.get(chave_exec) != agora.date():
                            proc = start_process(nome, local_exec)
                            if proc:
                                proc.wait()
                                log(f"✅ {nome} executado entre {h} e {hora_cfg:02d}:{(min_cfg+5)%60:02d}")
                            last_run[chave_exec] = agora.date()
                        elif diff < 0:
                            log(f"⏳ Aguardando janela de {h}–{hora_cfg:02d}:{(min_cfg+5)%60:02d} para {nome}")
                except Exception as e:
                    log(f"⚠️ Erro ao processar horários para {nome}: {e}")

            # --- INTERVALO EM MINUTOS ---
            elif intervalo > 0:
                ultima_exec = last_run.get(nome)
                if not ultima_exec or (time.time() - ultima_exec) >= intervalo * 60:
                    proc = start_process(nome, local_exec)
                    if proc:
                        proc.wait()
                        log(f"✅ {nome} rodou no intervalo de {intervalo} min")
                    last_run[nome] = time.time()

        time.sleep(CHECK_INTERVAL)
