📦 Documentação do Projeto: MonitoramentoBKP

🎯 Visão Geral

O MonitoramentoBKP é um sistema automatizado de monitoramento de backups e atualização de sistema. Ele tem como objetivo garantir que os backups sejam realizados corretamente e manter o sistema sempre atualizado.

🗂 Estrutura do Projeto

Abaixo está a estrutura do projeto com todos os arquivos descritos:

MonitoramentoBKP/
│
├── src/                    # Código fonte do projeto
│   ├── valida_bkp.py       # Script responsável pela verificação e monitoramento dos backups
│   ├── updater.py          # Script para atualização automática do sistema
│   └── instalador.py       # Script responsável pela criação do instalador do sistema
│
├── dist/                    
│   ├── valida_bkp.exe      # Executável do script de validação de backup
│   ├── updater.exe         # Executável do script de atualização
│   ├── versao.txt          # Arquivo contendo a versão do sistema
│   └── instalador.exe      # Instalador do sistema para facilitar a instalação
│
├── .gitignore              # Arquivo para configuração do Git e ignorar arquivos desnecessários
└── README.md               # Arquivo de documentação do projeto

1. Diretório src/ 🖥️

Contém os scripts principais que implementam as funcionalidades do projeto.

valida_bkp.py:

🛠️ Função: Verifica o status dos backups.

Verifica se o diretório de backup existe e se há subpastas com arquivos.

Envia alertas ou confirmações para o Google Sheets, dependendo do status.

Utiliza um URL de script do Google Apps Script para registrar status na planilha.

updater.py:

🔄 Função: Realiza a atualização automática do sistema.

Compara a versão local com a versão remota disponível no GitHub.

Baixa os novos arquivos executáveis, substitui os antigos e configura tarefas agendadas.

instalador.py:

⚙️ Função: Cria o instalador do sistema.

Cria o diretório de instalação em C:\Program Files (x86)\MonitoramentoBKP.

Baixa os arquivos executáveis do GitHub e configura as tarefas automáticas no Agendador de Tarefas do Windows.

2. Diretório dist/ 💾

Contém os arquivos compilados e instaláveis do sistema.

valida_bkp.exe: Executável gerado a partir do script valida_bkp.py, utilizado para monitorar e validar os backups.

updater.exe: Executável gerado a partir do script updater.py, responsável pela atualização do sistema.

versao.txt: Arquivo de texto que contém a versão atual do sistema.

instalador.exe: Instalador do sistema, que facilita a instalação em outras máquinas.

3. Arquivos de Configuração 🔧

config_atualizacao.json: Arquivo de configuração para agendamentos e atualização automática do sistema. Ele contém informações sobre a versão atual, a nova versão disponível, os arquivos a serem baixados e os agendamentos de execução.

Exemplo de config_atualizacao.json:

{
  "versao_atual": "1.0.0",
  "nova_versao": "1.0.1",
  "arquivos": [
    {
      "nome": "tste.exe",
      "url": "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/refs/heads/master/dist/tste.exe",
      "descricao": "teste de atualizacao"
    }
  ],
  "agendamentos": [
    {
      "nome_tarefa": "teste de agendamento",
      "comando": "C:\\Program Files (x86)\\MonitoramentoBKP\\tste.exe",
      "horario": "00:00",
      "frequencia": "diario"
    }
  ]
}


Este arquivo define:

versao_atual: A versão atual instalada do sistema.

nova_versao: A nova versão disponível para atualização.

arquivos: Lista de arquivos a serem baixados e atualizados, incluindo o nome, URL e descrição de cada arquivo.

agendamentos: Lista de tarefas agendadas para execução, com a definição de horário e frequência de execução (diário, semanal, etc.).

4. Arquivo .gitignore 🔒

O arquivo .gitignore é utilizado para definir quais arquivos e pastas não devem ser versionados pelo Git. Ele normalmente inclui arquivos temporários, dependências externas e arquivos compilados.

5. Arquivo README.md 📖

Este arquivo contém a documentação básica sobre o projeto, como descrição, objetivos, requisitos e instruções de instalação.

💡 Descrição dos Scripts

1. instalador.py 🔨

Função Principal: Cria o diretório de instalação em C:\Program Files (x86)\MonitoramentoBKP, baixa os executáveis do GitHub e configura agendamentos automáticos.

Passos:

Verifica se o script está sendo executado com privilégios de administrador.

Cria o diretório MonitoramentoBKP em C:\Program Files (x86) se ainda não existir.

Baixa os arquivos valida_bkp.exe, updater.exe e versao.txt do GitHub para o diretório.

Configura tarefas automáticas no Agendador de Tarefas do Windows para execução diária dos scripts de backup e atualização.

Exibe uma janela de sucesso ao concluir a instalação.

2. valida_bkp.py ✅

Função Principal: Realiza a verificação do diretório de backups e envia status para o Google Sheets.

Passos:

Verifica se o diretório de backups (C:\backup_sql) existe.

Checa se as subpastas dentro desse diretório contêm arquivos.

Se o backup estiver OK, envia um status "OK" para o Google Sheets; caso contrário, envia um alerta de erro.

Registra o status do backup no Google Sheets, junto com o código da filial, data e versão.

3. updater.py 🔄

Função Principal: Verifica e realiza a atualização do sistema automaticamente, se necessário.

Passos:

Obtém a versão atual do sistema através do arquivo versao.txt.

Compara a versão local com a versão remota disponível no arquivo config_atualizacao.json hospedado no GitHub.

Se houver uma nova versão, baixa e substitui os executáveis (valida_bkp.exe, updater.exe).

Configura agendamentos de tarefas no Agendador de Tarefas para executar os scripts de validação e atualização periodicamente.

📑 Como Usar

1. Instalar o Sistema ⚙️

Passo 1: Execute o instalador.exe.

O instalador irá automaticamente criar a pasta MonitoramentoBKP em C:\Program Files (x86)\MonitoramentoBKP.

Importante: O instalador precisa ser executado com privilégios de administrador para garantir que ele tenha permissão para criar a pasta em C:\Program Files (x86) e registrar as tarefas no Agendador de Tarefas.

Passo 2: Após a instalação, garanta que a pasta MonitoramentoBKP tenha as permissões necessárias.

Como fazer:

Navegue até o diretório C:\Program Files (x86)\MonitoramentoBKP.

Clique com o botão direito na pasta MonitoramentoBKP e selecione Propriedades.

Vá para a aba Segurança, clique em Editar e adicione permissões totais para o usuário "soma".

Isso é importante para garantir que os scripts possam ser executados corretamente e que o sistema tenha acesso total à pasta após a instalação.

2. Verificar Backup ✅

Após a instalação, o sistema estará configurado para verificar automaticamente os backups conforme os agendamentos realizados no Agendador de Tarefas do Windows. O script valida_bkp.exe será executado periodicamente para validar se os backups estão sendo realizados corretamente.

3. Atualizar o Sistema 🔄

O script updater.exe será responsável por verificar se há uma nova versão do sistema disponível.

Se uma nova versão for encontrada, o updater fará o download dos novos executáveis e os substituirá automaticamente.

⚠️ Considerações Finais

Certifique-se de que o sistema esteja sempre atualizado para garantir que a verificação de backups e a execução de tarefas ocorram sem problemas.

Caso haja alguma falha na instalação ou execução, revise as permissões do sistema e os logs gerados pelos scripts.