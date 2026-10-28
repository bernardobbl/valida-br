"""Validação, formatação e geração de CPF e CNPJ.

Os dois documentos usam o mesmo truque: dígitos verificadores calculados
por soma ponderada módulo 11. Só mudam os pesos.
"""

from __future__ import annotations

import random
import re

_PESOS_CPF = (list(range(10, 1, -1)), list(range(11, 1, -1)))
_PESOS_CNPJ = (
    [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
    [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
)


def somente_digitos(valor: str) -> str:
    """Remove pontos, traços, barras e espaços."""
    return re.sub(r"\D", "", valor or "")


def _digito(numeros: list[int], pesos: list[int]) -> int:
    resto = sum(n * p for n, p in zip(numeros, pesos, strict=True)) % 11
    return 0 if resto < 2 else 11 - resto


def _calcula_dvs(base: list[int], pesos: tuple[list[int], list[int]]) -> list[int]:
    d1 = _digito(base, pesos[0])
    d2 = _digito(base + [d1], pesos[1])
    return [d1, d2]


def _valida(valor: str, tamanho: int, pesos) -> bool:
    numeros = somente_digitos(valor)
    if len(numeros) != tamanho or len(set(numeros)) == 1:
        return False  # tamanho errado ou "111.111.111-11"
    digitos = [int(c) for c in numeros]
    return digitos[-2:] == _calcula_dvs(digitos[:-2], pesos)


def valida_cpf(cpf: str) -> bool:
    return _valida(cpf, 11, _PESOS_CPF)


def valida_cnpj(cnpj: str) -> bool:
    return _valida(cnpj, 14, _PESOS_CNPJ)


def formata_cpf(cpf: str) -> str:
    n = somente_digitos(cpf)
    if len(n) != 11:
        raise ValueError("CPF precisa ter 11 dígitos")
    return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"


def formata_cnpj(cnpj: str) -> str:
    n = somente_digitos(cnpj)
    if len(n) != 14:
        raise ValueError("CNPJ precisa ter 14 dígitos")
    return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"


def gera_cpf(rng: random.Random | None = None) -> str:
    """Gera um CPF válido (fictício) já formatado."""
    rng = rng or random.Random()
    while True:
        base = [rng.randint(0, 9) for _ in range(9)]
        if len(set(base)) > 1:
            break
    return formata_cpf("".join(map(str, base + _calcula_dvs(base, _PESOS_CPF))))


def gera_cnpj(rng: random.Random | None = None) -> str:
    """Gera um CNPJ válido (fictício) de matriz (0001) já formatado."""
    rng = rng or random.Random()
    base = [rng.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    return formata_cnpj("".join(map(str, base + _calcula_dvs(base, _PESOS_CNPJ))))


def identifica(valor: str) -> str:
    """Diz se o valor é um CPF válido, um CNPJ válido ou inválido."""
    if valida_cpf(valor):
        return "CPF"
    if valida_cnpj(valor):
        return "CNPJ"
    return "inválido"
