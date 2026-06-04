"""
Camada de persistencia em SQLite.

Este e o "banco de dados acumulado" da IA. Tudo o que ela aprende fica
guardado aqui e cresce ao longo do tempo. Usa um indice invertido
(tabela `postings`) para que a busca por similaridade seja rapida mesmo
com muito conhecimento armazenado.

Esquema:
    knowledge   -> cada coisa aprendida (pergunta/padrao -> resposta)
    vocab       -> vocabulario com document frequency (para o IDF)
    postings    -> indice invertido: token -> (knowledge_id, term frequency)
    meta        -> contadores globais (ex.: total de documentos)
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from . import text

SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern     TEXT NOT NULL,          -- texto original ensinado
    pattern_norm TEXT NOT NULL,         -- texto normalizado
    response    TEXT NOT NULL,          -- resposta a devolver
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL,
    used_count  INTEGER NOT NULL DEFAULT 0,
    score       REAL NOT NULL DEFAULT 0 -- reforco (feedback positivo)
);

CREATE TABLE IF NOT EXISTS vocab (
    token TEXT PRIMARY KEY,
    df    INTEGER NOT NULL DEFAULT 0    -- em quantos documentos o token aparece
);

CREATE TABLE IF NOT EXISTS postings (
    token        TEXT NOT NULL,
    knowledge_id INTEGER NOT NULL,
    tf           INTEGER NOT NULL,      -- frequencia do token no documento
    PRIMARY KEY (token, knowledge_id),
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_postings_token ON postings(token);
CREATE INDEX IF NOT EXISTS idx_knowledge_norm ON knowledge(pattern_norm);
"""


class Database:
    """Encapsula todo o acesso ao SQLite."""

    def __init__(self, path: str = "memoria.db"):
        self.path = path
        # check_same_thread=False permite uso simples fora da thread criadora.
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ------------------------------------------------------------------ meta
    def _get_meta_int(self, key: str, default: int = 0) -> int:
        row = self.conn.execute(
            "SELECT value FROM meta WHERE key = ?", (key,)
        ).fetchone()
        return int(row["value"]) if row else default

    def _set_meta_int(self, key: str, value: int) -> None:
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )

    @property
    def doc_count(self) -> int:
        """Numero total de documentos (itens de conhecimento)."""
        return self._get_meta_int("doc_count", 0)

    # ------------------------------------------------------------- aprender
    def add_knowledge(self, pattern: str, response: str) -> int:
        """
        Salva um novo item de conhecimento e atualiza o indice invertido.

        Se ja existir um padrao identico (apos normalizacao), apenas atualiza
        a resposta em vez de duplicar.
        """
        pattern_norm = text.normalize(pattern)
        now = time.time()

        existing = self.conn.execute(
            "SELECT id FROM knowledge WHERE pattern_norm = ?", (pattern_norm,)
        ).fetchone()

        if existing:
            kid = existing["id"]
            self.conn.execute(
                "UPDATE knowledge SET response = ?, updated_at = ? WHERE id = ?",
                (response, now, kid),
            )
            self.conn.commit()
            return kid

        cur = self.conn.execute(
            "INSERT INTO knowledge(pattern, pattern_norm, response, created_at, "
            "updated_at) VALUES(?, ?, ?, ?, ?)",
            (pattern, pattern_norm, response, now, now),
        )
        kid = cur.lastrowid

        # Atualiza indice invertido + vocabulario.
        tokens = text.tokenize(pattern)
        tf: dict[str, int] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0) + 1

        for tok, freq in tf.items():
            self.conn.execute(
                "INSERT INTO postings(token, knowledge_id, tf) VALUES(?, ?, ?)",
                (tok, kid, freq),
            )
            self.conn.execute(
                "INSERT INTO vocab(token, df) VALUES(?, 1) "
                "ON CONFLICT(token) DO UPDATE SET df = df + 1",
                (tok,),
            )

        self._set_meta_int("doc_count", self.doc_count + 1)
        self.conn.commit()
        return kid

    # --------------------------------------------------------------- buscar
    def candidates_for_tokens(self, tokens: list[str]) -> dict[int, dict]:
        """
        Dado um conjunto de tokens, devolve os documentos que contem ao menos
        um deles, junto das frequencias necessarias para o calculo do TF-IDF.

        Retorna: { knowledge_id: { "tf": {token: tf}, } }
        """
        if not tokens:
            return {}

        placeholders = ",".join("?" * len(tokens))
        rows = self.conn.execute(
            f"SELECT token, knowledge_id, tf FROM postings "
            f"WHERE token IN ({placeholders})",
            tokens,
        ).fetchall()

        result: dict[int, dict] = {}
        for row in rows:
            kid = row["knowledge_id"]
            result.setdefault(kid, {"tf": {}})
            result[kid]["tf"][row["token"]] = row["tf"]
        return result

    def df_for_tokens(self, tokens: list[str]) -> dict[str, int]:
        """Document frequency de cada token (para o IDF)."""
        if not tokens:
            return {}
        placeholders = ",".join("?" * len(tokens))
        rows = self.conn.execute(
            f"SELECT token, df FROM vocab WHERE token IN ({placeholders})",
            tokens,
        ).fetchall()
        return {row["token"]: row["df"] for row in rows}

    def get_doc_tokens(self, knowledge_id: int) -> dict[str, int]:
        """Tokens (e suas frequencias) de um documento, para normalizar o cosseno."""
        rows = self.conn.execute(
            "SELECT token, tf FROM postings WHERE knowledge_id = ?",
            (knowledge_id,),
        ).fetchall()
        return {row["token"]: row["tf"] for row in rows}

    def get_knowledge(self, knowledge_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM knowledge WHERE id = ?", (knowledge_id,)
        ).fetchone()

    def all_knowledge(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM knowledge ORDER BY id"
        ).fetchall()

    # ---------------------------------------------------------- manutencao
    def reinforce(self, knowledge_id: int, amount: float = 1.0) -> None:
        """Aumenta o score (feedback) e o contador de uso de um item."""
        self.conn.execute(
            "UPDATE knowledge SET score = score + ?, used_count = used_count + 1, "
            "updated_at = ? WHERE id = ?",
            (amount, time.time(), knowledge_id),
        )
        self.conn.commit()

    def mark_used(self, knowledge_id: int) -> None:
        self.conn.execute(
            "UPDATE knowledge SET used_count = used_count + 1 WHERE id = ?",
            (knowledge_id,),
        )
        self.conn.commit()

    def forget(self, knowledge_id: int) -> bool:
        """Remove um item de conhecimento e ajusta o indice/vocabulario."""
        row = self.get_knowledge(knowledge_id)
        if not row:
            return False

        tokens = self.conn.execute(
            "SELECT token FROM postings WHERE knowledge_id = ?", (knowledge_id,)
        ).fetchall()
        for t in tokens:
            self.conn.execute(
                "UPDATE vocab SET df = df - 1 WHERE token = ?", (t["token"],)
            )
        self.conn.execute("DELETE FROM vocab WHERE df <= 0")
        self.conn.execute(
            "DELETE FROM postings WHERE knowledge_id = ?", (knowledge_id,)
        )
        self.conn.execute("DELETE FROM knowledge WHERE id = ?", (knowledge_id,))
        self._set_meta_int("doc_count", max(0, self.doc_count - 1))
        self.conn.commit()
        return True

    def stats(self) -> dict:
        total = self.conn.execute(
            "SELECT COUNT(*) AS c FROM knowledge"
        ).fetchone()["c"]
        vocab = self.conn.execute(
            "SELECT COUNT(*) AS c FROM vocab"
        ).fetchone()["c"]
        uses = self.conn.execute(
            "SELECT COALESCE(SUM(used_count), 0) AS c FROM knowledge"
        ).fetchone()["c"]
        return {
            "itens_aprendidos": total,
            "tamanho_vocabulario": vocab,
            "total_de_usos": uses,
            "arquivo_banco": str(Path(self.path).resolve()),
        }

    def close(self) -> None:
        self.conn.close()
