@echo off
REM ============================================================================
REM  FARMA QUANTUM - Gerador de .EXE (Windows)
REM  Basta dar 2 cliques neste arquivo no Windows (com Python instalado).
REM  Resultado final:  dist\FarmaQuantum.exe
REM ============================================================================
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ===============================================
echo    FARMA QUANTUM - BUILD DO EXECUTAVEL (.EXE)
echo ===============================================
echo.

REM 1) Localiza o Python
where py >nul 2>&1 && (set "PY=py") || (set "PY=python")
%PY% --version >nul 2>&1 || (
    echo [ERRO] Python nao encontrado. Instale o Python 3.11 32-bit e tente de novo.
    pause
    exit /b 1
)
echo [1/5] Python encontrado.

REM 2) Descobre qual e o arquivo principal (.py)
set "FQ_MAIN="
if exist "Quantum_Farmacia.py"  set "FQ_MAIN=Quantum_Farmacia.py"
if exist "Quantum_Farmacia1.py" set "FQ_MAIN=Quantum_Farmacia1.py"
if "%FQ_MAIN%"=="" (
    echo [ERRO] Nao encontrei Quantum_Farmacia.py nem Quantum_Farmacia1.py nesta pasta.
    pause
    exit /b 1
)
echo [2/5] Script principal: %FQ_MAIN%

REM 3) Instala/atualiza as dependencias de build e de runtime
echo [3/5] Instalando dependencias (pode demorar na primeira vez)...
%PY% -m pip install --upgrade pip --quiet
%PY% -m pip install --upgrade pyinstaller pillow ^
    ttkbootstrap "mysql-connector-python==8.4.0" "reportlab>=4.0" "fpdf2>=2.7" ^
    "openpyxl>=3.1" "qrcode>=7.4" "pyserial>=3.5" "psutil==5.9.8" ^
    "flask>=3.0" "flask-cors>=4.0" "flask-socketio>=5.3" "pywin32>=306" --prefer-binary

REM 4) Gera o icone comercial (se ainda nao existir)
if not exist "farma_quantum.ico" (
    echo [4/5] Gerando icone comercial farma_quantum.ico ...
    %PY% tools\make_icon.py
) else (
    echo [4/5] Icone farma_quantum.ico ja existe.
)

REM 5) Empacota o .EXE com o PyInstaller usando o spec
echo [5/5] Gerando o executavel (.exe)...
set "FQ_MAIN=%FQ_MAIN%"
%PY% -m PyInstaller --noconfirm --clean farma_quantum.spec
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao gerar o executavel. Veja as mensagens acima.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo  CONCLUIDO! O executavel esta em:
echo     %CD%\dist\FarmaQuantum.exe
echo ===============================================
echo.
pause
endlocal
