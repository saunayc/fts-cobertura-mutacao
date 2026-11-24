#!/usr/bin/env python3
"""Extrai os trechos não cobertos pela suíte funcional (QP2).

Unidade de análise ("trecho"):
  * L — bloco máximo de comandos consecutivos não executados dentro da mesma
        função/método (ou do nível de módulo/classe);
  * D — desvio não exercitado cuja origem e cujo destino foram executados
        por outros caminhos (ou cujo destino é a saída da função): é a
        cobertura parcial de desvio "pura". Desvios que levam a um comando não
        executado já estão representados pelo trecho L correspondente.

Entrada:  resultados/inicial/<lib>/coverage.json
Saída:    classificacao/trechos_<lib>.csv  (uma linha por trecho, com o código)

Uso: python scripts/extract_uncovered.py [tinydb arrow humanize]
"""
from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = json.loads((ROOT / "subjects.lock.json").read_text())
CAMPOS = ["id", "biblioteca", "modulo", "escopo", "tipo", "linhas", "n_comandos", "codigo"]


def scopes(tree: ast.AST) -> list[tuple[int, int, str]]:
    out = []

    def visit(node, prefix=""):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{ch.name}"
                out.append((ch.lineno, ch.end_lineno, name))
                visit(ch, name + ".")
            else:
                visit(ch, prefix)

    visit(tree)
    return out


def scope_of(line: int, sc) -> str:
    best = "<módulo>"
    size = 10**9
    for a, b, name in sc:
        if a <= line <= b and b - a < size:
            best, size = name, b - a
    return best


def extract(lib: str) -> list[dict]:
    cov = json.loads((ROOT / "resultados" / "inicial" / lib / "coverage.json").read_text())
    ws = ROOT / "work" / lib
    rows = []
    for fname, f in sorted(cov["files"].items()):
        src = (ws / fname).read_text().splitlines()
        tree = ast.parse("\n".join(src))
        sc = scopes(tree)
        stmts = sorted(set(f["executed_lines"]) | set(f["missing_lines"]) | set(f.get("excluded_lines", [])))
        missing = set(f["missing_lines"])
        executed = set(f["executed_lines"])
        mod = fname.removeprefix("src/")

        # Blocos de comandos não executados
        bloco: list[int] = []

        def fecha():
            if bloco:
                a, b = bloco[0], bloco[-1]
                rows.append({
                    "biblioteca": lib, "modulo": mod, "escopo": scope_of(a, sc), "tipo": "L",
                    "linhas": f"{a}-{b}" if a != b else str(a), "n_comandos": len(bloco),
                    "codigo": "\n".join(src[a - 1:b]),
                })
                bloco.clear()

        for ln in stmts:
            if ln in missing:
                if bloco and scope_of(ln, sc) != scope_of(bloco[0], sc):
                    fecha()
                bloco.append(ln)
            else:
                fecha()
        fecha()

        # Desvios parciais (origem executada)
        for orig, dest in f.get("missing_branches", []):
            if orig not in executed or dest in missing:
                continue   # já representado por um trecho L
            destino = "saída da função" if dest < 0 else f"linha {dest}"
            rows.append({
                "biblioteca": lib, "modulo": mod, "escopo": scope_of(orig, sc), "tipo": "D",
                "linhas": f"{orig}->{dest}", "n_comandos": 0,
                "codigo": f"{src[orig - 1].rstrip()}    # desvio não exercitado -> {destino}",
            })

    prefix = {"tinydb": "TDB", "arrow": "ARW", "humanize": "HUM"}[lib]
    for i, r in enumerate(rows, 1):
        r["id"] = f"{prefix}-T{i:03d}"
    return rows


def main(libs):
    out = ROOT / "classificacao"
    out.mkdir(exist_ok=True)
    for lib in libs:
        rows = extract(lib)
        with open(out / f"trechos_{lib}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(rows)
        nl = sum(r["tipo"] == "L" for r in rows)
        print(f"{lib}: {len(rows)} trechos ({nl} blocos de linhas, {len(rows) - nl} desvios parciais)")


if __name__ == "__main__":
    main(sys.argv[1:] or list(LOCK))
