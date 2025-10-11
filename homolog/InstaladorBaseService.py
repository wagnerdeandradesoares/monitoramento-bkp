import os
import urllib.request
import shutil
import subprocess
import sys
import ctypes
import zipfile
import tkinter as tk
from tkinter import messagebox

# ----------------------
# Funções de permissão
# ----------------------

def is_admin():
    return os.name != 'nt' or ctypes.windll.shell32.IsUserAnAdmin() != 0

def run_as_admin():
    if sys.argv[-1] != 'as_admin':
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]]) + " as_admin"
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit(0)

# ----------------------
# Funções auxiliares
# ----------------------

def create_directory():
    folder_path = r"C:\Program Files (x86)\MonitoramentoBKP"
    if not os.path.exists(folder_path):
        try:
            print("Criando a pasta MonitoramentoBKP...")
            os.makedirs(folder_path)
            return True
        except Exception as e:
            print(f"Erro ao criar a pasta: {e}")
            return False
    else:
        print("Pasta MonitoramentoBKP já existe.")
        return True

def download_file(url, destination):
    try:
        print(f"Baixando: {url}")
        urllib.request.urlretrieve(url, destination)
        if os.path.exists(destination):
            print(f"Arquivo salvo em: {destination}")
            return True
        else:
            print(f"Erro: Arquivo não encontrado após download.")
            return False
    except Exception as e:
        print(f"Erro ao baixar {url}: {e}")
        return False


def show_installation_success():
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Instalação concluída", "A instalação foi concluída com sucesso!")
    root.quit()

# ----------------------
# NSSM + Serviço
# ----------------------

def download_and_install_nssm():
    nssm_url = "https://nssm.cc/release/nssm-2.24.zip"
    temp_zip = os.path.join(os.getenv("TEMP"), "nssm.zip")
    extract_dir = os.path.join(os.getenv("TEMP"), "nssm_temp")
    nssm_exe_target = r"C:\Program Files\nssm\nssm.exe"

    if os.path.exists(nssm_exe_target):
        print("✅ NSSM já instalado.")
        return nssm_exe_target

    print("🔽 Baixando NSSM...")
    try:
        urllib.request.urlretrieve(nssm_url, temp_zip)
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        os.makedirs(os.path.dirname(nssm_exe_target), exist_ok=True)
        shutil.copy(os.path.join(extract_dir, "nssm-2.24", "win64", "nssm.exe"), nssm_exe_target)
        print("✅ NSSM instalado com sucesso.")
        return nssm_exe_target
    except Exception as e:
        print(f"❌ Falha ao instalar NSSM: {e}")
        return None

def create_base_service(nssm_path):
    service_name = "BaseService"
    display_name = "Base Service"
    launcher_path = r"C:\Program Files (x86)\MonitoramentoBKP\launcher.exe"

    if not os.path.exists(launcher_path):
        print(f"❌ launcher.exe não encontrado: {launcher_path}")
        return

    print(f"🛠️ Criando serviço: {display_name}")
    try:
        subprocess.run([nssm_path, "install", service_name, launcher_path], check=True)
        subprocess.run([nssm_path, "set", service_name, "DisplayName", display_name], check=True)
        subprocess.run([nssm_path, "set", service_name, "Start", "SERVICE_AUTO_START"], check=True)
        subprocess.run(["net", "start", service_name], check=True)
        print(f"✅ Serviço '{display_name}' criado e iniciado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar serviço: {e}")

# ----------------------
# Execução principal
# ----------------------

if not is_admin():
    run_as_admin()

print("🚀 Iniciando instalação...")

if create_directory():
    files_downloaded = True

    files_downloaded &= download_file("https://github.com/wagnerdeandradesoares/monitoramento-bkp/releases/download/v1.0.2/valida_bkp.exe", r"C:\Program Files (x86)\MonitoramentoBKP\valida_bkp.exe")
    files_downloaded &= download_file("https://github.com/wagnerdeandradesoares/monitoramento-bkp/releases/download/v1.0.2/updater.exe", r"C:\Program Files (x86)\MonitoramentoBKP\updater.exe")
    files_downloaded &= download_file("https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/versao.txt", r"C:\Program Files (x86)\MonitoramentoBKP\versao.txt")
    files_downloaded &= download_file("https://github.com/wagnerdeandradesoares/monitoramento-bkp/releases/download/v1.0.2/launcher.exe", r"C:\Program Files (x86)\MonitoramentoBKP\launcher.exe")
     

    if files_downloaded:
        nssm_path = download_and_install_nssm()
        if nssm_path:
            create_base_service(nssm_path)

        show_installation_success()
        print("✅ Instalação concluída com sucesso.")
    else:
        print("❌ Falha na instalação: um ou mais arquivos não foram baixados.")
else:
    print("❌ Falha na instalação: não foi possível criar o diretório.")

sys.exit(0)
