"""
Backend de persistencia em MySQL (pymysql).

Espelha EXATAMENTE a interface da classe `Database` (SQLite) em
`ia/database.py`, para que o `Brain` funcione com qualquer um dos dois
sem alteracoes. Mantem a mesma ideia: conhecimento acumulado + indice
invertido (token -> documentos) para busca por similaridade.

Diferencas de dialeto tratadas aqui:
    - AUTO_INCREMENT (em vez de AUTOINCREMENT)
    - placeholders %s (em vez de ?)
    - upsert via "ON DUPLICATE KEY UPDATE" (em vez de "ON CONFLICT")
    - VARCHAR(255) nas colunas indexadas (TEXT nao pode ser PK/UNIQUE direto)
    - charset utf8mb4 e engine InnoDB (para FOREIGN KEY ON DELETE CASCADE)
"""

from __future__ import annotations

import time
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from . import text

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS knowledge (
        id           BIGINT PRIMARY KEY AUTO_INCREMENT,
        pattern      TEXT NOT NULL,
        pattern_norm VARCHAR(255) NOT NULL,
        response     TEXT NOT NULL,
        created_at   DOUBLE NOT NULL,
        updated_at   DOUBLE NOT NULL,
        used_count   INT NOT NULL DEFAULT 0,
        score        DOUBLE NOT NULL DEFAULT 0,
        UNIQUE KEY uq_pattern_norm (pattern_norm)
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
    CREATE TABLE IF NOT EXISTS meta (
        `key`   VARCHAR(255) PRIMARY KEY,
        `value` TEXT NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


class MySQLDatabase:
    """Mesmo contrato da `Database` (SQLite), porem sobre MySQL."""

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int = 3306,
        connect_timeout: int = 10,
    ):
        self._conn_kwargs = dict(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            connect_timeout=connect_timeout,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )
        self.database = database
        self.conn = pymysql.connect(**self._conn_kwargs)
        for stmt in SCHEMA:
            with self.conn.cursor() as cur:
                cur.execute(stmt)
        self.conn.commit()

    # ----------------------------------------------------------- helpers
    def _cursor(self):
        """Garante a conexao viva (hospedagens derrubam conexoes ociosas)."""
        self.conn.ping(reconnect=True)
        return self.conn.cursor()

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
    def add_knowledge(self, pattern: str, response: str) -> int:
        pattern_norm = text.normalize(pattern)
        now = time.time()

        existing = self._query_one(
            "SELECT id FROM knowledge WHERE pattern_norm = %s", (pattern_norm,)
        )
        if existing:
            kid = existing["id"]
            with self._cursor() as cur:
                cur.execute(
                    "UPDATE knowledge SET response = %s, updated_at = %s "
                    "WHERE id = %s",
                    (response, now, kid),
                )
            self.conn.commit()
            return kid

        tokens = text.tokenize(pattern)
        tf: dict[str, int] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0) + 1

        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO knowledge(pattern, pattern_norm, response, "
                "created_at, updated_at) VALUES(%s, %s, %s, %s, %s)",
                (pattern, pattern_norm, response, now, now),
            )
            kid = cur.lastrowid

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

            self._set_meta_int(cur, "doc_count", self.doc_count + 1)
        self.conn.commit()
        return kid

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
        uses = self._query_one(
            "SELECT COALESCE(SUM(used_count), 0) AS c FROM knowledge"
        )["c"]
        return {
            "itens_aprendidos": total,
            "tamanho_vocabulario": vocab,
            "total_de_usos": int(uses),
            "arquivo_banco": f"MySQL://{self._conn_kwargs['host']}/{self.database}",
        }

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
