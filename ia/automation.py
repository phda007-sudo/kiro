"""
Automacao de tarefas com arquivos para a PHDA CEREBROZ.

Capacidades (locais, com limites de seguranca):
    - inspect(): analisa QUALQUER arquivo
        * .py            -> estrutura via AST (funcoes, classes, imports, sintaxe)
        * .exe/.dll      -> cabecalho PE (assinatura, arquitetura, secoes)
        * .apk/.jar/.zip -> conteudo do pacote (apk = zip; le AndroidManifest)
        * .docx/.xlsx    -> pacote office (zip)
        * texto/codigo   -> conteudo
        * outros         -> tipo por "magic bytes" + metadados
    - third_party_imports()/auto_install(): descobre e BAIXA as bibliotecas
      que um codigo Python precisa (pip).
    - run_python(): executa um script Python (subprocesso, com timeout).
    - build_exe(): empacota um .py em executavel (PyInstaller), best-effort.

Observacao de seguranca: este modulo NAO reescreve binarios arbitrarios
(.exe/.apk ja compilados) nem baixa/roda programas fora do escopo da tarefa.
O caminho suportado para "criar um .exe" e a partir de codigo-fonte.
"""

from __future__ import annotations

import ast
import io
import os
import struct
import subprocess
import sys
import zipfile

# Conjunto de modulos da biblioteca padrao (para nao tentar instalar via pip).
try:
    _STDLIB = set(sys.stdlib_module_names)  # Python 3.10+
except AttributeError:  # Python 3.9
    _STDLIB = {
        "os", "sys", "re", "json", "math", "time", "datetime", "random",
        "subprocess", "collections", "itertools", "functools", "typing",
        "pathlib", "io", "struct", "zipfile", "ast", "urllib", "http",
        "socket", "ssl", "sqlite3", "hashlib", "base64", "logging", "argparse",
        "threading", "multiprocessing", "csv", "unittest", "asyncio", "shutil",
        "tempfile", "glob", "enum", "dataclasses", "decimal", "statistics",
        "string", "textwrap", "uuid", "copy", "queue", "heapq", "bisect",
        "pickle", "gzip", "tarfile", "xml", "html", "email", "ftplib",
        "smtplib", "unicodedata", "secrets", "abc", "contextlib", "inspect",
        "importlib", "platform", "signal", "traceback", "warnings", "weakref",
    }

# import -> nome do pacote no pip (quando diferem).
IMPORT_TO_PACKAGE = {
    "cv2": "opencv-python", "PIL": "Pillow", "bs4": "beautifulsoup4",
    "yaml": "PyYAML", "sklearn": "scikit-learn", "Crypto": "pycryptodome",
    "docx": "python-docx", "fitz": "PyMuPDF", "dotenv": "python-dotenv",
    "serial": "pyserial", "OpenSSL": "pyOpenSSL", "git": "GitPython",
    "matplotlib": "matplotlib", "np": "numpy", "numpy": "numpy",
    "pandas": "pandas", "requests": "requests", "flask": "Flask",
}

# Extensoes tratadas como texto/codigo editavel.
CODE_EXTS = {
    "py", "txt", "md", "markdown", "json", "csv", "tsv", "xml", "html", "htm",
    "yaml", "yml", "ini", "cfg", "toml", "js", "ts", "jsx", "tsx", "java", "c",
    "cpp", "cc", "h", "hpp", "cs", "go", "rb", "php", "rs", "css", "sql", "sh",
    "bash", "bat", "ps1", "r", "kt", "swift", "scala", "pl", "lua", "dart",
}


# ----------------------------------------------------------------- inspecao
def py_structure(source: str) -> dict:
    """Estrutura de um arquivo Python via AST."""
    info: dict = {"funcoes": [], "classes": [], "imports": [], "sintaxe_ok": True}
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        info["sintaxe_ok"] = False
        info["erro_sintaxe"] = f"linha {e.lineno}: {e.msg}"
        return info
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            info["funcoes"].append(node.name)
        elif isinstance(node, ast.ClassDef):
            info["classes"].append(node.name)
        elif isinstance(node, ast.Import):
            for n in node.names:
                info["imports"].append(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                info["imports"].append(node.module.split(".")[0])
    info["imports"] = sorted(set(info["imports"]))
    return info


def pe_info(data: bytes) -> dict:
    """Informacoes basicas de um executavel Windows (PE), sem dependencias."""
    info: dict = {"formato": "PE/Windows"}
    if data[:2] != b"MZ":
        info["valido"] = False
        return info
    try:
        e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
        if data[e_lfanew:e_lfanew + 4] != b"PE\x00\x00":
            info["valido"] = False
            return info
        machine, n_sections = struct.unpack_from("<HH", data, e_lfanew + 4)
        characteristics = struct.unpack_from("<H", data, e_lfanew + 4 + 18)[0]
        arqs = {0x14c: "x86 (32 bits)", 0x8664: "x64 (64 bits)", 0x1c0: "ARM",
                0xaa64: "ARM64"}
        info.update(
            {
                "valido": True,
                "arquitetura": arqs.get(machine, hex(machine)),
                "secoes": n_sections,
                "tipo": "DLL" if characteristics & 0x2000 else "executavel",
            }
        )
    except Exception as e:  # noqa: BLE001
        info["valido"] = False
        info["erro"] = str(e)
    return info


def zip_info(data: bytes) -> dict:
    """Conteudo de pacotes baseados em ZIP (apk, jar, zip, docx, xlsx)."""
    info: dict = {}
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
        nomes = zf.namelist()
        info["arquivos_no_pacote"] = len(nomes)
        info["amostra"] = nomes[:25]
        if "AndroidManifest.xml" in nomes or "classes.dex" in nomes:
            info["tipo"] = "APK (aplicativo Android)"
            info["tem_dex"] = any(n.endswith(".dex") for n in nomes)
            info["bibliotecas_nativas"] = sorted(
                {n.split("/")[1] for n in nomes if n.startswith("lib/") and "/" in n[4:]}
            )[:10]
        elif "word/document.xml" in nomes:
            info["tipo"] = "DOCX (Word)"
        elif any(n.startswith("xl/") for n in nomes):
            info["tipo"] = "XLSX (Excel)"
        elif any(n.endswith(".class") for n in nomes):
            info["tipo"] = "JAR (Java)"
        else:
            info["tipo"] = "ZIP"
    except zipfile.BadZipFile:
        info["tipo"] = "nao e um ZIP valido"
    return info


_MAGIC = [
    (b"%PDF", "PDF"), (b"\x89PNG", "imagem PNG"), (b"\xff\xd8\xff", "imagem JPEG"),
    (b"GIF8", "imagem GIF"), (b"PK\x03\x04", "ZIP/pacote"), (b"MZ", "executavel PE"),
    (b"\x7fELF", "executavel ELF (Linux)"), (b"\x1f\x8b", "GZIP"),
    (b"Rar!", "RAR"), (b"ID3", "audio MP3"), (b"OggS", "audio OGG"),
]


def inspect(filename: str, data: bytes) -> dict:
    """Analisa um arquivo de qualquer tipo e devolve informacoes uteis."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    res: dict = {"arquivo": filename, "ext": ext, "tamanho_bytes": len(data)}

    if ext in ("exe", "dll") or data[:2] == b"MZ":
        res["tipo"] = "executavel Windows (.exe/.dll)"
        res["detalhes"] = pe_info(data)
        res["editavel"] = False
    elif ext in ("apk", "jar", "zip", "ipa") or data[:4] == b"PK\x03\x04":
        res["tipo"] = "pacote/arquivo compactado"
        res["detalhes"] = zip_info(data)
        res["editavel"] = False
    elif ext == "py":
        source = data.decode("utf-8", "replace")
        res["tipo"] = "codigo Python"
        res["detalhes"] = py_structure(source)
        res["conteudo"] = source
        res["editavel"] = True
    elif ext in CODE_EXTS:
        res["tipo"] = f"texto/codigo ({ext})"
        res["conteudo"] = data.decode("utf-8", "replace")
        res["editavel"] = True
    else:
        tipo = "binario desconhecido"
        for assinatura, nome in _MAGIC:
            if data.startswith(assinatura):
                tipo = nome
                break
        res["tipo"] = tipo
        res["editavel"] = False
    return res


# -------------------------------------------------------------- dependencias
def third_party_imports(source: str) -> list[str]:
    """Pacotes pip que um codigo Python precisa (ignora a biblioteca padrao)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                mods.add(node.module.split(".")[0])
    pacotes = []
    for m in sorted(mods):
        if m in _STDLIB or not m or m.startswith("_"):
            continue
        pacotes.append(IMPORT_TO_PACKAGE.get(m, m))
    return pacotes


def auto_install(packages: list[str], timeout: int = 300) -> dict:
    """Instala (pip) os pacotes informados. Best-effort, devolve log resumido."""
    instalados, falhas, logs = [], [], []
    for pkg in packages:
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", pkg],
                capture_output=True, text=True, timeout=timeout,
            )
            if proc.returncode == 0:
                instalados.append(pkg)
            else:
                falhas.append(pkg)
                logs.append(f"{pkg}: {proc.stderr.strip()[-200:]}")
        except Exception as e:  # noqa: BLE001
            falhas.append(pkg)
            logs.append(f"{pkg}: {e}")
    return {"instalados": instalados, "falhas": falhas, "log": logs}


def install_dependencies(source: str, timeout: int = 300) -> dict:
    """Descobre os imports de um codigo e instala o que faltar."""
    pacotes = third_party_imports(source)
    if not pacotes:
        return {"instalados": [], "falhas": [], "log": [], "necessarios": []}
    res = auto_install(pacotes, timeout=timeout)
    res["necessarios"] = pacotes
    return res


# ------------------------------------------------------------- execucao/build
def run_python(path: str, timeout: int = 30, cwd: str | None = None) -> dict:
    """Executa um script Python e captura a saida (com timeout)."""
    try:
        proc = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, timeout=timeout,
            cwd=cwd or os.path.dirname(path) or ".",
        )
        return {
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-2000:],
            "codigo": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"tempo excedido ({timeout}s)", "codigo": -1}
    except Exception as e:  # noqa: BLE001
        return {"stdout": "", "stderr": str(e), "codigo": -1}


def build_exe(py_path: str, workdir: str, name: str = "app") -> dict:
    """Empacota um .py em executavel via PyInstaller (best-effort)."""
    auto_install(["pyinstaller"], timeout=600)
    dist = os.path.join(workdir, "dist")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--onefile", "--noconfirm",
             "--name", name, "--distpath", dist,
             "--workpath", os.path.join(workdir, "build"),
             "--specpath", workdir, py_path],
            capture_output=True, text=True, timeout=1200,
        )
        exe = os.path.join(dist, name + (".exe" if os.name == "nt" else ""))
        if proc.returncode == 0 and os.path.exists(exe):
            return {"ok": True, "path": exe}
        # acha qualquer artefato gerado
        if os.path.isdir(dist):
            for f in os.listdir(dist):
                return {"ok": True, "path": os.path.join(dist, f)}
        return {"ok": False, "log": proc.stderr[-500:]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "log": str(e)}
