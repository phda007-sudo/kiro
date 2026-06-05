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
import uuid
import webbrowser

from flask import Flask, jsonify, request

from ia import Brain

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024  # 512 MB por upload

# Conexao de ESCRITA (jobs/aprendizado) e conexao de LEITURA dedicada.
# Assim o chat (leitura) responde mesmo enquanto um upload longo (escrita)
# esta em andamento -> mais agilidade e sem travar.
_lock = threading.Lock()          # serializa escritas
_rlock = threading.Lock()         # serializa a conexao de leitura
_brain: Brain | None = None       # escrita
_brain_ro: Brain | None = None    # leitura

# ----------------------------------------------------------------- jobs
# Trabalhos demorados rodam em thread separada (a UI nao trava) e reportam
# progresso em tempo real, consultado por /api/progresso/<job_id>.
_JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()


def _novo_job() -> str:
    jid = uuid.uuid4().hex
    with _JOBS_LOCK:
        _JOBS[jid] = {"pct": 0, "etapa": "na fila...", "done": False,
                      "erro": None, "resultado": None}
    return jid


def _progress_cb(jid: str):
    def cb(pct=None, etapa=None):
        with _JOBS_LOCK:
            j = _JOBS.get(jid)
            if not j:
                return
            if pct is not None:
                j["pct"] = max(0, min(100, int(pct)))
            if etapa:
                j["etapa"] = etapa
    return cb


def _run_job(jid: str, fn):
    """Executa fn(progress_cb) numa thread; serializa o acesso ao brain/DB."""
    def worker():
        cb = _progress_cb(jid)
        try:
            cb(1, "iniciando...")
            with _lock:
                resultado = fn(cb)
            with _JOBS_LOCK:
                _JOBS[jid].update(resultado=resultado, pct=100,
                                  etapa="concluido", done=True)
        except Exception as e:  # noqa: BLE001
            with _JOBS_LOCK:
                _JOBS[jid].update(erro=str(e), done=True, etapa="falha")
    threading.Thread(target=worker, daemon=True).start()


def get_brain() -> Brain:
    assert _brain is not None
    return _brain


def get_brain_ro() -> Brain:
    """Conexao de leitura (cai para a de escrita se indisponivel)."""
    return _brain_ro if _brain_ro is not None else get_brain()


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
  .barwrap { font-size:12px; color:var(--muted); margin:8px 0 4px; }
  .bar { height:10px; background:#0e1322; border:1px solid var(--line);
         border-radius:6px; overflow:hidden; }
  .bar > i { display:block; height:100%; width:30%; border-radius:6px;
             background:linear-gradient(90deg,var(--accent),#8ab4ff);
             animation: ind 1.1s infinite ease-in-out; }
  .bar.det > i { animation:none; transition:width .25s ease; }
  @keyframes ind { 0%{margin-left:-32%} 100%{margin-left:102%} }
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
      Quando eu nao souber, pergunto <b>automaticamente</b> as IAs externas
      cadastradas e aprendo a resposta. Cadastre-as no painel
      "IAs externas" abaixo.
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
    <p class="hint">Cadastre uma IA externa com os dados de autenticacao. Quando a
       IA local nao souber, ela pergunta automaticamente a essa IA e <b>aprende</b>
       a resposta. Os dados (inclusive a chave) <b>ficam salvos no MySQL</b> e
       persistem ao fechar. Para editar um cadastro, repita o mesmo apelido; deixe
       a chave em branco para manter a atual.</p>
    <div class="row">
      <select id="prov-kind" style="max-width:150px">
        <option value="openai">OpenAI</option>
        <option value="deepseek">DeepSeek</option>
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

  <!-- TAREFA AUTOMATICA -->
  <section class="card full">
    <h2>⚙️ Tarefa automatica: analisar / criar / modificar arquivos</h2>
    <p class="hint">Descreva o que voce quer. A PHDA analisa o arquivo (se enviar),
       cria/edita o codigo, <b>baixa sozinha as bibliotecas e dependencias</b>
       necessarias e entrega o resultado pronto para download. Para criar/editar
       codigo de verdade, cadastre uma IA externa acima. (Binarios .exe/.apk sao
       analisados; a criacao de .exe e feita a partir de codigo-fonte.)</p>
    <div class="row">
      <textarea id="ta-tarefa" placeholder="Ex: crie um script python que renomeia todos os arquivos .txt de uma pasta para minusculo"></textarea>
    </div>
    <div class="row">
      <input type="file" id="ta-arquivo" style="max-width:260px">
      <input type="text" id="ta-saida" placeholder="extensao de saida (ex: py)" style="max-width:180px">
      <label class="hint"><input type="checkbox" id="ta-exec"> executar e mostrar a saida</label>
      <button onclick="tarefa()">Executar tarefa</button>
    </div>
    <div class="result" id="res-tarefa"></div>
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
  return d;
}

async function api(url, opts) {
  const r = await fetch(url, opts);
  return await r.json();
}

function barIndet(texto) {
  return `<div class="barwrap">${esc(texto || 'trabalhando...')}</div>` +
         `<div class="bar"><i></i></div>`;
}
function barDet(texto, pct) {
  pct = Math.max(0, Math.min(100, pct | 0));
  return `<div class="barwrap">${esc(texto)} ${pct}%</div>` +
         `<div class="bar det"><i style="width:${pct}%"></i></div>`;
}
// Upload com barra de progresso REAL (percentual do envio) via XHR.
function uploadXHR(url, formData, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(Math.round(e.loaded / e.total * 100));
    };
    xhr.onload = () => {
      try { resolve(JSON.parse(xhr.responseText)); }
      catch (_) { resolve({ erro: 'resposta invalida do servidor' }); }
    };
    xhr.onerror = () => reject(new Error('erro de rede'));
    xhr.send(formData);
  });
}
// Acompanha um job em tempo real (etapa + porcentagem), sem travar a pagina.
function pollProgress(jobId, onUpdate) {
  return new Promise((resolve) => {
    const tick = async () => {
      let j;
      try {
        const r = await fetch('/api/progresso/' + jobId);
        j = await r.json();
      } catch (_) { setTimeout(tick, 700); return; }
      if (onUpdate) onUpdate(j);
      if (j.done || j.resultado || (j.erro && j.erro !== 'job nao encontrado')) {
        resolve(j);
      } else { setTimeout(tick, 400); }
    };
    tick();
  });
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
  const ph = addMsg('', 'ia');
  ph.innerHTML = barIndet('pensando... (consulto uma IA externa se eu nao souber)');
  const r = await api('/api/ask', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({pergunta: p})
  });
  if (r.resposta) {
    const via = (r.fonte && r.fonte !== 'local') ? '   [via ' + esc(r.fonte) + ']' : '';
    ph.textContent = r.resposta + `  (confianca ${(r.confianca*100|0)}%)` + via;
    if (r.fonte && r.fonte !== 'local') { carregarStats(); carregarDocs(); }
  } else {
    let msg;
    if (r.sem_externa) {
      msg = 'Ainda nao sei isso e nao ha nenhuma IA externa cadastrada. ' +
            'Cadastre uma IA externa abaixo para eu buscar a resposta.';
    } else {
      msg = 'Ainda nao sei isso e as IAs externas cadastradas nao responderam.';
    }
    if (r.palpite) msg += '\\nMais parecido que conheco: ' + r.palpite;
    ph.className = 'msg ia low';
    ph.textContent = msg;
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
  if (!body.name) { $('res-prov').innerHTML = '<span class="warn">informe um apelido.</span>'; return; }
  $('res-prov').innerHTML = barIndet('salvando no banco...');
  const r = await api('/api/provedores', {
    method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)
  });
  if (r.erro) { $('res-prov').innerHTML = '<span class="warn">' + esc(r.erro) + '</span>'; return; }
  $('res-prov').innerHTML = '<span class="ok">Salvo no MySQL (id=' + r.id + '). Persiste mesmo apos fechar.</span>';
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
  $('res-prov').innerHTML = barIndet('testando conexao com a IA externa...');
  const r = await api('/api/provedores/' + id + '/testar', { method:'POST' });
  if (r.ok) $('res-prov').innerHTML = '<span class="ok">OK: ' + esc((r.resposta||'').slice(0,80)) + '</span>';
  else $('res-prov').innerHTML = '<span class="warn">falhou: ' + esc(r.erro||'') + '</span>';
}

async function tarefa() {
  const t = $('ta-tarefa').value.trim();
  const f = $('ta-arquivo').files[0];
  if (!t && !f) { $('res-tarefa').innerHTML = '<span class="warn">descreva a tarefa ou envie um arquivo.</span>'; return; }
  const upd = (p) => {
    $('res-tarefa').innerHTML = (f && p < 100)
      ? barDet('enviando <b>' + esc(f.name) + '</b>', p)
      : barIndet('recebido; iniciando...');
  };
  upd(f ? 0 : 100);
  const fd = new FormData();
  fd.append('tarefa', t);
  if (f) fd.append('arquivo', f);
  if ($('ta-saida').value.trim()) fd.append('saida', $('ta-saida').value.trim());
  fd.append('executar', $('ta-exec').checked ? '1' : '0');
  try {
    const start = await uploadXHR('/api/tarefa', fd, (p) => {
      if (p < 100) upd(p);
      else $('res-tarefa').innerHTML = barIndet('recebido; iniciando...');
    });
    if (start.erro) { $('res-tarefa').innerHTML = '<span class="warn">' + esc(start.erro) + '</span>'; return; }
    const j = await pollProgress(start.job_id, (st) => {
      if (st.resultado || st.done) return;
      $('res-tarefa').innerHTML = barDet(st.etapa || 'trabalhando...', st.pct || 0);
    });
    if (j.erro && !j.resultado) { $('res-tarefa').innerHTML = '<span class="warn">' + esc(j.erro) + '</span>'; return; }
    const r = j.resultado;
    if (r.erro) { $('res-tarefa').innerHTML = '<span class="warn">' + esc(r.erro) + '</span>'; return; }
    let html = barDet('concluido', 100);
    if (r.analise) {
      html += `<p><b>Analise de ${esc(r.analise.arquivo)}</b> — ${esc(r.analise.tipo)} ` +
              `(${r.analise.tamanho_bytes} bytes)</p>` +
              `<pre style="white-space:pre-wrap;background:#0e1322;padding:8px;border-radius:6px;max-height:160px;overflow:auto">` +
              esc(JSON.stringify(r.analise.detalhes||r.analise.estrutura||{}, null, 1)) + `</pre>`;
    }
    if (r.arquivo_gerado) {
      html += `<p class="ok">Gerado: <b>${esc(r.arquivo_gerado)}</b> ` +
              `(fonte: ${esc(r.fonte_codigo||'')}) ` +
              (r.doc_id ? `— <a href="/api/documentos/${r.doc_id}/baixar">baixar</a>` : '') + `</p>`;
      if (r.sintaxe_ok === false) html += `<p class="warn">sintaxe invalida: ${esc(r.erro_sintaxe||'')}</p>`;
    }
    if (r.dependencias) {
      const d = r.dependencias;
      html += `<p class="hint">dependencias: instaladas [${(d.instalados||[]).join(', ')||'-'}]` +
              ((d.falhas&&d.falhas.length)?` · falhas [${d.falhas.join(', ')}]`:'') + `</p>`;
    }
    if (r.codigo) {
      html += `<pre style="white-space:pre-wrap;background:#0e1322;padding:8px;border-radius:6px;max-height:220px;overflow:auto">` +
              esc(r.codigo) + `</pre>`;
    }
    if (r.execucao) {
      html += `<p><b>Execucao</b> (codigo ${r.execucao.codigo}):</p>` +
              `<pre style="white-space:pre-wrap;background:#0e1322;padding:8px;border-radius:6px;max-height:180px;overflow:auto">` +
              esc((r.execucao.stdout||'') + (r.execucao.stderr?('\\n[erros]\\n'+r.execucao.stderr):'')) + `</pre>`;
    }
    $('res-tarefa').innerHTML = html;
    carregarStats(); carregarDocs();
  } catch (e) {
    $('res-tarefa').innerHTML = '<span class="warn">falha: ' + esc(''+e) + '</span>';
  }
}

async function enviarArquivo() {
  const f = $('arquivo').files[0];
  if (!f) return;
  const upd = (p) => { $('res-upload').innerHTML = barDet('enviando <b>' + esc(f.name) + '</b>', p); };
  upd(0);
  const fd = new FormData();
  fd.append('arquivo', f);
  try {
    const start = await uploadXHR('/api/upload', fd, (p) => {
      if (p < 100) upd(p);
      else $('res-upload').innerHTML = barIndet('recebido; iniciando processamento...');
    });
    if (start.erro) { $('res-upload').innerHTML = '<span class="warn">'+esc(start.erro)+'</span>'; return; }
    const j = await pollProgress(start.job_id, (st) => {
      if (st.resultado || st.done) return;
      $('res-upload').innerHTML = barDet(st.etapa || 'processando...', st.pct || 0);
    });
    if (j.erro && !j.resultado) { $('res-upload').innerHTML = '<span class="warn">'+esc(j.erro)+'</span>'; return; }
    const r = j.resultado;
    let chips = (r.palavras_chave||[]).map(k => `<span>${esc(k.palavra)} (${k.freq})</span>`).join('');
    $('res-upload').innerHTML =
      barDet('concluido', 100) +
      `<p class="ok">Analisado e absorvido: <b>${esc(r.arquivo)}</b> ` +
      `(${r.trechos_indexados} trechos)${r.ftps?' · guardado no FTPS':''}.</p>` +
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
  $('res-feed').innerHTML = barIndet('absorvendo conteudo...');
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
  const upd = (p) => { $('res-feed').innerHTML = barDet('enviando <b>' + esc(f.name) + '</b>', p); };
  upd(0);
  const fd = new FormData();
  fd.append('arquivo', f);
  fd.append('ia', ia);
  try {
    const start = await uploadXHR('/api/upload', fd, (p) => {
      if (p < 100) upd(p);
      else $('res-feed').innerHTML = barIndet('recebido; iniciando processamento...');
    });
    if (start.erro) { $('res-feed').innerHTML = '<span class="warn">'+esc(start.erro)+'</span>'; return; }
    const j = await pollProgress(start.job_id, (st) => {
      if (st.resultado || st.done) return;
      $('res-feed').innerHTML = barDet(st.etapa || 'processando...', st.pct || 0);
    });
    if (j.erro && !j.resultado) { $('res-feed').innerHTML = '<span class="warn">'+esc(j.erro)+'</span>'; return; }
    const r = j.resultado;
    let chips = (r.palavras_chave||[]).map(k => `<span>${esc(k.palavra)} (${k.freq})</span>`).join('');
    $('res-feed').innerHTML =
      barDet('concluido', 100) +
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
  $('res-gen').innerHTML = barIndet('gerando <b>' + esc(assunto) + '</b> em .' + esc(formato) + '...');
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


@app.get("/api/health")
def api_health():
    """Verificacao rapida de saude e latencia do banco."""
    import time as _t
    info = {"ok": True}
    t0 = _t.time()
    try:
        with _rlock:
            s = get_brain_ro().stats()
        info["mysql_ms"] = round((_t.time() - t0) * 1000, 1)
        info["itens_aprendidos"] = s.get("itens_aprendidos")
        info["ias_externas"] = s.get("ias_externas")
    except Exception as e:  # noqa: BLE001
        info = {"ok": False, "erro": str(e)}
    return jsonify(info)


@app.get("/api/stats")
def api_stats():
    with _rlock:
        b = get_brain_ro()
        s = b.stats()
        s["ftps"] = b.storage.host
    return jsonify(s)


@app.get("/api/documentos")
def api_documentos():
    with _rlock:
        docs = get_brain_ro().documents()
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
    with _rlock:
        res = get_brain_ro().download_document(doc_id)
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
    if not pergunta:
        return jsonify({"erro": "pergunta vazia"}), 400
    # Leitura concorrente: o chat responde mesmo durante um upload em andamento.
    with _rlock:
        res = get_brain_ro().answer(pergunta, use_external=True)
    return jsonify(res)


@app.post("/api/buscar")
def api_buscar():
    data = request.get_json(silent=True) or {}
    consulta = (data.get("consulta") or "").strip()
    if not consulta:
        return jsonify({"erro": "consulta vazia"}), 400
    with _rlock:
        matches = get_brain_ro().search(consulta, top_k=int(data.get("top_k", 5)))
    return jsonify(
        {
            "resultados": [
                {
                    "id": m.knowledge_id,
                    "pattern": m.pattern,
                    "response": m.response,
                    "similaridade": round(m.similarity, 3),
                    "confianca": round(m.confidence, 3),
                }
                for m in matches
            ]
        }
    )


# ----------------------------------------------------- provedores de IA
@app.get("/api/provedores")
def api_provedores_listar():
    with _rlock:
        return jsonify({"provedores": get_brain_ro().list_providers()})


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
    ia = (request.form.get("ia") or "").strip()
    source = f"ia:{ia}" if ia else "upload"
    nome = f.filename
    jid = _novo_job()
    _run_job(jid, lambda cb: dict(
        get_brain().ingest_document(nome, data, source=source, progress=cb),
        origem=source,
    ))
    return jsonify({"job_id": jid})


@app.get("/api/progresso/<jid>")
def api_progresso(jid: str):
    with _JOBS_LOCK:
        j = _JOBS.get(jid)
        if not j:
            return jsonify({"erro": "job nao encontrado"}), 404
        out = dict(j)
        if j["done"]:
            _JOBS.pop(jid, None)  # libera memoria apos a entrega
    return jsonify(out)


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


@app.post("/api/tarefa")
def api_tarefa():
    tarefa = (request.form.get("tarefa") or "").strip()
    saida = (request.form.get("saida") or "").strip() or None
    executar = (request.form.get("executar") or "").strip().lower() in (
        "1", "true", "on", "sim", "yes"
    )
    filename = data = None
    if "arquivo" in request.files and request.files["arquivo"].filename:
        f = request.files["arquivo"]
        filename = f.filename
        data = f.read()
    if not tarefa and not filename:
        return jsonify({"erro": "descreva a tarefa ou envie um arquivo"}), 400
    jid = _novo_job()
    _run_job(jid, lambda cb: get_brain().automate(
        tarefa, filename=filename, data=data, saida=saida,
        executar=executar, progress=cb,
    ))
    return jsonify({"job_id": jid})


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
    global _brain, _brain_ro
    try:
        _brain = Brain(threshold=threshold)
        # Conexao separada para leitura (chat responde durante uploads longos).
        try:
            _brain_ro = Brain(threshold=threshold)
        except Exception:  # noqa: BLE001
            _brain_ro = _brain
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
