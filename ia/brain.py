"""
O cerebro da IA: aprende, busca e responde.

Nao usa nenhuma API externa. A "inteligencia" vem de:
    1. Representar cada frase aprendida como um vetor TF-IDF.
    2. Comparar a pergunta do usuario com tudo o que ja foi aprendido
       usando similaridade do cosseno.
    3. Devolver a melhor resposta se a confianca passar de um limiar;
       caso contrario, admite que nao sabe e pede para aprender.

Quanto mais a IA e ensinada, maior fica o banco MySQL e melhores ficam as
respostas (o conhecimento e acumulado e reaproveitado).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import files, text
from .db_mysql import MySQLDatabase


@dataclass
class Match:
    """Resultado de uma busca: um item de conhecimento e sua pontuacao."""

    knowledge_id: int
    pattern: str
    response: str
    similarity: float
    score: float

    @property
    def confidence(self) -> float:
        """
        Confianca final combina a similaridade textual com o reforco
        acumulado (itens muito reforcados sobem um pouco na lista).
        """
        boost = 1.0 + min(self.score, 10.0) * 0.02  # ate +20%
        return min(self.similarity * boost, 1.0)


class Brain:
    def __init__(
        self,
        threshold: float = 0.30,
        db: MySQLDatabase | None = None,
        **mysql_kwargs,
    ):
        """
        A IA usa exclusivamente MySQL como banco de conhecimento.

        :param threshold: confianca minima para considerar que "sabe" a resposta.
        :param db: instancia de MySQLDatabase ja pronta. Se nao informada, uma
                   nova conexao e criada com as credenciais padrao (ou as
                   passadas em `mysql_kwargs` / variaveis de ambiente).
        :param mysql_kwargs: parametros de conexao opcionais (host, user,
                   password, database, port) repassados ao MySQLDatabase.
        """
        self.db = db if db is not None else MySQLDatabase(**mysql_kwargs)
        self.threshold = threshold

    # --------------------------------------------------------------- idf
    def _idf(self, token: str, df: int) -> float:
        """
        Inverse Document Frequency suavizado.
        Tokens raros (df baixo) valem mais que tokens comuns.
        """
        n = self.db.doc_count
        return math.log((1 + n) / (1 + df)) + 1.0

    # ------------------------------------------------------------ aprender
    def learn(self, pattern: str, response: str) -> int:
        """Ensina um novo par pergunta/resposta e salva no banco."""
        pattern = pattern.strip()
        response = response.strip()
        if not pattern or not response:
            raise ValueError("Pergunta e resposta nao podem ser vazias.")
        return self.db.add_knowledge(pattern, response)

    # -------------------------------------------------------------- buscar
    def search(self, query: str, top_k: int = 5) -> list[Match]:
        """
        Busca no banco os itens mais parecidos com a pergunta, ordenados
        por confianca (maior primeiro).
        """
        q_tokens = text.tokenize(query)
        if not q_tokens:
            return []

        # Vetor TF-IDF da consulta.
        q_tf: dict[str, int] = {}
        for tok in q_tokens:
            q_tf[tok] = q_tf.get(tok, 0) + 1

        df_map = self.db.df_for_tokens(list(q_tf.keys()))
        q_vec: dict[str, float] = {}
        for tok, tf in q_tf.items():
            df = df_map.get(tok, 0)
            q_vec[tok] = tf * self._idf(tok, df)
        q_norm = math.sqrt(sum(v * v for v in q_vec.values()))
        if q_norm == 0:
            return []

        # Candidatos: documentos que compartilham ao menos um token.
        candidates = self.db.candidates_for_tokens(list(q_tf.keys()))
        matches: list[Match] = []

        for kid, data in candidates.items():
            doc_tf = self.db.get_doc_tokens(kid)
            # Vetor TF-IDF do documento (sobre todos os seus tokens).
            doc_df = self.db.df_for_tokens(list(doc_tf.keys()))
            doc_vec: dict[str, float] = {}
            for tok, tf in doc_tf.items():
                doc_vec[tok] = tf * self._idf(tok, doc_df.get(tok, 0))
            doc_norm = math.sqrt(sum(v * v for v in doc_vec.values()))
            if doc_norm == 0:
                continue

            # Produto interno apenas nos tokens em comum.
            dot = 0.0
            for tok, qval in q_vec.items():
                if tok in doc_vec:
                    dot += qval * doc_vec[tok]

            similarity = dot / (q_norm * doc_norm)
            if similarity <= 0:
                continue

            row = self.db.get_knowledge(kid)
            matches.append(
                Match(
                    knowledge_id=kid,
                    pattern=row["pattern"],
                    response=row["response"],
                    similarity=similarity,
                    score=row["score"],
                )
            )

        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches[:top_k]

    # ------------------------------------------------------------ responder
    def respond(self, query: str) -> tuple[str | None, Match | None]:
        """
        Tenta responder usando o que ja aprendeu.

        Retorna (resposta, match). Se nao houver confianca suficiente,
        retorna (None, melhor_palpite_ou_None) para que a interface possa
        pedir que o usuario ensine.
        """
        matches = self.search(query, top_k=3)
        if not matches:
            return None, None

        best = matches[0]
        if best.confidence >= self.threshold:
            self.db.mark_used(best.knowledge_id)
            return best.response, best
        # Sabe algo parecido, mas sem confianca suficiente.
        return None, best

    # ------------------------------------------------------------- feedback
    def reinforce(self, knowledge_id: int, amount: float = 1.0) -> None:
        self.db.reinforce(knowledge_id, amount)

    def forget(self, knowledge_id: int) -> bool:
        return self.db.forget(knowledge_id)

    # --------------------------------------------------------- arquivos
    def ingest_document(
        self, filename: str, data: bytes, source: str = "upload"
    ) -> dict:
        """
        Analisa um arquivo e ABSORVE seu conteudo para o banco.

        Cada trecho do arquivo vira um item pesquisavel (indexado por TF-IDF),
        e sao criados itens de "resumo" para perguntas do tipo
        "resumo do arquivo X". Devolve a analise (palavras-chave + resumo).
        """
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        conteudo, nota = files.extract_text(data, filename)
        tamanho = len(data)

        if not conteudo.strip():
            doc_id = self.db.add_document(filename, ext, tamanho, 0, source, "")
            return {
                "arquivo": filename,
                "ext": ext,
                "tamanho_bytes": tamanho,
                "trechos_indexados": 0,
                "nota": nota or "nao foi possivel extrair texto",
                "resumo": "",
                "palavras_chave": [],
                "doc_id": doc_id,
            }

        analise = files.analyze(conteudo)
        resumo = analise["resumo"]
        trechos = files.chunk_text(conteudo)
        src = f"{source}:{filename}"

        ids = self.db.add_knowledge_bulk([(t, t) for t in trechos], source=src)

        # Itens dedicados de resumo (varias formas de perguntar).
        resumo_resp = resumo or "(arquivo sem texto suficiente para resumo)"
        self.db.add_knowledge_bulk(
            [
                (f"resumo do arquivo {filename}", resumo_resp),
                (f"sobre o arquivo {filename}", resumo_resp),
                (f"o que tem no arquivo {filename}", resumo_resp),
            ],
            source=src,
        )

        doc_id = self.db.add_document(
            filename, ext, tamanho, len(trechos), source, resumo
        )

        return {
            "arquivo": filename,
            "ext": ext,
            "tamanho_bytes": tamanho,
            "trechos_indexados": len(ids),
            "nota": nota,
            "resumo": resumo,
            "palavras_chave": analise["palavras_chave"],
            "estatisticas": {
                "caracteres": analise["caracteres"],
                "linhas": analise["linhas"],
                "palavras": analise["palavras"],
                "palavras_unicas": analise["palavras_unicas"],
            },
            "doc_id": doc_id,
        }

    def feed_from_ai(
        self, filename: str, content: str, ai_name: str = "ia-externa"
    ) -> dict:
        """
        Alimenta a IA com informacoes produzidas por OUTRA inteligencia
        artificial sobre um determinado arquivo.

        O conteudo e indexado como conhecimento (marcado com a origem
        'ia:<nome>'), ficando disponivel nas buscas e associado ao arquivo.
        """
        content = (content or "").strip()
        if not content:
            raise ValueError("O conteudo fornecido pela IA esta vazio.")
        if not filename.strip():
            filename = "(sem nome)"

        src = f"ia:{ai_name}"
        analise = files.analyze(content)
        resumo = analise["resumo"]
        trechos = files.chunk_text(content)

        ids = self.db.add_knowledge_bulk([(t, t) for t in trechos], source=src)
        resumo_resp = resumo or content[:500]
        self.db.add_knowledge_bulk(
            [
                (f"o que a {ai_name} disse sobre {filename}", resumo_resp),
                (f"informacoes sobre {filename}", resumo_resp),
            ],
            source=src,
        )

        doc_id = self.db.add_document(
            filename, "", len(content.encode("utf-8")), len(trechos), src, resumo
        )

        return {
            "arquivo": filename,
            "ia": ai_name,
            "trechos_indexados": len(ids),
            "resumo": resumo,
            "palavras_chave": analise["palavras_chave"],
            "doc_id": doc_id,
        }

    def documents(self) -> list[dict]:
        return self.db.list_documents()

    def stats(self) -> dict:
        return self.db.stats()

    def close(self) -> None:
        self.db.close()
