import os
import urllib.request
import shutil
import subprocess
import sys
import ctypes

# Função para verificar se o script está sendo executado como administrador
def is_admin():
    """Verifica se o script está sendo executado como administrador."""
    return os.geteuid() == 0 if os.name != 'nt' else ctypes.windll.shell32.IsUserAnAdmin() != 0

# Função para reiniciar o script como administrador
def run_as_admin():
    """Reinicia o script como administrador."""
    if sys.argv[-1] != 'as_admin':
        script = sys.argv[0]
        params = ' '.join(sys.argv[1:])
        subprocess.run(f'runas /user:Administrator "{script} {params} as_admin"')
        sys.exit(0)

# Função para criar o diretório MonitoramentoBKP em C:\Program Files (x86)
def create_directory():
    """Cria a pasta MonitoramentoBKP em C:\Program Files (x86)"""
    folder_path = r"C:\Program Files (x86)\MonitoramentoBKP"
    if not os.path.exists(folder_path):
        try:
            print("Criando a pasta C:\\Program Files (x86)\\MonitoramentoBKP...")
            os.makedirs(folder_path)
            return True
        except Exception as e:
            print(f"Erro ao criar a pasta: {e}")
            return False
    else:
        print("Pasta C:\\Program Files (x86)\\MonitoramentoBKP já existe.")
        return True

# Função para baixar o arquivo do GitHub
def download_file(url, destination):
    """Baixa um arquivo do GitHub"""
    try:
        print(f"Baixando arquivo de {url} para {destination}...")
        urllib.request.urlretrieve(url, destination)
        
        # Verifica se o arquivo foi realmente baixado
        if os.path.exists(destination):
            print(f"Arquivo baixado com sucesso: {destination}")
            return True
        else:
            print(f"Falha ao baixar o arquivo: {destination}")
            return False
    except Exception as e:
        print(f"Erro ao baixar o arquivo {destination}: {e}")
        return False

# Função para criar agendamentos no Agendador de Tarefas
def create_task_scheduler():
    """Cria agendamentos no Agendador de Tarefas para o Updater e o Valida Backup"""
    
    updater_path = r"C:\Program Files (x86)\MonitoramentoBKP\updater.exe"
    valida_path = r"C:\Program Files (x86)\MonitoramentoBKP\valida_bkp.exe"

    if not os.path.exists(updater_path):
        print(f"❌ O arquivo {updater_path} não foi encontrado.")
        return

    if not os.path.exists(valida_path):
        print(f"❌ O arquivo {valida_path} não foi encontrado.")
        return

    # ⚠️ Correção: colocar o caminho completo com aspas escapadas
    task_command_updater = f'schtasks /create /tn "Monitoramento Updater" /tr "\\"{updater_path}\\"" /sc daily /st 10:00 /f'
    task_command_valida_12h = f'schtasks /create /tn "Monitoramento Backup 12h" /tr "\\"{valida_path}\\"" /sc daily /st 12:00 /f'

    try:
        print("Criando agendamentos no Agendador de Tarefas...")
        subprocess.run(task_command_updater, shell=True, check=True)
        subprocess.run(task_command_valida_12h, shell=True, check=True)
        print("✅ Agendamentos criados com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao criar agendamentos: {e}")

# Função para mostrar uma janela de sucesso após a instalação
def show_installation_success():
    """Exibe uma janela de sucesso após a instalação."""
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Instalação concluída", "A instalação foi concluída com sucesso!")
    root.quit()

# Execução do script
if not is_admin():
    run_as_admin()

print("Iniciando instalação...")

if create_directory():
    files_downloaded = True
    
    files_downloaded &= download_file("https://github.com/wagnerdeandradesoares/monitoramento-bkp/releases/download/v1.0.0/valida_bkp.exe", r"C:\Program Files (x86)\MonitoramentoBKP\valida_bkp.exe")
    files_downloaded &= download_file("https://github.com/wagnerdeandradesoares/monitoramento-bkp/releases/download/v1.0.0/updater.exe", r"C:\Program Files (x86)\MonitoramentoBKP\updater.exe")
    files_downloaded &= download_file("https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/versao.txt", r"C:\Program Files (x86)\MonitoramentoBKP\versao.txt")
    
    if files_downloaded:
        create_task_scheduler()
        show_installation_success()
        print("Instalação concluída com sucesso!")
    else:
        print("❌ Falha na instalação: alguns arquivos não foram baixados corretamente.")
else:
    print("❌ Falha na instalação: a pasta não pôde ser criada.")

sys.exit(0)
