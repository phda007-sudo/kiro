"""
Armazenamento dos ARQUIVOS em si num servidor FTPS.

A IA continua guardando o CONHECIMENTO (texto/trechos) no MySQL, mas os
arquivos originais (de qualquer tipo: pdf, docx, imagens, zip, etc.) sao
enviados para um servidor FTPS. Assim o banco fica leve e os binarios ficam
guardados de forma adequada.

Usa apenas a biblioteca padrao (ftplib.FTP_TLS), sem dependencias novas.
Todas as operacoes sao "best-effort": se o FTPS estiver indisponivel, a IA
continua funcionando (apenas nao guarda o arquivo bruto).

Credenciais padrao do projeto (sobrescrevíveis por variaveis de ambiente
IA_FTPS_HOST / IA_FTPS_USER / IA_FTPS_PASS / IA_FTPS_DIR).
"""

from __future__ import annotations

import ftplib
import io
import os
import re
import time

DEFAULT_HOST = os.environ.get("IA_FTPS_HOST", "ftps2.50webs.com")
DEFAULT_USER = os.environ.get("IA_FTPS_USER", "intart")
DEFAULT_PASS = os.environ.get("IA_FTPS_PASS", "intart")
DEFAULT_DIR = os.environ.get("IA_FTPS_DIR", "phda_cerebroz")
DEFAULT_PORT = int(os.environ.get("IA_FTPS_PORT", "21"))


def _safe_name(filename: str) -> str:
    base = os.path.basename(filename or "arquivo")
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("_")
    return base or "arquivo"


class FtpsStorage:
    """Cliente FTPS simples para guardar/recuperar arquivos."""

    def __init__(
        self,
        host: str | None = None,
        user: str | None = None,
        password: str | None = None,
        base_dir: str | None = None,
        port: int | None = None,
        timeout: int = 30,
    ):
        self.host = host or DEFAULT_HOST
        self.user = user or DEFAULT_USER
        self.password = password if password is not None else DEFAULT_PASS
        self.base_dir = (base_dir or DEFAULT_DIR).strip("/")
        self.port = port or DEFAULT_PORT
        self.timeout = timeout

    # ------------------------------------------------------------ interno
    def _connect(self) -> ftplib.FTP_TLS:
        ftps = ftplib.FTP_TLS(timeout=self.timeout)
        ftps.connect(self.host, self.port)
        ftps.login(self.user, self.password)
        ftps.prot_p()  # protege tambem o canal de dados
        return ftps

    def _ensure_dir(self, ftps: ftplib.FTP_TLS) -> None:
        if not self.base_dir:
            return
        try:
            ftps.cwd("/" + self.base_dir)
        except ftplib.error_perm:
            try:
                ftps.mkd("/" + self.base_dir)
            except ftplib.error_perm:
                pass
            ftps.cwd("/" + self.base_dir)

    # ------------------------------------------------------------ publico
    def available(self) -> bool:
        try:
            ftps = self._connect()
            ftps.quit()
            return True
        except Exception:  # noqa: BLE001
            return False

    def store(self, filename: str, data: bytes) -> str | None:
        """
        Envia os bytes para o FTPS. Devolve o caminho remoto (ex.:
        'phda_cerebroz/169..._arquivo.pdf') ou None se falhar.
        """
        remote_name = f"{int(time.time() * 1000)}_{_safe_name(filename)}"
        try:
            ftps = self._connect()
            self._ensure_dir(ftps)
            ftps.storbinary(f"STOR {remote_name}", io.BytesIO(data))
            ftps.quit()
            return f"{self.base_dir}/{remote_name}" if self.base_dir else remote_name
        except Exception:  # noqa: BLE001
            return None

    def retrieve(self, remote_path: str) -> bytes | None:
        if not remote_path:
            return None
        try:
            ftps = self._connect()
            buf = io.BytesIO()
            ftps.retrbinary(f"RETR /{remote_path.lstrip('/')}", buf.write)
            ftps.quit()
            return buf.getvalue()
        except Exception:  # noqa: BLE001
            return None

    def list_files(self) -> list[str]:
        try:
            ftps = self._connect()
            self._ensure_dir(ftps)
            nomes = ftps.nlst()
            ftps.quit()
            return [n for n in nomes if n not in (".", "..")]
        except Exception:  # noqa: BLE001
            return []

    def delete(self, remote_path: str) -> bool:
        try:
            ftps = self._connect()
            ftps.delete("/" + remote_path.lstrip("/"))
            ftps.quit()
            return True
        except Exception:  # noqa: BLE001
            return False
