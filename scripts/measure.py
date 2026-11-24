#!/usr/bin/env python3
"""Mede cobertura (comandos, desvios, blocos except) e escore de mutação.

Uso:
    python scripts/measure.py <lib> <fase> [--sem-mutacao] [--jobs N]

``fase``:
    inicial -> apenas a suíte funcional (QP1)
    final   -> suíte funcional + suíte estrutural (QP3)

Saídas em ``resultados/<fase>/<lib>/``:
    coverage.json       relatório bruto do Coverage.py (--branch)
    modulos.csv         métricas consolidadas por módulo
    projeto.json        métricas consolidadas do projeto
    mutantes.csv        status de cada mutante (mutmut)
    pytest.txt          saída do pytest
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
LOCK = json.loads((ROOT / "subjects.lock.json").read_text())

STATUS = {1: "killed", 3: "killed", 0: "survived", 5: "no tests", 33: "no tests", 34: "skipped",
          35: "suspicious", 36: "timeout", 37: "caught by type check", -24: "timeout", 24: "timeout",
          152: "timeout", 255: "timeout", -11: "segfault", -9: "segfault", None: "not checked"}

SELECAO = {"inicial": ["tests/functional"], "final": ["tests/functional", "tests/structural"]}


def write_pyproject(ws: Path, info: dict, fase: str) -> None:
    pkg = info["package"]
    omit = [f"src/{pkg}/{o}" for o in info["omit"]]
    sel = SELECAO[fase]
    content = f"""# Gerado por scripts/measure.py (fase {fase}) — não editar
[tool.pytest.ini_options]
pythonpath = ["src"]
addopts = "-p no:cacheprovider"

[tool.mutmut]
source_paths = ["src/{pkg}"]
pytest_add_cli_args_test_selection = {json.dumps(sel)}
do_not_mutate = {json.dumps(omit)}
also_copy = ["tests"]
"""
    (ws / "pyproject.toml").write_text(content)


def run(cmd, cwd, log=None, check=True, env=None):
    print("+", " ".join(map(str, cmd)), flush=True)
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, env=env)
    if log is not None:
        log.write(r.stdout + r.stderr)
    if check and r.returncode not in (0,):
        sys.stderr.write(r.stdout[-4000:] + r.stderr[-4000:])
        raise SystemExit(f"falhou: {' '.join(map(str, cmd))}")
    return r


# ------------------------------------------------------------------ cobertura
def except_blocks(path: Path) -> list[tuple[int, int]]:
    """Retorna (linha do except, primeira linha executável do corpo)."""
    tree = ast.parse(path.read_text())
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            out.append((node.lineno, node.body[0].lineno))
    return sorted(out)


def coverage_metrics(ws: Path, info: dict, outdir: Path) -> list[dict]:
    data = json.loads((outdir / "coverage.json").read_text())
    rows = []
    for fname, f in sorted(data["files"].items()):
        s = f["summary"]
        executed = set(f["executed_lines"])
        excs = except_blocks(ws / fname)
        exc_cov = sum(1 for _, body in excs if body in executed)
        rows.append({
            "modulo": fname.removeprefix("src/"),
            "comandos_total": s["num_statements"],
            "comandos_cobertos": s["covered_lines"],
            "cobertura_comandos": pct(s["covered_lines"], s["num_statements"]),
            "desvios_total": s["num_branches"],
            "desvios_cobertos": s["covered_branches"],
            "cobertura_desvios": pct(s["covered_branches"], s["num_branches"]),
            "except_total": len(excs),
            "except_cobertos": exc_cov,
            "cobertura_except": pct(exc_cov, len(excs)),
            "linhas_nao_cobertas": f["missing_lines"],
            "desvios_nao_cobertos": f["missing_branches"],
        })
    return rows


def pct(a, b):
    return round(100.0 * a / b, 2) if b else None


# ------------------------------------------------------------------ mutação
def mutation_metrics(ws: Path, outdir: Path, jobs: int) -> dict[str, Counter]:
    shutil.rmtree(ws / "mutants", ignore_errors=True)
    r = run([str(ws / ".venv/bin/mutmut"), "run", "--max-children", str(jobs)], cwd=ws, check=False)
    linhas = [ln.rsplit("\r", 1)[-1] for ln in (r.stdout + r.stderr).splitlines()]
    linhas = [ln for ln in linhas if ln.strip() and not ln.lstrip().startswith(tuple("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"))]
    (outdir / "mutmut.log").write_text("\n".join(linhas[-40:]) + "\n")
    per_mod: dict[str, Counter] = defaultdict(Counter)
    rows = []
    for meta in sorted((ws / "mutants").rglob("*.py.meta")):
        rel = meta.relative_to(ws / "mutants").as_posix().removesuffix(".meta").removeprefix("src/")
        m = json.loads(meta.read_text())
        for key, code in sorted(m.get("exit_code_by_key", {}).items()):
            st = STATUS.get(code, "suspicious")
            per_mod[rel][st] += 1
            rows.append({"modulo": rel, "mutante": key, "status": st})
    with open(outdir / "mutantes.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["modulo", "mutante", "status"])
        w.writeheader()
        w.writerows(rows)
    return per_mod


def score(c: Counter) -> dict:
    total = sum(c.values())
    mortos = c["killed"] + c["timeout"] + c["segfault"]
    considerados = total - c["skipped"] - c["caught by type check"]
    return {
        "mutantes_total": total,
        "mutantes_mortos": mortos,
        "mutantes_sobreviventes": c["survived"],
        "mutantes_sem_teste": c["no tests"],
        "mutantes_timeout": c["timeout"],
        "mutantes_suspeitos": c["suspicious"],
        "escore_mutacao": pct(mortos, considerados),
    }


# ------------------------------------------------------------------ principal
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lib", choices=list(LOCK))
    ap.add_argument("fase", choices=list(SELECAO))
    ap.add_argument("--sem-mutacao", action="store_true")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()

    info = LOCK[a.lib]
    ws = WORK / a.lib
    if not (ws / ".venv").exists():
        raise SystemExit("rode antes: python scripts/prepare.py " + a.lib)
    from prepare import sync_tests  # noqa: E402  (mesmo diretório)
    sync_tests(a.lib)
    write_pyproject(ws, info, a.fase)
    outdir = ROOT / "resultados" / a.fase / a.lib
    outdir.mkdir(parents=True, exist_ok=True)
    py = str(ws / ".venv/bin/python")
    env = {**os.environ, "PYTHONHASHSEED": "0"}

    pkg = info["package"]
    omit = ",".join(f"src/{pkg}/{o}" for o in info["omit"]) or ""
    (ws / ".coverage").unlink(missing_ok=True)
    cov_run = [py, "-m", "coverage", "run", "--branch", f"--source=src/{pkg}"]
    if omit:
        cov_run.append(f"--omit={omit}")
    with open(outdir / "pytest.txt", "w") as log:
        r = run(cov_run + ["-m", "pytest", "-q", "-rxX", *SELECAO[a.fase]], cwd=ws, log=log, check=False, env=env)
    if r.returncode != 0:
        raise SystemExit(f"suíte falhou (código {r.returncode}); veja {outdir / 'pytest.txt'}")
    run([py, "-m", "coverage", "json", "-o", str(outdir / "coverage.json")], cwd=ws)

    rows = coverage_metrics(ws, info, outdir)
    mut = {} if a.sem_mutacao else mutation_metrics(ws, outdir, a.jobs)

    total_mut = Counter()
    for r_ in rows:
        c = mut.get(r_["modulo"], Counter())
        total_mut.update(c)
        r_.update(score(c) if mut else {})

    campos = [k for k in rows[0] if k not in ("linhas_nao_cobertas", "desvios_nao_cobertos")]
    with open(outdir / "modulos.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    def soma(k):
        return sum(r_[k] for r_ in rows)

    proj = {
        "biblioteca": a.lib, "fase": a.fase, "commit": info["commit"],
        "testes": SELECAO[a.fase],
        "comandos_total": soma("comandos_total"), "comandos_cobertos": soma("comandos_cobertos"),
        "desvios_total": soma("desvios_total"), "desvios_cobertos": soma("desvios_cobertos"),
        "except_total": soma("except_total"), "except_cobertos": soma("except_cobertos"),
    }
    proj["cobertura_comandos"] = pct(proj["comandos_cobertos"], proj["comandos_total"])
    proj["cobertura_desvios"] = pct(proj["desvios_cobertos"], proj["desvios_total"])
    proj["cobertura_except"] = pct(proj["except_cobertos"], proj["except_total"])
    if mut:
        proj.update(score(total_mut))
    (outdir / "projeto.json").write_text(json.dumps(proj, indent=2, ensure_ascii=False))
    print(json.dumps(proj, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
