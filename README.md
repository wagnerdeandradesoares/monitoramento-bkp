Documentação do Projeto: Monitoramento de Backup
1. Visão Geral

O projeto monitora e valida backups de lojas, atualiza executáveis de forma centralizada e mantém logs de execução.

O launcher é instalado como serviço do Windows, garantindo execução automática ao iniciar o computador, sem intervenção manual.

2. Estrutura de Arquivos
C:\Program Files (x86)\MonitoramentoBKP\
│
├── launcher.exe         # Programa principal, roda em loop como serviço
├── updater.exe          # Atualizador de arquivos do sistema
├── valida_bkp.exe       # Validação do backup da loja
├── versao.txt           # Contém a versão local do sistema
├── launcher.log         # Log enxuto das últimas execuções importantes
└── outros arquivos      # Novos executáveis adicionados via config

3. Configuração Remota

O launcher baixa o config JSON do GitHub:

{
  "versao": "1.0.5",
  "arquivos": [
    {
      "nome": "valida_bkp.exe",
      "url": "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/valida_bkp.exe",
      "descricao": "Validação de backup"
    },
    {
      "nome": "updater.exe",
      "url": "https://raw.githubusercontent.com/wagnerdeandradesoares/monitoramento-bkp/master/dist/updater.exe",
      "descricao": "Atualizador de arquivos"
    }
  ],
  "executar": [
    {
      "nome": "novo_exe.exe",
      "ativo": true,
      "horario": "14:00",
      "intervalo": 60
    }
  ]
}


Campos importantes:

Campo	Descrição
versao	Versão remota do sistema. Atualização só ocorre se remota > local (versao.txt).
arquivos	Lista de arquivos que podem ser atualizados. Contém nome, url e descricao.
executar	Lista de novos executáveis que serão rodados automaticamente, com horário fixo ou intervalo. ativo controla se deve executar.
4. Descrição dos Executáveis
4.1 Launcher.exe

Programa principal, agora como serviço do Windows (Base Service - Monitoramento de Backup).

Funções:

Rodar em loop constante.

Baixar config remoto e verificar versão.

Executar updater se houver nova versão.

Executar valida_bkp.exe às 12h ou após updater.

Executar futuros EXEs do config, respeitando horários ou intervalos.

Mantém logs enxutos em launcher.log.

4.2 Updater.exe

Atualiza arquivos do sistema quando há nova versão.

Compara versão remota com local (versao.txt).

Baixa e substitui arquivos da lista arquivos.

Atualiza versao.txt.

Executa valida_bkp.exe após atualização.

Executa uma vez e encerra.

4.3 Valida_bkp.exe

Valida backups das lojas e envia relatórios para Google Sheets.

Roda:

Pelo launcher às 12h.

Sempre após updater.

Verifica existência de pastas e arquivos de backup.

Envia status OK ou ERRO.

4.4 Outros executáveis futuros

Adicionados via config (executar).

Podem ter horário fixo (horario) ou intervalo em minutos (intervalo).

Só rodam se ativo: true.

Permitem expansão do sistema sem alterar o launcher.

5. Serviço do Windows

Nome: Base Service - Monitoramento de Backup

Criado automaticamente pelo instalador.

Benefícios:

Executa ao iniciar o Windows.

Roda em segundo plano sem janelas.

Para verificar serviços: sc query.

Para deletar serviço: sc delete "Base Service - Monitoramento de Backup".

6. Controle de Logs

launcher.log registra eventos importantes:

Atualização de arquivos (updater)

Validação de backup (valida_bkp)

Execução de novos EXEs

Erros de download ou execução

Mantém apenas últimas 100 linhas.

7. Instalação

Execute o instalador como administrador, garantindo permissões completas para criar pastas e serviços.

O instalador cria automaticamente a pasta MonitoramentoBKP no local correto (C:\Program Files (x86)\).

Permissões: conceda permissão de leitura/escrita na pasta criada para o usuário SOMA.

O instalador cria o serviço do launcher automaticamente.

Configuração do serviço no Windows:

Abra o Gerenciador de Serviços (services.msc).

Localize o serviço: Base Service - Monitoramento de Backup.

Clique com o botão direito → Propriedades.

Na aba Recuperação:

Em Primeira falha, Segunda falha e Falhas posteriores, selecione Reiniciar o serviço.

Na aba Logon:

Marque Esta conta e informe o usuário SOMA com a senha correspondente.

Verifique se o serviço está em execução. O launcher iniciará automaticamente e gerenciará updater, valida e futuros EXEs conforme definido no config remoto.

8. Boas Práticas

Evitar executar manualmente o launcher quando o serviço já está ativo.

Não alterar executáveis enquanto o launcher está rodando.

Para rollback de versão, alterar manualmente versao.txt e reiniciar launcher.

Para adicionar novos executáveis, atualizar apenas o config remoto com ativo, horario ou intervalo.