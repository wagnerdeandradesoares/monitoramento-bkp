import os
import socket
import json
from datetime import datetime
import urllib.request
import winreg
import time

# -----------------------------
# Configurações
# -----------------------------
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"  # Caminho base para os arquivos
BACKUP_DIR = r"C:\backup_sql"  # O backup está no C:\
LOG_BASE_DIR = os.path.join(BASE_DIR, "logs")
VERSAO_FILE_PATH = os.path.join(BASE_DIR, "versao.txt")

# URL do Google Apps Script
SHEET_URL = "https://script.google.com/macros/s/AKfycbwnhW-pfrI0p6KS2G5G1cOPz63k6yjcgdYCKcZ1NQja-N1DwvneyHlLXUx-ADoBh4PYFg/exec" # URL de testes

# -----------------------------
# Funções de log
# -----------------------------

def garantir_diretorio_logs():
    """Garante que a pasta 'logs' exista"""
    if not os.path.exists(LOG_BASE_DIR):  # Verifica se a pasta não existe
        try:
            os.makedirs(LOG_BASE_DIR, exist_ok=True)  # Cria a pasta
            log(f"✅ Pasta de logs criada: {LOG_BASE_DIR}")
        except Exception as e:
            log(f"❌ Erro ao criar a pasta de logs: {e}")
            raise  # Re-levanta a exceção caso falhe

# Função de log
def log(msg):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    line = f"[{now}] {msg}\n"
    
    # Garantir que a pasta de logs exista antes de gravar
    garantir_diretorio_logs()

    # Define o arquivo de log
    LOG_FILE = os.path.join(LOG_BASE_DIR, "valida_bkp.log")  # Pode mudar o nome conforme necessário

    # Mantém no máximo as últimas MAX_LOG_LINES
    MAX_LOG_LINES = 100  # ou outro valor que você desejar
    lines = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    lines.append(line)
    if len(lines) > MAX_LOG_LINES:
        lines = lines[-MAX_LOG_LINES:]

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(line.strip())  # Para manter a saída no console

# -----------------------------
# Funções
# -----------------------------

def send_to_sheet(filial_id, terminal, status, detalhe):
    """
    Envia alerta ou status OK para Google Sheets
    """
    payload = {
        "filial": filial_id,
        "terminal": terminal,
        "status": status,
        "detalhe": detalhe,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            SHEET_URL,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                log(f"✅ Status '{status}' enviado para planilha (linha atualizada ou inserida)")
            else:
                log(f"⚠️ Erro ao enviar: {response.status}")
    except Exception as e:
        log(f"❌ Falha na conexão com planilha: {e}")

def get_loja_code():
    """Recupera o código da filial do registro do Windows"""
    key_path = r"Software\Linx Sistemas\LinxPOS-e"
    value_name = "Código da loja"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        loja_code, regtype = winreg.QueryValueEx(key, value_name)
        winreg.CloseKey(key)
        return str(loja_code)
    except FileNotFoundError:
        return "Código não encontrado"
    except Exception as e:
        log(f"❌ Erro ao acessar o registro da filial: {e}")
        return "Erro ao obter código"

def get_terminal_code():
    """Recupera o código do terminal do registro do Windows"""
    key_path = r"Software\Linx Sistemas\LinxPOS-e"
    value_name = "Terminal"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        terminal_code, regtype = winreg.QueryValueEx(key, value_name)
        winreg.CloseKey(key)
        return str(terminal_code).zfill(3)  # Formata com 3 dígitos
    except FileNotFoundError:
        return "Terminal não encontrado"
    except Exception as e:
        log(f"❌ Erro ao acessar o registro do terminal: {e}")
        return "Erro ao obter terminal"

def ler_versao():
    """Lê a versão do arquivo versao.txt"""
    try:
        with open(VERSAO_FILE_PATH, "r", encoding="utf-8") as f:
            versao = f.read().strip()
            log(f"Versão lida do arquivo: {versao}")
            return versao
    except Exception as e:
        log(f"Erro ao ler a versão: {e}")
        return "Versão não encontrada"

# -----------------------------
# Checagem de backup
# -----------------------------

def check_backup():
    hostname = socket.gethostname()
    data_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Recupera códigos do registro
    filial_code = get_loja_code()
    terminal_code = get_terminal_code()

    # Recupera a versão
    versao = ler_versao()

    # Verifica se o diretório de backup (C:\) existe
    if not os.path.exists(BACKUP_DIR):
        detalhe = "Pasta de backup inexistente"
        log_msg = f"Backup não encontrado\nData: {data_now}\n{detalhe}\nFilial: {filial_code} - {hostname}\nVersão: {versao}"
        send_to_sheet(hostname, terminal_code, "ERRO", log_msg)
        return

    # Lista subpastas dentro do diretório
    subfolders = [f.path for f in os.scandir(BACKUP_DIR) if f.is_dir()]
    if not subfolders:
        detalhe = "Nenhuma subpasta encontrada"
        log_msg = f"Backup não encontrado\nData: {data_now}\n{detalhe}\nFilial: {filial_code} - {hostname}\nVersão: {versao}"
        send_to_sheet(hostname, terminal_code, "ERRO", log_msg)
        return

    # Verifica se há subpastas vazias
    empty_subs = []
    for sub in subfolders:
        files = [f for f in os.listdir(sub) if os.path.isfile(os.path.join(sub, f))]
        if not files:
            empty_subs.append(os.path.basename(sub))

    if empty_subs:
        detalhe = f"Subpastas vazias: {', '.join(empty_subs)}"
        log_msg = f"Backup não encontrado\nData: {data_now}\n{detalhe}\nFilial: {filial_code} - {hostname}\nVersão: {versao}"
        send_to_sheet(hostname, terminal_code, "ERRO", log_msg)
    else:
        detalhe = "Backup encontrado corretamente"
        log_msg = f"Backup OK\nData: {data_now}\n{detalhe}\nFilial: {filial_code} - {hostname}\nVersão: {versao}"
        send_to_sheet(hostname, terminal_code, "OK", log_msg)

if __name__ == "__main__":
    check_backup()
