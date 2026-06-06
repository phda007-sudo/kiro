# -*- mode: python ; coding: utf-8 -*-
# ============================================================================
#  PyInstaller spec do FARMA QUANTUM
#  Gera um unico .exe (onefile) com o icone comercial farma_quantum.ico,
#  empacotando todas as dependencias usadas pelo sistema (mysql-connector
#  com locales/plugins, ttkbootstrap com temas, Pillow, reportlab, etc.).
#
#  Como usar (no Windows, com Python 32-bit recomendado p/ este sistema):
#     pip install pyinstaller
#     pyinstaller --noconfirm farma_quantum.spec
#  O executavel sai em:  dist\FarmaQuantum.exe
# ============================================================================
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Permite trocar o nome do script-fonte via variavel de ambiente
# (ex.: set FQ_MAIN=Quantum_Farmacia1.py) sem editar este arquivo.
MAIN_SCRIPT = os.environ.get("FQ_MAIN", "Quantum_Farmacia.py")
ICON_FILE = "farma_quantum.ico"

datas = []
binaries = []
hiddenimports = []

# Inclui o proprio icone dentro do .exe (util para definir o icone da janela
# em runtime, se desejado).
if os.path.exists(ICON_FILE):
    datas.append((ICON_FILE, "."))

# Coleta COMPLETA (modulos + dados) das libs que costumam quebrar em .exe.
for _pkg in [
    "ttkbootstrap",        # temas/estilos (precisa dos arquivos de tema)
    "mysql.connector",     # inclui locales/eng e plugins de autenticacao
    "PIL",
    "reportlab",
    "fpdf",
    "openpyxl",
    "qrcode",
    "serial",
    "engineio",
    "socketio",
    "flask_socketio",
    "flask_cors",
    "flask",
]:
    try:
        d, b, h = collect_all(_pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# Garante explicitamente os modulos de localizacao e plugins do MySQL,
# que o sistema importa dinamicamente (corrige "No localization support
# for language 'eng'" e "Authentication plugin ... is not supported").
hiddenimports += [
    "mysql.connector.locales",
    "mysql.connector.locales.eng",
    "mysql.connector.locales.eng.client_error",
    "mysql.connector.locales.client_error",
    "mysql.connector.plugins",
    "mysql.connector.plugins.mysql_native_password",
    "mysql.connector.plugins.caching_sha2_password",
    "mysql.connector.plugins.sha256_password",
    "mysql.connector.plugins.mysql_clear_password",
]
try:
    hiddenimports += collect_submodules("mysql.connector.plugins")
    hiddenimports += collect_submodules("mysql.connector.locales")
except Exception:
    pass

# Modulos opcionais (nao falha se nao estiverem instalados)
for _opt in ["psutil", "bleak"]:
    hiddenimports.append(_opt)

# pywin32 (impressao termica/spooler e APIs do Windows). Garante que os
# submodulos usados sejam incluidos no .exe.
for _w in ["win32print", "win32api", "win32con", "pywintypes", "pythoncom",
           "win32gui", "win32ui", "win32file", "win32event", "winerror",
           "win32com", "win32com.client"]:
    hiddenimports.append(_w)
try:
    hiddenimports += collect_submodules("win32com")
except Exception:
    pass
try:
    d, b, h = collect_all("win32com")
    datas += d
    binaries += b
    hiddenimports += h
except Exception:
    pass

a = Analysis(
    [MAIN_SCRIPT],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tests", "tkinter.test"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="FarmaQuantum",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # UPX desligado: reduz falsos positivos de antivirus
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,             # GUI (sem janela de console). Use True p/ depurar.
    disable_windowed_traceback=False,
    icon=ICON_FILE,
    version=None,
)
