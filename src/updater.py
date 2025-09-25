import os
import urllib.request
import shutil
import json
import subprocess

# Caminho para os arquivos locais
LOCAL_EXE = r"C:\Program Files (x86)\MonitoramentoBKP\valida_bkp.exe"
LOCAL_VERSION = r"C:\Program Files (x86)\MonitoramentoBKP\versao.txt"

# URL do arquivo JSON de configuração hospedado no GitHub
URL_CONFIG = "https://github.com/wagnerdeandradesoares/monitoramento-bkp/releases/download/v1.0.0/config_atualizacao.json"

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

def atualizar_exe(novo_arquivo_url, nome_arquivo):
    """Baixa o novo arquivo executável e substitui o arquivo local"""
    try:
        tmp_file = nome_arquivo + ".tmp"
        with urllib.request.urlopen(novo_arquivo_url) as response, open(tmp_file, "wb") as out:
            shutil.copyfileobj(response, out)

        if os.path.exists(nome_arquivo):
            os.remove(nome_arquivo)
        os.rename(tmp_file, nome_arquivo)
        print(f"{nome_arquivo} atualizado com sucesso!")
    except Exception as e:
        print(f"Erro ao atualizar {nome_arquivo}: {e}")

def configurar_agendamentos(agendamentos):
    """Configura os agendamentos das tarefas no Agendador de Tarefas"""
    for tarefa in agendamentos:
        nome_tarefa = tarefa["nome_tarefa"]
        comando = tarefa["comando"]
        horario = tarefa["horario"]
        frequencia = tarefa["frequencia"]

        # Ajusta a frequência para o formato correto (daily, weekly, monthly, etc.)
        if frequencia == "diario":
            frequencia = "daily"
        elif frequencia == "semanal":
            frequencia = "weekly"
        elif frequencia == "mensal":
            frequencia = "monthly"

        # Comando para adicionar a tarefa no Agendador de Tarefas
        comando_tarefa = f'schtasks /create /tn "{nome_tarefa}" /tr "{comando}" /sc {frequencia} /st {horario} /f'
        try:
            subprocess.run(comando_tarefa, shell=True, check=True)
            print(f"Tarefa '{nome_tarefa}' agendada para {horario}.")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao agendar a tarefa '{nome_tarefa}': {e}")
            print(f"Comando falhou: {comando_tarefa}")  # Mostra o comando que falhou

def verificar_atualizacao():
    """Verifica se há uma atualização e realiza a atualização, se necessário"""
    # Obtém a configuração de atualização do GitHub
    config = obter_config_atualizacao()

    if config:
        versao_local = obter_versao_local()
        versao_remota = config["nova_versao"]

        print(f"Versão local: {versao_local}")
        print(f"Versão remota: {versao_remota}")

        # Se houver uma nova versão, atualiza os arquivos
        if versao_local != versao_remota:
            print(f"Atualizando para versão {versao_remota}...")
            for arquivo in config["arquivos"]:
                nome_arquivo = os.path.join(r"C:\Program Files (x86)\MonitoramentoBKP", arquivo["nome"])
                atualizar_exe(arquivo["url"], nome_arquivo)

            # Atualiza a versão local
            with open(LOCAL_VERSION, "w", encoding="utf-8") as f:
                f.write(versao_remota)

            # Configura os agendamentos
            configurar_agendamentos(config["agendamentos"])
        else:
            print("A versão já está atualizada!")

if __name__ == "__main__":
    verificar_atualizacao()
