"""valida-br: valida, formata e gera CPF e CNPJ."""

from .documentos import (
    formata_cnpj,
    formata_cpf,
    gera_cnpj,
    gera_cpf,
    identifica,
    somente_digitos,
    valida_cnpj,
    valida_cpf,
)

__version__ = "1.0.0"

__all__ = [
    "formata_cnpj",
    "formata_cpf",
    "gera_cnpj",
    "gera_cpf",
    "identifica",
    "somente_digitos",
    "valida_cnpj",
    "valida_cpf",
]
