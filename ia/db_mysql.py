"""
Backend de persistencia em MySQL (pymysql) - UNICO banco usado pela IA.

Mantem a ideia central: conhecimento acumulado + indice invertido
(token -> documentos) para busca por similaridade. As tabelas sao criadas
automaticamente na primeira execucao.

Detalhes do dialeto MySQL:
    - AUTO_INCREMENT na chave primaria
    - placeholders %s nas queries
    - upsert via "ON DUPLICATE KEY UPDATE"
    - VARCHAR(255) nas colunas indexadas (TEXT nao pode ser PK/UNIQUE direto)
    - charset utf8mb4 e engine InnoDB (para FOREIGN KEY ON DELETE CASCADE)
"""

from __future__ import annotations

import hashlib
import os
import time
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from . import text


def _hash(normalized: str) -> str:
    """Hash estavel do padrao normalizado (usado como chave de unicidade)."""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

# Credenciais padrao do projeto. Podem ser sobrescritas por variaveis de
# ambiente (recomendado para nao versionar a senha em repositorio publico).
DEFAULT_HOST = os.environ.get("IA_MYSQL_HOST", "mysql.50webs.com")
DEFAULT_USER = os.environ.get("IA_MYSQL_USER", "intart_1")
DEFAULT_PASS = os.environ.get("IA_MYSQL_PASS", "intart_1")
DEFAULT_DB = os.environ.get("IA_MYSQL_DB", "intart_1")
DEFAULT_PORT = int(os.environ.get("IA_MYSQL_PORT", "3306"))

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS knowledge (
        id           BIGINT PRIMARY KEY AUTO_INCREMENT,
        pattern      TEXT NOT NULL,
        pattern_hash CHAR(64) NOT NULL,
        response     MEDIUMTEXT NOT NULL,
        source       VARCHAR(255) NOT NULL DEFAULT 'manual',
        created_at   DOUBLE NOT NULL,
        updated_at   DOUBLE NOT NULL,
        used_count   INT NOT NULL DEFAULT 0,
        score        DOUBLE NOT NULL DEFAULT 0,
        UNIQUE KEY uq_pattern_hash (pattern_hash)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS vocab (
        token VARCHAR(255) PRIMARY KEY,
        df    INT NOT NULL DEFAULT 0
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS postings (
        token        VARCHAR(255) NOT NULL,
        knowledge_id BIGINT NOT NULL,
        tf           INT NOT NULL,
        PRIMARY KEY (token, knowledge_id),
        KEY idx_postings_token (token),
        CONSTRAINT fk_post_know FOREIGN KEY (knowledge_id)
            REFERENCES knowledge(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS documents (
        id         BIGINT PRIMARY KEY AUTO_INCREMENT,
        filename   VARCHAR(255) NOT NULL,
        ext        VARCHAR(32) NOT NULL DEFAULT '',
        size_bytes BIGINT NOT NULL DEFAULT 0,
        chunks     INT NOT NULL DEFAULT 0,
        source     VARCHAR(255) NOT NULL DEFAULT 'upload',
        summary    MEDIUMTEXT,
        remote_path VARCHAR(512) NOT NULL DEFAULT '',
        created_at DOUBLE NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_providers (
        id         BIGINT PRIMARY KEY AUTO_INCREMENT,
        name       VARCHAR(128) NOT NULL,
        kind       VARCHAR(32) NOT NULL DEFAULT 'openai',
        base_url   VARCHAR(512) NOT NULL DEFAULT '',
        model      VARCHAR(128) NOT NULL DEFAULT '',
        api_key    TEXT NOT NULL,
        enabled    TINYINT NOT NULL DEFAULT 1,
        created_at DOUBLE NOT NULL,
        updated_at DOUBLE NOT NULL DEFAULT 0,
        UNIQUE KEY uq_provider_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS meta (
        `key`   VARCHAR(255) PRIMARY KEY,
        `value` TEXT NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


class MySQLDatabase:
    """Camada de acesso ao MySQL: aprende, busca e mantem o indice invertido."""

    def __init__(
        self,
        host: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
        port: int | None = None,
        connect_timeout: int = 10,
    ):
        self._conn_kwargs = dict(
            host=host or DEFAULT_HOST,
            user=user or DEFAULT_USER,
            password=password if password is not None else DEFAULT_PASS,
            database=database or DEFAULT_DB,
            port=port or DEFAULT_PORT,
            connect_timeout=connect_timeout,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
            # READ COMMITTED: cada leitura enxerga o ultimo commit (essencial
            # para a conexao de leitura ver o que a de escrita acabou de gravar).
            init_command="SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED",
        )
        self.database = self._conn_kwargs["database"]
        self.conn = pymysql.connect(**self._conn_kwargs)
        for stmt in SCHEMA:
            with self.conn.cursor() as cur:
                cur.execute(stmt)
        self.conn.commit()
        self._migrate()

    # ----------------------------------------------------------- helpers
    def _cursor(self):
        """Garante a conexao viva (hospedagens derrubam conexoes ociosas)."""
        self.conn.ping(reconnect=True)
        return self.conn.cursor()

    def _exec(self, sql: str, params: tuple = ()) -> None:
        with self._cursor() as cur:
            cur.execute(sql, params)
        self.conn.commit()

    def _column_exists(self, table: str, column: str) -> bool:
        row = self._query_one(
            "SELECT COUNT(*) AS c FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            (self.database, table, column),
        )
        return bool(row and row["c"])

    def _index_exists(self, table: str, index: str) -> bool:
        row = self._query_one(
            "SELECT COUNT(*) AS c FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND INDEX_NAME = %s",
            (self.database, table, index),
        )
        return bool(row and row["c"])

    def _migrate(self) -> None:
        """
        Migra bancos criados por versoes anteriores (que usavam
        `pattern_norm VARCHAR(255) UNIQUE`) para o esquema atual, que usa
        `pattern_hash` (permite trechos longos de arquivos) e tem coluna
        `source`. Idempotente via meta.schema_version.
        """
        if self._get_meta_int("schema_version", 0) >= 4:
            return

        if not self._column_exists("knowledge", "source"):
            self._exec(
                "ALTER TABLE knowledge ADD COLUMN source VARCHAR(255) "
                "NOT NULL DEFAULT 'manual'"
            )

        if not self._column_exists("knowledge", "pattern_hash"):
            self._exec("ALTER TABLE knowledge ADD COLUMN pattern_hash CHAR(64) NULL")
            # Aproveita o conteudo antigo para preencher o hash.
            self._exec(
                "UPDATE knowledge SET pattern_hash = SHA2(pattern, 256) "
                "WHERE pattern_hash IS NULL OR pattern_hash = ''"
            )
            if self._index_exists("knowledge", "uq_pattern_norm"):
                self._exec("ALTER TABLE knowledge DROP INDEX uq_pattern_norm")
            self._exec(
                "ALTER TABLE knowledge ADD UNIQUE KEY uq_pattern_hash (pattern_hash)"
            )
            self._exec("ALTER TABLE knowledge MODIFY pattern_hash CHAR(64) NOT NULL")

        if self._column_exists("knowledge", "pattern_norm"):
            self._exec("ALTER TABLE knowledge DROP COLUMN pattern_norm")

        # Garante espaco para respostas grandes (resumos / trechos).
        self._exec("ALTER TABLE knowledge MODIFY response MEDIUMTEXT NOT NULL")

        # v3: caminho do arquivo no FTPS.
        if not self._column_exists("documents", "remote_path"):
            self._exec(
                "ALTER TABLE documents ADD COLUMN remote_path VARCHAR(512) "
                "NOT NULL DEFAULT ''"
            )

        # v4: data de atualizacao das IAs externas (persistencia/edicao).
        if not self._column_exists("ai_providers", "updated_at"):
            self._exec(
                "ALTER TABLE ai_providers ADD COLUMN updated_at DOUBLE "
                "NOT NULL DEFAULT 0"
            )

        with self._cursor() as cur:
            self._set_meta_int(cur, "schema_version", 4)
        self.conn.commit()

    def _query_all(self, sql: str, params: tuple = ()) -> list[dict]:
        with self._cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def _query_one(self, sql: str, params: tuple = ()) -> dict | None:
        with self._cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    # -------------------------------------------------------------- meta
    def _get_meta_int(self, key: str, default: int = 0) -> int:
        row = self._query_one("SELECT `value` FROM meta WHERE `key` = %s", (key,))
        return int(row["value"]) if row else default

    def _set_meta_int(self, cur, key: str, value: int) -> None:
        cur.execute(
            "INSERT INTO meta(`key`, `value`) VALUES(%s, %s) "
            "ON DUPLICATE KEY UPDATE `value` = VALUES(`value`)",
            (key, str(value)),
        )

    @property
    def doc_count(self) -> int:
        return self._get_meta_int("doc_count", 0)

    # ----------------------------------------------------------- aprender
    def add_knowledge(self, pattern: str, response: str, source: str = "manual") -> int:
        """Salva um item de conhecimento (ou atualiza, se o padrao ja existe)."""
        return self.add_knowledge_bulk([(pattern, response)], source=source)[0]

    def add_knowledge_bulk(
        self, items: list[tuple[str, str]], source: str = "manual", progress=None
    ) -> list[int]:
        """
        Insere varios itens (pattern, response) numa unica transacao.

        Reduz drasticamente a latencia ao indexar muitos trechos de um arquivo
        (um unico commit em vez de um por trecho). Atualiza o indice invertido
        e o vocabulario. Itens com padrao ja existente apenas atualizam a
        resposta/origem. `progress(feito, total)` e chamado a cada item.
        """
        ids: list[int] = []
        now = time.time()
        added = 0
        n = self.doc_count
        total = len(items)

        with self._cursor() as cur:
            for _i, (pattern, response) in enumerate(items, 1):
                if progress:
                    progress(_i, total)
                pattern = (pattern or "").strip()
                response = (response or "").strip()
                if not pattern or not response:
                    continue
                h = _hash(text.normalize(pattern))

                cur.execute(
                    "SELECT id FROM knowledge WHERE pattern_hash = %s", (h,)
                )
                row = cur.fetchone()
                if row:
                    kid = row["id"]
                    cur.execute(
                        "UPDATE knowledge SET response = %s, source = %s, "
                        "updated_at = %s WHERE id = %s",
                        (response, source, now, kid),
                    )
                    ids.append(kid)
                    continue

                cur.execute(
                    "INSERT INTO knowledge(pattern, pattern_hash, response, "
                    "source, created_at, updated_at) VALUES(%s, %s, %s, %s, %s, %s)",
                    (pattern, h, response, source, now, now),
                )
                kid = cur.lastrowid
                ids.append(kid)

                tf: dict[str, int] = {}
                for tok in text.tokenize(pattern):
                    tf[tok] = tf.get(tok, 0) + 1
                for tok, freq in tf.items():
                    cur.execute(
                        "INSERT INTO postings(token, knowledge_id, tf) "
                        "VALUES(%s, %s, %s)",
                        (tok, kid, freq),
                    )
                    cur.execute(
                        "INSERT INTO vocab(token, df) VALUES(%s, 1) "
                        "ON DUPLICATE KEY UPDATE df = df + 1",
                        (tok,),
                    )
                added += 1

            if added:
                self._set_meta_int(cur, "doc_count", n + added)
        self.conn.commit()
        return ids

    # --------------------------------------------------------- documentos
    def add_document(
        self,
        filename: str,
        ext: str,
        size_bytes: int,
        chunks: int,
        source: str,
        summary: str,
        remote_path: str = "",
    ) -> int:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO documents(filename, ext, size_bytes, chunks, "
                "source, summary, remote_path, created_at) "
                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
                (filename, ext, size_bytes, chunks, source, summary,
                 remote_path, time.time()),
            )
            doc_id = cur.lastrowid
        self.conn.commit()
        return doc_id

    def get_document(self, doc_id: int) -> dict | None:
        return self._query_one("SELECT * FROM documents WHERE id = %s", (doc_id,))

    def list_documents(self) -> list[dict]:
        return self._query_all("SELECT * FROM documents ORDER BY id DESC")

    # ------------------------------------------------------ provedores IA
    def add_provider(
        self,
        name: str,
        kind: str,
        base_url: str,
        model: str,
        api_key: str,
        enabled: bool = True,
    ) -> int:
        """Cadastra (ou atualiza, pelo nome) um provedor de IA externa.

        Se `api_key` vier vazio numa ATUALIZACAO, a chave ja salva e mantida
        (permite editar tipo/modelo/url sem redigitar a chave)."""
        now = time.time()
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO ai_providers(name, kind, base_url, model, api_key, "
                "enabled, created_at, updated_at) "
                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE kind=VALUES(kind), "
                "base_url=VALUES(base_url), model=VALUES(model), "
                "api_key=IF(VALUES(api_key)='', api_key, VALUES(api_key)), "
                "enabled=VALUES(enabled), updated_at=VALUES(updated_at)",
                (name, kind, base_url, model, api_key,
                 1 if enabled else 0, now, now),
            )
            pid = cur.lastrowid
        self.conn.commit()
        if not pid:
            row = self._query_one(
                "SELECT id FROM ai_providers WHERE name = %s", (name,)
            )
            pid = row["id"] if row else 0
        return pid

    def list_providers(self) -> list[dict]:
        return self._query_all("SELECT * FROM ai_providers ORDER BY id")

    def enabled_providers(self) -> list[dict]:
        return self._query_all(
            "SELECT * FROM ai_providers WHERE enabled = 1 ORDER BY id"
        )

    def get_provider(self, provider_id: int) -> dict | None:
        return self._query_one(
            "SELECT * FROM ai_providers WHERE id = %s", (provider_id,)
        )

    def set_provider_enabled(self, provider_id: int, enabled: bool) -> None:
        self._exec(
            "UPDATE ai_providers SET enabled = %s WHERE id = %s",
            (1 if enabled else 0, provider_id),
        )

    def delete_provider(self, provider_id: int) -> bool:
        with self._cursor() as cur:
            cur.execute("DELETE FROM ai_providers WHERE id = %s", (provider_id,))
            ok = cur.rowcount > 0
        self.conn.commit()
        return ok

    # ------------------------------------------------------------- buscar
    def candidates_for_tokens(self, tokens: list[str]) -> dict[int, dict]:
        if not tokens:
            return {}
        placeholders = ",".join(["%s"] * len(tokens))
        rows = self._query_all(
            f"SELECT token, knowledge_id, tf FROM postings "
            f"WHERE token IN ({placeholders})",
            tuple(tokens),
        )
        result: dict[int, dict] = {}
        for row in rows:
            kid = row["knowledge_id"]
            result.setdefault(kid, {"tf": {}})
            result[kid]["tf"][row["token"]] = row["tf"]
        return result

    def df_for_tokens(self, tokens: list[str]) -> dict[str, int]:
        if not tokens:
            return {}
        placeholders = ",".join(["%s"] * len(tokens))
        rows = self._query_all(
            f"SELECT token, df FROM vocab WHERE token IN ({placeholders})",
            tuple(tokens),
        )
        return {row["token"]: row["df"] for row in rows}

    def get_doc_tokens(self, knowledge_id: int) -> dict[str, int]:
        rows = self._query_all(
            "SELECT token, tf FROM postings WHERE knowledge_id = %s",
            (knowledge_id,),
        )
        return {row["token"]: row["tf"] for row in rows}

    def fetch_doc_tokens_bulk(self, kids: list[int]) -> dict[int, dict[str, int]]:
        """Tokens (e tf) de VARIOS documentos numa unica query (performance)."""
        if not kids:
            return {}
        placeholders = ",".join(["%s"] * len(kids))
        rows = self._query_all(
            f"SELECT token, knowledge_id, tf FROM postings "
            f"WHERE knowledge_id IN ({placeholders})",
            tuple(kids),
        )
        out: dict[int, dict[str, int]] = {}
        for row in rows:
            out.setdefault(row["knowledge_id"], {})[row["token"]] = row["tf"]
        return out

    def fetch_knowledge_bulk(self, kids: list[int]) -> dict[int, dict]:
        """Linhas de conhecimento (id/pattern/response/score) em uma query."""
        if not kids:
            return {}
        placeholders = ",".join(["%s"] * len(kids))
        rows = self._query_all(
            f"SELECT id, pattern, response, score FROM knowledge "
            f"WHERE id IN ({placeholders})",
            tuple(kids),
        )
        return {row["id"]: row for row in rows}

    def get_knowledge(self, knowledge_id: int) -> dict | None:
        return self._query_one(
            "SELECT * FROM knowledge WHERE id = %s", (knowledge_id,)
        )

    def all_knowledge(self) -> list[dict]:
        return self._query_all("SELECT * FROM knowledge ORDER BY id")

    # ---------------------------------------------------------- manutencao
    def reinforce(self, knowledge_id: int, amount: float = 1.0) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE knowledge SET score = score + %s, "
                "used_count = used_count + 1, updated_at = %s WHERE id = %s",
                (amount, time.time(), knowledge_id),
            )
        self.conn.commit()

    def mark_used(self, knowledge_id: int) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE knowledge SET used_count = used_count + 1 WHERE id = %s",
                (knowledge_id,),
            )
        self.conn.commit()

    def forget(self, knowledge_id: int) -> bool:
        if not self.get_knowledge(knowledge_id):
            return False
        with self._cursor() as cur:
            cur.execute(
                "SELECT token FROM postings WHERE knowledge_id = %s",
                (knowledge_id,),
            )
            tokens = cur.fetchall()
            for t in tokens:
                cur.execute(
                    "UPDATE vocab SET df = df - 1 WHERE token = %s", (t["token"],)
                )
            cur.execute("DELETE FROM vocab WHERE df <= 0")
            # postings sai por ON DELETE CASCADE ao remover o knowledge.
            cur.execute("DELETE FROM knowledge WHERE id = %s", (knowledge_id,))
            self._set_meta_int(cur, "doc_count", max(0, self.doc_count - 1))
        self.conn.commit()
        return True

    def stats(self) -> dict[str, Any]:
        total = self._query_one("SELECT COUNT(*) AS c FROM knowledge")["c"]
        vocab = self._query_one("SELECT COUNT(*) AS c FROM vocab")["c"]
        docs = self._query_one("SELECT COUNT(*) AS c FROM documents")["c"]
        provs = self._query_one(
            "SELECT COUNT(*) AS c FROM ai_providers WHERE enabled = 1"
        )["c"]
        uses = self._query_one(
            "SELECT COALESCE(SUM(used_count), 0) AS c FROM knowledge"
        )["c"]
        return {
            "itens_aprendidos": total,
            "documentos": docs,
            "tamanho_vocabulario": vocab,
            "total_de_usos": int(uses),
            "ias_externas": provs,
            "banco": f"MySQL://{self._conn_kwargs['host']}/{self.database}",
        }

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
