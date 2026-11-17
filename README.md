# valida-br

[![CI/CD](https://github.com/bernardobbl/valida-br/actions/workflows/ci.yml/badge.svg)](https://github.com/bernardobbl/valida-br/actions/workflows/ci.yml)

Biblioteca e linha de comando em Python para **validar, formatar e gerar CPF e CNPJ**.
Trabalho da disciplina de DevOps: repositório no GitHub, pipeline no GitHub Actions e fluxo GitFlow.

## Como funciona

CPF e CNPJ terminam em dois **dígitos verificadores**, calculados com uma soma ponderada módulo 11
dos dígitos anteriores. O código implementa esse cálculo uma única vez e só troca os pesos:

| Documento | Pesos do 1º dígito | Pesos do 2º dígito |
|-----------|--------------------|--------------------|
| CPF  | 10 → 2 | 11 → 2 |
| CNPJ | 5,4,3,2,9,8,7,6,5,4,3,2 | 6,5,4,3,2,9,8,7,6,5,4,3,2 |

## Uso

```bash
pip install -e ".[dev]"

validabr checa 529.982.247-25 11.222.333/0001-81 123
# ✓ 529.982.247-25: CPF válido
# ✓ 11.222.333/0001-81: CNPJ válido
# ✗ 123: inválido

validabr gera cpf -q 3     # gera 3 CPFs válidos fictícios
validabr gera cnpj
```

Como biblioteca:

```python
from validabr import valida_cpf, formata_cnpj, identifica

valida_cpf("529.982.247-25")  # True
formata_cnpj("11222333000181")  # '11.222.333/0001-81'
identifica("11.222.333/0001-81")  # 'CNPJ'
```

## Pipeline (GitHub Actions)

Arquivo: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

```
lint ──► testes (3.10, 3.11, 3.12, 3.13) ──► build ──► DAST (OWASP ZAP) ──► release (só em tag v*)
SAST (Semgrep) ──────────────────────────────┘
```

| Job | O que faz |
|-----|-----------|
| **lint** | `ruff check` e `ruff format --check` |
| **sast** | Semgrep no código e no workflow; o gate reprova achados de severidade média ou maior |
| **test** | `pytest` com cobertura mínima de 90%, em matriz de 4 versões do Python, e smoke test da CLI |
| **build** | gera o pacote (`.whl` e `.tar.gz`) e guarda como artefato; só roda se testes **e** SAST passarem |
| **dast** | instala o pacote do build, sobe a API e roda o OWASP ZAP contra ela; o gate reprova alertas de risco médio ou maior |
| **release** | quando uma tag `v*` é enviada, cria a Release no GitHub com o pacote anexado; só roda se o DAST passar |

Dispara em push para `main`, `develop`, `feature/**`, `release/**`, `hotfix/**`, em pull requests
para `main`/`develop` e manualmente (`workflow_dispatch`).

## Segurança no pipeline (SAST e DAST)

### SAST: Semgrep

Analisa o código-fonte **sem executá-lo**. O job `sast` roda:

- pacotes do registro do Semgrep: `p/python`, `p/secrets` e `p/github-actions` (este último
  verifica o próprio `ci.yml`, por exemplo actions sem SHA fixo);
- regras próprias em [`.semgrep/regras-valida-br.yml`](.semgrep/regras-valida-br.yml):
  `eval`/`exec`, `subprocess` com `shell=True`, segredo escrito no código, servidor escutando em
  `0.0.0.0` e `pickle` com dados externos.

O resultado vai para o artefato `relatorio-sast` (JSON e SARIF) e para a aba **Security** do GitHub.

### DAST: OWASP ZAP

Ataca a aplicação **rodando**. Como o valida-br era só biblioteca/CLI, ele ganhou uma API HTTP
mínima (só biblioteca padrão) para servir de alvo:

```bash
validabr serve --porta 8000
curl "http://127.0.0.1:8000/api/valida?doc=529.982.247-25"
# {"documento": "52998224725", "tipo": "CPF", "valido": true, "formatado": "529.982.247-25"}
curl "http://127.0.0.1:8000/api/gera/cnpj?quantidade=2"
```

O job `dast` instala o `.whl` gerado no build, sobe a API e roda o `zap-baseline.py` (spider +
regras passivas) com a imagem oficial `ghcr.io/zaproxy/zaproxy:stable`. A API envia em todas as
respostas os cabeçalhos que o ZAP cobra (CSP, `X-Frame-Options`, `X-Content-Type-Options` etc.),
não revela a versão do Python no cabeçalho `Server` e limita o tamanho das entradas.

O relatório (HTML, JSON e Markdown) vai para o artefato `relatorio-dast`.

### Validações (gates)

As duas ferramentas passam pelo mesmo script, [`scripts/gate_seguranca.py`](scripts/gate_seguranca.py),
que lê o relatório, escreve uma tabela no resumo da execução e **reprova o job** quando:

| Gate | Reprova se |
|------|-----------|
| SAST | houver achado do Semgrep com severidade `WARNING` (média) ou `ERROR` (alta) |
| DAST | houver alerta do ZAP com risco médio ou alto, **ou** um alerta de qualquer risco cuja regra esteja marcada `FAIL` em [`.zap/rules.tsv`](.zap/rules.tsv) (ex.: cabeçalho `Server` revelando versão) |

Regras marcadas `IGNORE` no `rules.tsv` são falsos positivos aceitos e não contam.

Para rodar o gate localmente:

```bash
pip install semgrep
semgrep scan --config p/python --config p/secrets --config p/github-actions --config .semgrep/ \
  --json-output=semgrep.json
python scripts/gate_seguranca.py semgrep semgrep.json --falha-em media
```

## GitFlow

| Branch | Papel |
|--------|-------|
| `main` | código em produção; cada merge vira uma tag de versão |
| `develop` | integração das funcionalidades |
| `feature/*` | uma funcionalidade nova, sai de `develop` e volta para `develop` |
| `release/*` | prepara uma versão, sai de `develop` e vai para `main` **e** `develop` |
| `hotfix/*` | correção urgente, sai de `main` e vai para `main` **e** `develop` |

O roteiro para demonstrar o fluxo ao vivo está em [`APRESENTACAO.md`](APRESENTACAO.md).
