#!/usr/bin/env python3
"""Concordância entre avaliadores (QP2): Kappa de Cohen + matriz de confusão.

Uso:
    python scripts/kappa.py classificacao/avaliador_A_<lib>.csv classificacao/avaliador_B_<lib>.csv
    python scripts/kappa.py --todas     # junta as três bibliotecas

Também grava classificacao/divergencias_<rotulo>.csv com os trechos em que os
avaliadores discordam, para a reunião de consenso.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATS = ["EXC", "VAL", "CFG", "LIM", "MORTO", "OUTRO"]


def carregar(path: Path) -> dict[str, str]:
    out = {}
    for r in csv.DictReader(open(path)):
        c = r["categoria"].strip().upper()
        if c:
            if c not in CATS:
                raise SystemExit(f"{path}: categoria inválida {c!r} em {r['id']}")
            out[r["id"]] = c
    return out


def cohen_kappa(a: list[str], b: list[str]) -> tuple[float, float, float]:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[c] * cb[c] for c in CATS) / n**2
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return k, po, pe


def interpretar(k: float) -> str:
    for lim, txt in ((0.0, "pobre"), (0.20, "leve"), (0.40, "razoável"), (0.60, "moderada"),
                     (0.80, "substancial"), (1.01, "quase perfeita")):
        if k <= lim:
            return txt
    return "quase perfeita"


def relatorio(pares: list[tuple[Path, Path]], rotulo: str) -> None:
    ids, a, b = [], [], []
    for pa, pb in pares:
        A, B = carregar(pa), carregar(pb)
        comuns = sorted(set(A) & set(B))
        if len(comuns) < len(A):
            print(f"aviso: {pb.name} classificou {len(comuns)} de {len(A)} trechos")
        ids += comuns
        a += [A[i] for i in comuns]
        b += [B[i] for i in comuns]
    if not ids:
        raise SystemExit("nenhum trecho classificado por ambos os avaliadores")
    k, po, pe = cohen_kappa(a, b)
    print(f"[{rotulo}] n={len(ids)}  concordância observada={po:.3f}  esperada={pe:.3f}  "
          f"kappa={k:.3f} ({interpretar(k)}, Landis & Koch)")
    print("matriz (linhas = A, colunas = B):")
    print("        " + " ".join(f"{c:>6}" for c in CATS))
    m = Counter(zip(a, b))
    for ca in CATS:
        print(f"{ca:>6}  " + " ".join(f"{m[(ca, cb)]:>6}" for cb in CATS))
    out = ROOT / "classificacao" / f"divergencias_{rotulo}.csv"
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "A", "B", "consenso"])
        for i, x, y in zip(ids, a, b):
            if x != y:
                w.writerow([i, x, y, ""])
    print(f"divergências: {out.relative_to(ROOT)}")


def main(argv: list[str]) -> None:
    if argv == ["--todas"]:
        cls = ROOT / "classificacao"
        pares = []
        for l in ("tinydb", "arrow", "humanize"):
            for nome in (f"avaliador_B_{l}.csv", f"avaliador_B_IA_{l}.csv"):
                if (cls / nome).exists():
                    pares.append((cls / f"avaliador_A_{l}.csv", cls / nome))
                    break
        relatorio(pares, "todas")
    elif len(argv) == 2:
        pa, pb = map(Path, argv)
        relatorio([(pa, pb)], pa.stem.split("_")[-1])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
