import os
import json
import urllib.request

# -----------------------------
# CONFIGURAÇÕES
# -----------------------------
CONFIG_URL = "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/refs/heads/master/config.json"
LOCAL_VERSOES = r"C:\Program Files (x86)\MonitoramentoBKP\versoes.json"

# -----------------------------
def carregar_config():
    with urllib.request.urlopen(CONFIG_URL, timeout=15) as f:
        return json.load(f)

def carregar_versoes():
    if os.path.exists(LOCAL_VERSOES):
        with open(LOCAL_VERSOES, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_versoes(data):
    with open(LOCAL_VERSOES, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def baixar_arquivo(url, destino):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    tmp = destino + ".tmp"
    urllib.request.urlretrieve(url, tmp)
    if os.path.exists(destino):
        os.remove(destino)
    os.rename(tmp, destino)

# -----------------------------
if __name__ == "__main__":
    try:
        config = carregar_config()
    except Exception as e:
        print("❌ Erro ao baixar config.json:", e)
        exit(1)

    versoes = carregar_versoes()
    alterado = False

    for arq in config.get("arquivos", []):
        nome = arq["nome"]
        url = arq["url"]
        destino = arq["destino"]
        versao_remota = arq["versao"]

        versao_local = versoes.get(nome, "0.0.0")

        if versao_local != versao_remota:
            print(f"🔄 Atualizando {nome} ({versao_local} → {versao_remota})")
            try:
                baixar_arquivo(url, destino)
                versoes[nome] = versao_remota
                alterado = True
                print(f"✅ {nome} atualizado com sucesso!")
            except Exception as e:
                print(f"❌ Falha ao atualizar {nome}: {e}")
        else:
            print(f"✔ {nome} já está na versão {versao_local}")

    if alterado:
        salvar_versoes(versoes)
