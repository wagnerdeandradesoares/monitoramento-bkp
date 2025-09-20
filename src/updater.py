import os
import urllib.request
import shutil

LOCAL_EXE = r"C:\Program Files (x86)\MonitoramentoBKP\valida_bkp.exe"
LOCAL_VERSION = r"C:\Program Files (x86)\MonitoramentoBKP\versao.txt"

# Corrigido: sem "refs/heads"
URL_VERSION = "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/versao.txt"
URL_EXE     = "https://github.com/wagnerdeandradesoares/monitoramento-bkp/releases/download/v1.0.0/valida_bkp.exe"

def get_remote_version():
    try:
        with urllib.request.urlopen(URL_VERSION, timeout=10) as f:
            return f.read().decode("utf-8").strip()
    except Exception as e:
        print("❌ Erro ao verificar versão remota:", e)
        return None

def get_local_version():
    if os.path.exists(LOCAL_VERSION):
        with open(LOCAL_VERSION, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "0.0.0"

def set_local_version(version):
    with open(LOCAL_VERSION, "w", encoding="utf-8") as f:
        f.write(version)

def download_new_exe():
    tmp_file = LOCAL_EXE + ".tmp"
    with urllib.request.urlopen(URL_EXE, timeout=30) as response, open(tmp_file, "wb") as out:
        shutil.copyfileobj(response, out)
    if os.path.exists(LOCAL_EXE):
        os.remove(LOCAL_EXE)
    os.rename(tmp_file, LOCAL_EXE)

if __name__ == "__main__":
    remote_ver = get_remote_version()
    local_ver = get_local_version()

    print(f"🔎 Versão remota: {remote_ver}")
    print(f"🔎 Versão local: {local_ver}")

    if remote_ver and remote_ver != local_ver:
        print(f"🔄 Atualizando de {local_ver} para {remote_ver}...")
        try:
            download_new_exe()
            set_local_version(remote_ver)
            print("✅ Atualização concluída!")
        except Exception as e:
            print("❌ Falha na atualização:", e)
    else:
        print("✔ Nenhuma atualização necessária.")
