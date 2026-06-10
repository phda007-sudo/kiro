@echo off
REM ============================================================================
REM  FARMA QUANTUM - Gerar backup de produtos (pacote Farmacia Popular 2026)
REM  Gera: produtos_farmacia_popular_import.csv (importar via Ctrl+I)
REM        products_backup.json + categorias_backup.json (backup)
REM  E TAMBEM carrega os produtos direto no banco 'farmacia' (MySQL).
REM  Todos os produtos: preco R$ 1,00 | estoque 10 | estoque minimo 1.
REM
REM  Uso: 2 cliques (procura o zip nesta pasta) ou ARRASTE o zip sobre este .bat
REM ============================================================================
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ===========================================================
echo   FARMA QUANTUM - BACKUP DE PRODUTOS (FARMACIA POPULAR)
echo ===========================================================
echo.

where py >nul 2>&1 && (set "PY=py") || (set "PY=python")
%PY% --version >nul 2>&1 || (echo [ERRO] Python nao encontrado. & pause & exit /b 1)

REM Localiza o script conversor (em tools\ ou na pasta atual)
set "SCRIPT=tools\gerar_bkp_produtos_farmacia_popular.py"
if not exist "%SCRIPT%" set "SCRIPT=gerar_bkp_produtos_farmacia_popular.py"
if not exist "%SCRIPT%" (echo [ERRO] script conversor nao encontrado. & pause & exit /b 1)

REM Pacote: arrastado sobre o .bat (%1) ou nome padrao nesta pasta
set "ZIP=%~1"
if "%ZIP%"=="" set "ZIP=pacote_medicamentos_ean_farmacia_popular_2026.zip"
if not exist "%ZIP%" (
  echo [ERRO] Pacote nao encontrado: %ZIP%
  echo Coloque o zip nesta pasta OU arraste o arquivo .zip sobre este .bat.
  pause & exit /b 1
)
echo [1/3] Pacote: %ZIP%

echo [2/3] Instalando dependencias (mysql-connector, openpyxl)...
%PY% -m pip install --upgrade pip --quiet
%PY% -m pip install --upgrade "mysql-connector-python==8.4.0" openpyxl --quiet

echo [3/3] Gerando CSV + JSON e carregando no MySQL...
%PY% "%SCRIPT%" "%ZIP%" --mysql
if errorlevel 1 (echo. & echo [ERRO] Falha. Veja as mensagens acima. & pause & exit /b 1)

echo.
echo ===========================================================
echo  CONCLUIDO!
echo    - produtos_farmacia_popular_import.csv   (importar via Ctrl+I)
echo    - products_backup.json / categorias_backup.json
echo    - Produtos tambem inseridos no banco 'farmacia'
echo  Todos: preco R$ 1,00 ^| estoque 10 ^| estoque minimo 1
echo ===========================================================
pause
endlocal
