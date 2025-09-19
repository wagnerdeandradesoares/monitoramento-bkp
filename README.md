MonitoramentoBKP

MonitoramentoBKP é um sistema projetado para monitorar backups de dados em filiais, verificando a integridade dos arquivos de backup e enviando alertas em tempo real caso haja problemas. O sistema também inclui funcionalidades de atualização automática e uma instalação simplificada através de um instalador.

📂 Estrutura de Diretórios

A estrutura de diretórios do projeto é organizada de forma a facilitar a manutenção e a distribuição do software. Veja como o repositório está estruturado:

MonitoramentoBKP/
│
├── src/                    # Código fonte do projeto
│   ├── valida_bkp.py       # Script responsável pela verificação e monitoramento dos backups
│   └── updater.py          # Script para atualização automática do sistema
│
├── dist/                   # Arquivos distribuíveis (executáveis e versão)
│   ├── valida_bkp.exe      # Executável do script de validação de backup
│   ├── updater.exe         # Executável do script de atualização
│   └── versao.txt          # Arquivo contendo a versão do sistema
│   └── instalador.exe      # Instalador do sistema para facilitar a instalação
│
├── .gitignore              # Arquivo para configuração do Git e ignorar arquivos desnecessários
└── README.md               # Arquivo de documentação do projeto

📜 Descrição dos Arquivos
src/ - Código Fonte

valida_bkp.py: Script principal que monitora o processo de backup. Verifica se os arquivos estão presentes nas pastas designadas e envia alertas via Google Sheets caso o backup esteja incompleto ou com falhas.

updater.py: Responsável por manter o sistema atualizado. Este script verifica se há novas versões disponíveis, baixa os arquivos necessários e realiza a instalação das atualizações automaticamente.

dist/ - Arquivos Distribuíveis

valida_bkp.exe: Arquivo executável gerado a partir do script valida_bkp.py. Pode ser executado em máquinas Windows para realizar o monitoramento de backups.

updater.exe: Arquivo executável gerado a partir do script updater.py, utilizado para realizar a atualização automática do sistema.

versao.txt: Arquivo simples contendo a versão do sistema. Utilizado para verificar se o sistema está atualizado.

instalador.exe: Arquivo do instalador que facilita a instalação e configuração do sistema em máquinas Windows, sem a necessidade de interação com o código-fonte.

README.md

Este é o arquivo de documentação do projeto. Ele descreve como configurar, instalar, executar e contribuir para o projeto.

⚙️ Como Usar
Requisitos:

Python 3.x: Certifique-se de que o Python esteja instalado na sua máquina.

Bibliotecas: Algumas bibliotecas podem ser necessárias para rodar o projeto. Estas bibliotecas estão listadas no arquivo requirements.txt (se existir). Para instalá-las, basta rodar o seguinte comando:

pip install -r requirements.txt

Passos para Instalação
1. Instalar Dependências

Caso o projeto utilize dependências externas, você pode instalá-las com o seguinte comando:

pip install -r requirements.txt

2. Rodar os Scripts

Para rodar o script que verifica o backup:

python src/valida_bkp.py


Para rodar o script de atualização automática:

python src/updater.py

3. Instalar o Sistema

Se você deseja distribuir o software, pode gerar executáveis a partir dos scripts usando ferramentas como PyInstaller ou cx_Freeze. Isso permite que os arquivos .exe sejam rodados em sistemas Windows sem a necessidade de Python instalado.

Executar o Instalador

Caso tenha o instalador (instalador.exe), basta rodá-lo para instalar o sistema de forma automatizada.

🛠️ Como Funciona
Monitoramento de Backup

O script valida_bkp.py realiza o monitoramento do backup verificando as pastas designadas. Se um backup não for encontrado ou se uma pasta estiver vazia, o script envia um alerta com as informações do erro. O sistema pode ser configurado para enviar os alertas para um Google Sheets para facilitar o acompanhamento remoto.

Atualização Automática

O script updater.py verifica a versão atual do sistema, compara com a versão mais recente e, caso necessário, faz o download e a instalação das últimas atualizações, garantindo que o sistema esteja sempre atualizado.

Instalação e Configuração

O arquivo instalador.exe foi criado para facilitar a instalação do sistema, configurando o ambiente de forma automatizada. O usuário precisa apenas executar o instalador e seguir as instruções.

🤝 Contribuindo

Contribuições são sempre bem-vindas! Caso queira contribuir para o projeto, siga as etapas abaixo:

Faça um fork deste repositório.

Crie uma branch para sua feature (git checkout -b minha-feature).

Faça suas alterações e commit (git commit -am 'Adicionando nova feature').

Envie sua branch para o repositório remoto (git push origin minha-feature).

Abra um pull request no repositório principal.

Como Submeter um Pull Request

Fork o repositório.

Clone o repositório para sua máquina local.

Crie uma nova branch para sua funcionalidade (git checkout -b minha-nova-feature).

Realize as alterações no código ou na documentação.

Comite as alterações (git commit -am 'Adicionando nova funcionalidade').

Push para o repositório remoto (git push origin minha-nova-feature).

Abra um pull request para revisão.

📜 Licença

Este projeto é licenciado sob a MIT License - veja o arquivo LICENSE
 para mais detalhes.

💬 Suporte

Caso tenha dúvidas ou precise de ajuda, entre em contato com a comunidade ou abra uma issue no GitHub.

👨‍💻 Autor

Feito por Wagner Soares - GitHub