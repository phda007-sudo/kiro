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
import os
import tempfile
from dataclasses import dataclass

from . import automation, files, generate, providers, storage, text
from .db_mysql import MySQLDatabase


def _strip_code_fences(texto: str) -> str:
    """Remove blocos de markdown (```), caso a IA externa os inclua."""
    t = texto.strip()
    if t.startswith("```"):
        linhas = t.splitlines()
        if linhas and linhas[0].startswith("```"):
            linhas = linhas[1:]
        if linhas and linhas[-1].strip().startswith("```"):
            linhas = linhas[:-1]
        t = "\n".join(linhas)
    return t.strip() + "\n"


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
        ftps: "storage.FtpsStorage | None" = None,
        **mysql_kwargs,
    ):
        """
        A IA usa MySQL para o conhecimento e FTPS para guardar os arquivos.

        :param threshold: confianca minima para considerar que "sabe" a resposta.
        :param db: instancia de MySQLDatabase ja pronta. Se nao informada, uma
                   nova conexao e criada com as credenciais padrao (ou as
                   passadas em `mysql_kwargs` / variaveis de ambiente).
        :param ftps: armazenamento FTPS dos arquivos. Se None, usa o padrao.
        :param mysql_kwargs: parametros de conexao opcionais (host, user,
                   password, database, port) repassados ao MySQLDatabase.
        """
        self.db = db if db is not None else MySQLDatabase(**mysql_kwargs)
        self.storage = ftps if ftps is not None else storage.FtpsStorage()
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
    def learn(self, pattern: str, response: str, source: str = "manual") -> int:
        """Ensina um novo par pergunta/resposta e salva no banco."""
        pattern = pattern.strip()
        response = response.strip()
        if not pattern or not response:
            raise ValueError("Pergunta e resposta nao podem ser vazias.")
        return self.db.add_knowledge(pattern, response, source=source)

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

    # --------------------------------------------------- IAs externas
    def add_provider(
        self,
        name: str,
        kind: str = "openai",
        base_url: str = "",
        model: str = "",
        api_key: str = "",
        enabled: bool = True,
    ) -> int:
        """Cadastra/atualiza um provedor de IA externa (persistido no MySQL)."""
        name = (name or "").strip()
        if not name:
            raise ValueError("Informe um nome para a IA externa.")
        kind = (kind or "openai").lower()
        if kind not in providers.KINDS:
            raise ValueError(f"tipo invalido. Use um de: {', '.join(providers.KINDS)}")
        ja_existe = any(p["name"] == name for p in self.db.list_providers())
        if not (api_key or "").strip() and not ja_existe:
            raise ValueError("Informe a chave de autenticacao da IA externa.")
        return self.db.add_provider(
            name, kind, base_url.strip(), model.strip(),
            (api_key or "").strip(), enabled,
        )

    def list_providers(self) -> list[dict]:
        """Lista provedores com a chave MASCARADA (nunca expoe a chave inteira)."""
        out = []
        for p in self.db.list_providers():
            k = p.get("api_key") or ""
            mascara = ("*" * max(0, len(k) - 4) + k[-4:]) if k else ""
            out.append(
                {
                    "id": p["id"],
                    "name": p["name"],
                    "kind": p["kind"],
                    "base_url": p["base_url"],
                    "model": p["model"],
                    "enabled": bool(p["enabled"]),
                    "api_key_mascara": mascara,
                }
            )
        return out

    def set_provider_enabled(self, provider_id: int, enabled: bool) -> None:
        self.db.set_provider_enabled(provider_id, enabled)

    def delete_provider(self, provider_id: int) -> bool:
        return self.db.delete_provider(provider_id)

    def test_provider(self, provider_id: int) -> str:
        p = self.db.get_provider(provider_id)
        if not p:
            raise ValueError("Provedor nao encontrado.")
        return providers.ask(
            p["kind"], p["base_url"], p["model"], p["api_key"],
            "Responda apenas com a palavra: OK",
        )

    def ask_external(
        self, question: str, learn: bool = True
    ) -> tuple[str | None, str | None]:
        """
        Pergunta as IAs externas HABILITADAS, na ordem de cadastro. Devolve a
        primeira resposta valida (resposta, nome_da_ia) e, por padrao, APRENDE
        essa resposta no banco (origem 'ia:<nome>'). Se nenhuma responder,
        devolve (None, None).
        """
        prompt = (
            "Responda de forma objetiva e em portugues a seguinte pergunta:\n\n"
            f"{question}"
        )
        for p in self.db.enabled_providers():
            try:
                ans = providers.ask(
                    p["kind"], p["base_url"], p["model"], p["api_key"], prompt
                )
            except Exception:  # noqa: BLE001
                continue  # tenta o proximo provedor
            ans = (ans or "").strip()
            if ans:
                if learn:
                    try:
                        self.db.add_knowledge(question, ans, source=f"ia:{p['name']}")
                    except Exception:  # noqa: BLE001
                        pass
                return ans, p["name"]
        return None, None

    def has_external(self) -> bool:
        return len(self.db.enabled_providers()) > 0

    def answer(self, question: str, use_external: bool = True) -> dict:
        """
        Responde combinando o conhecimento local e as IAs externas.

        1. Tenta responder com o que aprendeu (local).
        2. Se nao tiver confianca, pergunta AUTOMATICAMENTE as IAs externas
           cadastradas, aprende a resposta e a devolve (nao pergunta ao usuario).
        Retorna um dict com: resposta, fonte ('local' | 'ia:<nome>' | None),
        confianca, e (quando nao sabe) palpite, alem de sinalizar se nao ha IA
        externa cadastrada ou se elas nao responderam.
        """
        resposta, match = self.respond(question)
        if resposta is not None:
            return {
                "resposta": resposta,
                "fonte": "local",
                "confianca": round(match.confidence, 3),
                "id": match.knowledge_id,
            }

        tem_externa = self.has_external()
        if use_external and tem_externa:
            ans, nome = self.ask_external(question, learn=True)
            if ans:
                return {
                    "resposta": ans,
                    "fonte": f"ia:{nome}",
                    "confianca": 1.0,
                    "aprendido": True,
                }

        return {
            "resposta": None,
            "fonte": None,
            "palpite": match.response if match else None,
            "confianca": round(match.confidence, 3) if match else 0,
            "sem_externa": not tem_externa,
            "externa_tentada": bool(use_external and tem_externa),
        }

    # --------------------------------------------------------- arquivos
    def ingest_document(
        self, filename: str, data: bytes, source: str = "upload", progress=None
    ) -> dict:
        """
        Analisa um arquivo e ABSORVE seu conteudo para o banco.

        `progress(pct, etapa)` (opcional) reporta o andamento em tempo real.
        """
        prog = progress or (lambda *a, **k: None)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        tamanho = len(data)

        prog(8, "extraindo texto do arquivo")
        conteudo, nota = files.extract_text(data, filename)

        prog(20, f"guardando arquivo no FTPS ({tamanho} bytes)")
        remote_path = self.storage.store(filename, data) or ""

        if not conteudo.strip():
            prog(95, "registrando documento")
            doc_id = self.db.add_document(
                filename, ext, tamanho, 0, source, "", remote_path
            )
            prog(100, "concluido")
            return {
                "arquivo": filename,
                "ext": ext,
                "tamanho_bytes": tamanho,
                "trechos_indexados": 0,
                "nota": nota or "nao foi possivel extrair texto",
                "resumo": "",
                "palavras_chave": [],
                "doc_id": doc_id,
                "ftps": bool(remote_path),
            }

        prog(32, "analisando conteudo (resumo e palavras-chave)")
        analise = files.analyze(conteudo)
        resumo = analise["resumo"]
        prog(42, "dividindo o texto em trechos")
        trechos = files.chunk_text(conteudo)
        src = f"{source}:{filename}"

        def _ind(feito, total):
            pct = 45 + int(40 * feito / max(1, total))
            prog(pct, f"indexando trecho {feito}/{total}")

        ids = self.db.add_knowledge_bulk(
            [(t, t) for t in trechos], source=src, progress=_ind
        )

        prog(88, "salvando resumo")
        resumo_resp = resumo or "(arquivo sem texto suficiente para resumo)"
        self.db.add_knowledge_bulk(
            [
                (f"resumo do arquivo {filename}", resumo_resp),
                (f"sobre o arquivo {filename}", resumo_resp),
                (f"o que tem no arquivo {filename}", resumo_resp),
            ],
            source=src,
        )

        prog(95, "registrando documento")
        doc_id = self.db.add_document(
            filename, ext, tamanho, len(trechos), source, resumo, remote_path
        )
        prog(100, "concluido")

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
            "ftps": bool(remote_path),
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

        # Guarda a carga de informacao como arquivo .txt no FTPS.
        nome_arq = filename if filename != "(sem nome)" else f"{ai_name}_info"
        remote_path = self.storage.store(
            f"{generate.slugify(nome_arq)}.txt", content.encode("utf-8")
        ) or ""

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
            filename, "", len(content.encode("utf-8")), len(trechos), src,
            resumo, remote_path
        )

        return {
            "arquivo": filename,
            "ia": ai_name,
            "trechos_indexados": len(ids),
            "resumo": resumo,
            "palavras_chave": analise["palavras_chave"],
            "doc_id": doc_id,
            "ftps": bool(remote_path),
        }

    def documents(self) -> list[dict]:
        return self.db.list_documents()

    # ---------------------------------------------------------- gerar
    def compose(self, subject: str, max_items: int = 12) -> list[str]:
        """Reune os trechos de conhecimento mais relevantes sobre um assunto."""
        matches = self.search(subject, top_k=max_items)
        sections: list[str] = []
        seen: set[str] = set()
        for m in matches:
            resp = (m.response or "").strip()
            if not resp:
                continue
            chave = resp[:80].lower()
            if chave in seen:
                continue
            seen.add(chave)
            sections.append(resp)
        return sections

    def generate_file(
        self, subject: str, ext: str, max_items: int = 12
    ) -> tuple[str, bytes, str]:
        """
        Gera um arquivo sobre `subject` na extensao `ext`, usando o que a IA
        aprendeu. Retorna (nome_do_arquivo, bytes, mimetype).
        """
        subject = (subject or "").strip()
        if not subject:
            raise ValueError("Informe o assunto a ser gerado.")
        sections = self.compose(subject, max_items=max_items)
        filename, blob, mime = generate.render(subject, sections, ext)
        # Guarda tambem o arquivo gerado no FTPS (best-effort).
        try:
            self.storage.store(filename, blob)
        except Exception:  # noqa: BLE001
            pass
        return filename, blob, mime

    def download_document(self, doc_id: int) -> tuple[str, bytes] | None:
        """Recupera do FTPS o arquivo bruto de um documento absorvido."""
        doc = self.db.get_document(doc_id)
        if not doc or not doc.get("remote_path"):
            return None
        data = self.storage.retrieve(doc["remote_path"])
        if data is None:
            return None
        return doc["filename"], data

    # --------------------------------------------------- tarefas automaticas
    def consult_provider(self, prompt: str) -> tuple[str | None, str | None]:
        """Consulta a primeira IA externa habilitada SEM aprender (uso interno)."""
        for p in self.db.enabled_providers():
            try:
                ans = providers.ask(
                    p["kind"], p["base_url"], p["model"], p["api_key"],
                    prompt, timeout=60,
                )
            except Exception:  # noqa: BLE001
                continue
            if ans and ans.strip():
                return ans.strip(), p["name"]
        return None, None

    def _gerar_codigo(
        self, task: str, out_name: str, base_content: str, progress=None
    ) -> tuple[str | None, str | None]:
        """Gera/edita o conteudo do arquivo (IA externa, ou scaffold local)."""
        prog = progress or (lambda *a, **k: None)
        if self.has_external():
            partes = [
                "Voce e um gerador/editor de codigo experiente.",
                f"Tarefa: {task}",
            ]
            if base_content:
                partes.append(
                    "Conteudo atual do arquivo (edite conforme a tarefa):\n"
                    + base_content[:6000]
                )
            partes.append(
                f"Responda APENAS com o conteudo final do arquivo '{out_name}', "
                "sem explicacoes e sem blocos de markdown."
            )
            prog(35, "consultando IA externa para gerar o codigo")
            ans, nome = self.consult_provider("\n\n".join(partes))
            if ans:
                return _strip_code_fences(ans), f"ia:{nome}"

        # Fallback local (sem IA externa): scaffold a partir do conhecimento.
        if out_name.endswith(".py"):
            sections = self.compose(task, max_items=6)
            coment = (
                "\n".join(f"# {s}" for s in sections)
                if sections else "# (sem conhecimento previo sobre o tema)"
            )
            code = (
                '"""\n'
                f"Tarefa: {task}\n"
                "Gerado pela PHDA CEREBROZ (scaffold local; cadastre uma IA "
                "externa para geracao/edicao completa).\n"
                '"""\n\n'
                f"{coment}\n\n\n"
                "def main():\n"
                f"    # TODO: implementar: {task}\n"
                f"    print({task!r})\n\n\n"
                'if __name__ == "__main__":\n'
                "    main()\n"
            )
            return code, "local"
        sections = self.compose(task, max_items=8)
        if sections:
            return "\n\n".join(sections) + "\n", "local"
        return None, None

    def automate(
        self,
        task: str,
        filename: str | None = None,
        data: bytes | None = None,
        saida: str | None = None,
        executar: bool = False,
        progress=None,
    ) -> dict:
        """
        Executa uma tarefa automatica com arquivos:
          - analisa o arquivo enviado (qualquer tipo);
          - cria/edita o codigo pedido (IA externa configurada, ou conhecimento);
          - BAIXA sozinha as dependencias Python necessarias;
          - opcionalmente executa o resultado;
          - guarda o resultado no FTPS para download.

        `progress(pct, etapa)` (opcional) reporta o andamento em tempo real.
        """
        prog = progress or (lambda *a, **k: None)
        task = (task or "").strip()
        if not task and not (data and filename):
            raise ValueError("Descreva a tarefa.")

        result: dict = {"tarefa": task}
        base_content = ""
        in_ext = ""

        if data is not None and filename:
            prog(10, f"analisando {filename}")
            analise = automation.inspect(filename, data)
            result["analise"] = analise
            in_ext = analise.get("ext", "")
            prog(18, "guardando arquivo de entrada no FTPS")
            rp_in = self.storage.store(filename, data) or ""
            self.db.add_document(
                filename, in_ext, len(data), 0, "tarefa-entrada",
                analise.get("tipo", ""), rp_in,
            )
            if analise.get("editavel"):
                base_content = analise.get("conteudo", "")

        out_ext = (saida or in_ext or "py").lower().lstrip(".")
        if filename and base_content and not saida:
            out_name = os.path.basename(filename)
        else:
            out_name = f"{generate.slugify(task or filename or 'resultado')}.{out_ext}"

        codigo, fonte = self._gerar_codigo(task, out_name, base_content, progress=prog)
        result["fonte_codigo"] = fonte
        if codigo is None:
            result["erro"] = (
                "Nenhuma IA externa configurada e sem conhecimento suficiente "
                "para gerar. Cadastre uma IA externa (painel de IAs externas)."
            )
            return result
        result["codigo"] = codigo

        if out_ext == "py":
            prog(58, "validando a sintaxe do codigo")
            estrutura = automation.py_structure(codigo)
            result["sintaxe_ok"] = estrutura.get("sintaxe_ok")
            if not estrutura.get("sintaxe_ok"):
                result["erro_sintaxe"] = estrutura.get("erro_sintaxe")
            result["estrutura"] = {
                k: estrutura.get(k) for k in ("funcoes", "classes", "imports")
            }

            def _depprog(feito, total, pkg):
                pct = 62 + int(22 * feito / max(1, total))
                prog(pct, f"baixando dependencia {feito}/{total}: {pkg}")

            prog(62, "verificando dependencias")
            result["dependencias"] = automation.install_dependencies(
                codigo, progress=_depprog
            )
            if executar and estrutura.get("sintaxe_ok"):
                prog(88, "executando o codigo gerado")
                with tempfile.TemporaryDirectory() as td:
                    p = os.path.join(td, "script.py")
                    with open(p, "w", encoding="utf-8") as fh:
                        fh.write(codigo)
                    result["execucao"] = automation.run_python(p)

        prog(95, "guardando resultado no FTPS")
        blob = codigo.encode("utf-8")
        rp_out = self.storage.store(out_name, blob) or ""
        doc_id = self.db.add_document(
            out_name, out_ext, len(blob), 0, "tarefa-saida",
            f"tarefa: {task[:200]}", rp_out,
        )
        result["arquivo_gerado"] = out_name
        result["doc_id"] = doc_id
        result["ftps"] = bool(rp_out)
        prog(100, "concluido")
        return result

    def stats(self) -> dict:
        return self.db.stats()

    def close(self) -> None:
        self.db.close()
