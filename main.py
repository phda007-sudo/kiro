#!/usr/bin/env python3
"""
IA de aprendizado proprio - interface de chat (terminal).

Sem nenhuma API externa. A IA comeca "vazia" e aprende com o que voce
ensina. Tudo fica salvo em um banco MySQL acumulado, entao o conhecimento
persiste entre execucoes e pode ser compartilhado.

Como funciona a conversa:
    - Voce escreve uma pergunta/frase.
    - A IA busca no banco a resposta mais parecida.
    - Se souber (confianca suficiente), responde.
    - Se nao souber, ela pede que voce ensine a resposta e salva.

Comandos especiais (comecam com "/"):
    /ensinar              -> ensina um par pergunta|resposta de forma guiada
    /ensinar P | R        -> ensina direto: "P" vira pergunta e "R" a resposta
    /buscar texto         -> mostra os itens mais parecidos com pontuacao
    /analisar <caminho>   -> le um arquivo do disco, analisa e absorve para a IA
    /gerar <ext> <assunto>-> gera um arquivo (pdf, py, md, txt...) sobre o assunto
    /documentos           -> lista os arquivos ja absorvidos
    /esquecer <id>        -> remove um item de conhecimento pelo id
    /bom                  -> reforca (feedback positivo) a ultima resposta dada
    /stats                -> mostra estatisticas do banco
    /listar               -> lista tudo o que foi aprendido
    /web                  -> dica de como abrir a interface web (upload/analise)
    /ajuda                -> mostra esta ajuda
    /sair                 -> encerra
"""

from __future__ import annotations

import argparse
import os
import sys

from ia import Brain

PROMPT = "voce> "


def imprimir_ajuda() -> None:
    print(__doc__)


def ensinar_guiado(brain: Brain) -> None:
    try:
        pergunta = input("  pergunta/padrao: ").strip()
        resposta = input("  resposta: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  (cancelado)")
        return
    if not pergunta or not resposta:
        print("  Pergunta e resposta nao podem ser vazias.")
        return
    kid = brain.learn(pergunta, resposta)
    print(f"  Aprendido e salvo no banco (id={kid}).")


def comando(brain: Brain, linha: str, ultimo_id: list[int | None]) -> bool:
    """Trata comandos que comecam com '/'. Retorna False para encerrar."""
    partes = linha.split(maxsplit=1)
    cmd = partes[0].lower()
    arg = partes[1].strip() if len(partes) > 1 else ""

    if cmd in ("/sair", "/exit", "/quit"):
        return False

    if cmd in ("/ajuda", "/help"):
        imprimir_ajuda()

    elif cmd == "/ensinar":
        if "|" in arg:
            pergunta, resposta = arg.split("|", 1)
            pergunta, resposta = pergunta.strip(), resposta.strip()
            if pergunta and resposta:
                kid = brain.learn(pergunta, resposta)
                print(f"  Aprendido e salvo no banco (id={kid}).")
            else:
                print("  Use: /ensinar pergunta | resposta")
        else:
            ensinar_guiado(brain)

    elif cmd == "/buscar":
        if not arg:
            print("  Use: /buscar <texto>")
        else:
            matches = brain.search(arg, top_k=5)
            if not matches:
                print("  Nada parecido no banco ainda.")
            for m in matches:
                print(
                    f"  [id={m.knowledge_id}] conf={m.confidence:.2f} "
                    f"sim={m.similarity:.2f} | {m.pattern!r} -> {m.response!r}"
                )

    elif cmd == "/analisar":
        if not arg:
            print("  Use: /analisar <caminho-do-arquivo>")
        elif not os.path.isfile(arg):
            print(f"  Arquivo nao encontrado: {arg}")
        else:
            with open(arg, "rb") as fh:
                data = fh.read()
            nome = os.path.basename(arg)
            r = brain.ingest_document(nome, data, source="upload")
            print(f"  Analisado: {r['arquivo']} (tipo: {r.get('nota')})")
            print(f"  Trechos absorvidos: {r['trechos_indexados']}")
            if r.get("resumo"):
                print(f"  Resumo: {r['resumo']}")
            chaves = ", ".join(
                k["palavra"] for k in r.get("palavras_chave", [])[:8]
            )
            if chaves:
                print(f"  Palavras-chave: {chaves}")

    elif cmd == "/gerar":
        partes_g = arg.split(maxsplit=1)
        if len(partes_g) < 2:
            print("  Use: /gerar <extensao> <assunto>   (ex: /gerar pdf vendas Aurora)")
        else:
            ext, assunto = partes_g[0].lstrip("."), partes_g[1]
            filename, blob, _mime = brain.generate_file(assunto, ext)
            with open(filename, "wb") as fh:
                fh.write(blob)
            print(f"  Gerado: {os.path.abspath(filename)} ({len(blob)} bytes)")

    elif cmd == "/documentos":
        docs = brain.documents()
        if not docs:
            print("  Nenhum documento absorvido ainda. Use /analisar <arquivo>.")
        for d in docs:
            print(
                f"  [id={d['id']}] {d['filename']} | origem={d['source']} | "
                f"trechos={d['chunks']}"
            )

    elif cmd == "/web":
        print("  Para a interface com botao de upload, rode:  python3 web.py")
        print("  e abra http://127.0.0.1:5000 no navegador.")

    elif cmd == "/esquecer":
        if not arg.isdigit():
            print("  Use: /esquecer <id>")
        elif brain.forget(int(arg)):
            print(f"  Item {arg} removido do banco.")
        else:
            print(f"  Nao encontrei o item {arg}.")

    elif cmd == "/bom":
        if ultimo_id[0] is None:
            print("  Nao ha resposta recente para reforcar.")
        else:
            brain.reinforce(ultimo_id[0])
            print("  Obrigado! Vou priorizar essa resposta no futuro.")

    elif cmd == "/stats":
        for k, v in brain.stats().items():
            print(f"  {k}: {v}")

    elif cmd == "/listar":
        itens = brain.db.all_knowledge()
        if not itens:
            print("  Banco vazio. Ensine algo com /ensinar.")
        for row in itens:
            print(
                f"  [id={row['id']}] usos={row['used_count']} "
                f"score={row['score']:.0f} | {row['pattern']!r} -> "
                f"{row['response']!r}"
            )

    else:
        print(f"  Comando desconhecido: {cmd}. Use /ajuda.")

    return True


def conversar(brain: Brain, linha: str, ultimo_id: list[int | None]) -> None:
    """Fluxo normal de conversa: tenta responder, se nao souber, aprende."""
    resposta, match = brain.respond(linha)

    if resposta is not None:
        print(f"ia> {resposta}")
        ultimo_id[0] = match.knowledge_id
        return

    # Nao soube responder.
    if match is not None:
        print(
            f"ia> Nao tenho certeza. O mais parecido que conheco e: "
            f"{match.response!r} (confianca {match.confidence:.2f})."
        )
    else:
        print("ia> Ainda nao sei responder isso.")

    try:
        ensinar = input("ia> Qual seria a resposta certa? (enter p/ pular) ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if ensinar:
        kid = brain.learn(linha, ensinar)
        ultimo_id[0] = kid
        print(f"ia> Entendi! Aprendi e salvei no banco (id={kid}).")


def build_brain(args) -> Brain:
    """Conecta ao MySQL (unico backend) e devolve o Brain."""
    from ia.db_mysql import MySQLDatabase

    db = MySQLDatabase(
        host=args.mysql_host,
        user=args.mysql_user,
        password=args.mysql_pass,
        database=args.mysql_db,
        port=args.mysql_port,
    )
    return Brain(threshold=args.threshold, db=db)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="IA de aprendizado proprio (sem APIs externas), com MySQL."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.30,
        help="confianca minima para responder (0..1, padrao: 0.30)",
    )
    # Conexao MySQL (unico banco usado pela IA). Os valores padrao podem ser
    # sobrescritos por variaveis de ambiente, evitando deixar a senha fixa.
    parser.add_argument(
        "--mysql-host",
        default=os.environ.get("IA_MYSQL_HOST", "mysql.50webs.com"),
    )
    parser.add_argument(
        "--mysql-user", default=os.environ.get("IA_MYSQL_USER", "intart_1")
    )
    parser.add_argument(
        "--mysql-pass", default=os.environ.get("IA_MYSQL_PASS", "intart_1")
    )
    parser.add_argument(
        "--mysql-db", default=os.environ.get("IA_MYSQL_DB", "intart_1")
    )
    parser.add_argument(
        "--mysql-port",
        type=int,
        default=int(os.environ.get("IA_MYSQL_PORT", "3306")),
    )
    args = parser.parse_args()

    try:
        brain = build_brain(args)
    except Exception as e:
        print(f"[ERRO] Nao consegui conectar ao MySQL: {e}")
        print(
            "Verifique host/usuario/senha/banco (flags --mysql-* ou variaveis "
            "de ambiente IA_MYSQL_*)."
        )
        return 1

    ultimo_id: list[int | None] = [None]

    print("=" * 60)
    print(" IA de aprendizado proprio  (digite /ajuda para comandos)")
    print(f" Banco: {brain.stats()['banco']}")
    print(f" Itens ja aprendidos: {brain.stats()['itens_aprendidos']}")
    print("=" * 60)

    try:
        while True:
            try:
                linha = input(PROMPT).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nAte logo!")
                break

            if not linha:
                continue
            if linha.startswith("/"):
                if not comando(brain, linha, ultimo_id):
                    print("Ate logo!")
                    break
            else:
                conversar(brain, linha, ultimo_id)
    finally:
        brain.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
