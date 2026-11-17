"""
Confere a tabela linha a linha de docs/roteiro_rotas.md contra codigo/rotas.py.

Para cada linha da tabela:
    - linha única: o texto da coluna "código" tem de ser igual à linha do arquivo;
    - intervalo (ex.: 90–92): só pode cobrir comentário, docstring ou linha em branco,
      e o texto da coluna "código" tem de aparecer no início de uma dessas linhas.
Além disso, toda linha não vazia de rotas.py tem de aparecer exatamente uma vez, e
os intervalos da tabela de funções (seção 1.3) têm de bater com o def/class real.

Uso (na raiz do repositório), depois de qualquer mudança em rotas.py:
    python docs/conferir_roteiro.py
Sai com código 1 e lista os problemas se a tabela estiver desatualizada.
"""

import ast
import os
import re
import sys
from typing import Dict, List, Set, Tuple

PASTA_DOCS = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ROTEIRO = os.path.join(PASTA_DOCS, "roteiro_rotas.md")
CAMINHO_ROTAS = os.path.join(os.path.dirname(PASTA_DOCS), "codigo", "rotas.py")
MARCADOR_INICIO = "<!-- tabela-linha-a-linha:inicio -->"
MARCADOR_FIM = "<!-- tabela-linha-a-linha:fim -->"
MARCADOR_FUNCOES_INICIO = "<!-- funcoes:inicio -->"
MARCADOR_FUNCOES_FIM = "<!-- funcoes:fim -->"
LINHA_DA_TABELA = re.compile(r"^\| (\d+)(?:–(\d+))? \| `(.*)` \| .* \|$")
LINHA_DA_TABELA_DE_FUNCOES = re.compile(r"^\| \d+ \| `(\w+)` \| (\d+)–(\d+) \|")
RETICENCIAS = "…"


def lerLinhasDeDocstring(fonte: str) -> Set[int]:
    """Números das linhas que pertencem a alguma docstring (módulo, classe ou função)."""
    linhasDeDocstring: Set[int] = set()
    arvore = ast.parse(fonte)
    for no in [arvore] + [n for n in ast.walk(arvore)
                          if isinstance(n, (ast.FunctionDef, ast.ClassDef))]:
        primeiro = no.body[0] if no.body else None
        if (isinstance(primeiro, ast.Expr) and isinstance(primeiro.value, ast.Constant)
                and isinstance(primeiro.value.value, str)):
            linhasDeDocstring.update(range(primeiro.lineno, primeiro.end_lineno + 1))
    return linhasDeDocstring


def lerTabela(textoDoRoteiro: str) -> List[Tuple[int, int, str]]:
    """Devolve (linha inicial, linha final, texto da coluna código) de cada linha da tabela."""
    trecho = textoDoRoteiro.split(MARCADOR_INICIO)[1].split(MARCADOR_FIM)[0]
    linhasDaTabela = []
    for linha in trecho.splitlines():
        encontrada = LINHA_DA_TABELA.match(linha.strip())
        if encontrada:
            inicio = int(encontrada.group(1))
            fim = int(encontrada.group(2) or inicio)
            codigo = encontrada.group(3).replace("\\|", "|")
            linhasDaTabela.append((inicio, fim, codigo))
    return linhasDaTabela


def conferirTabelaDeFuncoes(fonte: str, textoDoRoteiro: str) -> List[str]:
    """Cada função citada na seção 1.3 tem de ocupar exatamente o intervalo informado."""
    intervaloReal: Dict[str, Tuple[int, int]] = {}
    for no in ast.walk(ast.parse(fonte)):
        if isinstance(no, (ast.FunctionDef, ast.ClassDef)):
            intervaloReal[no.name] = (no.lineno, no.end_lineno)
    trecho = textoDoRoteiro.split(MARCADOR_FUNCOES_INICIO)[1].split(MARCADOR_FUNCOES_FIM)[0]
    problemas: List[str] = []
    for linha in trecho.splitlines():
        encontrada = LINHA_DA_TABELA_DE_FUNCOES.match(linha.strip())
        if not encontrada:
            continue
        nome, inicio, fim = encontrada.group(1), int(encontrada.group(2)), int(encontrada.group(3))
        if intervaloReal.get(nome) != (inicio, fim):
            problemas.append(f"seção 1.3: `{nome}` diz {inicio}–{fim}, "
                             f"real é {intervaloReal.get(nome)}")
    return problemas


def conferir() -> List[str]:
    with open(CAMINHO_ROTAS, encoding="utf-8") as arquivo:
        fonte = arquivo.read()
    with open(CAMINHO_ROTEIRO, encoding="utf-8") as arquivo:
        textoDoRoteiro = arquivo.read()
    tabela = lerTabela(textoDoRoteiro)
    linhasDoArquivo = [linha.strip() for linha in fonte.splitlines()]
    linhasDeDocstring = lerLinhasDeDocstring(fonte)
    cobertura: Dict[int, int] = {}
    problemas = conferirTabelaDeFuncoes(fonte, textoDoRoteiro)
    for inicio, fim, codigo in tabela:
        if fim > len(linhasDoArquivo):
            problemas.append(f"linha {fim} não existe (rotas.py tem {len(linhasDoArquivo)})")
            continue
        for numero in range(inicio, fim + 1):
            cobertura[numero] = cobertura.get(numero, 0) + 1
        linhaUnicaDeCodigo = (inicio == fim and inicio not in linhasDeDocstring
                              and not codigo.startswith("#"))
        if linhaUnicaDeCodigo:
            if linhasDoArquivo[inicio - 1] != codigo:
                problemas.append(f"linha {inicio}: tabela diz `{codigo}`, "
                                 f"arquivo tem `{linhasDoArquivo[inicio - 1]}`")
            continue
        for numero in range(inicio, fim + 1):
            texto = linhasDoArquivo[numero - 1]
            if texto and numero not in linhasDeDocstring and not texto.startswith("#"):
                problemas.append(f"intervalo {inicio}–{fim} cobre código na linha {numero}")
        prefixo = codigo.rstrip(RETICENCIAS).rstrip()
        trechoDoArquivo = linhasDoArquivo[inicio - 1:fim]
        if not any(texto.startswith(prefixo) for texto in trechoDoArquivo):
            problemas.append(f"intervalo {inicio}–{fim}: `{codigo}` não aparece nessas linhas")
    for numero, texto in enumerate(linhasDoArquivo, start=1):
        if texto and cobertura.get(numero, 0) != 1:
            problemas.append(f"linha {numero} aparece {cobertura.get(numero, 0)} vez(es) na tabela")
    return problemas


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    problemas = conferir()
    if problemas:
        print("Tabela desatualizada:")
        for problema in problemas:
            print("  -", problema)
        sys.exit(1)
    print("OK: a tabela de docs/roteiro_rotas.md confere com codigo/rotas.py, linha por linha.")


if __name__ == "__main__":
    main()
