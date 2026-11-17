# Changelog

## [Não lançado]
- Secure pipeline: job **SAST** com Semgrep (regras do registro e regras próprias em `.semgrep/`).
- Secure pipeline: job **DAST** com OWASP ZAP baseline contra a aplicação rodando.
- Gates de segurança (`scripts/gate_seguranca.py`): SAST e DAST reprovam achados de severidade
  média ou maior; o DAST também reprova regras marcadas `FAIL` em `.zap/rules.tsv`.
- API HTTP `validabr serve` (`/api/valida`, `/api/gera/{cpf,cnpj}`, `/health`) com cabeçalhos
  de segurança, usada como alvo do DAST.
- Actions do workflow fixadas pelo SHA do commit.

## [1.0.0]
- Validação, formatação e geração de CPF e CNPJ.
- Linha de comando `validabr` com os subcomandos `checa` e `gera`.
- Pipeline no GitHub Actions: lint, testes em matriz (Python 3.10–3.13), build e release por tag.
