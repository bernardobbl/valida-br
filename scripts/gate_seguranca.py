"""Gate de segurança do pipeline: lê o relatório do Semgrep (SAST) ou do ZAP (DAST)
e faz o job falhar se houver achado com severidade igual ou acima do limite.

Uso:
    python scripts/gate_seguranca.py semgrep semgrep.json --falha-em media
    python scripts/gate_seguranca.py zap zap-report.json --falha-em media --regras .zap/rules.tsv

Níveis (do menor para o maior): info, baixa, media, alta.
No ZAP, o arquivo --regras (o mesmo rules.tsv passado ao zap-baseline com -c) permite
marcar regras como FAIL (bloqueiam mesmo com risco baixo) ou IGNORE (falso positivo aceito).
Se a variável GITHUB_STEP_SUMMARY existir (GitHub Actions), escreve uma tabela
com os achados no resumo da execução.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

NIVEIS = {"info": 0, "baixa": 1, "media": 2, "alta": 3}
NOMES = {v: k for k, v in NIVEIS.items()}

# Semgrep usa INFO/WARNING/ERROR (e, em regras novas, LOW/MEDIUM/HIGH/CRITICAL).
SEVERIDADE_SEMGREP = {
    "INFO": 0,
    "LOW": 1,
    "WARNING": 2,
    "MEDIUM": 2,
    "ERROR": 3,
    "HIGH": 3,
    "CRITICAL": 3,
}


def achados_semgrep(relatorio: dict) -> list[dict]:
    achados = []
    for r in relatorio.get("results", []):
        sev = r.get("extra", {}).get("severity", "INFO").upper()
        achados.append(
            {
                "nivel": SEVERIDADE_SEMGREP.get(sev, 0),
                "regra": r.get("check_id", "?"),
                "onde": f"{r.get('path', '?')}:{r.get('start', {}).get('line', '?')}",
                "descricao": r.get("extra", {}).get("message", "").strip().splitlines()[0][:120],
            }
        )
    return achados


def le_regras_zap(caminho: Path | None) -> dict[str, str]:
    """Lê o rules.tsv do ZAP: <id>\t<IGNORE|INFO|WARN|FAIL>\t(comentário)."""
    if caminho is None:
        return {}
    regras = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        partes = linha.split("\t")
        if len(partes) >= 2 and not linha.startswith("#"):
            regras[partes[0].strip()] = partes[1].strip().upper()
    return regras


def achados_zap(relatorio: dict, regras: dict[str, str]) -> list[dict]:
    achados = []
    for site in relatorio.get("site", []):
        for alerta in site.get("alerts", []):
            acao = regras.get(str(alerta.get("pluginid")))
            if acao == "IGNORE":
                continue
            instancias = alerta.get("instances", [])
            nivel = int(alerta.get("riskcode", 0))
            achados.append(
                {
                    "nivel": nivel,
                    "forcado": acao == "FAIL",
                    "regra": f"{alerta.get('pluginid', '?')} {alerta.get('name', '?')}",
                    "onde": _onde_zap(instancias, site.get("@name", "?")),
                    "descricao": alerta.get("solution", "")
                    .replace("<p>", "")
                    .replace("</p>", " ")[:120],
                }
            )
    return achados


def _onde_zap(instancias: list[dict], site: str) -> str:
    exemplo = instancias[0].get("uri", site) if instancias else site
    return f"{len(instancias)} URL(s), ex.: {exemplo}"


def bloqueia(achado: dict, limite: int) -> bool:
    return achado["nivel"] >= limite or achado.get("forcado", False)


def resumo_markdown(ferramenta: str, achados: list[dict], limite: int, reprovados: int) -> str:
    status = "❌ REPROVADO" if reprovados else "✅ APROVADO"
    regra = f"falha com severidade **{NOMES[limite]}** ou maior (ou regra marcada FAIL)"
    contagem = f"Achados: {len(achados)} (bloqueantes: {reprovados})."
    linhas = [
        f"### Gate de segurança: {ferramenta.upper()} — {status}",
        "",
        f"{regra}. {contagem}",
        "",
    ]
    if achados:
        linhas += ["| Severidade | Regra | Onde |", "|---|---|---|"]
        for a in sorted(achados, key=lambda a: -a["nivel"]):
            marca = " ⛔" if bloqueia(a, limite) else ""
            linhas.append(f"| {NOMES[a['nivel']]}{marca} | {a['regra']} | {a['onde']} |")
    return "\n".join(linhas) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ferramenta", choices=["semgrep", "zap"])
    parser.add_argument("relatorio", type=Path)
    parser.add_argument("--falha-em", choices=list(NIVEIS), default="media")
    parser.add_argument("--regras", type=Path, help="rules.tsv do ZAP (FAIL/IGNORE por regra)")
    args = parser.parse_args(argv)

    if not args.relatorio.exists():
        print(f"::error::Relatório {args.relatorio} não encontrado — a varredura não rodou.")
        return 2

    relatorio = json.loads(args.relatorio.read_text(encoding="utf-8"))
    if args.ferramenta == "semgrep":
        achados = achados_semgrep(relatorio)
    else:
        achados = achados_zap(relatorio, le_regras_zap(args.regras))
    limite = NIVEIS[args.falha_em]
    bloqueantes = [a for a in achados if bloqueia(a, limite)]

    for a in sorted(achados, key=lambda a: -a["nivel"]):
        tipo = "error" if bloqueia(a, limite) else "warning"
        print(f"::{tipo}::[{NOMES[a['nivel']]}] {a['regra']} em {a['onde']} — {a['descricao']}")

    resumo = resumo_markdown(args.ferramenta, achados, limite, len(bloqueantes))
    print(resumo)
    if destino := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(destino, "a", encoding="utf-8") as f:
            f.write(resumo)

    if bloqueantes:
        print(f"{len(bloqueantes)} achado(s) bloqueante(s). Pipeline barrado.")
        return 1
    print(f"Nenhum achado com severidade >= {args.falha_em}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
