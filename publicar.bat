@echo off
setlocal
chcp 65001 >nul
title Alexandria - copiar para o clone do git

REM ---------------------------------------------------------------------------
REM  Copia desta pasta de teste para o clone do repositorio, deixando de fora
REM  tudo o que nao deve ser versionado (.venv, target, dbt_packages, data,
REM  logs e o proprio banco). Depois e so commitar no clone.
REM ---------------------------------------------------------------------------

cd /d "%~dp0"

echo.
echo ==================================================
echo   Copiar Alexandria para o clone do repositorio
echo ==================================================
echo.
echo Origem:  %CD%
echo.

set "DESTINO=%~1"
if "%DESTINO%"=="" (
    echo Arraste a pasta do clone para cima desta janela e aperte Enter,
    echo ou digite o caminho completo. Exemplo:
    echo     C:\Users\%USERNAME%\OneDrive\Area de Trabalho\alexandria
    echo.
    set /p DESTINO="Pasta do clone: "
)

REM Tira aspas que o arrastar-e-soltar adiciona.
set "DESTINO=%DESTINO:"=%"

if "%DESTINO%"=="" goto sem_destino
if not exist "%DESTINO%" goto nao_existe

echo.
echo Destino: %DESTINO%
echo.

if not exist "%DESTINO%\.git" (
    echo [AVISO] Nao encontrei uma pasta .git no destino.
    echo         Tem certeza de que esse e o clone do repositorio?
    echo.
    choice /c SN /n /m "Continuar mesmo assim? [S/N] "
    if errorlevel 2 goto cancelado
)

echo ATENCAO: a copia espelha a origem. Arquivos que existirem no destino
echo          e nao existirem aqui serao APAGADOS la (a pasta .git e poupada).
echo.
choice /c SN /n /m "Confirmar a copia para a pasta acima? [S/N] "
if errorlevel 2 goto cancelado

echo.
echo Copiando...
echo.

REM /MIR espelha, entao o que voce apagar aqui tambem some la. As exclusoes
REM cobrem tudo o que o .gitignore ja ignora, para nao levar 30 mil arquivos
REM do ambiente virtual para dentro do OneDrive.
robocopy "%CD%" "%DESTINO%" /MIR ^
    /XD ".venv" "dbt_packages" "target" "logs" "data" ".git" "__pycache__" ".dbt" ^
    /XF "*.duckdb" "*.duckdb.wal" "*.pyc" ".user.yml" "package-lock.yml" ^
    /NFL /NDL /NJH /NJS /NP

if errorlevel 8 goto erro_copia

echo.
echo ==================================================
echo   COPIA CONCLUIDA
echo ==================================================
echo.
echo Agora, no clone:
echo     cd /d "%DESTINO%"
echo     git add .
echo     git status
echo     git commit -m "Alexandria: dashboard de qualidade"
echo     git push
echo.
echo Confira no git status se os arquivos gerados foram junto:
echo     site\resultados.json  site\qualidade.json
echo     site\qualidade.html   site\historico.jsonl
echo.
echo Se eles nao aparecerem, rode o rodar.bat aqui antes e copie de novo.
echo.
goto fim

:sem_destino
echo.
echo [ERRO] Nenhuma pasta informada.
goto fim

:nao_existe
echo.
echo [ERRO] A pasta nao existe: %DESTINO%
echo        Clone o repositorio primeiro.
goto fim

:erro_copia
echo.
echo [ERRO] A copia falhou. A mensagem do robocopy esta acima.
goto fim

:cancelado
echo.
echo Cancelado. Nada foi copiado.

:fim
echo.
pause
