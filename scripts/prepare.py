#!/usr/bin/env python3
"""Prepara os ambientes de medição de cada biblioteca.

Para cada biblioteca listada em ``subjects.lock.json``:

1. clona o repositório oficial e faz checkout no commit fixado;
2. cria ``work/<lib>/`` contendo apenas o pacote (``src/<pkg>``) — a pasta de
   testes original é descartada para evitar contaminação;
3. copia as suítes do estudo (``suites/<lib>/functional`` e ``structural``);
4. cria um ambiente virtual ``work/<lib>/.venv`` com dependências travadas.

Uso: python scripts/prepare.py [tinydb arrow humanize]
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
LOCK = json.loads((ROOT / "subjects.lock.json").read_text())
TOOLS = (ROOT / "requirements-tools.txt").read_text().split()


def run(cmd, **kw):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True, **kw)


def clone(lib: str, info: dict) -> Path:
    dest = WORK / "_repos" / lib
    if not dest.exists():
        run(["git", "clone", "--quiet", info["repo"], str(dest)])
    run(["git", "-C", str(dest), "-c", "advice.detachedHead=false", "checkout", "--quiet", info["commit"]])
    head = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
    assert head == info["commit"], f"{lib}: commit {head} != {info['commit']}"
    return dest


def build_workspace(lib: str, info: dict, repo: Path) -> Path:
    ws = WORK / lib
    pkg_dst = ws / "src" / info["package"]
    if pkg_dst.exists():
        shutil.rmtree(pkg_dst)
    shutil.copytree(repo / info["package_dir"], pkg_dst,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name, content in info.get("extra_files", {}).items():
        (pkg_dst / name).write_text(content)
    sync_tests(lib)
    return ws


def sync_tests(lib: str) -> None:
    ws = WORK / lib
    tests = ws / "tests"
    if tests.exists():
        shutil.rmtree(tests)
    for kind in ("functional", "structural"):
        src = ROOT / "suites" / lib / kind
        dst = tests / kind
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.glob("*.py"):
            shutil.copy2(f, dst / f.name)
    shutil.copy2(ROOT / "suites" / "conftest.py", tests / "conftest.py")


def make_venv(lib: str, info: dict) -> None:
    ws = WORK / lib
    py = ws / ".venv" / "bin" / "python"
    if not py.exists():
        venv.EnvBuilder(with_pip=True, clear=True).create(ws / ".venv")
    run([str(py), "-m", "pip", "install", "--quiet", *TOOLS, *info["runtime_deps"], *info.get("build_deps", [])])
    if info.get("compile_mo"):
        # Etapa de build do pacote oficial: compila os catálogos de tradução (.po -> .mo).
        code = (
            "import pathlib,sys\n"
            "from babel.messages.pofile import read_po\n"
            "from babel.messages.mofile import write_mo\n"
            "for po in pathlib.Path(sys.argv[1]).rglob('*.po'):\n"
            "    with open(po,'rb') as f: cat=read_po(f)\n"
            "    with open(po.with_suffix('.mo'),'wb') as f: write_mo(f,cat)\n"
        )
        run([str(py), "-c", code, str(ws / "src" / info["package"] / "locale")])
    freeze = subprocess.check_output([str(py), "-m", "pip", "freeze"], text=True)
    (ws / "requirements.lock.txt").write_text(freeze)


def main(libs: list[str]) -> None:
    WORK.mkdir(exist_ok=True)
    for lib in libs:
        info = LOCK[lib]
        repo = clone(lib, info)
        build_workspace(lib, info, repo)
        make_venv(lib, info)
        print(f"[ok] {lib} pronto em {WORK / lib}")


if __name__ == "__main__":
    main(sys.argv[1:] or list(LOCK))
