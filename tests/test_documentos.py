import random

import pytest

from validabr import (
    formata_cnpj,
    formata_cpf,
    gera_cnpj,
    gera_cpf,
    identifica,
    valida_cnpj,
    valida_cpf,
)


@pytest.mark.parametrize("cpf", ["529.982.247-25", "52998224725", "111.444.777-35"])
def test_cpf_valido(cpf):
    assert valida_cpf(cpf)


@pytest.mark.parametrize(
    "cpf",
    ["529.982.247-24", "111.111.111-11", "123", "", "abc.def.ghi-jk", "529.982.247-255"],
)
def test_cpf_invalido(cpf):
    assert not valida_cpf(cpf)


@pytest.mark.parametrize("cnpj", ["11.222.333/0001-81", "11222333000181"])
def test_cnpj_valido(cnpj):
    assert valida_cnpj(cnpj)


@pytest.mark.parametrize("cnpj", ["11.222.333/0001-80", "00.000.000/0000-00", "1234"])
def test_cnpj_invalido(cnpj):
    assert not valida_cnpj(cnpj)


def test_formatacao():
    assert formata_cpf("52998224725") == "529.982.247-25"
    assert formata_cnpj("11222333000181") == "11.222.333/0001-81"


@pytest.mark.parametrize("func", [formata_cpf, formata_cnpj])
def test_formatacao_tamanho_errado(func):
    with pytest.raises(ValueError):
        func("123")


def test_gerados_sao_validos():
    rng = random.Random(42)
    for _ in range(200):
        assert valida_cpf(gera_cpf(rng))
        assert valida_cnpj(gera_cnpj(rng))


def test_identifica():
    assert identifica("529.982.247-25") == "CPF"
    assert identifica("11.222.333/0001-81") == "CNPJ"
    assert identifica("000") == "inválido"
