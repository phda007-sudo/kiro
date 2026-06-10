# -*- coding: utf-8 -*-
"""
Gera o backup/cadastro de produtos a partir do pacote
'pacote_medicamentos_ean_farmacia_popular_2026.zip'.

Para CADA medicamento do pacote, pega: nome, codigo de barras (EAN) e
categoria; e cria o produto com:
    preco = R$ 1,00 | estoque = 10 | estoque minimo = 1 | tipo = unidade

Saidas (na pasta atual):
  1) produtos_farmacia_popular_import.csv -> importar no sistema
        (Cadastros > Importar Medicamentos/Produtos, ou Ctrl+I)
  2) products_backup.json + categorias_backup.json -> backup em JSON

Opcional: --mysql -> insere direto no banco 'farmacia' (le config.ini),
  criando as categorias e gravando categoria_id correto + estoque_minimo=1.

Uso:
  python tools/gerar_bkp_produtos_farmacia_popular.py [caminho_do_zip] [--mysql]
"""
import csv
import io
import json
import os
import sys
import zipfile

PRECO = 1.00
ESTOQUE = 10
ESTOQUE_MIN = 1

# Aliases de colunas aceitos no pacote (case-insensitive).
COLS = {
    'nome': ['nome', 'produto', 'descricao', 'description', 'name', 'item',
             'medicamento', 'apresentacao', 'produto/apresentacao', 'descricao_produto'],
    'codigo_barras': ['codigo_barras', 'ean', 'ean13', 'barcode', 'codigo', 'cod_barras',
                      'gtin', 'codigo de barras', 'cod barras', 'barras', 'cod. barras'],
    'categoria': ['categoria', 'category', 'grupo', 'group', 'classe', 'classe_terapeutica',
                  'grupo_terapeutico', 'classe terapeutica', 'grupo terapeutico', 'tipo_medicamento',
                  'indicacao', 'indicação', 'indicacao_terapeutica', 'indicaçao'],
}


def _norm(s):
    return str(s if s is not None else '').strip().lower()



def _detect(headers):
    """Mapeia campo -> nome real da coluna presente no arquivo."""
    m = {}
    low = [_norm(h) for h in headers]
    for campo, aliases in COLS.items():
        for i, h in enumerate(low):
            if h in aliases:
                m[campo] = headers[i]
                break
    return m


def _read_rows_from_bytes(name, data):
    """Le um arquivo (csv/txt/tsv/json/xlsx) e retorna lista de dicts."""
    n = name.lower()
    if n.endswith(('.csv', '.txt', '.tsv')):
        text = data.decode('utf-8-sig', errors='replace')
        sample = text[:4096]
        delim = ';' if sample.count(';') >= sample.count(',') else ','
        if '\t' in sample and sample.count('\t') > sample.count(delim):
            delim = '\t'
        return list(csv.DictReader(io.StringIO(text), delimiter=delim))
    if n.endswith('.json'):
        obj = json.loads(data.decode('utf-8', errors='replace'))
        if isinstance(obj, dict):
            obj = list(obj.values())
        return [r for r in obj if isinstance(r, dict)]
    if n.endswith(('.xlsx', '.xls')):
        try:
            import openpyxl
        except ImportError:
            print('[ERRO] openpyxl necessario p/ .xlsx: pip install openpyxl')
            return []
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        if not rows:
            return []
        headers = [str(h).strip() if h is not None else f'col{i}'
                   for i, h in enumerate(rows[0])]
        out = []
        for r in rows[1:]:
            if any(c is not None and str(c).strip() for c in r):
                out.append(dict(zip(headers, r)))
        return out
    return []



def carregar_pacote(zip_path):
    """Extrai (nome, codigo_barras, categoria) de todos os arquivos do zip."""
    registros = []
    with zipfile.ZipFile(zip_path) as z:
        nomes = [i for i in z.namelist() if not i.endswith('/')]
        dados = [i for i in nomes
                 if i.lower().endswith(('.csv', '.xlsx', '.xls', '.json', '.tsv', '.txt'))]
        for nome in (dados or nomes):
            try:
                linhas = _read_rows_from_bytes(nome, z.read(nome))
            except Exception as e:
                print(f'[AVISO] nao consegui ler {nome}: {e}')
                continue
            if not linhas:
                continue
            m = _detect(list(linhas[0].keys()))
            if 'nome' not in m:
                print(f'[AVISO] {nome}: sem coluna de nome; ignorado. '
                      f'Colunas: {list(linhas[0].keys())}')
                continue
            for r in linhas:
                nome_p = str(r.get(m['nome'], '')).strip()
                if not nome_p or nome_p.lower() in ('none', 'nan'):
                    continue
                ean = str(r.get(m.get('codigo_barras', ''), '')).strip()
                if ean.lower() in ('none', 'nan'):
                    ean = ''
                if ean.endswith('.0'):
                    ean = ean[:-2]
                cat = str(r.get(m.get('categoria', ''), '')).strip()
                if not cat or cat.lower() in ('none', 'nan'):
                    cat = 'Geral'
                registros.append({'nome': nome_p, 'codigo_barras': ean, 'categoria': cat})
            print(f'[OK] {nome}: {len(linhas)} linha(s) lida(s)')
    return registros


def dedupe(regs):
    vistos = set()
    out = []
    for r in regs:
        chave = r['codigo_barras'] or ('NOME:' + r['nome'].lower())
        if chave in vistos:
            continue
        vistos.add(chave)
        out.append(r)
    return out



def gerar_csv(regs, path):
    """CSV pronto para o importador do sistema (delimitador ';')."""
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['nome', 'codigo_barras', 'categoria', 'preco',
                    'estoque', 'estoque_minimo', 'tipo', 'unidade'])
        for r in regs:
            w.writerow([r['nome'], r['codigo_barras'], r['categoria'],
                        '1,00', '10', '1', 'unidade', 'un'])


def gerar_json(regs, prod_path, cat_path):
    """Backup em JSON no formato de cadastro de produtos do sistema."""
    cat_ids = {}
    cats = {}
    nid = 1
    for r in regs:
        c = r['categoria']
        if c not in cat_ids:
            cat_ids[c] = nid
            cats[str(nid)] = {'nome': c, 'descricao': ''}
            nid += 1
    produtos = {}
    for i, r in enumerate(regs, start=1):
        cid = str(cat_ids[r['categoria']])
        produtos[str(i)] = {
            'nome': r['nome'], 'codigo_barras': r['codigo_barras'],
            'categoria_id': cid, 'categoria': cid,
            'preco': 1.0, 'preco_compra': 0.0, 'preco_atacado': 0.0, 'tipo': 'unidade',
            'estoque': 10, 'estoque_minimo': 1, 'fidelidade_pontos': 0,
            'controlar_lote_validade': False, 'ativo': True,
        }
    with open(prod_path, 'w', encoding='utf-8') as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)
    with open(cat_path, 'w', encoding='utf-8') as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)
    return cats



def carregar_config_mysql():
    import configparser
    for p in [r'C:\Quantum\config.ini', os.path.join(os.getcwd(), 'config.ini')]:
        if os.path.exists(p):
            cp = configparser.ConfigParser()
            cp.read(p, encoding='utf-8')
            if cp.has_section('mysql'):
                m = cp['mysql']
                return dict(host=m.get('host', '127.0.0.1'), port=int(m.get('port', '3306')),
                            user=m.get('user', 'root'), password=m.get('password', ''),
                            database=m.get('database', 'farmacia'))
    return None


def carregar_no_mysql(regs):
    """Insere os produtos direto no banco com categoria_id e estoque_minimo=1."""
    import mysql.connector
    cfg = carregar_config_mysql()
    if not cfg:
        print('[ERRO] config.ini nao encontrado (C:\\Quantum\\config.ini).')
        return
    cn = mysql.connector.connect(**cfg)
    cur = cn.cursor()
    cat_id = {}
    for r in regs:
        c = r['categoria']
        if c in cat_id:
            continue
        cur.execute("SELECT id FROM categorias WHERE nome=%s LIMIT 1", (c,))
        row = cur.fetchone()
        if row:
            cat_id[c] = row[0]
        else:
            cur.execute("INSERT INTO categorias (nome, descricao, ativo) VALUES (%s,'',1)", (c,))
            cat_id[c] = cur.lastrowid
    cn.commit()
    ins = pulados = 0
    for r in regs:
        if r['codigo_barras']:
            cur.execute("SELECT id FROM produtos WHERE codigo_barras=%s LIMIT 1", (r['codigo_barras'],))
            if cur.fetchone():
                pulados += 1
                continue
        cur.execute(
            "INSERT INTO produtos (nome, codigo_barras, categoria_id, preco, preco_compra, "
            "preco_atacado, tipo, estoque, estoque_minimo, controlar_lote_validade, ativo) "
            "VALUES (%s,%s,%s,%s,0,0,'unidade',%s,%s,0,1)",
            (r['nome'], r['codigo_barras'], cat_id[r['categoria']], PRECO, ESTOQUE, ESTOQUE_MIN))
        ins += 1
    cn.commit()
    cur.close()
    cn.close()
    print(f'[MYSQL] Inseridos {ins} produto(s); {pulados} ja existiam (mesmo EAN).')



def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    zip_path = args[0] if args else 'pacote_medicamentos_ean_farmacia_popular_2026.zip'
    if not os.path.exists(zip_path):
        print(f'[ERRO] zip nao encontrado: {zip_path}')
        print('       Coloque o pacote nesta pasta ou informe o caminho como argumento.')
        sys.exit(1)
    regs = dedupe(carregar_pacote(zip_path))
    if not regs:
        print('[ERRO] Nenhum produto extraido. Verifique as colunas do pacote.')
        sys.exit(2)
    gerar_csv(regs, 'produtos_farmacia_popular_import.csv')
    cats = gerar_json(regs, 'products_backup.json', 'categorias_backup.json')
    print('')
    print(f'[OK] {len(regs)} produto(s) | {len(cats)} categoria(s)')
    print('  -> produtos_farmacia_popular_import.csv  (importar via Ctrl+I no sistema)')
    print('  -> products_backup.json / categorias_backup.json  (backup em JSON)')
    print('  Todos: preco R$ 1,00 | estoque 10 | estoque minimo 1 | tipo unidade')
    if '--mysql' in flags:
        carregar_no_mysql(regs)


if __name__ == '__main__':
    main()
