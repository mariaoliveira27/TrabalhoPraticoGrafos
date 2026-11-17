"""Deixa grafo.py, mapa.py e rotas.py (em codigo/) importáveis pelos testes desta pasta.

Assim `python -m pytest` funciona tanto da raiz do repositório quanto de dentro de codigo/.
"""

import os
import sys

PASTA_CODIGO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_CODIGO not in sys.path:
    sys.path.insert(0, PASTA_CODIGO)
