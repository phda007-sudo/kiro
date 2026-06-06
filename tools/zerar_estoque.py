# -*- coding: utf-8 -*-
"""
Zera o ESTOQUE (quantidade) de TODOS os produtos no banco 'farmacia'.
Le as credenciais do config.ini (C:\\Quantum\\config.ini ou pasta atual).
Apenas a coluna 'estoque' vai a 0; preco, estoque_minimo, etc. NAO mudam.

Uso:
    python tools/zerar_estoque.py
"""
import os
import sys


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


def main():
    import mysql.connector
    cfg = carregar_config_mysql()
    if not cfg:
        print('[ERRO] config.ini nao encontrado (C:\\Quantum\\config.ini).')
        sys.exit(1)
    cn = mysql.connector.connect(**cfg)
    cur = cn.cursor()
    # Conta quantos produtos serao afetados
    cur.execute("SELECT COUNT(*) FROM produtos")
    total = cur.fetchone()[0]
    # Zera o estoque (quantidade) de TODOS os produtos
    cur.execute("UPDATE produtos SET estoque = 0")
    afetados = cur.rowcount
    cn.commit()
    cur.close()
    cn.close()
    print(f"[OK] Estoque zerado. Produtos no banco: {total} | linhas atualizadas: {afetados}.")
    print("     (preco, estoque_minimo e demais campos foram preservados)")


if __name__ == '__main__':
    main()
