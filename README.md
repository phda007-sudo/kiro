# IA de Aprendizado Proprio (sem APIs, armazenamento em MySQL)

Uma IA conversacional construida **do zero**, em **Python puro**. Ela **nao usa
nenhuma API externa** nem modelos prontos. Toda a "inteligencia" vem de tecnicas
classicas de recuperacao de informacao implementadas a mao.

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
  brain.py        # TF-IDF + cosseno: aprende, busca e responde
main.py           # interface de chat no terminal
requirements.txt  # PyMySQL (driver MySQL)
```

As tabelas (`knowledge`, `vocab`, `postings`, `meta`) sao criadas
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
ia.close()
```

## Limitacoes (e proximos passos possiveis)

- E uma IA de **recuperacao** (encontra a melhor resposta ja aprendida), nao
  uma que **gera** texto novo. Isso a torna leve e transparente.
- Ideias de evolucao: gerar respostas com cadeias de Markov a partir do que
  aprendeu, suporte a sinonimos, e correcao de erros de digitacao (distancia
  de edicao) na busca.
