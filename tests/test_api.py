import json
import threading
from http.client import HTTPConnection

import pytest

from validabr import api
from validabr.cli import main


@pytest.fixture(scope="module")
def servidor():
    srv = api.cria_servidor("127.0.0.1", 0)  # porta 0 = qualquer porta livre
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv.server_address[1]
    srv.shutdown()
    srv.server_close()


def get(porta, caminho, metodo="GET"):
    conn = HTTPConnection("127.0.0.1", porta, timeout=5)
    conn.request(metodo, caminho)
    resp = conn.getresponse()
    corpo = resp.read().decode()
    conn.close()
    return resp, corpo


def test_pagina_inicial(servidor):
    resp, corpo = get(servidor, "/")
    assert resp.status == 200
    assert resp.getheader("Content-Type").startswith("text/html")
    assert "/api/valida" in corpo


def test_health(servidor):
    resp, corpo = get(servidor, "/health")
    assert resp.status == 200
    assert json.loads(corpo)["status"] == "ok"


@pytest.mark.parametrize(
    "doc, tipo, formatado",
    [
        ("52998224725", "CPF", "529.982.247-25"),
        ("11.222.333/0001-81", "CNPJ", "11.222.333/0001-81"),
    ],
)
def test_valida_documento_valido(servidor, doc, tipo, formatado):
    resp, corpo = get(servidor, f"/api/valida?doc={doc}")
    dados = json.loads(corpo)
    assert resp.status == 200
    assert dados["tipo"] == tipo
    assert dados["valido"] is True
    assert dados["formatado"] == formatado


def test_valida_documento_invalido(servidor):
    resp, corpo = get(servidor, "/api/valida?doc=123")
    dados = json.loads(corpo)
    assert resp.status == 200
    assert dados == {"documento": "123", "tipo": "inválido", "valido": False}


def test_valida_nao_reflete_entrada(servidor):
    """A resposta devolve só os dígitos: nada de HTML/script refletido (XSS)."""
    _, corpo = get(servidor, "/api/valida?doc=%3Cscript%3E1%3C/script%3E")
    assert "<script>" not in corpo


@pytest.mark.parametrize("caminho", ["/api/valida", "/api/valida?doc=" + "1" * 65])
def test_valida_rejeita_entrada_ruim(servidor, caminho):
    resp, _ = get(servidor, caminho)
    assert resp.status == 400


def test_gera(servidor):
    resp, corpo = get(servidor, "/api/gera/cpf?quantidade=3")
    assert resp.status == 200
    assert len(json.loads(corpo)["documentos"]) == 3
    _, corpo = get(servidor, "/api/gera/cnpj")
    assert "/0001-" in json.loads(corpo)["documentos"][0]


@pytest.mark.parametrize("qtd", ["0", "51", "abc", "-1"])
def test_gera_limita_quantidade(servidor, qtd):
    resp, _ = get(servidor, f"/api/gera/cpf?quantidade={qtd}")
    assert resp.status == 400


def test_rota_inexistente(servidor):
    resp, _ = get(servidor, "/admin")
    assert resp.status == 404


@pytest.mark.parametrize("caminho", ["/", "/health", "/nao-existe"])
def test_cabecalhos_de_seguranca(servidor, caminho):
    resp, _ = get(servidor, caminho)
    for nome, valor in api.CABECALHOS_SEGURANCA.items():
        assert resp.getheader(nome) == valor
    assert "Python" not in resp.getheader("Server")


def test_metodo_nao_suportado_tambem_tem_cabecalhos(servidor):
    resp, _ = get(servidor, "/", metodo="POST")
    assert resp.status == 501
    assert resp.getheader("X-Frame-Options") == "DENY"


def test_cli_serve(monkeypatch):
    chamadas = []
    monkeypatch.setattr(api, "serve", lambda host, porta: chamadas.append((host, porta)))
    assert main(["serve", "--porta", "9999"]) == 0
    assert chamadas == [("127.0.0.1", 9999)]
