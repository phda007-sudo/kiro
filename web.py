#!/usr/bin/env python3
"""
Interface WEB da PHDA CEREBROZ (conhecimento no MySQL, arquivos no FTPS).

Sobe um servidor local com:
    - um chat para conversar/ensinar a IA;
    - um BOTAO de upload/analise que abre o seletor de arquivos do sistema
      (a "telinha" para buscar o arquivo), analisa o conteudo de diversas
      extensoes e absorve o que aprendeu para o banco;
    - um painel para ALIMENTAR a IA com informacoes produzidas por OUTRAS
      inteligencias artificiais sobre determinados arquivos (texto colado OU
      arquivo: pdf, md, txt, docx, etc);
    - um gerador que produz um arquivo sobre um ASSUNTO no formato pedido
      (pdf, py, md, txt, html, json, csv, docx, xlsx, ...), a partir do que a
      IA aprendeu.

Sem nenhuma API externa: o servidor e local (Flask) e o unico servico de rede
usado e o seu proprio MySQL.

Como rodar:
    pip install -r requirements.txt
    python3 web.py            # abre em http://127.0.0.1:5000
"""

from __future__ import annotations

import argparse
import os
import threading
import time
import webbrowser

from flask import Flask, jsonify, request

from ia import Brain

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MB por upload

# A conexao MySQL (pymysql) nao e thread-safe; serializamos o acesso.
_lock = threading.Lock()
_brain: Brain | None = None


def get_brain() -> Brain:
    assert _brain is not None
    return _brain


INDEX_HTML = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PHDA CEREBROZ</title>
<style>
  :root { --bg:#0f1320; --panel:#1a2032; --line:#2a3350; --txt:#e6e9f2;
          --muted:#9aa3bd; --accent:#5b8cff; --ok:#36c08a; --warn:#e0a44b; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;
         background:var(--bg); color:var(--txt); }
  header { padding:16px 22px; border-bottom:1px solid var(--line);
           display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
  header h1 { font-size:18px; margin:0; }
  .stats { color:var(--muted); font-size:13px; margin-left:auto; }
  .wrap { display:grid; grid-template-columns:1fr 1fr; gap:18px; padding:18px;
          max-width:1200px; margin:0 auto; }
  .card { background:var(--panel); border:1px solid var(--line);
          border-radius:12px; padding:16px; }
  .card h2 { font-size:15px; margin:0 0 12px; }
  .full { grid-column:1 / -1; }
  #chat { height:300px; overflow-y:auto; border:1px solid var(--line);
          border-radius:8px; padding:12px; background:#11162400; }
  .msg { margin:8px 0; padding:8px 12px; border-radius:10px; max-width:85%;
         white-space:pre-wrap; line-height:1.4; }
  .me { background:#23304f; margin-left:auto; }
  .ia { background:#1c2740; }
  .ia.low { border:1px dashed var(--warn); }
  .row { display:flex; gap:8px; margin-top:10px; flex-wrap:wrap; }
  input[type=text], textarea {
     background:#0e1322; color:var(--txt); border:1px solid var(--line);
     border-radius:8px; padding:10px; font-size:14px; width:100%; }
  textarea { min-height:120px; resize:vertical; font-family:inherit; }
  button { background:var(--accent); color:#fff; border:0; border-radius:8px;
           padding:10px 16px; font-size:14px; cursor:pointer; font-weight:600; }
  button.sec { background:#2a3350; }
  button:disabled { opacity:.5; cursor:default; }
  .hint { color:var(--muted); font-size:12px; margin:6px 0 0; }
  .result { margin-top:12px; font-size:13px; }
  .chips span { display:inline-block; background:#23304f; color:#cdd6f0;
                border-radius:20px; padding:3px 10px; margin:3px 4px 0 0;
                font-size:12px; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th,td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--line); }
  .grow { flex:1; }
  .ok { color:var(--ok); } .warn { color:var(--warn); }
  code { background:#0e1322; padding:1px 5px; border-radius:5px; }
</style>
</head>
<body>
<header>
  <h1>🧠 PHDA CEREBROZ</h1>
  <span class="stats" id="stats">carregando...</span>
</header>

<div class="wrap">
  <!-- CHAT -->
  <section class="card full">
    <h2>Conversar</h2>
    <div id="chat"></div>
    <div class="row">
      <input type="text" id="pergunta" class="grow" placeholder="Pergunte algo..."
             onkeydown="if(event.key==='Enter')perguntar()">
      <button onclick="perguntar()">Enviar</button>
    </div>
    <p class="hint">
      <label><input type="checkbox" id="consultar-externa">
      Perguntar a uma IA externa quando eu nao souber (e aprender a resposta)</label>
      &nbsp;·&nbsp; Se a IA nao souber e a opcao estiver desligada, ela pede a
      resposta certa e aprende na hora.
    </p>
  </section>

  <!-- UPLOAD / ANALISE -->
  <section class="card">
    <h2>📎 Enviar arquivo para analise</h2>
    <p class="hint">Clique no botao para escolher um arquivo (txt, md, csv, json,
       pdf, docx, xlsx, codigo-fonte, etc). A IA analisa e <b>alimenta o banco</b>
       com o conteudo, passando a responder sobre ele.</p>
    <div class="row">
      <input type="file" id="arquivo" style="display:none" onchange="enviarArquivo()">
      <button onclick="document.getElementById('arquivo').click()">
        Escolher arquivo e analisar
      </button>
    </div>
    <div class="result" id="res-upload"></div>
  </section>

  <!-- ALIMENTAR COM OUTRA IA -->
  <section class="card">
    <h2>🤖 Alimentar com info de outra IA</h2>
    <p class="hint">Informe a IA de origem e o arquivo. Voce pode <b>colar o texto</b>
       que outra IA produziu, ou <b>enviar um arquivo</b> direto como carga de
       informacao. Tudo vira conhecimento marcado com a origem.</p>
    <div class="row">
      <input type="text" id="ia-nome" placeholder="Nome da IA (ex: GPT, Claude)">
      <input type="text" id="ia-arquivo" placeholder="Arquivo relacionado (ex: relatorio.pdf)">
    </div>
    <div class="row">
      <textarea id="ia-conteudo" placeholder="Cole aqui as informacoes da outra IA... (opcional se enviar um arquivo)"></textarea>
    </div>
    <div class="row">
      <button class="sec" onclick="alimentar()">Alimentar com o texto colado</button>
      <input type="file" id="feed-arquivo" style="display:none" onchange="alimentarArquivo()">
      <button class="sec" onclick="document.getElementById('feed-arquivo').click()">
        Alimentar a partir de um arquivo
      </button>
    </div>
    <div class="result" id="res-feed"></div>
  </section>

  <!-- GERAR ARQUIVO -->
  <section class="card full">
    <h2>🛠️ Gerar arquivo sobre um assunto</h2>
    <p class="hint">A IA reune o que ja aprendeu sobre o assunto e gera um arquivo
       no formato que voce pedir: <b>pdf, py, md, txt, html, json, csv, docx,
       xlsx</b> ou qualquer outra extensao (ex.: js, sql, java...).</p>
    <div class="row">
      <input type="text" id="gen-assunto" class="grow"
             placeholder="Assunto (ex: manual do produto Aurora)">
      <input type="text" id="gen-formato" list="formatos" style="max-width:140px"
             value="pdf" placeholder="formato">
      <datalist id="formatos">
        <option value="pdf"><option value="py"><option value="md">
        <option value="txt"><option value="html"><option value="json">
        <option value="csv"><option value="docx"><option value="xlsx">
        <option value="js"><option value="sql"><option value="java">
      </datalist>
      <button onclick="gerar()">Gerar e baixar</button>
    </div>
    <div class="result" id="res-gen"></div>
  </section>

  <!-- IAs EXTERNAS (FALLBACK) -->
  <section class="card full">
    <h2>🌐 IAs externas (consultar quando nao souber)</h2>
    <p class="hint">Cadastre uma IA externa com os dados de autenticacao. Quando
       voce marcar a opcao no chat e a IA local nao souber, ela pergunta a essa
       IA e <b>aprende</b> a resposta. A chave fica guardada no seu MySQL e so e
       enviada ao provedor escolhido.</p>
    <div class="row">
      <select id="prov-kind" style="max-width:150px">
        <option value="openai">OpenAI</option>
        <option value="anthropic">Anthropic</option>
        <option value="gemini">Gemini</option>
        <option value="custom">Custom (compat. OpenAI)</option>
      </select>
      <input type="text" id="prov-nome" placeholder="Apelido (ex: meu-gpt)" style="max-width:180px">
      <input type="text" id="prov-modelo" placeholder="Modelo (opcional)" style="max-width:200px">
    </div>
    <div class="row">
      <input type="text" id="prov-baseurl" class="grow"
             placeholder="Base URL (opcional; obrigatorio para 'custom')">
      <input type="password" id="prov-key" class="grow" placeholder="Chave de API / token">
      <button onclick="addProvedor()">Adicionar IA</button>
    </div>
    <div class="result" id="res-prov"></div>
    <div id="provs" style="margin-top:10px"></div>
  </section>

  <!-- DOCUMENTOS -->
  <section class="card full">
    <h2>📚 Documentos absorvidos</h2>
    <div id="docs">nenhum ainda.</div>
  </section>
</div>

<script>
const $ = (id) => document.getElementById(id);

function addMsg(texto, classe) {
  const c = $('chat');
  const d = document.createElement('div');
  d.className = 'msg ' + classe;
  d.textContent = texto;
  c.appendChild(d);
  c.scrollTop = c.scrollHeight;
}

async function api(url, opts) {
  const r = await fetch(url, opts);
  return await r.json();
}

async function carregarStats() {
  const s = await api('/api/stats');
  $('stats').textContent =
    `itens: ${s.itens_aprendidos} · documentos: ${s.documentos} · ` +
    `IAs externas: ${s.ias_externas} · MySQL ${s.banco.split('//')[1]||''} · FTPS ${s.ftps}`;
}

async function carregarDocs() {
  const d = await api('/api/documentos');
  if (!d.documentos.length) { $('docs').textContent = 'nenhum ainda.'; return; }
  let html = '<table><tr><th>arquivo</th><th>origem</th><th>trechos</th>' +
             '<th>resumo</th><th>arquivo (FTPS)</th></tr>';
  for (const doc of d.documentos) {
    const baixar = doc.ftps
      ? `<a href="/api/documentos/${doc.id}/baixar">baixar</a>`
      : '<span class="hint">-</span>';
    html += `<tr><td>${esc(doc.filename)}</td><td>${esc(doc.source)}</td>` +
            `<td>${doc.chunks}</td><td>${esc((doc.summary||'').slice(0,100))}</td>` +
            `<td>${baixar}</td></tr>`;
  }
  $('docs').innerHTML = html + '</table>';
}

function esc(s){ return (s||'').replace(/[&<>]/g, c =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }

async function perguntar() {
  const p = $('pergunta').value.trim();
  if (!p) return;
  addMsg(p, 'me');
  $('pergunta').value = '';
  const usarExterna = $('consultar-externa').checked;
  const r = await api('/api/ask', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({pergunta: p, consultar_externa: usarExterna})
  });
  if (r.resposta) {
    const via = (r.fonte && r.fonte !== 'local') ? '   [via ' + esc(r.fonte) + ']' : '';
    addMsg(r.resposta + `  (confianca ${(r.confianca*100|0)}%)` + via, 'ia');
    if (r.fonte && r.fonte !== 'local') { carregarStats(); carregarDocs(); }
  } else {
    const palpite = r.palpite ? `\\nMais parecido: ${r.palpite}` : '';
    addMsg('Ainda nao sei responder isso.' + palpite, 'ia low');
    const ensino = prompt('Qual seria a resposta certa? (cancele para pular)');
    if (ensino && ensino.trim()) {
      await api('/api/ensinar', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({pergunta: p, resposta: ensino.trim()})
      });
      addMsg('Aprendi! Da proxima vez eu respondo.', 'ia');
      carregarStats();
    }
  }
}

async function carregarProvedores() {
  const d = await api('/api/provedores');
  if (!d.provedores.length) { $('provs').innerHTML = '<p class="hint">Nenhuma IA externa cadastrada.</p>'; return; }
  let html = '<table><tr><th>IA</th><th>tipo</th><th>modelo</th><th>chave</th>' +
             '<th>ativa</th><th></th></tr>';
  for (const p of d.provedores) {
    html += `<tr><td>${esc(p.name)}</td><td>${esc(p.kind)}</td>` +
            `<td>${esc(p.model||'(padrao)')}</td><td><code>${esc(p.api_key_mascara)}</code></td>` +
            `<td><input type="checkbox" ${p.enabled?'checked':''} ` +
            `onchange="ativarProvedor(${p.id}, this.checked)"></td>` +
            `<td><button class="sec" onclick="testarProvedor(${p.id})">testar</button> ` +
            `<button class="sec" onclick="removerProvedor(${p.id})">remover</button></td></tr>`;
  }
  $('provs').innerHTML = html + '</table>';
}

async function addProvedor() {
  const body = {
    name: $('prov-nome').value.trim(),
    kind: $('prov-kind').value,
    base_url: $('prov-baseurl').value.trim(),
    model: $('prov-modelo').value.trim(),
    api_key: $('prov-key').value.trim()
  };
  if (!body.name || !body.api_key) { $('res-prov').innerHTML = '<span class="warn">informe apelido e chave.</span>'; return; }
  const r = await api('/api/provedores', {
    method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)
  });
  if (r.erro) { $('res-prov').innerHTML = '<span class="warn">' + esc(r.erro) + '</span>'; return; }
  $('res-prov').innerHTML = '<span class="ok">IA cadastrada.</span>';
  $('prov-key').value = ''; $('prov-nome').value = '';
  carregarProvedores(); carregarStats();
}

async function removerProvedor(id) {
  await api('/api/provedores/' + id, { method:'DELETE' });
  carregarProvedores(); carregarStats();
}

async function ativarProvedor(id, enabled) {
  await api('/api/provedores/' + id + '/ativar', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({enabled})
  });
  carregarStats();
}

async function testarProvedor(id) {
  $('res-prov').innerHTML = 'testando...';
  const r = await api('/api/provedores/' + id + '/testar', { method:'POST' });
  if (r.ok) $('res-prov').innerHTML = '<span class="ok">OK: ' + esc((r.resposta||'').slice(0,80)) + '</span>';
  else $('res-prov').innerHTML = '<span class="warn">falhou: ' + esc(r.erro||'') + '</span>';
}

async function enviarArquivo() {
  const f = $('arquivo').files[0];
  if (!f) return;
  $('res-upload').innerHTML = 'analisando <b>' + esc(f.name) + '</b>...';
  const fd = new FormData();
  fd.append('arquivo', f);
  try {
    const r = await api('/api/upload', { method:'POST', body: fd });
    if (r.erro) { $('res-upload').innerHTML = '<span class="warn">'+esc(r.erro)+'</span>'; return; }
    let chips = (r.palavras_chave||[]).map(k => `<span>${esc(k.palavra)} (${k.freq})</span>`).join('');
    $('res-upload').innerHTML =
      `<p class="ok">Analisado e absorvido: <b>${esc(r.arquivo)}</b> ` +
      `(${r.trechos_indexados} trechos).</p>` +
      (r.nota ? `<p class="hint">tipo: ${esc(r.nota)}</p>` : '') +
      `<p><b>Resumo:</b> ${esc(r.resumo)||'(sem resumo)'}</p>` +
      `<div class="chips">${chips}</div>`;
    carregarStats(); carregarDocs();
  } catch (e) {
    $('res-upload').innerHTML = '<span class="warn">falha: '+esc(''+e)+'</span>';
  }
  $('arquivo').value = '';
}

async function alimentar() {
  const conteudo = $('ia-conteudo').value.trim();
  const arquivo = $('ia-arquivo').value.trim() || '(sem nome)';
  const ia = $('ia-nome').value.trim() || 'ia-externa';
  if (!conteudo) { $('res-feed').innerHTML = '<span class="warn">cole algum conteudo.</span>'; return; }
  $('res-feed').textContent = 'absorvendo...';
  const r = await api('/api/alimentar', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({arquivo, conteudo, ia})
  });
  if (r.erro) { $('res-feed').innerHTML = '<span class="warn">'+esc(r.erro)+'</span>'; return; }
  $('res-feed').innerHTML =
    `<p class="ok">Absorvido de <b>${esc(r.ia)}</b> sobre <b>${esc(r.arquivo)}</b> ` +
    `(${r.trechos_indexados} trechos).</p>`;
  $('ia-conteudo').value = '';
  carregarStats(); carregarDocs();
}

async function alimentarArquivo() {
  const f = $('feed-arquivo').files[0];
  if (!f) return;
  const ia = $('ia-nome').value.trim() || 'ia-externa';
  $('res-feed').innerHTML = 'absorvendo arquivo <b>'+esc(f.name)+'</b> de '+esc(ia)+'...';
  const fd = new FormData();
  fd.append('arquivo', f);
  fd.append('ia', ia);
  try {
    const r = await api('/api/upload', { method:'POST', body: fd });
    if (r.erro) { $('res-feed').innerHTML = '<span class="warn">'+esc(r.erro)+'</span>'; return; }
    let chips = (r.palavras_chave||[]).map(k => `<span>${esc(k.palavra)} (${k.freq})</span>`).join('');
    $('res-feed').innerHTML =
      `<p class="ok">Arquivo absorvido como conhecimento de <b>${esc(ia)}</b>: ` +
      `<b>${esc(r.arquivo)}</b> (${r.trechos_indexados} trechos).</p>` +
      (r.nota ? `<p class="hint">tipo: ${esc(r.nota)}</p>` : '') +
      `<p><b>Resumo:</b> ${esc(r.resumo)||'(sem resumo)'}</p>` +
      `<div class="chips">${chips}</div>`;
    carregarStats(); carregarDocs();
  } catch (e) {
    $('res-feed').innerHTML = '<span class="warn">falha: '+esc(''+e)+'</span>';
  }
  $('feed-arquivo').value = '';
}

async function gerar() {
  const assunto = $('gen-assunto').value.trim();
  const formato = ($('gen-formato').value.trim() || 'txt').replace(/^\\./, '');
  if (!assunto) { $('res-gen').innerHTML = '<span class="warn">informe o assunto.</span>'; return; }
  $('res-gen').innerHTML = 'gerando <b>' + esc(assunto) + '</b> em .' + esc(formato) + '...';
  try {
    const r = await fetch('/api/gerar', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({assunto, formato})
    });
    if (!r.ok) {
      let msg = 'falha ao gerar';
      try { const e = await r.json(); msg = e.erro || msg; } catch (_) {}
      $('res-gen').innerHTML = '<span class="warn">' + esc(msg) + '</span>';
      return;
    }
    let nome = r.headers.get('X-Arquivo') || ('documento.' + formato);
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = nome; document.body.appendChild(a);
    a.click(); a.remove(); URL.revokeObjectURL(url);
    $('res-gen').innerHTML = '<span class="ok">gerado e baixado: <b>' + esc(nome) + '</b></span>';
  } catch (e) {
    $('res-gen').innerHTML = '<span class="warn">falha: ' + esc(''+e) + '</span>';
  }
}

carregarStats(); carregarDocs(); carregarProvedores();
</script>
</body>
</html>
"""


@app.get("/")
def index():
    return INDEX_HTML


@app.get("/api/stats")
def api_stats():
    with _lock:
        b = get_brain()
        s = b.stats()
        s["ftps"] = b.storage.host
    return jsonify(s)


@app.get("/api/documentos")
def api_documentos():
    with _lock:
        docs = get_brain().documents()
    # Datas/numeros ja sao serializaveis; devolve so o que a UI usa.
    return jsonify(
        {
            "documentos": [
                {
                    "id": d["id"],
                    "filename": d["filename"],
                    "ext": d["ext"],
                    "chunks": d["chunks"],
                    "source": d["source"],
                    "summary": d.get("summary") or "",
                    "ftps": bool(d.get("remote_path")),
                }
                for d in docs
            ]
        }
    )


@app.get("/api/documentos/<int:doc_id>/baixar")
def api_documento_baixar(doc_id: int):
    with _lock:
        res = get_brain().download_document(doc_id)
    if res is None:
        return jsonify({"erro": "arquivo nao disponivel no FTPS"}), 404
    filename, data = res
    resp = app.response_class(data, mimetype="application/octet-stream")
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@app.post("/api/ask")
def api_ask():
    data = request.get_json(silent=True) or {}
    pergunta = (data.get("pergunta") or "").strip()
    consultar_externa = bool(data.get("consultar_externa"))
    if not pergunta:
        return jsonify({"erro": "pergunta vazia"}), 400
    with _lock:
        res = get_brain().answer(pergunta, use_external=consultar_externa)
    return jsonify(res)


# ----------------------------------------------------- provedores de IA
@app.get("/api/provedores")
def api_provedores_listar():
    with _lock:
        return jsonify({"provedores": get_brain().list_providers()})


@app.post("/api/provedores")
def api_provedores_add():
    data = request.get_json(silent=True) or {}
    try:
        with _lock:
            pid = get_brain().add_provider(
                name=data.get("name", ""),
                kind=data.get("kind", "openai"),
                base_url=data.get("base_url", ""),
                model=data.get("model", ""),
                api_key=data.get("api_key", ""),
                enabled=bool(data.get("enabled", True)),
            )
        return jsonify({"ok": True, "id": pid})
    except Exception as e:  # noqa: BLE001
        return jsonify({"erro": str(e)}), 400


@app.route("/api/provedores/<int:pid>", methods=["DELETE", "POST"])
def api_provedores_remover(pid: int):
    with _lock:
        ok = get_brain().delete_provider(pid)
    return jsonify({"ok": ok})


@app.post("/api/provedores/<int:pid>/ativar")
def api_provedores_ativar(pid: int):
    data = request.get_json(silent=True) or {}
    with _lock:
        get_brain().set_provider_enabled(pid, bool(data.get("enabled", True)))
    return jsonify({"ok": True})


@app.post("/api/provedores/<int:pid>/testar")
def api_provedores_testar(pid: int):
    try:
        with _lock:
            resposta = get_brain().test_provider(pid)
        return jsonify({"ok": True, "resposta": resposta})
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "erro": str(e)}), 400


@app.post("/api/ensinar")
def api_ensinar():
    data = request.get_json(silent=True) or {}
    pergunta = (data.get("pergunta") or "").strip()
    resposta = (data.get("resposta") or "").strip()
    if not pergunta or not resposta:
        return jsonify({"erro": "pergunta e resposta sao obrigatorias"}), 400
    with _lock:
        kid = get_brain().learn(pergunta, resposta)
    return jsonify({"ok": True, "id": kid})


@app.post("/api/upload")
def api_upload():
    if "arquivo" not in request.files:
        return jsonify({"erro": "nenhum arquivo enviado"}), 400
    f = request.files["arquivo"]
    if not f.filename:
        return jsonify({"erro": "arquivo sem nome"}), 400
    data = f.read()
    if not data:
        return jsonify({"erro": "arquivo vazio"}), 400
    # Origem opcional: se vier o nome de uma IA, o arquivo e absorvido como
    # conhecimento vindo dela (source "ia:<nome>"); senao, como "upload".
    # Em ambos os casos o arquivo ALIMENTA a IA (vira conhecimento pesquisavel).
    ia = (request.form.get("ia") or "").strip()
    source = f"ia:{ia}" if ia else "upload"
    try:
        with _lock:
            resultado = get_brain().ingest_document(f.filename, data, source=source)
        resultado["origem"] = source
        return jsonify(resultado)
    except Exception as e:  # noqa: BLE001
        return jsonify({"erro": f"falha ao analisar: {e}"}), 500


@app.post("/api/alimentar")
def api_alimentar():
    data = request.get_json(silent=True) or {}
    arquivo = (data.get("arquivo") or "").strip()
    conteudo = (data.get("conteudo") or "").strip()
    ia = (data.get("ia") or "ia-externa").strip()
    if not conteudo:
        return jsonify({"erro": "conteudo vazio"}), 400
    try:
        with _lock:
            resultado = get_brain().feed_from_ai(arquivo, conteudo, ai_name=ia)
        return jsonify(resultado)
    except Exception as e:  # noqa: BLE001
        return jsonify({"erro": f"falha ao alimentar: {e}"}), 500


@app.post("/api/gerar")
def api_gerar():
    data = request.get_json(silent=True) or request.form
    assunto = (data.get("assunto") or "").strip()
    formato = (data.get("formato") or "txt").strip()
    if not assunto:
        return jsonify({"erro": "informe o assunto"}), 400
    try:
        with _lock:
            filename, blob, mime = get_brain().generate_file(assunto, formato)
    except Exception as e:  # noqa: BLE001
        return jsonify({"erro": f"falha ao gerar: {e}"}), 500

    resp = app.response_class(blob, mimetype=mime)
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp.headers["X-Arquivo"] = filename
    return resp


def run_server(
    host: str = "127.0.0.1",
    port: int = 5000,
    threshold: float = 0.30,
    open_browser: bool = False,
) -> int:
    """
    Conecta ao MySQL, inicia o servidor e (opcionalmente) abre o navegador.

    Usado tanto pela linha de comando (`python3 web.py`) quanto pelo executavel
    (.exe) gerado pelo PyInstaller via launcher.py.
    """
    global _brain
    try:
        _brain = Brain(threshold=threshold)
    except Exception as e:  # noqa: BLE001
        print(f"[ERRO] Nao consegui conectar ao MySQL: {e}")
        print("Defina IA_MYSQL_* nas variaveis de ambiente, se necessario.")
        return 1

    url = f"http://{host}:{port}"
    print(f"PHDA CEREBROZ em {url}  (Ctrl+C para sair)")
    print(f"Banco: {_brain.stats()['banco']}  |  Arquivos: FTPS {_brain.storage.host}")

    if open_browser:
        def _abrir():
            time.sleep(1.5)
            try:
                webbrowser.open(url)
            except Exception:  # noqa: BLE001
                pass

        threading.Thread(target=_abrir, daemon=True).start()

    app.run(host=host, port=port, threaded=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Interface web da PHDA CEREBROZ (MySQL + FTPS)."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--threshold", type=float, default=0.30)
    parser.add_argument(
        "--abrir-navegador",
        action="store_true",
        help="abre o navegador automaticamente ao iniciar",
    )
    args = parser.parse_args()
    return run_server(
        host=args.host,
        port=args.port,
        threshold=args.threshold,
        open_browser=args.abrir_navegador,
    )


if __name__ == "__main__":
    raise SystemExit(main())
