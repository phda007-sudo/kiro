# IA de Aprendizado Proprio (sem APIs)

Uma IA conversacional construida **do zero**, em **Python puro** (somente a
biblioteca padrao). Ela **nao usa nenhuma API externa** nem modelos prontos.
Toda a "inteligencia" vem de tecnicas classicas de recuperacao de informacao
implementadas a mao.

A ideia central:

> A IA comeca "vazia". Voce a ensina. Tudo o que ela aprende e **salvo num
> banco de dados SQLite acumulado**. Quando voce pergunta algo, ela **busca**
> nesse banco a resposta mais parecida. Quanto mais voce ensina, mais ela sabe.

## Como funciona

1. **Processamento de texto** (`ia/text.py`): normaliza a frase (minusculas,
   remove acentos e pontuacao) e quebra em palavras (tokens), descartando
   stopwords em portugues.
2. **Banco acumulado** (`ia/database.py`): SQLite com um **indice invertido**
   (`token -> documentos`). Guarda cada conhecimento, o vocabulario e contadores
   de uso/reforco. E aqui que a IA "busca e salva".
3. **Cerebro** (`ia/brain.py`): representa cada frase como um vetor **TF-IDF** e
   compara a pergunta com o que ja foi aprendido usando **similaridade do
   cosseno**. Se a confianca passa de um limiar, responde; senao, pede para
   aprender.

Nenhum servico de rede e chamado em momento algum.

## Estrutura

```
ia/
  __init__.py     # exporta Brain e Database
  text.py         # normalizacao e tokenizacao
  database.py     # backend SQLite (indice invertido + vocabulario)
  db_mysql.py     # backend MySQL (mesma interface, via PyMySQL)
  brain.py        # TF-IDF + cosseno: aprende, busca e responde
main.py           # interface de chat no terminal (escolhe o backend)
requirements.txt  # PyMySQL (so para o backend MySQL)
memoria.db        # criado automaticamente no backend SQLite
```

## Como usar

Requisitos: Python 3.9+.

- Backend **SQLite** (padrao historico): nao precisa instalar nada.
- Backend **MySQL**: precisa do driver `PyMySQL`:

```bash
pip install -r requirements.txt
```

### Rodando

Por padrao agora a IA usa **MySQL** (configurado para o banco do projeto):

```bash
python3 main.py                 # usa MySQL (mysql.50webs.com / intart_1)
python3 main.py --backend sqlite  # usa um arquivo local memoria.db
```

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

### Opcoes de linha de comando

```bash
# SQLite local
python3 main.py --backend sqlite --db meu_cerebro.db --threshold 0.25

# MySQL (host/usuario/senha/banco podem vir por flag ou variavel de ambiente)
python3 main.py --backend mysql \
  --mysql-host mysql.50webs.com --mysql-user intart_1 \
  --mysql-pass intart_1 --mysql-db intart_1
```

- `--backend`: `sqlite` ou `mysql` (padrao: `mysql`).
- `--db`: arquivo SQLite (quando `--backend sqlite`).
- `--threshold`: confianca minima (0 a 1) para a IA responder em vez de
  perguntar. Mais baixo = responde mais (e arrisca mais); mais alto = so
  responde quando tem certeza.
- `--mysql-host/-user/-pass/-db/-port`: conexao MySQL. Tambem podem ser
  definidos por variaveis de ambiente: `IA_MYSQL_HOST`, `IA_MYSQL_USER`,
  `IA_MYSQL_PASS`, `IA_MYSQL_DB`, `IA_MYSQL_PORT` e `IA_BACKEND`.

> Dica de seguranca: prefira passar a senha por variavel de ambiente
> (`export IA_MYSQL_PASS=...`) em vez de deixa-la no comando/historico.

## Backends de armazenamento

A logica de aprendizado e a mesma; muda so onde o conhecimento e guardado:

| Backend | Arquivo | Quando usar |
|---|---|---|
| SQLite (`ia/database.py`) | `memoria.db` local | offline, sem dependencias |
| MySQL (`ia/db_mysql.py`) | servidor MySQL | conhecimento compartilhado/remoto |

Os dois implementam a mesma interface, entao o `Brain` funciona com qualquer
um. Para usar MySQL como biblioteca:

```python
from ia import Brain
from ia.db_mysql import MySQLDatabase

db = MySQLDatabase(host="mysql.50webs.com", user="intart_1",
                   password="intart_1", database="intart_1")
ia = Brain(db=db)
ia.learn("quem criou o python", "Guido van Rossum")
print(ia.respond("quem inventou o python?")[0])
ia.close()
```

## Usando como biblioteca

```python
from ia import Brain

ia = Brain(db_path="memoria.db")
ia.learn("quem criou o python", "Guido van Rossum")

resposta, match = ia.respond("quem inventou o python?")
print(resposta)  # Guido van Rossum
print(match.confidence)  # confianca da resposta

ia.close()
```

## Limitacoes (e proximos passos possiveis)

- E uma IA de **recuperacao** (encontra a melhor resposta ja aprendida), nao
  uma que **gera** texto novo. Isso a torna leve, transparente e 100% offline.
- Ideias de evolucao: gerar respostas com cadeias de Markov a partir do que
  aprendeu, suporte a sinonimos, e correcao de erros de digitacao (distancia
  de edicao) na busca.
