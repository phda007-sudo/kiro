"""
IA de aprendizado proprio (sem APIs externas), com armazenamento em MySQL.

Pacote com os modulos:
    - text:     processamento de texto (normalizacao, tokenizacao)
    - db_mysql: camada de persistencia em MySQL (banco acumulado, unico backend)
    - brain:    motor de aprendizado e busca por similaridade (TF-IDF + cosseno)
"""

from .brain import Brain
from .db_mysql import MySQLDatabase

__all__ = ["Brain", "MySQLDatabase"]
__version__ = "2.0.0"
