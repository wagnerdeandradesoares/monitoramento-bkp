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
CONFIG_URL = "https://github.com/wagnerdeandradesoares/monitoramento-bkp/releases/download/v1.0.2/config.json"
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"
CHECK_INTERVAL = 60  # segundos
VERSION_FILE = os.path.join(BASE_DIR, "versao.config")
LOG_BASE_DIR = os.path.join(BASE_DIR, "logs")
MAX_LOG_LINES = 100

last_run = {}

# -----------------------------
# Log
# -----------------------------
def garantir_diretorio_logs():
    if not os.path.exists(LOG_BASE_DIR):
        os.makedirs(LOG_BASE_DIR, exist_ok=True)

def log(msg):
    garantir_diretorio_logs()
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    linha = f"[{now}] {msg}\n"
    LOG_FILE = os.path.join(LOG_BASE_DIR, "launcher.log")

    linhas = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            linhas = f.readlines()

    linhas.append(linha)
    if len(linhas) > MAX_LOG_LINES:
        linhas = linhas[-MAX_LOG_LINES:]

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(linhas)
    print(linha.strip())

# -----------------------------
# Utilitários
# -----------------------------
def baixar_config():
    try:
        url = f"{CONFIG_URL}?nocache={random.randint(1000,999999)}"
        log(f"🌐 Baixando config remoto: {url}")
        with urllib.request.urlopen(url, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                log("✅ Config.json carregado com sucesso")

                # salva localmente como cache
                with open(os.path.join(BASE_DIR, "config_cache.json"), "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                return data
    except Exception as e:
        log(f"⚠️ Falha ao baixar config: {e}")

        # tenta ler cache local
        cache_path = os.path.join(BASE_DIR, "config_cache.json")
        if os.path.exists(cache_path):
            log("📦 Usando config_cache.json local (fallback).")
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
    return None

def ler_versao_local():
    try:
        if not os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "w", encoding="utf-8") as f:
                json.dump({"versao": "0.0.0", "tipo": "CX1"}, f)
            return "0.0.0", "CX1"
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("versao", "0.0.0"), data.get("tipo", "CX1").upper()
    except Exception as e:
        log(f"⚠️ Erro ao ler versao.config: {e}")
        return "0.0.0", "CX1"

def comparar_versoes(v1, v2):
    try:
        return [int(x) for x in v1.split(".")] < [int(x) for x in v2.split(".")]
    except:
        return False

def executar_process(path):
    try:
        if not os.path.exists(path):
            log(f"⚠️ Arquivo não encontrado: {path}")
            return None

        # Garante pasta de logs
        garantir_diretorio_logs()

        # Nome fixo do log por executável
        nome_exe = os.path.splitext(os.path.basename(path))[0]
        log_individual = os.path.join(LOG_BASE_DIR, f"{nome_exe}.txt")

        # Lê linhas atuais
        linhas = []
        if os.path.exists(log_individual):
            with open(log_individual, "r", encoding="utf-8") as f:
                linhas = f.readlines()

        # Adiciona nova execução
        linhas.append(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Executado: {path}\n")

        # Mantém apenas as últimas MAX_LOG_LINES
        if len(linhas) > MAX_LOG_LINES:
            linhas = linhas[-MAX_LOG_LINES:]

        # Salva novamente
        with open(log_individual, "w", encoding="utf-8") as f:
            f.writelines(linhas)

        # Executa normalmente
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(
            ["cmd.exe", "/c", path],
            cwd=os.path.dirname(path),
            startupinfo=si,
            shell=True
        )

        log(f"▶️ Iniciando execução: {path} (registrado em {log_individual})")
        return proc

    except Exception as e:
        log(f"❌ Erro ao executar {path}: {e}")
        return None



def resolve_executable_path(info):
    nome = info.get("nome")
    local = info.get("local", BASE_DIR)
    if os.path.isdir(local):
        return os.path.join(local, nome)
    return local

# -----------------------------
# Execuções fixas
# -----------------------------
def rodar_valida():
    try:
        valida_path = os.path.join(BASE_DIR, "valida_bkp.exe")
        if os.path.exists(valida_path):
            log("▶️ Executando valida_bkp.exe após atualização...")
            proc = executar_process(valida_path)
            if proc:
                proc.wait()
                log("✅ valida_bkp concluído com sucesso")
        else:
            log("⚠️ valida_bkp.exe não encontrado")
    except Exception as e:
        log(f"❌ Erro ao executar valida_bkp.exe: {e}")

def rodar_updater(versao_remota, versao_local):
    try:
        log(f"🔄 Nova versão detectada ({versao_local} → {versao_remota})")
        updater_path = os.path.join(BASE_DIR, "updater.exe")
        if os.path.exists(updater_path):
            log("▶️ Executando updater.exe")
            proc = executar_process(updater_path)
            if proc:
                proc.wait()
                log("✅ updater.exe concluído — iniciando valida_bkp.exe")
                rodar_valida()
        else:
            log("⚠️ updater.exe não encontrado")
    except Exception as e:
        log(f"❌ Erro ao rodar updater: {e}")

# -----------------------------
# Regras de execução
# -----------------------------
def dentro_da_janela(horarios, tolerancia_min=5):
    agora = datetime.now()
    if isinstance(horarios, str):
        horarios = [horarios]
    for h in horarios:
        try:
            alvo = datetime.strptime(h, "%H:%M").replace(year=agora.year, month=agora.month, day=agora.day)
            fim = alvo + timedelta(minutes=tolerancia_min)
            if alvo <= agora <= fim:
                return True, h
        except:
            continue
    return False, None

def deve_executar(exe_info):
    agora = datetime.now()
    nome = exe_info.get("nome")

    meses = exe_info.get("mes")
    if meses and agora.month not in meses:
        return False

    dias = exe_info.get("dia")
    if dias and agora.day not in dias:
        return False

    horario = exe_info.get("horario")
    if horario:
        dentro, h = dentro_da_janela(horario)
        if not dentro:
            return False

        intervalo_dias = exe_info.get("intervalo_dias", 0)
        if intervalo_dias > 0:
            chave = f"{nome}__ultimo_dia"
            ultima_execucao = last_run.get(chave)
            if not ultima_execucao or (agora - ultima_execucao).days >= intervalo_dias:
                last_run[chave] = agora
                log(f"🗓️ Agendamento detectado: '{nome}' → {h} a cada {intervalo_dias} dias")
                return True
            else:
                return False

        # 🔒 Evita execuções repetidas dentro da janela de horário
        chave = f"{nome}__{agora.strftime('%Y-%m-%d')}__{h}"
        ultima_execucao = last_run.get(chave)
        if ultima_execucao:
            if (agora - ultima_execucao).seconds < 600:  # 10 minutos
                log(f"⏳ '{nome}' já executado recentemente (janela de 10 min). Ignorando.")
                return False

        last_run[chave] = agora
        log(f"⏰ Agendamento detectado: '{nome}' → horário {h}")
        return True

    intervalo = exe_info.get("intervalo", 0)
    if intervalo > 0:
        chave = f"{nome}__interval"
        agora_ts = time.time()
        ultima = last_run.get(chave, 0)
        if agora_ts - ultima >= intervalo * 60:
            last_run[chave] = agora_ts
            log(f"🔁 Agendamento detectado: '{nome}' → a cada {intervalo} minutos")
            return True

    if dias and not horario:
        log(f"📅 Agendamento detectado: '{nome}' → dia(s) {dias}")
        return True

    return False


# -----------------------------
# Principal
# -----------------------------
if __name__ == "__main__":
    log("🚀 Launcher iniciado")

    while True:
        config = baixar_config()
        if not config:
            log("⚠️ Falha ao carregar config. Tentando novamente...")
            time.sleep(CHECK_INTERVAL)
            continue

        versao_remota = config.get("versao", "0.0.0")
        versao_local, tipo_terminal = ler_versao_local()
        log(f"💻 Tipo deste terminal: {tipo_terminal}")

        if comparar_versoes(versao_local, versao_remota):
            rodar_updater(versao_remota, versao_local)
        else:
            log(f"✔️ Sistema atualizado — versão atual {versao_local}")

        # Execução conforme configuração
        for exe_info in config.get("executar", []):
            try:
                nome = exe_info.get("nome", "desconhecido")
                if not exe_info.get("ativo", True):
                    continue

                tipos = [t.upper() for t in exe_info.get("terminal", [])]
                if tipos:
                    if tipo_terminal not in tipos:
                        log(f"💡 Execução '{nome}' ignorada — restrita a {tipos}.")
                        continue
                else:
                    log(f"⚙️ Execução '{nome}' configurada para todos os terminais.")

                horario = exe_info.get("horario")
                intervalo_dias = exe_info.get("intervalo_dias", 0)
                dias = exe_info.get("dia")
                meses = exe_info.get("mes")

                if dias and meses:
                    log(f"📅 Agendamento '{nome}' configurado para rodar no(s) dia(s) {dias} do(s) mês(es) {meses}.")
                elif dias:
                    log(f"📅 Agendamento '{nome}' configurado para rodar no(s) dia(s): {dias}.")
                elif meses:
                    log(f"📅 Agendamento '{nome}' configurado para rodar no(s) mês(es): {meses}.")
                elif intervalo_dias > 0 and horario:
                    log(f"🔄 Agendamento '{nome}' configurado para rodar às {horario} a cada {intervalo_dias} dia(s).")
                elif horario:
                    log(f"⏰ Agendamento '{nome}' configurado para rodar nos horários: {horario}")
                else:
                    log(f"⚠️ Nenhum horário definido para '{nome}'.")

                if deve_executar(exe_info):
                    caminho = resolve_executable_path(exe_info)
                    proc = executar_process(caminho)
                    if proc:
                        proc.wait()
                        log(f"✅ Execução concluída com sucesso: {nome}")

            except Exception as e:
                log(f"❌ Erro ao processar agendamento '{exe_info.get('nome', 'desconhecido')}': {e}")

        time.sleep(CHECK_INTERVAL)
