# Roteiro da apresentação

Duração estimada: 8–10 minutos. Tudo pode ser feito com `git` puro (abaixo); se a extensão
`git-flow` estiver instalada, o comando equivalente aparece em comentário.

## 0. Preparação (antes da aula)

```bash
git clone https://github.com/bernardobbl/valida-br.git
cd valida-br
git checkout develop
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                                              # deve passar com 100% de cobertura
```

Deixe aberta a aba **Actions** do repositório:
https://github.com/bernardobbl/valida-br/actions

## 1. Mostrar o projeto e a pipeline (2 min)

1. Rodar a CLI:
   ```bash
   validabr checa 529.982.247-25 11.222.333/0001-81 123
   validabr gera cpf -q 3
   ```
2. Abrir `.github/workflows/ci.yml` e explicar os 4 jobs:
   `lint → testes (matriz 3.10–3.13) → build → release (só em tag)`.
3. Na aba Actions, mostrar uma execução verde e o grafo dos jobs.
4. Mostrar a Release `v1.0.0` com o pacote anexado (gerada automaticamente pela pipeline).

## 2. GitFlow ao vivo: nova feature (3 min)

Funcionalidade: um subcomando `formata`, que coloca a máscara em CPF/CNPJ.

```bash
git checkout develop
git pull
git checkout -b feature/comando-formata          # git flow feature start comando-formata
```

Em `src/validabr/cli.py`, logo depois do bloco do subcomando `gera`, adicione:

```python
    formata = sub.add_parser("formata", help="coloca a máscara no documento")
    formata.add_argument("documento")
```

E, logo depois de `args = parser.parse_args(argv)`:

```python
    if args.comando == "formata":
        tipo = identifica(args.documento)
        if tipo == "inválido":
            print(f"{VERMELHO}✗{FIM} {args.documento}: inválido")
            return 1
        print(formata_cpf(args.documento) if tipo == "CPF" else formata_cnpj(args.documento))
        return 0
```

Ajuste o import no topo:

```python
from .documentos import formata_cnpj, formata_cpf, gera_cnpj, gera_cpf, identifica
```

Em `tests/test_cli.py`, adicione o teste:

```python
def test_formata(capsys):
    assert main(["formata", "52998224725"]) == 0
    assert "529.982.247-25" in capsys.readouterr().out
    assert main(["formata", "11222333000181"]) == 0
    assert "11.222.333/0001-81" in capsys.readouterr().out
    assert main(["formata", "999"]) == 1
```

```bash
pytest
git add .
git commit -m "feat: subcomando formata"
git push -u origin feature/comando-formata
```

👉 Mostrar na aba Actions que a pipeline **disparou sozinha** para a branch da feature.

Abrir um **Pull Request** `feature/comando-formata → develop` no GitHub, mostrar os checks rodando
no PR e fazer o merge. Ou, pelo terminal:

```bash
git checkout develop
git merge --no-ff feature/comando-formata        # git flow feature finish comando-formata
git push origin develop
```

## 3. GitFlow ao vivo: release (2 min)

```bash
git checkout -b release/1.1.0 develop            # git flow release start 1.1.0
```

Troque a versão de `1.0.0` para `1.1.0` em `pyproject.toml` e em `src/validabr/__init__.py`,
e adicione no topo do `CHANGELOG.md`:

```markdown
## [1.1.0]
- Subcomando `validabr formata`.
```

```bash
git commit -am "chore: versão 1.1.0"
git checkout main
git merge --no-ff release/1.1.0                  # git flow release finish 1.1.0
git tag -a v1.1.0 -m "v1.1.0"
git checkout develop
git merge --no-ff release/1.1.0
git branch -d release/1.1.0
git push origin main develop --tags
```

👉 Mostrar na aba Actions que a tag `v1.1.0` rodou o job **release** e, na página de Releases,
a versão nova com o `.whl` anexado.

## 4. (Se sobrar tempo) Hotfix

```bash
git checkout -b hotfix/1.1.1 main                # git flow hotfix start 1.1.1
# corrige algo, troca a versão para 1.1.1, commit
git checkout main && git merge --no-ff hotfix/1.1.1 && git tag -a v1.1.1 -m "v1.1.1"
git checkout develop && git merge --no-ff hotfix/1.1.1
git branch -d hotfix/1.1.1
git push origin main develop --tags
```

## Perguntas prováveis

- **Por que `--no-ff`?** Para manter o commit de merge e deixar visível no histórico que aquilo
  foi uma feature/release.
- **Por que a release volta para `develop`?** Ajustes feitos na branch de release (versão,
  changelog, correções) não podem se perder na próxima versão.
- **O que a pipeline impede?** Código com erro de lint, teste quebrado ou cobertura abaixo de 90%
  fica vermelho e não deve ser mergeado.
- **Por que matriz de versões?** Garante que a biblioteca funciona do Python 3.10 ao 3.13.
