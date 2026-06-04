# -*- mode: python ; coding: utf-8 -*-
"""
Spec do PyInstaller para gerar o executavel da IA (arquivo unico).

Build:
    pip install -r requirements.txt pyinstaller
    pyinstaller --noconfirm intart-ia.spec

Resultado: dist/intart-ia.exe  (no Windows) ou dist/intart-ia (no Linux/macOS).

Use collect_all para incluir dados/imports ocultos das dependencias que
costumam precisar (Flask/Jinja, pdfminer, python-docx, openpyxl, lxml).
"""

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = ["pymysql"]

for _pkg in (
    "flask",
    "jinja2",
    "werkzeug",
    "click",
    "blinker",
    "markupsafe",
    "pdfminer",
    "docx",
    "openpyxl",
    "lxml",
):
    try:
        _d, _b, _h = collect_all(_pkg)
        datas += _d
        binaries += _b
        hiddenimports += _h
    except Exception:
        # Dependencia opcional ausente: segue sem ela (degradacao graciosa).
        pass

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="intart-ia",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
