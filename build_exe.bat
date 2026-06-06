@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================================
REM  PDV QUANTUM FARMACIA - SCRIPT DE BUILD (.py  ->  .exe)
REM  Compila o sistema em um executavel com TODAS as dependencias via PyInstaller.
REM  Uso: clique duas vezes neste arquivo (de preferencia "Executar como admin").
REM ============================================================================

title PDV Quantum Farmacia - Compilador para EXE

REM ====== CONFIGURACOES (edite somente se precisar) ===========================
set "SCRIPT=Quantum_igor.py"
set "APPNAME=PDV_Quantum_Farmacia"
set "ICON=icone.ico"
REM  BUILD_MODE  : onefile (1 unico .exe)  ou  onedir (pasta com .exe + libs)
set "BUILD_MODE=onefile"
REM  WINDOW_MODE : windowed (sem console)  ou  console (mostra terminal/debug)
set "WINDOW_MODE=windowed"
set "LOG=build_log.txt"
REM ============================================================================

cd /d "%~dp0"
break > "%LOG%"

echo ============================================================================
echo    PDV QUANTUM FARMACIA - COMPILADOR PARA .EXE
echo ============================================================================
echo.

REM ------ 1) Verifica o Python -------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado no PATH.
    echo        Instale o Python 3.8 ou superior ^(64-bit^) em:
    echo        https://www.python.org/downloads/
    echo        e marque a opcao "Add Python to PATH" durante a instalacao.
    goto :fim_erro
)

for /f "delims=" %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
echo [INFO] %PYVER%
python -c "import struct;print('[INFO] Arquitetura do Python:', struct.calcsize('P')*8, 'bits')"
python -c "import struct,sys;sys.exit(0 if struct.calcsize('P')*8==64 else 1)"
if errorlevel 1 (
    echo [AVISO] Python 32-bit detectado. numpy/Flask-SocketIO podem ter limitacoes.
    echo         Para um build completo, recomenda-se o Python 64-bit.
)

if not exist "%SCRIPT%" (
    echo [ERRO] O arquivo "%SCRIPT%" nao foi encontrado nesta pasta:
    echo        %CD%
    goto :fim_erro
)

REM ------ 2) Atualiza as ferramentas de build ---------------------------------
echo.
echo [PASSO 1/4] Atualizando pip, setuptools e wheel...
python -m pip install --upgrade pip setuptools wheel >>"%LOG%" 2>&1
if errorlevel 1 echo [AVISO] Nao foi possivel atualizar o pip (continuando)...

REM ------ 3) Instala as dependencias OBRIGATORIAS -----------------------------
echo.
echo [PASSO 2/4] Instalando dependencias do projeto (pode demorar alguns minutos)...
set "PKGS=pyinstaller ttkbootstrap Pillow reportlab fpdf2 pyserial bcrypt cryptography numpy qrcode openpyxl psutil flask flask-cors flask-socketio pywin32"
for %%P in (%PKGS%) do (
    echo    - Instalando %%P ...
    python -m pip install --upgrade %%P >>"%LOG%" 2>&1
    if errorlevel 1 echo      [AVISO] Falha ao instalar %%P  ^(detalhes em %LOG%^)
)

REM ------ 3b) Dependencias OPCIONAIS (nao bloqueiam o build) -------------------
echo.
echo [PASSO 2b] Dependencias opcionais (USB / Bluetooth)...
for %%P in (pyusb bleak) do (
    echo    - Instalando %%P (opcional) ...
    python -m pip install --upgrade %%P >>"%LOG%" 2>&1
)

REM ------ 4) Limpa builds anteriores ------------------------------------------
echo.
echo [PASSO 3/4] Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%APPNAME%.spec" del /q "%APPNAME%.spec"

REM ------ 5) Monta os argumentos do PyInstaller -------------------------------
set "PI_ARGS=--noconfirm --clean --name %APPNAME%"
if /i "%BUILD_MODE%"=="onefile"   set "PI_ARGS=%PI_ARGS% --onefile"
if /i "%WINDOW_MODE%"=="windowed" set "PI_ARGS=%PI_ARGS% --windowed"
if exist "%ICON%" set "PI_ARGS=%PI_ARGS% --icon %ICON%"

REM  Coleta completa de pacotes que possuem dados/temas/fontes
set "PI_ARGS=%PI_ARGS% --collect-all ttkbootstrap --collect-all reportlab --collect-all qrcode"

REM  Hidden imports que o PyInstaller costuma nao detectar sozinho
set "HID=PIL._tkinter_finder win32timezone win32print win32api win32con win32ui pywintypes pythoncom engineio.async_drivers.threading flask_socketio flask_cors serial.tools.list_ports numpy"
for %%H in (%HID%) do set "PI_ARGS=!PI_ARGS! --hidden-import %%H"

echo.
echo [PASSO 4/4] Compilando com PyInstaller...
echo    Modo: %BUILD_MODE%  /  %WINDOW_MODE%
echo    Aguarde, isso pode levar varios minutos...
echo.
python -m PyInstaller %PI_ARGS% "%SCRIPT%" 2>>"%LOG%"
if errorlevel 1 (
    echo.
    echo [ERRO] A compilacao falhou. Consulte o arquivo "%LOG%" e a saida acima.
    goto :fim_erro
)

echo.
echo ============================================================================
echo    [OK] BUILD CONCLUIDO COM SUCESSO!
echo.
if /i "%BUILD_MODE%"=="onefile" (
    echo    Executavel gerado em:  %CD%\dist\%APPNAME%.exe
) else (
    echo    Executavel gerado em:  %CD%\dist\%APPNAME%\%APPNAME%.exe
)
echo ============================================================================
if exist dist start "" explorer "%CD%\dist"
goto :fim_ok

:fim_erro
echo.
pause
exit /b 1

:fim_ok
echo.
echo Pressione qualquer tecla para sair...
pause >nul
exit /b 0
