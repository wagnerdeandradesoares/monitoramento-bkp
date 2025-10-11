import subprocess
import os
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def executar_process(path):
    """Executa um arquivo local (.bat, .cmd, .ps1 ou .exe) em segundo plano, com log"""
    try:
        if not os.path.exists(path):
            log(f"❌ Arquivo não encontrado: {path}")
            return None

        pasta = os.path.dirname(path)
        nome_arquivo = os.path.splitext(os.path.basename(path))[0]
        log_file = os.path.join(pasta, f"{nome_arquivo}_exec.log")

        # Cria ou limpa o log anterior
        open(log_file, "w").close()

        with open(log_file, "a", encoding="utf-8") as log_out:
            ext = os.path.splitext(path)[1].lower()

            if ext in (".bat", ".cmd"):
                comando = ["cmd", "/c", path]
            elif ext == ".ps1":
                comando = ["powershell", "-ExecutionPolicy", "Bypass", "-File", path]
            else:
                comando = [path]

            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

            processo = subprocess.Popen(
                comando,
                cwd=pasta,
                stdout=log_out,
                stderr=subprocess.STDOUT,
                creationflags=flags,
                shell=False
            )

        log(f"✅ Processo '{path}' iniciado. Log em: {log_file}")
        return processo

    except Exception as e:
        log(f"❌ Erro ao executar {path}: {e}")
        return None


# ------------------------------
# Caminho do arquivo a executar
# ------------------------------
CAMINHO_BAT = r"C:\Programas\abrir_teste.bat"

if os.path.exists(CAMINHO_BAT):
    log(f"▶️ Executando {CAMINHO_BAT} ...")
    proc = executar_process(CAMINHO_BAT)
    if proc:
        log("🚀 Execução iniciada (acompanhe o .log)")
    else:
        log("⚠️ Falha ao iniciar processo")
else:
    log(f"❌ Arquivo não encontrado: {CAMINHO_BAT}")


    
