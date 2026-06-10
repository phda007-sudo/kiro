@echo off
REM ============================================================================
REM  FARMA QUANTUM - ZERAR ESTOQUE (quantidade) de TODOS os produtos
REM  Define estoque = 0 em todos os produtos do banco 'farmacia'.
REM  NAO altera preco nem estoque minimo.
REM ============================================================================
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ===========================================================
echo   FARMA QUANTUM - ZERAR ESTOQUE DE TODOS OS PRODUTOS
echo   (a quantidade em estoque ira para 0 em TODOS os itens)
echo ===========================================================
echo.

set /p CONF=Tem certeza que deseja ZERAR o estoque de TODOS os produtos? (S/N): 
if /I not "%CONF%"=="S" (echo Operacao cancelada. & pause & exit /b 0)

where py >nul 2>&1 && (set "PY=py") || (set "PY=python")
%PY% --version >nul 2>&1 || (echo [ERRO] Python nao encontrado. & pause & exit /b 1)

set "SCRIPT=tools\zerar_estoque.py"
if not exist "%SCRIPT%" set "SCRIPT=zerar_estoque.py"
if not exist "%SCRIPT%" (echo [ERRO] script zerar_estoque.py nao encontrado. & pause & exit /b 1)

echo Instalando dependencia (mysql-connector)...
%PY% -m pip install --upgrade "mysql-connector-python==8.4.0" --quiet

echo Zerando estoque...
%PY% "%SCRIPT%"
if errorlevel 1 (echo. & echo [ERRO] Falha. Veja as mensagens acima. & pause & exit /b 1)

echo.
echo CONCLUIDO! Estoque de todos os produtos zerado.
pause
endlocal
