"""
Consulta a IAs externas (fallback) - usado APENAS quando configurado.

Por padrao a IA continua sem APIs externas. Mas o usuario pode cadastrar um
provedor de IA (com os dados de autenticacao) para ser consultado quando a IA
local nao souber a resposta. As chamadas HTTP usam apenas a biblioteca padrao
(urllib), entao nao ha dependencias novas.

Provedores suportados (campo `kind`):
    - openai   : API estilo OpenAI  (POST /v1/chat/completions, Bearer key)
    - anthropic: API da Anthropic    (POST /v1/messages, header x-api-key)
    - gemini   : Google Gemini       (POST /v1beta/models/<model>:generateContent?key=)
    - custom   : qualquer endpoint compativel com OpenAI (informe a base_url)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

# base_url e modelo padrao por tipo de provedor.
DEFAULTS = {
    "openai": ("https://api.openai.com", "gpt-4o-mini"),
    "anthropic": ("https://api.anthropic.com", "claude-3-5-sonnet-latest"),
    "gemini": ("https://generativelanguage.googleapis.com", "gemini-1.5-flash"),
    "custom": ("", "gpt-3.5-turbo"),
}

KINDS = tuple(DEFAULTS.keys())


def _post(url: str, headers: dict, payload: dict, timeout: int) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalhe = ""
        try:
            detalhe = e.read().decode("utf-8", "replace")[:300]
        except Exception:  # noqa: BLE001
            pass
        raise RuntimeError(f"HTTP {e.code} do provedor: {detalhe}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"falha de conexao com o provedor: {e.reason}") from None


def ask(
    kind: str,
    base_url: str,
    model: str,
    api_key: str,
    prompt: str,
    timeout: int = 40,
) -> str:
    """
    Envia o prompt ao provedor escolhido e devolve o texto da resposta.

    Lanca RuntimeError com mensagem clara em caso de falha (HTTP/conexao).
    """
    kind = (kind or "openai").lower()
    base_default, model_default = DEFAULTS.get(kind, DEFAULTS["custom"])
    base = (base_url or base_default).rstrip("/")
    model = model or model_default
    if not api_key:
        raise RuntimeError("provedor sem chave de autenticacao")

    if kind == "anthropic":
        data = _post(
            base + "/v1/messages",
            {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            {
                "model": model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout,
        )
        return (data["content"][0]["text"]).strip()

    if kind == "gemini":
        data = _post(
            f"{base}/v1beta/models/{model}:generateContent?key={api_key}",
            {"content-type": "application/json"},
            {"contents": [{"parts": [{"text": prompt}]}]},
            timeout,
        )
        return (data["candidates"][0]["content"]["parts"][0]["text"]).strip()

    # openai e custom (compativel com OpenAI: Groq, OpenRouter, LM local, etc.)
    if not base:
        raise RuntimeError("informe a base_url para o provedor 'custom'")
    data = _post(
        base + "/v1/chat/completions",
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        timeout,
    )
    return (data["choices"][0]["message"]["content"]).strip()
