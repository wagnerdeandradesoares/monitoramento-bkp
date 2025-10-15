import os
import json
import urllib.request
import subprocess
import time
from datetime import datetime
import random

# -----------------------------
# Configurações
# -----------------------------
CONFIG_URL = "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config.json"
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"
LOG_BASE_DIR = os.path.join(BASE_DIR, "logs")
VERSION_FILE = os.path.join(BASE_DIR, "versao.config")   # agora JSON
MAX_LOG_LINES = 200

# -----------------------------
# Logging simples (arquivo + console)
# -----------------------------
def garantir_diretorio_logs():
    os.makedirs(LOG_BASE_DIR, exist_ok=True)

def log(msg):
    garantir_diretorio_logs()
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    line = f"[{now}] {msg}\n"
    log_path = os.path.join(LOG_BASE_DIR, "updater.log")
    try:
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        else:
            lines = []
        lines.append(line)
        if len(lines) > MAX_LOG_LINES:
            lines = lines[-MAX_LOG_LINES:]
        with open(log_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception:
        # não travar por falha de log
        pass
    print(line.strip())

# -----------------------------
# Utilitários de rede / arquivos
# -----------------------------
def baixar_config_forcado():
    """Baixa config forçando evitar cache (adiciona query string aleatória)."""
    try:
        url = f"{CONFIG_URL}?nocache={random.randint(1000,999999)}"
        log(f"🌐 Baixando config (forçado): {url}")
        with urllib.request.urlopen(url, timeout=15) as resp:
            content = resp.read().decode()
            cfg = json.loads(content)
            log(f"✅ Config carregado. Versão remota no config: {cfg.get('versao')}")
            return cfg
    except Exception as e:
        log(f"❌ Falha ao baixar config: {e}")
        return None

def baixar_arquivo(url, destino):
    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        log(f"⬇️ Baixando {url} → {destino}")
        urllib.request.urlretrieve(url, destino)
        log(f"✅ Download concluído: {destino} (tamanho: {os.path.getsize(destino)} bytes)")
        return True
    except Exception as e:
        log(f"❌ Erro ao baixar {url}: {e}")
        return False

# -----------------------------
# Versão local (JSON) helpers
# -----------------------------
def ler_versao_local_dict():
    """Retorna dicionário { 'versao': ..., 'tipo': ... }"""
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                vers = str(dados.get("versao", "0.0.0")).strip()
                tipo = str(dados.get("tipo", "CX1")).strip().upper()
                log(f"🔍 Versão local lida: {vers} | Tipo: {tipo}")
                return {"versao": vers, "tipo": tipo}
        except Exception as e:
            log(f"⚠️ Erro ao ler {VERSION_FILE}: {e} — vamos recriar com padrão")
    # padrão se não existe / falha
    dados_padrao = {"versao": "0.0.0", "tipo": "CX1"}
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(dados_padrao, f, indent=2, ensure_ascii=False)
        log(f"♻️ Criado {VERSION_FILE} padrão: {dados_padrao}")
    except Exception as e:
        log(f"⚠️ Não consegui criar {VERSION_FILE}: {e}")
    return dados_padrao

def gravar_versao_local(versao, tipo):
    dados = {"versao": versao.strip(), "tipo": tipo.strip().upper()}
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        log(f"💾 versao.config gravado: {dados}")
        return True
    except Exception as e:
        log(f"❌ Falha ao gravar {VERSION_FILE}: {e}")
        return False

# -----------------------------
# Controle serviço (opcional)
# -----------------------------
def parar_servico_nssm(service_name="BaseService"):
    try:
        log(f"🛑 Parando serviço {service_name} ...")
        subprocess.run(["sc", "stop", service_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        log(f"✔️ Serviço {service_name} parado.")
        return True
    except Exception as e:
        log(f"⚠️ Não foi possível parar serviço {service_name}: {e}")
        return False

def iniciar_servico_nssm(service_name="BaseService"):
    try:
        log(f"🚀 Iniciando serviço {service_name} ...")
        subprocess.run(["sc", "start", service_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f"✔️ Serviço {service_name} iniciado.")
        return True
    except Exception as e:
        log(f"⚠️ Não foi possível iniciar serviço {service_name}: {e}")
        return False

# -----------------------------
# Atualização de arquivos
# -----------------------------
def substituir_arquivo(caminho_destino, arquivo_url):
    tmp = caminho_destino + ".tmp"
    try:
        os.makedirs(os.path.dirname(caminho_destino), exist_ok=True)
        log(f"⬇️ Baixando para tmp: {arquivo_url} -> {tmp}")
        urllib.request.urlretrieve(arquivo_url, tmp)
        # substitui atomicamente
        if os.path.exists(caminho_destino):
            try:
                os.remove(caminho_destino)
            except Exception as e_rm:
                log(f"⚠️ Falha ao remover antigo {caminho_destino}: {e_rm}")
        os.rename(tmp, caminho_destino)
        log(f"✅ Substituído: {caminho_destino}")
        return True
    except Exception as e:
        log(f"❌ Falha ao substituir {caminho_destino}: {e}")
        # tenta limpar tmp
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except:
            pass
        return False

def atualizar_item(item):
    """Atualiza um item do config: {nome, url, destino(optional)}"""
    nome = item.get("nome")
    url = item.get("url")
    destino_dir = item.get("destino", BASE_DIR)
    if not nome or not url:
        log("⚠️ Item inválido (sem nome ou URL). Pulando.")
        return False
    if os.path.isabs(destino_dir):
        destino = destino_dir if os.path.splitext(destino_dir)[1] else os.path.join(destino_dir, nome)
    else:
        destino = os.path.join(BASE_DIR, destino_dir, nome)
    log(f"📦 Atualizando item '{nome}' para {destino}")
    # Se for o launcher e existe serviço, parar antes (nome exato)
    if nome.lower() == "launcher.exe":
        if not parar_servico_nssm("BaseService"):
            log("⚠️ Não foi possível parar BaseService. Continuando tentativa de atualização.")
    ok = substituir_arquivo(destino, url)
    if not ok:
        log(f"❌ Falha ao atualizar {nome}")
        return False
    # se atualizou launcher, reinicia serviço
    if nome.lower() == "launcher.exe":
        iniciar_servico_nssm("BaseService")
    return True

# -----------------------------
# Fluxo principal do updater
# -----------------------------
def main():
    log("🚀 Iniciando updater")

    cfg = baixar_config_forcado()
    if not cfg:
        log("❌ Não foi possível baixar o config. Abortando.")
        return

    versao_remota = str(cfg.get("versao", "0.0.0")).strip()
    log(f"🔎 Versão remota (config): {versao_remota}")

    local = ler_versao_local_dict()
    versao_local = str(local.get("versao", "0.0.0")).strip()
    tipo_local = str(local.get("tipo", "CX1")).strip().upper()

    log(f"📌 Versão local antes: {versao_local} | tipo: {tipo_local}")

    # Atualiza arquivos listados
    arquivos = cfg.get("arquivos", [])
    any_updated = False
    for item in arquivos:
        nome = item.get("nome")
        log(f"— processando item do config: {nome}")
        ok = atualizar_item(item)
        any_updated = any_updated or ok
        # sleeping curto para não sobrecarregar rede/IO em ambientes lentos
        time.sleep(0.2)

    # Se houve atualização de arquivos, ou versão remota diferente, grava versao.config
    if any_updated or versao_local != versao_remota:
        success = gravar_versao_local(versao_remota, tipo_local)
        if success:
            log(f"✅ Versão local atualizada para {versao_remota}")
        else:
            log("⚠️ Não foi possível gravar versão local.")
    else:
        log("ℹ️ Nada mudou (arquivos não alterados e versão igual).")

    log("🏁 Updater finalizado")

if __name__ == "__main__":
    main()
