import subprocess
import time
import os
import urllib.request
import json
import random
from datetime import datetime, timedelta

# -----------------------------
# Configurações
# -----------------------------
CONFIG_URL = "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config.json"
#URL de testes para produção: https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config.json
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP" 
# dirotório de testes para produção: C:\Program Files (x86)\MonitoramentoBKP

CHECK_INTERVAL = 60  # intervalo em segundos
VERSION_FILE = os.path.join(BASE_DIR, "versao.config")
LOG_BASE_DIR = os.path.join(BASE_DIR, "logs")
MAX_LOG_LINES = 100  # mantém apenas as últimas 100 linhas do log

processes = {}
last_run = {}
_last_wait_log = {}

# -----------------------------
# Função de log
# -----------------------------
def garantir_diretorio_logs():
    if not os.path.exists(LOG_BASE_DIR):
        try:
            os.makedirs(LOG_BASE_DIR, exist_ok=True)
            print(f"✅ Pasta de logs criada: {LOG_BASE_DIR}")
        except Exception as e:
            print(f"❌ Erro ao criar a pasta de logs: {e}")
            raise

def log(msg):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    line = f"[{now}] {msg}\n"
    garantir_diretorio_logs()
    LOG_FILE = os.path.join(LOG_BASE_DIR, "launcher.log")

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
    """Baixa o config remoto forçando atualização (evita cache do GitHub)"""
    try:
        # Adiciona um parâmetro aleatório à URL para burlar cache da CDN do GitHub
        url = f"{CONFIG_URL}?nocache={random.randint(1000, 999999)}"
        log(f"🌐 Baixando config atualizado: {url}")

        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                log("✅ Config baixado e carregado com sucesso")
                return data
            else:
                log(f"⚠️ Resposta HTTP inesperada: {response.status}")
    except Exception as e:
        log(f"❌ Erro ao baixar config JSON: {e}")
    return None

def ler_versao_local():
    """Lê a versão e o tipo do arquivo versao.config (JSON)."""
    try:
        versao_file = os.path.join(BASE_DIR, "versao.config")

        if not os.path.exists(versao_file):
            log("⚠️ versao.config não encontrado. Criando arquivo padrão.")
            with open(versao_file, "w", encoding="utf-8") as f:
                json.dump({"versao": "0.0.0", "tipo": "CX1"}, f, indent=4)
            return "0.0.0", "CX1"

        with open(versao_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        versao = data.get("versao", "0.0.0").strip()
        tipo = data.get("tipo", "CX1").strip().upper()
        return versao, tipo

    except Exception as e:
        log(f"❌ Erro ao ler versao.config: {e}")
        return "0.0.0", "CX1"


def comparar_versoes(v1, v2):
    try:
        return [int(x) for x in v1.split(".")] < [int(x) for x in v2.split(".")]
    except:
        return False

def baixar_arquivo(url, destino):
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
            proc.wait()
            log("✅ valida_bkp concluído")
    else:
        log("⚠️ valida_bkp.exe não encontrado")

def rodar_updater():
    log(f"🔄 Nova versão detectada: {versao_remota} (local: {versao_local})")
    updater_path = os.path.join(BASE_DIR, "updater.exe")
    if os.path.exists(updater_path):
        log("▶️ Rodando updater.exe")
        proc = executar_process(updater_path)
        if proc:
            proc.wait()
            log("✅ updater.exe concluído")
            rodar_valida()
    else:
        log("⚠️ updater.exe não encontrado")

def start_process_by_path(path):
    if os.path.exists(path):
        log(f"▶️ Iniciando: {path}")
        return executar_process(path)
    else:
        log(f"⚠️ Arquivo não encontrado: {path}")
        return None

def dentro_da_janela(horarios, tolerancia_min=5):
    agora = datetime.now()

    # Garantir que 'horarios' seja uma lista ou string
    if isinstance(horarios, str):
        horarios = [horarios]  # Se for uma string, converte para lista com 1 item
    elif not isinstance(horarios, list):
        log(f"⚠️ 'horarios' deve ser uma lista ou string, mas recebeu {type(horarios)}.")
        return (False, None)

    # Verificação do horário
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
    try:
        if not os.path.exists(path):
            log(f"⚠️ Arquivo não encontrado: {path}")
            return None

        nome = os.path.basename(path)
        log(f"🚀 Executando {nome} via subprocess.Popen()...")

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(
            ["cmd.exe", "/c", path],
            cwd=os.path.dirname(path),
            startupinfo=si,
            shell=True
        )

        return proc
    except Exception as e:
        log(f"❌ Erro ao executar {path}: {e}")
        return None

def resolve_executable_path(exe_info):
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
        versao_local, tipo_terminal = ler_versao_local()
        log(f"💻 Tipo deste terminal: {tipo_terminal}")

        if comparar_versoes(versao_local, versao_remota):
            rodar_updater()
        else:
            log(f"✔️ Sistema já está na versão atual ({versao_local})")

        agora = datetime.now()

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

            tipos_permitidos = [t.upper() for t in exe_info.get("terminal", [])]
            if tipos_permitidos and tipo_terminal not in tipos_permitidos:
                log(f"💡 Execução '{nome}' ignorada — permitida apenas para {tipos_permitidos}.")
                continue

            horario = exe_info.get("horario")
            intervalo = exe_info.get("intervalo", 0)
            caminho_exe = resolve_executable_path(exe_info)

        # Verificando se 'horario' é fornecido (uma string ou lista de strings)
            if horario:
                # Agora o 'horario' deve ser uma string ou uma lista
                dentro, horario_str = dentro_da_janela(horario)  # Passando o 'horario' diretamente
                if dentro and horario_str:
                    chave_hor = f"valida_{agora.strftime('%Y-%m-%d')}__{horario_str}"
                    if not last_run.get(chave_hor):
                        start_process_by_path(caminho_exe)
                        last_run[chave_hor] = True

            # Verificando se 'intervalo' é fornecido e maior que 0
            elif intervalo and intervalo > 0:
                chave_int = f"{nome}__interval"
                ultima = last_run.get(chave_int)
                now_ts = time.time()
                if not ultima or (now_ts - ultima) >= (intervalo * 60):
                    start_process_by_path(caminho_exe)
                    last_run[chave_int] = now_ts

        time.sleep(CHECK_INTERVAL)
