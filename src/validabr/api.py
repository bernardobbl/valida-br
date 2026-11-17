"""API HTTP mínima (só biblioteca padrão) usada como alvo do DAST.

Rotas:
    GET /                         página inicial com links de exemplo
    GET /health                   {"status": "ok"}
    GET /api/valida?doc=...       diz se o documento é CPF, CNPJ ou inválido
    GET /api/gera/cpf?quantidade=N gera N documentos fictícios (cpf ou cnpj, máx. 50)

Rodando:
    validabr serve --porta 8000
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .documentos import formata_cnpj, formata_cpf, gera_cnpj, gera_cpf, identifica, somente_digitos

MAX_QUANTIDADE = 50
MAX_DOC = 64  # ninguém precisa mandar um "CPF" de 10 mil caracteres

# Cabeçalhos de segurança enviados em TODAS as respostas (inclusive erros).
# São exatamente o tipo de coisa que o OWASP ZAP verifica no DAST.
CABECALHOS_SEGURANCA = {
    "Content-Security-Policy": (
        "default-src 'none'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Cross-Origin-Resource-Policy": "same-origin",
}

PAGINA_INICIAL = """<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>valida-br {versao}</title></head>
<body>
<h1>valida-br {versao}</h1>
<p>API para validar e gerar CPF e CNPJ. Exemplos:</p>
<ul>
<li><a href="/api/valida?doc=529.982.247-25">/api/valida?doc=529.982.247-25</a></li>
<li><a href="/api/valida?doc=11.222.333/0001-81">/api/valida?doc=11.222.333/0001-81</a></li>
<li><a href="/api/gera/cpf?quantidade=3">/api/gera/cpf?quantidade=3</a></li>
<li><a href="/api/gera/cnpj">/api/gera/cnpj</a></li>
<li><a href="/health">/health</a></li>
</ul>
</body>
</html>
"""


class ValidaBRHandler(BaseHTTPRequestHandler):
    # Não revela "BaseHTTP/0.6 Python/3.x" no cabeçalho Server.
    server_version = "valida-br"
    sys_version = ""

    def version_string(self) -> str:
        return self.server_version

    def end_headers(self) -> None:
        for nome, valor in CABECALHOS_SEGURANCA.items():
            self.send_header(nome, valor)
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        pass  # silencioso; o pipeline não precisa do log de cada requisição

    # -- respostas -------------------------------------------------------

    def _envia(self, status: HTTPStatus, corpo: str, tipo: str) -> None:
        dados = corpo.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{tipo}; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def _json(self, status: HTTPStatus, dados: dict) -> None:
        self._envia(status, json.dumps(dados, ensure_ascii=False), "application/json")

    # -- rotas -----------------------------------------------------------

    def do_GET(self) -> None:  # nome exigido pelo http.server
        url = urlsplit(self.path)
        params = parse_qs(url.query)

        if url.path == "/":
            self._envia(HTTPStatus.OK, PAGINA_INICIAL.format(versao=__version__), "text/html")
        elif url.path == "/health":
            self._json(HTTPStatus.OK, {"status": "ok", "versao": __version__})
        elif url.path == "/api/valida":
            self._valida(params.get("doc", [""])[0])
        elif url.path in ("/api/gera/cpf", "/api/gera/cnpj"):
            self._gera(url.path.rsplit("/", 1)[1], params.get("quantidade", ["1"])[0])
        else:
            self._json(HTTPStatus.NOT_FOUND, {"erro": "rota não encontrada"})

    def _valida(self, doc: str) -> None:
        if not doc or len(doc) > MAX_DOC:
            self._json(HTTPStatus.BAD_REQUEST, {"erro": f"informe ?doc= com até {MAX_DOC} chars"})
            return
        tipo = identifica(doc)
        resposta = {"documento": somente_digitos(doc), "tipo": tipo, "valido": tipo != "inválido"}
        if tipo == "CPF":
            resposta["formatado"] = formata_cpf(doc)
        elif tipo == "CNPJ":
            resposta["formatado"] = formata_cnpj(doc)
        self._json(HTTPStatus.OK, resposta)

    def _gera(self, tipo: str, quantidade: str) -> None:
        if not quantidade.isdigit() or not 1 <= int(quantidade) <= MAX_QUANTIDADE:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {"erro": f"quantidade deve ser um número entre 1 e {MAX_QUANTIDADE}"},
            )
            return
        gerador = gera_cpf if tipo == "cpf" else gera_cnpj
        self._json(
            HTTPStatus.OK, {"tipo": tipo, "documentos": [gerador() for _ in range(int(quantidade))]}
        )


def cria_servidor(host: str = "127.0.0.1", porta: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, porta), ValidaBRHandler)


def serve(host: str = "127.0.0.1", porta: int = 8000) -> None:  # pragma: no cover
    servidor = cria_servidor(host, porta)
    print(f"valida-br {__version__} ouvindo em http://{host}:{porta}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
