"""
IA de aprendizado proprio (sem APIs externas).

Pacote com os modulos:
    - text:     processamento de texto (normalizacao, tokenizacao)
    - database: camada de persistencia em SQLite (banco acumulado)
    - brain:    motor de aprendizado e busca por similaridade (TF-IDF + cosseno)
"""

from .brain import Brain
from .database import Database

__all__ = ["Brain", "Database"]
__version__ = "1.0.0"
