#!/usr/bin/env python3
"""Consolida os resultados das três questões de pesquisa.

Gera:
  resultados/RESUMO.md                 tabelas prontas para o artigo
  resultados/qp1_modulos.csv           métricas por módulo (fase inicial)
  resultados/qp2_distribuicao.csv      categorias do código não coberto (avaliador A)
  resultados/qp3_comparacao.csv        inicial x final por biblioteca
  resultados/qp3_residuo.csv           trechos que continuam não cobertos após a QP3
  requisitos/rastreabilidade.csv       requisito -> testes funcionais

Uso: python scripts/analyze.py
"""
from __future__ import annotations

import ast
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBS = ["tinydb", "arrow", "humanize"]
CATS = ["EXC", "VAL", "CFG", "LIM", "MORTO", "OUTRO"]
NOMES = {"EXC": "Tratamento de exceções", "VAL": "Validação defensiva", "CFG": "Configuração/ambiente",
         "LIM": "Casos-limite internos", "MORTO": "Código morto", "OUTRO": "Outro"}
RES = ROOT / "resultados"


def proj(fase, lib):
    return json.loads((RES / fase / lib / "projeto.json").read_text())


def fmt(v):
    return "—" if v is None else f"{v:.1f}"


# ------------------------------------------------------------------ rastreabilidade
def marcadores(path: Path, nome: str) -> dict[str, list[str]]:
    tree = ast.parse(path.read_text())
    out = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            for d in node.decorator_list:
                if (isinstance(d, ast.Call) and isinstance(d.func, (ast.Name, ast.Attribute))
                        and (getattr(d.func, "id", None) == nome or getattr(d.func, "attr", None) == nome)):
                    out[d.args[0].value].append(f"{path.name}::{node.name}")
    return out


def rastreabilidade():
    linhas = []
    for lib in LIBS:
        reqs = list(csv.DictReader(open(ROOT / "requisitos" / f"{lib}.csv")))
        m = defaultdict(list)
        for f in (ROOT / "suites" / lib / "functional").glob("test_*.py"):
            for k, v in marcadores(f, "req").items():
                m[k] += v
        for r in reqs:
            linhas.append({"biblioteca": lib, "requisito": r["id"], "tecnica": r["tecnica"],
                           "n_testes": len(m[r["id"]]), "testes": " | ".join(m[r["id"]])})
            if not m[r["id"]]:
                print(f"aviso: requisito sem teste {r['id']}")
    with open(ROOT / "requisitos" / "rastreabilidade.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    return linhas


# ------------------------------------------------------------------ resíduo QP3
def ainda_nao_coberto(trecho, cov) -> bool:
    f = cov["files"].get("src/" + trecho["modulo"])
    if f is None:
        return True
    if trecho["tipo"] == "L":
        a, _, b = trecho["linhas"].partition("-")
        faixa = set(range(int(a), int(b or a) + 1))
        return bool(faixa & set(f["missing_lines"]))
    o, d = map(int, trecho["linhas"].split("->"))
    return [o, d] in f["missing_branches"]


def complementares(libs) -> list[str]:
    """Análises decididas depois da coleta (declaradas como tal no artigo)."""
    md = ["## Análises complementares (definidas após a coleta)", "",
          "Estas análises não estavam no plano original. Foram definidas depois de ver os dados e devem ser",
          "apresentadas como exploratórias / de sensibilidade.", ""]

    # 1. Onde estão os mutantes sobreviventes
    arq = RES / "qp_mutantes_sobreviventes.csv"
    if arq.exists():
        md += ["### Onde sobrevivem os mutantes", "",
               "Cada mutante foi localizado no comando que altera (`scripts/mutant_lines.py`). "
               "Sobreviventes incluem os mutantes sem teste.", "",
               "| Biblioteca | Fase | Sobreviventes | Em comando executado | Em comando não executado | Valor padrão na assinatura | Não identificado |",
               "|---|---|---:|---:|---:|---:|---:|"]
        for r in csv.DictReader(open(arq)):
            n = int(r["sobreviventes"])
            pc = lambda k: f"{r[k]} ({100 * int(r[k]) / n:.0f}%)"
            md.append(f"| {r['biblioteca']} | {r['fase']} | {n} | {pc('em_comando_executado')} | "
                      f"{pc('em_comando_nao_executado')} | {r['em_valor_padrao_assinatura']} | {r['nao_identificada']} |")
        md += ["", "Na fase final, praticamente todo mutante que sobrevive está num comando que a suíte executa: "
               "o limite passou a ser a força dos oráculos (asserções), não a cobertura.", ""]

    # 2. Arrow sem locales.py
    md += ["### Arrow com e sem `locales.py`", "",
           "| Recorte | Fase | Comandos | Desvios | Escore de mutação | Mutantes |", "|---|---|---:|---:|---:|---:|"]
    for recorte, filtro in (("com locales.py", lambda m: True), ("sem locales.py", lambda m: m != "arrow/locales.py")):
        for fase in ("inicial", "final"):
            rows = [r for r in csv.DictReader(open(RES / fase / "arrow" / "modulos.csv")) if filtro(r["modulo"])]
            sm = lambda k: sum(int(r[k] or 0) for r in rows)
            tot = sm("mutantes_total")
            mortos = sm("mutantes_mortos")
            md.append(f"| {recorte} | {fase} | {100 * sm('comandos_cobertos') / sm('comandos_total'):.1f}% | "
                      f"{100 * sm('desvios_cobertos') / sm('desvios_total'):.1f}% | {100 * mortos / tot:.1f}% | {tot} |")
    md.append("")

    # 3. Hipótese sob ponderações diferentes
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from kappa import carregar
    md += ["### Hipótese sob diferentes ponderações", "",
           "Participação de exceções + validações (EXC+VAL) no código não coberto pela suíte funcional.", "",
           "| Ponderação | Avaliador A | Avaliador B |", "|---|---:|---:|"]

    def pesos(lib):
        trechos = list(csv.DictReader(open(ROOT / "classificacao" / f"trechos_{lib}.csv")))
        mut = list(csv.DictReader(open(RES / "inicial" / lib / "mutantes_linhas.csv")))
        mut_por_linha = Counter((r["modulo"], int(r["linha"])) for r in mut if r["linha"])
        out = {}
        for t in trechos:
            if t["tipo"] == "L":
                a, _, b = t["linhas"].partition("-")
                faixa = range(int(a), int(b or a) + 1)
                nmut = sum(mut_por_linha[(t["modulo"], ln)] for ln in faixa)
                ncmd = int(t["n_comandos"])
            else:
                o = int(t["linhas"].split("->")[0])
                nmut, ncmd = mut_por_linha[(t["modulo"], o)], 1
            out[t["id"]] = {"trecho": 1, "comandos": ncmd, "mutantes": nmut, "modulo": t["modulo"]}
        return out

    P = {}
    for l in libs:
        P.update(pesos(l))
    aval = {}
    for nome, padrao in (("A", "avaliador_A_{}.csv"), ("B", "avaliador_B_IA_{}.csv")):
        d = {}
        for l in libs:
            arqv = ROOT / "classificacao" / padrao.format(l)
            if arqv.exists():
                d.update(carregar(arqv))
        aval[nome] = d
    linhas_hip = [("Contagem de trechos", "trecho", lambda i: True),
                  ("Ponderado por comandos", "comandos", lambda i: True),
                  ("Ponderado por mutantes", "mutantes", lambda i: True),
                  ("Contagem, sem `arrow/locales.py`", "trecho", lambda i: P[i]["modulo"] != "arrow/locales.py"),
                  ("Por comandos, sem `arrow/locales.py`", "comandos", lambda i: P[i]["modulo"] != "arrow/locales.py")]
    for rot, peso, filtro in linhas_hip:
        cel = []
        for nome in ("A", "B"):
            d = aval[nome]
            ids = [i for i in d if filtro(i)]
            tot = sum(P[i][peso] for i in ids)
            ev = sum(P[i][peso] for i in ids if d[i] in ("EXC", "VAL"))
            cel.append(f"{100 * ev / tot:.1f}%" if tot else "—")
        md.append(f"| {rot} | {cel[0]} | {cel[1]} |")
    md += ["", "Em nenhuma ponderação EXC+VAL passa de 50%; a hipótese não se sustenta em nenhum recorte.", ""]
    return md


def main():
    rast = rastreabilidade()
    md = ["# Resumo dos resultados", "",
          "Gerado por `scripts/analyze.py`. Commits fixados em `subjects.lock.json`.", ""]

    # QP1 -------------------------------------------------------------
    md += ["## QP1 — Suíte funcional (caixa-preta)", "",
           "| Biblioteca | Requisitos | Testes* | Comandos | Desvios | Blocos `except` | Mutantes | Escore de mutação |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    todos_mod = []
    for lib in LIBS:
        p = proj("inicial", lib)
        nreq = sum(1 for r in rast if r["biblioteca"] == lib)
        ntest = sum(1 for _ in (ROOT / "suites" / lib / "functional").glob("test_*.py"))
        txt = (RES / "inicial" / lib / "pytest.txt").read_text().strip().splitlines()[-1]
        md.append(f"| {lib} | {nreq} | {txt.split(' in ')[0]} | {fmt(p['cobertura_comandos'])}% | "
                  f"{fmt(p['cobertura_desvios'])}% | {fmt(p['cobertura_except'])}% "
                  f"({p['except_cobertos']}/{p['except_total']}) | {p.get('mutantes_total', '—')} | "
                  f"{fmt(p.get('escore_mutacao'))}% |")
        for r in csv.DictReader(open(RES / "inicial" / lib / "modulos.csv")):
            todos_mod.append({"biblioteca": lib, **r})
    md += ["", "\\* contagem de casos de teste executados pelo pytest (inclui parametrizações e `xfail`).", ""]
    with open(RES / "qp1_modulos.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(todos_mod[0]))
        w.writeheader()
        w.writerows(todos_mod)
    md += ["Métricas por módulo: `resultados/qp1_modulos.csv`.", ""]

    # QP2 -------------------------------------------------------------
    dist = []
    md += ["## QP2 — Categorias do código não coberto (Avaliador A)", "",
           "| Categoria | " + " | ".join(LIBS) + " | Total | % |", "|---|" + "---:|" * (len(LIBS) + 2)]
    cont = {lib: Counter(r["categoria"] for r in csv.DictReader(open(ROOT / "classificacao" / f"avaliador_A_{lib}.csv")))
            for lib in LIBS}
    total = sum(sum(c.values()) for c in cont.values())
    for c in CATS:
        t = sum(cont[l][c] for l in LIBS)
        md.append(f"| {NOMES[c]} | " + " | ".join(str(cont[l][c]) for l in LIBS) + f" | {t} | {100 * t / total:.1f}% |")
        for l in LIBS:
            dist.append({"biblioteca": l, "categoria": c, "trechos": cont[l][c]})
    md.append("| **Total** | " + " | ".join(str(sum(cont[l].values())) for l in LIBS) + f" | {total} | 100% |")
    exc_val = sum(cont[l]["EXC"] + cont[l]["VAL"] for l in LIBS)
    md += ["", f"**Hipótese** (exceções + validações defensivas > 50% do não coberto): "
           f"{exc_val}/{total} = {100 * exc_val / total:.1f}% na classificação A — "
           + ("**sustentada**." if exc_val / total > 0.5 else "**não sustentada**.")]
    for l in LIBS:
        n = sum(cont[l].values())
        md.append(f"- {l}: {cont[l]['EXC'] + cont[l]['VAL']}/{n} = {100 * (cont[l]['EXC'] + cont[l]['VAL']) / n:.1f}%")
    # Concordância entre avaliadores
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from kappa import carregar, cohen_kappa, interpretar
    md += ["", "### Concordância entre avaliadores (antes da resolução de divergências)", "",
           "Avaliador A e Avaliador B são duas instâncias de IA (Claude) que classificaram de forma independente;",
           "B trabalhou numa pasta isolada, só com o livro de códigos, os trechos e o código-fonte, sem acesso à classificação A.", "",
           "| Biblioteca | n | Concordância observada | Kappa de Cohen | Interpretação (Landis & Koch) |",
           "|---|---:|---:|---:|---|"]
    ta, tb = [], []
    contB = {}
    for l in LIBS:
        pb = ROOT / "classificacao" / f"avaliador_B_IA_{l}.csv"
        if not pb.exists():
            continue
        A_, B_ = carregar(ROOT / "classificacao" / f"avaliador_A_{l}.csv"), carregar(pb)
        ids = sorted(A_)
        a, b = [A_[i] for i in ids], [B_[i] for i in ids]
        ta += a; tb += b
        contB[l] = Counter(b)
        k, po, _ = cohen_kappa(a, b)
        md.append(f"| {l} | {len(ids)} | {100 * po:.1f}% | {k:.3f} | {interpretar(k)} |")
    if ta:
        k, po, _ = cohen_kappa(ta, tb)
        md.append(f"| **todas** | {len(ta)} | {100 * po:.1f}% | {k:.3f} | {interpretar(k)} |")
        tB = sum(sum(c.values()) for c in contB.values())
        evB = sum(contB[l]["EXC"] + contB[l]["VAL"] for l in contB)
        md += ["", "Distribuição segundo o Avaliador B: " + ", ".join(
            f"{NOMES[c]} {sum(contB[l][c] for l in contB)}" for c in CATS) +
            f". Exceções + validações = {evB}/{tB} = {100 * evB / tB:.1f}% — hipótese "
            + ("sustentada" if evB / tB > 0.5 else "também não sustentada") + " pelo Avaliador B.",
            "", "Matriz de confusão e lista de divergências: `python scripts/kappa.py --todas` e "
            "`classificacao/divergencias_todas.csv` (coluna `consenso` a preencher na reunião).", ""]
    with open(RES / "qp2_distribuicao.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["biblioteca", "categoria", "trechos"])
        w.writeheader()
        w.writerows(dist)

    # QP3 -------------------------------------------------------------
    comp, resid = [], []
    md += ["## QP3 — Ganho com testes estruturais direcionados", "",
           "| Biblioteca | Métrica | Inicial | Final | Ganho (p.p.) |", "|---|---|---:|---:|---:|"]
    for lib in LIBS:
        i, f = proj("inicial", lib), proj("final", lib)
        for k, nome in [("cobertura_comandos", "Comandos"), ("cobertura_desvios", "Desvios"),
                        ("cobertura_except", "Blocos except"), ("escore_mutacao", "Escore de mutação")]:
            vi, vf = i.get(k), f.get(k)
            g = None if vi is None or vf is None else vf - vi
            md.append(f"| {lib} | {nome} | {fmt(vi)}% | {fmt(vf)}% | {'—' if g is None else f'{g:+.1f}'} |")
            comp.append({"biblioteca": lib, "metrica": k, "inicial": vi, "final": vf, "ganho_pp": g})
        md.append(f"| {lib} | Mutantes (total) | {i.get('mutantes_total')} | {f.get('mutantes_total')} | |")
        def casos(fase):
            ult = (RES / fase / lib / "pytest.txt").read_text().strip().splitlines()[-1]
            return sum(int(x.split()[0]) for x in ult.split(" in ")[0].split(", "))
        nfunc_struct = 0
        for f_ in (ROOT / "suites" / lib / "structural").glob("test_*.py"):
            tree = ast.parse(f_.read_text())
            nfunc_struct += sum(isinstance(n_, ast.FunctionDef) and n_.name.startswith("test_") for n_ in ast.walk(tree))
        md.append(f"| {lib} | Testes estruturais adicionados | — | {nfunc_struct} funções / "
                  f"{casos('final') - casos('inicial')} casos | |")

        cov_f = json.loads((RES / "final" / lib / "coverage.json").read_text())
        clsA = {r["id"]: r for r in csv.DictReader(open(ROOT / "classificacao" / f"avaliador_A_{lib}.csv"))}
        for t in csv.DictReader(open(ROOT / "classificacao" / f"trechos_{lib}.csv")):
            if ainda_nao_coberto(t, cov_f):
                a = clsA[t["id"]]
                resid.append({"id": t["id"], "biblioteca": lib, "modulo": t["modulo"], "linhas": t["linhas"],
                              "categoria_A": a["categoria"], "alcancavel_A": a["alcancavel"],
                              "situacao": "previsto (inalcançável)" if a["alcancavel"] == "nao"
                              else "tentativa sem sucesso"})
        # Desvios parciais que surgiram só na fase final (linhas antes inteiramente não executadas)
        conhecidos = {(t["modulo"], t["linhas"]) for t in csv.DictReader(open(ROOT / "classificacao" / f"trechos_{lib}.csv"))}
        for fname, fd in cov_f["files"].items():
            for o, d in fd["missing_branches"]:
                mod = fname.removeprefix("src/")
                if o in fd["executed_lines"] and d not in fd["missing_lines"] and (mod, f"{o}->{d}") not in conhecidos:
                    resid.append({"id": "(novo)", "biblioteca": lib, "modulo": mod, "linhas": f"{o}->{d}",
                                  "categoria_A": "", "alcancavel_A": "",
                                  "situacao": "desvio parcial revelado na fase final"})
    with open(RES / "qp3_comparacao.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(comp[0]))
        w.writeheader()
        w.writerows(comp)
    with open(RES / "qp3_residuo.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(resid[0]))
        w.writeheader()
        w.writerows(resid)
    md += ["", "### Código residual (não coberto após a QP3)", "",
           "| Biblioteca | Trecho | Módulo | Linhas | Categoria (A) | Situação |", "|---|---|---|---|---|---|"]
    for r in resid:
        md.append(f"| {r['biblioteca']} | {r['id']} | {r['modulo']} | {r['linhas']} | {r['categoria_A']} | {r['situacao']} |")
    md.append("")
    md += complementares(LIBS)
    (RES / "RESUMO.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
