"""
Processamento de texto feito do zero (somente biblioteca padrao do Python).

Responsavel por transformar uma frase em uma lista de tokens limpos que
serao usados pelo motor de busca/aprendizado.
"""

from __future__ import annotations

import re
import unicodedata

# Stopwords comuns em portugues. Palavras muito frequentes que carregam
# pouco significado e atrapalham a comparacao de similaridade.
STOPWORDS = {
    "a", "o", "e", "de", "do", "da", "dos", "das", "em", "no", "na", "nos",
    "nas", "um", "uma", "uns", "umas", "para", "pra", "por", "com", "sem",
    "que", "se", "os", "as", "ao", "aos", "à", "às", "ou", "como", "mais",
    "mas", "ja", "tao", "the", "is", "are", "of", "to", "and", "me", "meu",
    "minha", "seu", "sua", "ele", "ela", "eles", "elas", "isso", "isto",
    "esse", "essa", "este", "esta", "aquele", "aquela", "voce", "vc", "eu",
    "tu", "nos", "vos", "lhe", "lhes", "ser", "estar", "ter", "foi", "era",
}


def strip_accents(text: str) -> str:
    """Remove acentos preservando as letras base (cafe -> cafe, acao -> acao)."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize(text: str) -> str:
    """
    Normaliza um texto:
        - converte para minusculas
        - remove acentos
        - remove pontuacao (mantendo letras, numeros e espacos)
        - colapsa espacos repetidos
    """
    text = text.lower().strip()
    text = strip_accents(text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str, keep_stopwords: bool = False) -> list[str]:
    """
    Quebra um texto em tokens limpos.

    Por padrao remove stopwords. Se todos os tokens forem stopwords
    (ex.: "o que e"), mantem-se as palavras para nao perder o sentido.
    """
    normalized = normalize(text)
    if not normalized:
        return []

    raw_tokens = normalized.split(" ")
    if keep_stopwords:
        return raw_tokens

    filtered = [t for t in raw_tokens if t not in STOPWORDS]
    # Se a filtragem removeu tudo, devolve os tokens originais.
    return filtered if filtered else raw_tokens
