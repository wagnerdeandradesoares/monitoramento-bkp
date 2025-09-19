Documentação do Script Python para Monitoramento de Backup e Envio de Dados para Google Sheets
Objetivo

Este script foi desenvolvido para monitorar o processo de backup em uma determinada pasta, verificar o status dos backups realizados, e enviar informações sobre esse status para uma planilha do Google Sheets.

Além disso, o script foi convertido em um arquivo executável .exe para facilitar a execução em máquinas Windows sem a necessidade de instalar o Python.

Funcionamento

O script realiza a verificação do backup em uma pasta local e coleta informações sobre a filial (loja) associada ao computador onde o script está sendo executado. Em seguida, ele envia essas informações para uma planilha do Google Sheets, onde são registradas informações como o status do backup e o código da filial.

Tecnologias Utilizadas

Python 3.x

Google Apps Script (para receber dados no Google Sheets)

winreg (para ler informações do registro do Windows)

socket (para obter o nome do host do computador)

datetime (para formatação de data e hora)

urllib.request (para fazer requisições HTTP)

PyInstaller (para converter o script Python em um arquivo executável .exe)

Estrutura do Código

Configuração Inicial

BASE_DIR: Caminho onde o backup será monitorado (exemplo: C:\backup_sql).

LOG_FILE: Caminho do arquivo de log onde os detalhes dos processos serão armazenados.

SHEET_URL: URL do Google Apps Script que recebe os dados para a planilha.

Funções do Script

log(message): Função para registrar mensagens no arquivo de log e exibi-las no terminal. A função cria o arquivo de log se não existir.

send_to_sheet(filial_id, status, detalhe): Função para enviar dados (status do backup) para o Google Sheets. Utiliza a URL do Google Apps Script para realizar um POST com os dados.

get_loja_code(): Função que acessa o registro do Windows para recuperar o código da filial. A chave do registro é: Software\Linx Sistemas\LinxPOS-e, e o valor esperado é Código da loja.

check_backup(): Função principal que verifica o status do backup. Ela verifica a existência de uma pasta principal e suas subpastas. Caso a pasta ou as subpastas estejam vazias, ela registra o erro no log e envia um alerta para o Google Sheets. Caso contrário, ela envia uma confirmação de que o backup foi realizado corretamente.

Passo a Passo do Script

Leitura do Código da Filial:
O script acessa o registro do Windows para obter o código da filial, que é utilizado na mensagem de log e enviado para o Google Sheets.

Verificação do Backup:
O script verifica se a pasta onde os backups são armazenados existe (BASE_DIR). Em seguida, ele lista as subpastas e verifica se há arquivos nelas. Caso as subpastas estejam vazias ou a pasta principal não exista, o script gera um log de erro e envia uma notificação para o Google Sheets.

Envio para o Google Sheets:
Após a verificação, o script envia os dados (status do backup, código da filial, nome do computador e detalhes) para uma planilha do Google Sheets usando um script do Google Apps (feito em Apps Script).

Função Google Apps Script

O Google Apps Script é utilizado para receber os dados e registrar as informações na planilha. Este script pode ser configurado no Google Sheets para processar os dados enviados pelo script Python.

Código do Google Apps Script
function doPost(e) {
  var SHEET_ID = "1kwFjRYRTy3OAPJjgn8ZYS_jLSJiLDDoJPaOKczQhQ9A";
  var SHEET_NAME = "pagina2";

  var lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) {
    return ContentService.createTextOutput(JSON.stringify({result:"error", message:"Could not obtain lock"})).setMimeType(ContentService.MimeType.JSON);
  }

  try {
    var payload = {};
    if (e && e.postData && e.postData.contents) {
      payload = JSON.parse(e.postData.contents);
    }

    var filialRaw = payload.filial || "";
    var status = payload.status || "";
    var detalhe = payload.detalhe || "";
    var dataIso = payload.data || new Date().toISOString();

    var filial = normalizeString(filialRaw);

    var ss = SpreadsheetApp.openById(SHEET_ID);
    var sheet = ss.getSheetByName(SHEET_NAME);
    if (!sheet) {
      sheet = ss.getSheets()[0];
    }

    var lastRow = sheet.getLastRow();
    var result = { action: "none", row: null };

    if (lastRow < 2) {
      sheet.appendRow([dataIso, filialRaw, status, detalhe]);
      result.action = "created";
      result.row = 2;
      return ContentService.createTextOutput(JSON.stringify({result: "ok", info: result}))
                           .setMimeType(ContentService.MimeType.JSON);
    }

    var numRows = lastRow - 1;
    var colBvals = sheet.getRange(2, 2, numRows, 1).getValues();
    var foundRow = -1;

    for (var i = 0; i < colBvals.length; i++) {
      var cell = colBvals[i][0];
      var cellNorm = normalizeString(cell);
      if (cellNorm === filial) {
        foundRow = i + 2;
        break;
      }
    }

    if (foundRow !== -1) {
      var currentStatus = sheet.getRange(foundRow, 3).getValue();
      if (String(currentStatus) !== String(status)) {
        sheet.getRange(foundRow, 1).setValue(dataIso);
        sheet.getRange(foundRow, 3).setValue(status);
        sheet.getRange(foundRow, 4).setValue(detalhe);
        result.action = "updated";
        result.row = foundRow;
      } else {
        result.action = "unchanged";
        result.row = foundRow;
      }
    } else {
      sheet.appendRow([dataIso, filialRaw, status, detalhe]);
      result.action = "created";
      result.row = sheet.getLastRow();
    }

    return ContentService.createTextOutput(JSON.stringify({result:"ok", info: result}))
                         .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({result:"error", message: err.toString()}))
                         .setMimeType(ContentService.MimeType.JSON);
  } finally {
    try { lock.releaseLock(); } catch(e){ /* ignore */ }
  }
}

function normalizeString(v) {
  if (v === null || v === undefined) return "";
  try {
    var s = v.toString();
    s = s.replace(/\u00A0/g, " ").replace(/\s+/g, " ").trim();
    return s.toUpperCase();
  } catch (e) {
    return "";
  }
}

Configuração Necessária no Google Sheets

Planilha:

Crie uma planilha no Google Sheets e configure a primeira linha com os seguintes cabeçalhos: Data, Filial, Status, Detalhe.

Script Google Apps:

Crie um novo Google Apps Script a partir da planilha e cole o código fornecido.

Salve e implemente o script como um Web App para obter a URL (que será usada no script Python).

Configure o script para permitir acesso anônimo se for necessário.

Execução do Script Python

O script Python pode ser executado manualmente ou agendado para rodar periodicamente (por exemplo, usando o Task Scheduler no Windows).

Para rodar o script, basta executar:

python valida_bkp.py


O script verificará a pasta de backup, coletará o código da filial, verificará as subpastas e enviará os resultados para o Google Sheets.

Geração do Arquivo Executável (.exe)

Para facilitar a execução do script sem a necessidade de instalar o Python, o script foi convertido em um arquivo executável utilizando a ferramenta PyInstaller. A geração do arquivo .exe permite que o script seja executado diretamente em máquinas Windows, mesmo que o Python não esteja instalado.

Como Gerar o .exe

Certifique-se de ter o PyInstaller instalado. Caso não tenha, instale com o comando:

pip install pyinstaller


No diretório onde o script valida_bkp.py está localizado, execute o seguinte comando para gerar o arquivo .exe:

pyinstaller --onefile --windowed valida_bkp.py


O arquivo executável será gerado na pasta dist dentro do seu diretório de trabalho. Agora você pode executar o arquivo .exe diretamente em qualquer máquina Windows.

Considerações Finais

Permissões de Acesso: Certifique-se de que a conta usada no Google Apps Script tenha permissão para editar a planilha.

Execução Local: O script Python pode ser executado como .exe em qualquer computador sem a necessidade de instalar o Python.

Manejo de Erros: O script registra mensagens de erro tanto no log local quanto no Google Sheets, permitindo rastrear qualquer problema durante a execução.