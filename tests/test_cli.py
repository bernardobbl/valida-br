from validabr.cli import main


def test_checa_tudo_valido(capsys):
    assert main(["checa", "529.982.247-25", "11.222.333/0001-81"]) == 0
    saida = capsys.readouterr().out
    assert "CPF válido" in saida
    assert "CNPJ válido" in saida


def test_checa_com_invalido_retorna_erro(capsys):
    assert main(["checa", "529.982.247-25", "123"]) == 1
    assert "inválido" in capsys.readouterr().out


def test_gera(capsys):
    assert main(["gera", "cpf", "-q", "3"]) == 0
    assert len(capsys.readouterr().out.strip().splitlines()) == 3
    assert main(["gera", "cnpj"]) == 0
    assert "/0001-" in capsys.readouterr().out
