import subprocess
import os
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def executar_process(path):
    """Executa um arquivo local (.bat, .cmd, .ps1 ou .exe)"""
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext in (".bat", ".cmd"):
            return subprocess.Popen(
                ["cmd", "/c", path],
                cwd=os.path.dirname(path),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        elif ext == ".ps1":
            return subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", path],
                cwd=os.path.dirname(path),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            return subprocess.Popen([path], cwd=os.path.dirname(path), creationflags=flags)
    except Exception as e:
        log(f"❌ Erro ao executar {path}: {e}")
        return None

# ------------------------------
# Caminho local para testar
# ------------------------------
CAMINHO_BAT = r"C:\Users\wagner.soares\Desktop\Monitoramento BKP\src\abrir_teste.bat"

if os.path.exists(CAMINHO_BAT):
    log(f"▶️ Executando {CAMINHO_BAT} ...")
    proc = executar_process(CAMINHO_BAT)
    if proc:
        log("✅ Processo iniciado (verifique se abriu o CMD)")
    else:
        log("⚠️ Falha ao iniciar processo")
else:
    log(f"❌ Arquivo não encontrado: {CAMINHO_BAT}")
