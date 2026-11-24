#!/usr/bin/env python3
"""Localiza a linha alterada por cada mutante e cruza com a cobertura.

O mutmut 3 grava cada mutante como uma cópia da função (``x_f__mutmut_N``) ao
lado da cópia original (``x_f__mutmut_orig``) em ``work/<lib>/mutants/``. Este
script compara cada cópia mutada com a original para achar a primeira linha
alterada e converte essa linha para o arquivo-fonte original. Depois cruza
com a cobertura de cada fase.

Pergunta respondida: os mutantes que sobrevivem estão em linhas que a suíte
executa (falta de verificação / oráculo fraco) ou em linhas que ela nem executa
(falta de cobertura)?

Pré-requisito: ``work/<lib>/mutants/`` gerado por ``scripts/measure.py``.
Saídas: resultados/<fase>/<lib>/mutantes_linhas.csv e resultados/qp_mutantes_sobreviventes.csv

Uso: python scripts/mutant_lines.py
"""
from __future__ import annotations

import ast
import csv
import difflib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBS = ["tinydb", "arrow", "humanize"]
NOME = re.compile(r"^(?P<base>.+)__mutmut_(?P<n>orig|\d+)$")


def funcoes(path: Path) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(path.read_text())
    return {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def localizar_original(base: str, src_tree: ast.AST):
    """base: 'x_func' (função de módulo) ou 'xǁClasseǁmetodo'."""
    # Com @typing.overload há várias definições com o mesmo nome: a implementação é a última.
    achado = None
    if base.startswith("xǁ"):
        _, classe, metodo = base.split("ǁ")
        for n in ast.walk(src_tree):
            if isinstance(n, ast.ClassDef) and n.name == classe:
                for m in n.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == metodo:
                        achado = m
    else:
        nome = base[2:]
        for n in src_tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nome:
                achado = n
    return achado


def mapear(lib: str) -> dict[str, int]:
    ws = ROOT / "work" / lib
    out: dict[str, int] = {}
    for mfile in sorted((ws / "mutants" / "src").rglob("*.py")):
        rel = mfile.relative_to(ws / "mutants")
        src_path = ws / rel
        if not src_path.exists():
            continue
        m_lines = mfile.read_text().splitlines()
        src_text = src_path.read_text()
        src_tree = ast.parse(src_text)
        fn = funcoes(mfile)
        modulo = ".".join(rel.with_suffix("").parts[1:])
        for nome, node in fn.items():
            g = NOME.match(nome)
            if not g or g["n"] == "orig":
                continue
            orig = fn.get(f"{g['base']}__mutmut_orig")
            original = localizar_original(g["base"], src_tree)
            if orig is None or original is None:
                continue
            a = m_lines[orig.lineno - 1: orig.end_lineno]
            b = m_lines[node.lineno - 1: node.end_lineno]
            sm = difflib.SequenceMatcher(a=a[1:], b=b[1:], autojunk=False)   # ignora a linha do def (nome difere)
            ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
            if not ops:
                continue
            offset = ops[0][1] + 1          # posição na cópia original, contando o def como 0
            # A cópia _orig é idêntica à função original linha a linha (exceto o nome).
            linha = original.lineno + offset
            out[f"{modulo}.{nome}"] = linha
    return out


def mapa_de_comandos(path: Path) -> dict[int, int | str]:
    """linha -> linha inicial do comando mais interno que a contém, ou 'assinatura'."""
    tree = ast.parse(path.read_text())
    melhor: dict[int, tuple[int, int | str]] = {}
    for n in ast.walk(tree):
        if not isinstance(n, ast.stmt):
            continue
        fim = n.end_lineno
        alvo: int | str = n.lineno
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            fim = n.body[0].lineno - 1          # só o cabeçalho
            alvo = "assinatura" if not isinstance(n, ast.ClassDef) else n.lineno
        elif hasattr(n, "body") and isinstance(n.body, list) and n.body:
            fim = n.body[0].lineno - 1          # cabeçalho de if/for/while/with/try
        for ln in range(n.lineno, fim + 1):
            tam = fim - n.lineno
            if ln not in melhor or tam < melhor[ln][0]:
                melhor[ln] = (tam, alvo)
    return {ln: v[1] for ln, v in melhor.items()}


def main():
    resumo = []
    for lib in LIBS:
        mapa = mapear(lib)
        for fase in ("inicial", "final"):
            d = ROOT / "resultados" / fase / lib
            cov = json.loads((d / "coverage.json").read_text())
            rows = []
            cmd_cache: dict[str, dict] = {}
            for r in csv.DictReader(open(d / "mutantes.csv")):
                linha = mapa.get(r["mutante"])
                f = cov["files"].get("src/" + r["modulo"], {})
                if r["modulo"] not in cmd_cache:
                    cmd_cache[r["modulo"]] = mapa_de_comandos(ROOT / "work" / lib / "src" / r["modulo"])
                cmd = cmd_cache[r["modulo"]].get(linha) if linha else None
                if linha is None or cmd is None:
                    situ = "não identificada"
                elif cmd == "assinatura":
                    situ = "valor padrão na assinatura"
                elif cmd in set(f.get("executed_lines", [])):
                    situ = "comando executado"
                elif cmd in set(f.get("missing_lines", [])):
                    situ = "comando não executado"
                else:
                    situ = "não identificada"
                rows.append({**r, "linha": linha or "", "cobertura_da_linha": situ})
            with open(d / "mutantes_linhas.csv", "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=["modulo", "mutante", "status", "linha", "cobertura_da_linha"])
                w.writeheader()
                w.writerows(rows)
            sobrev = [r for r in rows if r["status"] in ("survived", "no tests")]
            c = Counter(r["cobertura_da_linha"] for r in sobrev)
            resumo.append({"biblioteca": lib, "fase": fase, "mutantes": len(rows), "sobreviventes": len(sobrev),
                           "em_comando_executado": c["comando executado"],
                           "em_comando_nao_executado": c["comando não executado"],
                           "em_valor_padrao_assinatura": c["valor padrão na assinatura"],
                           "nao_identificada": c["não identificada"]})
            print(resumo[-1])
    with open(ROOT / "resultados" / "qp_mutantes_sobreviventes.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(resumo[0]))
        w.writeheader()
        w.writerows(resumo)


if __name__ == "__main__":
    main()
