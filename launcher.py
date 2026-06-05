#!/usr/bin/env python3
"""
Ponto de entrada para o executavel (.exe) gerado pelo PyInstaller.

Ao abrir o programa, ele:
    1. conecta ao MySQL;
    2. sobe o servidor web local;
    3. abre o navegador automaticamente na interface da IA.

A janela de console fica aberta mostrando o status; feche-a (ou Ctrl+C) para
encerrar a IA.
"""

from __future__ import annotations

import os
import sys

import web


def main() -> int:
    host = os.environ.get("IA_HOST", "127.0.0.1")
    port = int(os.environ.get("IA_PORT", "5000"))
    threshold = float(os.environ.get("IA_THRESHOLD", "0.30"))

    print("=" * 60)
    print(" PHDA CEREBROZ")
    print(" Iniciando servidor e abrindo o navegador...")
    print("=" * 60)

    code = web.run_server(
        host=host, port=port, threshold=threshold, open_browser=True
    )

    if code != 0:
        # Mantem a janela aberta para o usuario ler o erro (ex.: falha no MySQL).
        try:
            input("\nPressione Enter para fechar...")
        except EOFError:
            pass
    return code


if __name__ == "__main__":
    sys.exit(main())
