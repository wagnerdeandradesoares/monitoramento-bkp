import os
import urllib.request
import shutil
import json

# Caminho para os arquivos locais
LOCAL_EXE = r"C:\Program Files (x86)\MonitoramentoBKP\valida_bkp.exe"
LOCAL_VERSION = r"C:\Program Files (x86)\MonitoramentoBKP\versao.txt"

# URL do arquivo JSON de configuração hospedado no GitHub
URL_CONFIG = "https://github.com/wagnerdeandradesoares/monitoramento-bkp/releases/download/v1.0.2/config_atualizacao.json"

# Diretório padrão caso o campo 'destino' não seja fornecido no config
BASE_DIR = r"C:\Program Files (x86)\MonitoramentoBKP"

def obter_config_atualizacao():
    """Obtém as configurações de atualização do arquivo JSON hospedado no GitHub."""
    try:
        with urllib.request.urlopen(URL_CONFIG) as response:
            dados = json.loads(response.read())
            return dados
    except Exception as e:
        print(f"Erro ao obter a configuração de atualização: {e}")
        return None

def obter_versao_local():
    """Obtém a versão local do arquivo versao.txt"""
    try:
        with open(LOCAL_VERSION, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"

def atualizar_exe(novo_arquivo_url, nome_arquivo, destino):
    """Baixa o novo arquivo executável e substitui o arquivo local no destino especificado."""
    try:
        # Garantir que o diretório de destino exista
        if not os.path.exists(destino):
            os.makedirs(destino)

        # Caminho completo para o arquivo de destino
        caminho_destino = os.path.join(destino, nome_arquivo)

        # Baixa o novo arquivo para um arquivo temporário
        tmp_file = caminho_destino + ".tmp"
        with urllib.request.urlopen(novo_arquivo_url) as response, open(tmp_file, "wb") as out:
            shutil.copyfileobj(response, out)

        # Substitui o arquivo antigo se ele existir
        if os.path.exists(caminho_destino):
            os.remove(caminho_destino)
        
        os.rename(tmp_file, caminho_destino)
        print(f"{nome_arquivo} atualizado com sucesso em {caminho_destino}!")

    except Exception as e:
        print(f"Erro ao atualizar {nome_arquivo} em {destino}: {e}")

def verificar_atualizacao():
    """Verifica se há uma atualização e realiza a atualização, se necessário"""
    # Obtém a configuração de atualização do GitHub
    config = obter_config_atualizacao()

    if config:
        versao_local = obter_versao_local()
        versao_remota = config["versao"]

        print(f"Versão local: {versao_local}")
        print(f"Versão remota: {versao_remota}")

        # Se houver uma nova versão, atualiza os arquivos
        if versao_local != versao_remota:
            print(f"Atualizando para versão {versao_remota}...")
            for arquivo in config["arquivos"]:
                # Verifica se o campo 'destino' existe no arquivo de configuração
                destino = arquivo.get("destino", BASE_DIR)  # Usa BASE_DIR se 'destino' não existir
                nome_arquivo = arquivo["nome"]
                atualizar_exe(arquivo["url"], nome_arquivo, destino)

            # Atualiza a versão local
            with open(LOCAL_VERSION, "w", encoding="utf-8") as f:
                f.write(versao_remota)

if __name__ == "__main__":
    verificar_atualizacao()
