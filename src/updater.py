import os
import json
import urllib.request
from datetime import datetime

# -----------------------------
# Configurações
# -----------------------------
CONFIG_URL = "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/develop/dist/config.json"
#URL de testes para produção: https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/config.json
BASE_DIR = r"C:--Program Files (x86)\MonitoramentoBKP" 
# dirotório de testes para produção: C:\Program Files (x86)\MonitoramentoBKP
LOG_BASE_DIR = os.path.join(BASE_DIR, "logs")
VERSION_FILE = os.path.join(BASE_DIR, "versao.txt")
MAX_LOG_LINES = 100



def garantir_diretorio_logs():
    """Garante que a pasta 'logs' exista"""
    if not os.path.exists(LOG_BASE_DIR):  # Verifica se a pasta não existe
        try:
            os.makedirs(LOG_BASE_DIR, exist_ok=True)  # Cria a pasta
            print(f"✅ Pasta de logs criada: {LOG_BASE_DIR}")
        except Exception as e:
            print(f"❌ Erro ao criar a pasta de logs: {e}")
            raise  # Re-levanta a exceção caso falhe

# -----------------------------
# Funções de log
# -----------------------------
# Função de log
def log(msg):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    line = f"[{now}] {msg}\n"
    
    # Garantir que a pasta de logs exista antes de gravar
    garantir_diretorio_logs()

    # Define o arquivo de log
    LOG_FILE = os.path.join(LOG_BASE_DIR, "updater.log")  # Pode mudar o nome conforme necessário

    # Mantém no máximo as últimas MAX_LOG_LINES
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

def baixar_arquivo(url, destino):
    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        urllib.request.urlretrieve(url, destino)
        log(f"📦 Arquivo atualizado com sucesso: {destino}")
        return True
    except Exception as e:
        log(f"❌ Erro ao baixar {url}: {e}")
        return False

# -----------------------------
# Lógica principal
# -----------------------------
def main():
    log("🚀 Iniciando processo de atualização")

    config = baixar_config()
    if not config:
        log("❌ Falha ao obter configuração remota. Abortando.")
        return

    versao_remota = config.get("versao", "0.0.0")
    log(f"🔎 Versão remota encontrada: {versao_remota}")

    for item in config.get("arquivos", []):
        nome = item.get("nome")
        url = item.get("url")
        destino_dir = item.get("destino", BASE_DIR)
        destino_path = os.path.join(destino_dir, nome)

        if not nome or not url:
            log("⚠️ Configuração de arquivo inválida (faltando nome ou url). Pulando...")
            continue

        log(f"⬇️ Atualizando '{nome}'")
        log(f"📁 Destino: {destino_path}")
        if baixar_arquivo(url, destino_path):
            log(f"✅ {nome} atualizado em {destino_dir}")

    # Atualiza arquivo de versão
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(versao_remota)
        log(f"💾 Versão local atualizada para {versao_remota}")
    except Exception as e:
        log(f"❌ Erro ao salvar versão local: {e}")

    log("🏁 Atualização concluída com sucesso!")

# -----------------------------
if __name__ == "__main__":
    main()
