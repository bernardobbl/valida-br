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

valida_cpf("529.982.247-25")      # True
formata_cnpj("11222333000181")    # '11.222.333/0001-81'
identifica("11.222.333/0001-81")  # 'CNPJ'
```

## Pipeline (GitHub Actions)

Arquivo: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

```
lint ──► testes (3.10, 3.11, 3.12, 3.13) ──► build ──► release (só em tag v*)
```

| Job | O que faz |
|-----|-----------|
| **lint** | `ruff check` e `ruff format --check` |
| **test** | `pytest` com cobertura mínima de 90%, em matriz de 4 versões do Python, e smoke test da CLI |
| **build** | gera o pacote (`.whl` e `.tar.gz`) e guarda como artefato |
| **release** | quando uma tag `v*` é enviada, cria a Release no GitHub com o pacote anexado |

Dispara em push para `main`, `develop`, `feature/**`, `release/**`, `hotfix/**`, em pull requests
para `main`/`develop` e manualmente (`workflow_dispatch`).

## GitFlow

| Branch | Papel |
|--------|-------|
| `main` | código em produção; cada merge vira uma tag de versão |
| `develop` | integração das funcionalidades |
| `feature/*` | uma funcionalidade nova, sai de `develop` e volta para `develop` |
| `release/*` | prepara uma versão, sai de `develop` e vai para `main` **e** `develop` |
| `hotfix/*` | correção urgente, sai de `main` e vai para `main` **e** `develop` |

O roteiro para demonstrar o fluxo ao vivo está em [`APRESENTACAO.md`](APRESENTACAO.md).
