@ECHO OFF
setlocal enabledelayedexpansion

:: ============================
:: CONFIGURAÇÕES
:: ============================
set ROOTDIR=C:\backup_sql

set EMAIL_FROM=wagnergw770@gmail.com
set EMAIL_TO=wagner.soares@somagrupo.com.br
set SMTP_SERVER=smtp.gmail.com
set SMTP_PORT=587
set EMAIL_USER=wagnergw770@gmail.com
set EMAIL_PASS=fuwtrculwzolmmac
set ALERTA=0
set SUBPASTAS_VAZIAS=
:: ============================

:: Captura nome do computador
set PCNAME=%COMPUTERNAME% 
set DATA=%DATE% %TIME%

:: Verifica se a pasta principal existe
if not exist "%ROOTDIR%" (
    echo [%DATA%] Pasta %ROOTDIR% NÃO encontrada!
    set ALERTA=1
    set SUBPASTAS_VAZIAS=Pasta principal nao encontrada
) else (
    :: Variável para controlar se existe alguma subpasta
    set TEM_SUBPASTA=0

    :: Loop em todas as subpastas dentro de ROOTDIR
    for /d %%D in ("%ROOTDIR%\*") do (
        set TEM_SUBPASTA=1
        set SUBPASTA=%%~fD

        :: Lista apenas arquivos (sem subpastas)
        dir /a:-d /b "!SUBPASTA!" >nul 2>&1

        if errorlevel 1 (
            echo [%DATA%] Subpasta "!SUBPASTA!" está VAZIA!
            set ALERTA=1
            set SUBPASTAS_VAZIAS=!SUBPASTAS_VAZIAS! %%~nxD
        ) else (
            echo [%DATA%] Subpasta "!SUBPASTA!" contém arquivos. OK.
        )
    )

    :: Se não encontrou nenhuma subpasta
    if !TEM_SUBPASTA! == 0 (
        echo [%DATA%] Nenhuma subpasta encontrada dentro de "%ROOTDIR%"!
        set ALERTA=1
        set SUBPASTAS_VAZIAS=Nenhuma subpasta encontrada
    )
)

:: Se algum alerta foi detectado, dispara e-mail
if %ALERTA%==1 (
    echo [%DATA%] Enviando alerta por e-mail...

    powershell -ExecutionPolicy Bypass -Command ^
        "$user='%EMAIL_USER%';" ^
        "$pass=ConvertTo-SecureString '%EMAIL_PASS%' -AsPlainText -Force;" ^
        "$cred=New-Object System.Management.Automation.PSCredential($user,$pass);" ^
        "$body=\"Backup nao encontrado`r`nData: %DATA%`r`nSubpasta vazio ou inexistente: %SUBPASTAS_VAZIAS%`r`nNa filial: %PCNAME%\";" ^
        "Send-MailMessage -From $user -To '%EMAIL_TO%' -Subject 'ALERTA: Backup - %PCNAME%' -Body $body -SmtpServer '%SMTP_SERVER%' -Port %SMTP_PORT% -UseSsl -Credential $cred"

    echo [%DATA%] Alerta enviado!
) else (
    echo [%DATA%] Todas as subpastas possuem arquivos. Nenhum alerta necessário.
)


endlocal
exit
