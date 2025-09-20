import os
import socket
import json
from datetime import datetime
import urllib.request
import winreg

# -----------------------------
# Configurações
# -----------------------------
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"  # Caminho base para os arquivos

# Novo caminho para o diretório do backup
BACKUP_DIR = r"C:\backup_sql"  # O backup está no C:\

# Caminho para o arquivo de versão
VERSAO_FILE_PATH = os.path.join(BASE_DIR, "versao.txt")

# URL do Google Apps Script (substitua pelo seu script)
SHEET_URL = "https://script.google.com/macros/s/AKfycbz7sl_WZEeP6JgLZEd_fEvosOPl1aXShhNMiHjr2saGHVC6fQCqKqs71cLPAnObHT9S5g/exec"
             

# -----------------------------
# Funções
# -----------------------------

def send_to_sheet(filial_id, status, detalhe):
    """
    Envia alerta ou status OK para Google Sheets
    - filial_id: identificação única da filial (hostname)
    """
    payload = {
        "filial": filial_id,
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
                print(f"✅ Status '{status}' enviado para planilha (linha atualizada ou inserida)")
            else:
                print(f"⚠️ Erro ao enviar: {response.status}")
    except Exception as e:
        print(f"❌ Falha na conexão com planilha: {e}")

def get_loja_code():
    """Recupera o código da filial do registro do Windows"""
    key_path = r"Software\Linx Sistemas\LinxPOS-e"
    value_name = "Código da loja"  # Substitua pelo nome correto da chave do código da loja
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        loja_code, regtype = winreg.QueryValueEx(key, value_name)
        winreg.CloseKey(key)
        return loja_code
    except FileNotFoundError:
        return "Código não encontrado"
    except Exception as e:
        print(f"❌ Erro ao acessar o registro do Windows: {e}")
        return "Erro ao obter código"

def ler_versao():
    """Lê a versão do arquivo versao.txt"""
    try:
        with open(VERSAO_FILE_PATH, "r", encoding="utf-8") as f:
            versao = f.read().strip()
            print(f"Versão lida do arquivo: {versao}")
            return versao
    except Exception as e:
        print(f"Erro ao ler a versão: {e}")
        return "Versão não encontrada"

# -----------------------------
# Checagem de backup
# -----------------------------
def check_backup():
    hostname = socket.gethostname()
    data_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Recupera o código da loja do registro
    filial_code = get_loja_code()

    # Recupera a versão do arquivo versao.txt
    versao = ler_versao()

    # Verifica se o diretório de backup (C:\) existe
    if not os.path.exists(BACKUP_DIR):
        detalhe = f"Pasta de backup inexistente"
        log_msg = f"Backup não encontrado\nData: {data_now}\n{detalhe}\nFilial: {filial_code} - {hostname}\nVersão: {versao}"
        send_to_sheet(hostname, "ERRO", log_msg)
        return

    # Lista subpastas dentro do diretório de backup (C:\)
    subfolders = [f.path for f in os.scandir(BACKUP_DIR) if f.is_dir()]
    if not subfolders:
        detalhe = f"Nenhuma subpasta encontrada"
        log_msg = f"Backup não encontrado\nData: {data_now}\n{detalhe}\nFilial: {filial_code} - {hostname}\nVersão: {versao}"
        send_to_sheet(hostname, "ERRO", log_msg)
        return

    # Verifica cada subpasta por qualquer arquivo
    empty_subs = []
    for sub in subfolders:
        files = [f for f in os.listdir(sub) if os.path.isfile(os.path.join(sub, f))]
        if not files:
            empty_subs.append(os.path.basename(sub))

    if empty_subs:
        detalhe = f"Subpastas vazias: {', '.join(empty_subs)}"
        log_msg = f"Backup não encontrado\nData: {data_now}\n{detalhe}\nFilial: {filial_code} - {hostname}\nVersão: {versao}"
        send_to_sheet(hostname, "ERRO", log_msg)
    else:
        detalhe = f"Backup encontrado corretamente"
        log_msg = f"Backup OK\nData: {data_now}\n{detalhe}\nFilial: {filial_code} - {hostname}\nVersão: {versao}"
        send_to_sheet(hostname, "OK", log_msg)

# -----------------------------
# Execução
# -----------------------------
if __name__ == "__main__":
    check_backup()
