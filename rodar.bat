@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Alexandria - verificacao local

REM ---------------------------------------------------------------------------
REM  Roda o projeto inteiro na sua maquina ANTES de subir pro GitHub.
REM  Instala, carrega a bronze, constroi as camadas, executa os 73 testes,
REM  gera a documentacao e diz se esta liberado para commitar.
REM  Basta dar dois cliques neste arquivo.
REM ---------------------------------------------------------------------------

cd /d "%~dp0"

echo.
echo ==================================================
echo   ALEXANDRIA - verificacao local antes do commit
echo ==================================================
echo.

echo %CD% | find /i "OneDrive" >nul
if not errorlevel 1 (
    echo [AVISO] Este projeto esta dentro do OneDrive.
    echo         Vai funcionar, mas o OneDrive tenta sincronizar os milhares de
    echo         arquivos do ambiente virtual e do banco, o que deixa tudo lento
    echo         e as vezes trava arquivo em uso.
    echo         Recomendado: mover a pasta para algo como C:\dev\alexandria.
    echo.
)

where python >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo        Instale em python.org e marque "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/6] Criando o ambiente virtual...
    python -m venv .venv
    if errorlevel 1 goto erro
) else (
    echo [1/6] Ambiente virtual ja existe.
)

set PY=.venv\Scripts\python.exe
set DBT=.venv\Scripts\dbt.exe

echo [2/6] Instalando dependencias...
"%PY%" -m pip install --quiet --upgrade pip
"%PY%" -m pip install --quiet -r requirements.txt
if errorlevel 1 goto erro

"%DBT%" deps
if errorlevel 1 goto erro

echo [3/6] Preparando os dados...
if exist "data\raw\olist_orders_dataset.csv" (
    echo       Usando o dataset real da Olist em data\raw.
    set ORIGEM=data\raw
) else (
    echo       Dataset real nao encontrado. Gerando amostra sintetica.
    echo       Para usar os dados reais, descompacte os CSVs da Olist em data\raw.
    "%PY%" scripts\gerar_amostra.py --destino data\sample --pedidos 4000
    if errorlevel 1 goto erro
    set ORIGEM=data\sample
)

echo [4/6] Carregando a camada bronze...
"%PY%" scripts\carregar_bronze.py --origem !ORIGEM!
if errorlevel 1 goto erro

echo [5/6] Construindo as camadas e rodando os testes...
"%DBT%" build --profiles-dir .
if errorlevel 1 goto testes_falharam

echo [6/6] Gerando a documentacao e o dashboard de qualidade...
"%DBT%" docs generate --profiles-dir .
if errorlevel 1 goto erro
"%PY%" scripts\resumo_testes.py
if errorlevel 1 goto erro
"%PY%" scripts\coletar_qualidade.py
if errorlevel 1 goto erro
"%PY%" scripts\gerar_dashboard.py
if errorlevel 1 goto erro

echo.
echo ==================================================
echo   TUDO PASSOU. LIBERADO PARA SUBIR PRO GITHUB.
echo ==================================================
echo.
echo O que acabou de acontecer aqui e exatamente o que o GitHub Actions
echo vai repetir depois do push. Se passou aqui, passa la.
echo.
echo Os arquivos gerados que PRECISAM ir para o git:
echo     site\resultados.json   placar da pagina do case
echo     site\qualidade.json    dados do dashboard de qualidade
echo     site\qualidade.html    dashboard pronto para publicar
echo     site\historico.jsonl   uma linha por build, alimenta a tendencia
echo.
echo Para ver o dashboard interativo:  .venv\Scripts\streamlit run app\dashboard_qualidade.py
echo Para ver o dashboard estatico:    abra site\qualidade.html
echo.
echo Para subir:
echo     git add .
echo     git commit -m "Alexandria: camadas, testes e documentacao"
echo     git push
echo.
echo O .gitignore ja deixa de fora o ambiente virtual, o banco, a pasta
echo target e os CSVs. Nada pesado vai junto.
echo.

choice /c SN /n /m "Quer abrir a documentacao com o grafo de linhagem agora? [S/N] "
if errorlevel 2 goto fim

echo.
echo Abrindo no navegador. Feche esta janela ou aperte Ctrl+C para encerrar.
echo.
"%DBT%" docs serve --profiles-dir .
goto fim

:testes_falharam
echo.
echo ==================================================
echo   ALGUM TESTE FALHOU - NAO SUBA AINDA
echo ==================================================
echo.
echo O detalhe de cada falha esta logo acima, e tambem em
echo target\run_results.json.
echo.
echo Isso e o comportamento esperado quando o dado chega fora do
echo combinado: o build para antes de o numero chegar no dashboard.
echo Se voce subir assim, o GitHub Actions vai reprovar tambem e o
echo selo do README fica vermelho.
echo.
pause
exit /b 1

:erro
echo.
echo [ERRO] Alguma etapa falhou. A mensagem esta logo acima.
echo.
pause
exit /b 1

:fim
echo.
pause
