"""Linha de comando.

Exemplos:
    validabr checa 529.982.247-25 11.222.333/0001-81 123
    validabr gera cpf --quantidade 3
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .documentos import gera_cnpj, gera_cpf, identifica

VERDE, VERMELHO, FIM = "\033[32m", "\033[31m", "\033[0m"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validabr", description="Valida e gera CPF/CNPJ")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="comando", required=True)

    checa = sub.add_parser("checa", help="valida um ou mais documentos")
    checa.add_argument("documentos", nargs="+")

    gera = sub.add_parser("gera", help="gera documentos válidos fictícios")
    gera.add_argument("tipo", choices=["cpf", "cnpj"])
    gera.add_argument("-q", "--quantidade", type=int, default=1)

    args = parser.parse_args(argv)

    if args.comando == "gera":
        gerador = gera_cpf if args.tipo == "cpf" else gera_cnpj
        for _ in range(args.quantidade):
            print(gerador())
        return 0

    algum_invalido = False
    for doc in args.documentos:
        tipo = identifica(doc)
        if tipo == "inválido":
            algum_invalido = True
            print(f"{VERMELHO}✗{FIM} {doc}: inválido")
        else:
            print(f"{VERDE}✓{FIM} {doc}: {tipo} válido")
    return 1 if algum_invalido else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
