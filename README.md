# IA de Aprendizado Proprio (armazenamento em MySQL)

Uma IA conversacional construida **do zero**, em **Python puro**. Por padrao ela
**nao usa nenhuma API externa** nem modelos prontos: toda a "inteligencia" vem
de tecnicas classicas de recuperacao de informacao implementadas a mao.

Opcionalmente, voce pode cadastrar **IAs externas** (OpenAI, Anthropic, Gemini
ou qualquer endpoint compativel) para serem consultadas **so quando a IA local
nao souber** a resposta - e ela **aprende** o que recebe.

A ideia central:

> A IA comeca "vazia". Voce a ensina. Tudo o que ela aprende e **salvo num
> banco de dados MySQL acumulado**. Quando voce pergunta algo, ela **busca**
> nesse banco a resposta mais parecida. Quanto mais voce ensina, mais ela sabe.

O **MySQL e o unico banco** usado pela IA.

## Como funciona

1. **Processamento de texto** (`ia/text.py`): normaliza a frase (minusculas,
   remove acentos e pontuacao) e quebra em palavras (tokens), descartando
   stopwords em portugues.
2. **Banco acumulado** (`ia/db_mysql.py`): MySQL com um **indice invertido**
   (`token -> documentos`). Guarda cada conhecimento, o vocabulario e contadores
   de uso/reforco. E aqui que a IA "busca e salva".
3. **Cerebro** (`ia/brain.py`): representa cada frase como um vetor **TF-IDF** e
   compara a pergunta com o que ja foi aprendido usando **similaridade do
   cosseno**. Se a confianca passa de um limiar, responde; senao, pede para
   aprender.

Nenhum servico de rede e chamado, exceto a conexao com o seu proprio MySQL.

## Estrutura

```
ia/
  __init__.py     # exporta Brain e MySQLDatabase
  text.py         # normalizacao e tokenizacao
  db_mysql.py     # banco MySQL (indice invertido + vocabulario) - unico backend
  files.py        # extracao e analise de arquivos (txt, pdf, docx, xlsx, ...)
  brain.py        # TF-IDF + cosseno: aprende, busca, responde e absorve arquivos
main.py           # interface de chat no terminal
web.py            # interface WEB (chat + botao de upload + alimentar por IA)
requirements.txt  # PyMySQL, Flask e extratores de arquivos
```

As tabelas (`knowledge`, `vocab`, `postings`, `documents`, `meta`) sao criadas
automaticamente na primeira execucao.

## Como usar

Requisitos: Python 3.9+ e um banco MySQL.

```bash
pip install -r requirements.txt
python3 main.py
```

Por padrao conecta no MySQL do projeto:
`mysql.50webs.com / banco intart_1`. Para usar outro banco, passe as flags ou
defina variaveis de ambiente (veja abaixo).

Exemplo de conversa:

```
voce> /ensinar qual a capital da franca | Paris
  Aprendido e salvo no banco (id=1).
voce> qual eh a capital da franca?
ia> Paris
voce> me fale da capital de qualquer pais
ia> Ainda nao sei responder isso.
ia> Qual seria a resposta certa? (enter p/ pular) Depende do pais!
ia> Entendi! Aprendi e salvei no banco (id=2).
```

Quando a IA nao sabe, ela pergunta a resposta e **aprende na hora**. Da proxima
vez, ja responde sozinha (inclusive para variacoes da pergunta).

### Comandos

| Comando | O que faz |
|---|---|
| `/ensinar` | ensina um par pergunta/resposta de forma guiada |
| `/ensinar P \| R` | ensina direto: `P` vira pergunta e `R` a resposta |
| `/buscar texto` | mostra os itens mais parecidos com a pontuacao |
| `/esquecer <id>` | remove um item de conhecimento pelo id |
| `/bom` | reforca (feedback positivo) a ultima resposta dada |
| `/stats` | estatisticas do banco |
| `/listar` | lista tudo o que foi aprendido |
| `/ajuda` | mostra a ajuda |
| `/sair` | encerra |

### Conexao MySQL

Flags da linha de comando:

```bash
python3 main.py \
  --mysql-host mysql.50webs.com --mysql-user intart_1 \
  --mysql-pass intart_1 --mysql-db intart_1 --mysql-port 3306 \
  --threshold 0.30
```

Ou por variaveis de ambiente (recomendado para nao expor a senha):

```bash
export IA_MYSQL_HOST=mysql.50webs.com
export IA_MYSQL_USER=intart_1
export IA_MYSQL_PASS=intart_1
export IA_MYSQL_DB=intart_1
export IA_MYSQL_PORT=3306
python3 main.py
```

- `--threshold`: confianca minima (0 a 1) para a IA responder em vez de
  perguntar. Mais baixo = responde mais (e arrisca mais); mais alto = so
  responde quando tem certeza.

## Interface WEB (upload de arquivos e alimentacao por outras IAs)

Alem do terminal, ha uma interface no navegador:

```bash
pip install -r requirements.txt
python3 web.py          # abre em http://127.0.0.1:5000
```

A pagina tem quatro partes:

1. **Conversar** — chat com a IA. Se ela nao souber, pergunta a resposta certa
   e aprende na hora.
2. **Enviar arquivo para analise** — um **botao** que abre o seletor de
   arquivos do sistema (a "telinha"). Voce escolhe o arquivo, a IA **analisa**
   (palavras-chave + resumo) e **alimenta o banco** com o conteudo (cada trecho
   vira conhecimento pesquisavel), ficando disponivel nas respostas. Ou seja,
   todo arquivo analisado tambem alimenta a IA. Formatos suportados:
   - Texto/codigo: `txt, md, csv, tsv, json, xml, html, yaml, ini, py, js,
     java, c, cpp, go, rb, php, sql, sh, ...`
   - Binarios (via extratores opcionais): `pdf` (pdfminer.six / PyPDF2),
     `docx` (python-docx), `xlsx` (openpyxl). Se a biblioteca nao estiver
     instalada, a IA avisa em vez de quebrar.
3. **Alimentar com info de outra IA** — registre conhecimento vindo de **outra
   inteligencia artificial** sobre um arquivo. Duas formas:
   - **colar o texto** que a outra IA produziu, ou
   - **enviar um arquivo** (`pdf, md, txt, docx, ...`) direto como carga de
     informacao.
   Informe o nome da IA; o conteudo e guardado marcado com a origem `ia:<nome>`
   e passa a ser usado nas respostas.
4. **Gerar arquivo sobre um assunto** — informe um assunto e a **extensao**
   desejada; a IA reune o que aprendeu sobre o tema e **gera o arquivo para
   download** no formato pedido: `pdf, py, md, txt, html, json, csv, docx,
   xlsx` ou **qualquer outra extensao** (ex.: `js, sql, java`, que saem como
   texto/comentarios). PDF usa `fpdf2`; DOCX usa `python-docx`; XLSX usa
   `openpyxl`.
5. **IAs externas (fallback)** — cadastre uma IA externa com o tipo
   (`openai, anthropic, gemini, custom`), modelo, base URL (opcional) e a
   **chave de autenticacao**. Marque no chat a opcao *"Perguntar a uma IA
   externa quando eu nao souber"*: se a IA local nao tiver confianca, ela
   consulta a IA externa, **devolve a resposta e a aprende** (origem
   `ia:<apelido>`), ficando disponivel offline nas proximas vezes. A chave fica
   no seu MySQL e so e enviada ao provedor escolhido.

Os documentos absorvidos (por upload ou por outra IA) aparecem na lista
"Documentos absorvidos".

### Endpoints (caso queira integrar)

| Metodo | Rota | Funcao |
|---|---|---|
| POST | `/api/ask` | `{pergunta}` -> resposta + confianca |
| POST | `/api/ensinar` | `{pergunta, resposta}` -> aprende |
| POST | `/api/upload` | arquivo (multipart; campo opcional `ia` marca a origem) -> analisa e alimenta a IA |
| POST | `/api/alimentar` | `{arquivo, conteudo, ia}` -> absorve info (texto) de outra IA |
| POST | `/api/gerar` | `{assunto, formato}` -> gera e devolve o arquivo (download) |
| GET | `/api/provedores` | lista as IAs externas (chave mascarada) |
| POST | `/api/provedores` | `{name, kind, base_url, model, api_key}` -> cadastra IA externa |
| DELETE | `/api/provedores/<id>` | remove a IA externa |
| POST | `/api/provedores/<id>/ativar` | `{enabled}` -> ativa/desativa |
| POST | `/api/provedores/<id>/testar` | testa a conexao com a IA externa |
| GET | `/api/stats` | estatisticas do banco |
| GET | `/api/documentos` | lista de documentos absorvidos |

### Os mesmos recursos pelo terminal

```
voce> /analisar /caminho/para/relatorio.pdf   # analisa e absorve um arquivo
voce> /gerar pdf produto Aurora               # gera produto_aurora.pdf no disco
voce> /documentos                             # lista os arquivos absorvidos
voce> resumo do arquivo relatorio.pdf         # pergunta sobre o que absorveu
```

## Usando como biblioteca

```python
from ia import Brain

# Conecta ao MySQL com as credenciais padrao (ou variaveis de ambiente):
ia = Brain()

# Ou informando a conexao explicitamente:
# ia = Brain(host="mysql.50webs.com", user="intart_1",
#            password="intart_1", database="intart_1")

ia.learn("quem criou o python", "Guido van Rossum")
resposta, match = ia.respond("quem inventou o python?")
print(resposta)          # Guido van Rossum
print(match.confidence)  # confianca da resposta

# Analisar/absorver um arquivo:
with open("relatorio.pdf", "rb") as f:
    info = ia.ingest_document("relatorio.pdf", f.read())
print(info["resumo"], info["trechos_indexados"])

# Alimentar com info de outra IA sobre um arquivo:
ia.feed_from_ai("relatorio.pdf", "Resumo produzido por outra IA...", ai_name="GPT")

# Gerar um arquivo sobre um assunto no formato desejado:
nome, conteudo, mime = ia.generate_file("produto Aurora", "pdf")
with open(nome, "wb") as f:
    f.write(conteudo)   # -> produto_aurora.pdf

# (Opcional) cadastrar uma IA externa e consultar quando nao souber:
ia.add_provider(name="meu-gpt", kind="openai", model="gpt-4o-mini",
                api_key="sk-...")
print(ia.answer("pergunta dificil", use_external=True))

ia.close()
```

## Comandos do terminal (lista completa)

| Comando | O que faz |
|---|---|
| `/ensinar` / `/ensinar P \| R` | ensina um par pergunta/resposta |
| `/buscar texto` | mostra os itens mais parecidos |
| `/analisar <caminho>` | le um arquivo do disco, analisa e absorve |
| `/gerar <ext> <assunto>` | gera um arquivo (pdf, py, md, txt...) sobre o assunto |
| `/documentos` | lista os arquivos absorvidos |
| `/provedores` | lista as IAs externas (fallback) cadastradas |
| `/esquecer <id>` | remove um item de conhecimento |
| `/bom` | reforca a ultima resposta dada |
| `/stats` / `/listar` | estatisticas / lista tudo |
| `/web` | dica para abrir a interface web |
| `/ajuda` / `/sair` | ajuda / encerra |

## Gerar o executavel (.exe para Windows)

O programa pode ser empacotado num **executavel unico** com o
[PyInstaller](https://pyinstaller.org). Ao abrir o `.exe`, ele sobe o servidor
e abre o navegador automaticamente na interface da IA.

> Importante: o PyInstaller gera o executavel para o sistema onde roda. Para um
> `.exe` de **Windows**, e preciso compilar **no Windows** (ou usar o GitHub
> Actions abaixo). Compilar no Linux/macOS gera um binario daquele sistema.

### Opcao A - GitHub Actions (recomendado, sem precisar de Windows)

O repositorio inclui o workflow `.github/workflows/build-exe.yml`, que compila
o `.exe` num runner Windows:

1. Na aba **Actions** do GitHub, rode o workflow **"Build Windows EXE"**
   (botao *Run workflow*). Ao terminar, baixe o `intart-ia.exe` em
   **Artifacts**.
2. Para um **link de download permanente**, crie uma tag de versao:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   O workflow publica automaticamente uma **Release** com o `intart-ia.exe`
   anexado.

### Opcao B - compilar localmente (no Windows)

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm intart-ia.spec
```

O executavel aparece em `dist/intart-ia.exe`. Basta dar dois cliques.

> O `.exe` ainda precisa de internet para acessar o MySQL. As credenciais
> padrao ja vem embutidas; para troca-las, defina as variaveis de ambiente
> `IA_MYSQL_*` antes de abrir o programa.

## Limitacoes (e proximos passos possiveis)

- Por padrao e uma IA de **recuperacao**: responde e **gera documentos** a
  partir do que ja aprendeu (nao inventa conteudo novo do zero). Isso a torna
  leve e transparente. Para respostas que ela nao tem, voce pode (opcional)
  ligar uma **IA externa** como fallback — e o que ela responder vira
  conhecimento aprendido.
- As chaves das IAs externas ficam guardadas no MySQL. Em repositorio/host
  compartilhado, trate-as como segredo (use um banco proprio e seguro).
- Ideias de evolucao: gerar texto novo com cadeias de Markov, suporte a
  sinonimos, e correcao de erros de digitacao na busca.
