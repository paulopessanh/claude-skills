#!/usr/bin/env python3
"""brand_router.py — route a branding request to the right lane, in Portuguese or English.

Lanes and the skill each one loads:
  state      brand-studio     status, deadline, next step, reopen, approval
  discovery  brand-discovery  briefing, kick-off, research, competitors, ICP, territories (steps 1-3)
  direction  brand-direction  naming, anatomy, symbol paths, colour, type, shapes vote (steps 4-5)
  system     brand-system     identity presentation, guidelines, pieces, manual, file names (steps 6-8)
  ecosystem  brand-ecosystem  compile every approved step into the complete, audited brand package (step 9)
  review     brand-review     review a deliverable, read it through the client's eyes, triage a change request
  reverse    brand-reverse    reverse engineer a reference brand into method

Exit codes: 0 routed | 2 ambiguous (asks one question) | 3 no signal
With --state, a routed lane is checked against the project state and a BLOCKED note is printed when
the lane's steps cannot start yet. The note is information; the router never edits state.
Stdlib only. Deterministic.
"""

import argparse
import json
import re
import sys
import unicodedata

LANES = {
    "state": {"skill": "brand-studio", "steps": [], "kw": [
        "status", "prazo", "cronograma", "proximo passo", "onde estamos", "andamento", "next step", "deadline", "schedule",
        "reabrir", "reopen", "aprovado", "aprovar", "approve", "fup", "atraso", "late"]},
    "discovery": {"skill": "brand-discovery", "steps": ["1", "2", "3"], "kw": [
        "briefing", "brief", "kick-off", "kickoff", "extracao", "pesquisa", "imersao", "concorrente", "concorrentes", "competitor",
        "competitors", "mercado", "icp", "cliente ideal", "publico", "persona", "territorio", "territorios", "lacuna", "lacunas",
        "mapa cromatico", "espaco livre", "white space", "research", "market", "audience"]},
    "direction": {"skill": "brand-direction", "steps": ["4", "5"], "kw": [
        "naming", "nome", "anatomia", "tagline", "descriptor", "slogan", "hookline", "paleta", "cor", "cores", "tipografia", "fonte",
        "simbolo", "petreo", "petreos", "vetado", "vetados", "dinamica das formas", "votacao", "caminhos", "direcao criativa",
        "palette", "color", "typeface", "symbol", "logo concept", "vote", "name candidates", "inpi"]},
    "system": {"skill": "brand-system", "steps": ["6", "6.5", "7", "8"], "kw": [
        "guidelines", "diretrizes", "manual", "brandbook", "brand book", "apresentacao da marca", "versoes", "area de protecao",
        "reducao minima", "pecas", "aplicacoes", "tokens", "nomenclatura de arquivos", "nome de arquivo", "usos proibidos",
        "identity system", "clear space", "minimum size", "applications", "file naming"]},
    "ecosystem": {"skill": "brand-ecosystem", "steps": ["9"], "kw": [
        "ecossistema", "ecossistema da marca", "pacote da marca", "pacote completo", "gerar os assets", "gerar assets", "brandbook completo",
        "kit de marca", "entrega final da marca", "brand ecosystem", "brand package", "full brand kit", "generate the assets", "brand kit"]},
    "review": {"skill": "brand-review", "steps": [], "kw": [
        "revisar", "revisao", "review", "olhar do cliente", "feedback", "pedido de alteracao", "alteracao do cliente", "change request",
        "o cliente vai gostar", "client lens", "checar", "conferir", "validar", "lint", "premortem"]},
    "reverse": {"skill": "brand-reverse", "steps": [], "kw": [
        "engenharia reversa", "reverse engineer", "reverse engineering", "teardown", "como foi feita", "como essa marca foi criada",
        "marca de referencia", "reference brand", "reconstruir o processo", "benchmark de marca", "dissecar"]},
}


# Verbs and phrases that name the action itself outweigh the nouns they act on ("review the manual" is a review).
STRONG = {"revisar", "revisao", "review", "olhar do cliente", "client lens", "premortem", "engenharia reversa", "reverse engineer",
          "reverse engineering", "teardown"}


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def score(text):
    t = " " + re.sub(r"[^a-z0-9.\- ]", " ", fold(text)) + " "
    out = {}
    for lane, d in LANES.items():
        out[lane] = sum(4 if k in STRONG else (2 if " " in k else 1) for k in d["kw"]
                        if re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", t))
    return out


def blocked_note(lane, state_path):
    if not state_path:
        return None
    try:
        with open(state_path, encoding="utf-8") as fh:
            st = json.load(fh)
    except (OSError, ValueError):
        return f"state file {state_path} could not be read"
    steps = LANES[lane]["steps"]
    if not steps:
        return None
    S = st["steps"]
    live = [s for s in steps if S[s]["status"] in ("in_progress", "in_review", "with_client", "reopened", "stale")]
    if live:
        return f"work already open on step(s) {', '.join(live)}"
    startable = [s for s in steps if S[s]["status"] == "not_started"]
    deps = {"1": [], "2": ["1"], "3": ["1", "2"], "4": ["1", "2", "3"], "5": ["4"], "6": ["4", "5"], "6.5": ["6"], "7": ["6", "6.5"],
            "8": ["1", "2", "3", "4", "5", "6", "6.5", "7"], "9": ["1", "2", "3", "4", "5", "6", "6.5", "7", "8"]}
    if startable and all(any(S[d]["status"] != "approved" for d in deps[s]) for s in startable):
        need = sorted({d for s in startable for d in deps[s] if S[d]["status"] != "approved" and d not in steps})
        return f"BLOCKED: step(s) {', '.join(startable)} need approved step(s) {', '.join(need)} first"
    return None


def main():
    ap = argparse.ArgumentParser(description="Route a branding request to a lane (pt or en).")
    ap.add_argument("--goal", help="the request, in the user's words")
    ap.add_argument("--state", help="optional brand-state.json to check prerequisites")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    if a.sample:
        goals = ["quero fazer o briefing e levantar os concorrentes", "como essa marca foi criada? faça engenharia reversa",
                 "revisar o deck e checar o que o cliente vai achar", "preciso de ajuda com a marca"]
        rows = []
        for g in goals:
            sc = score(g)
            top = sorted(sc.items(), key=lambda kv: -kv[1])
            rows.append({"goal": g, "route": top[0][0] if top[0][1] else None, "scores": {k: v for k, v in top if v}})
        if a.output == "json":
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            for r in rows:
                print(f"{r['goal']!r} -> {r['route'] or 'none'} {r['scores']}")
        return
    if not a.goal:
        ap.error("provide --goal or --sample")
    sc = score(a.goal)
    ranked = sorted(sc.items(), key=lambda kv: -kv[1])
    (w, ws), (r, rs) = ranked[0], ranked[1]
    res = {"scores": {k: v for k, v in sc.items() if v}}
    if ws == 0:
        res.update(route=None, reason="no signal")
        code = 3
    elif rs == 0 or (ws >= 2 and ws >= 2 * rs):
        res.update(route=w, skill=LANES[w]["skill"], steps=LANES[w]["steps"])
        note = blocked_note(w, a.state)
        if note:
            res["state_note"] = note
        code = 0
    else:
        res.update(route=None, reason="ambiguous", candidates=[w, r],
                   question=f"Is this about {LANES[w]['skill']} or {LANES[r]['skill']}? Say which step or deliverable you mean.")
        code = 2
    print(json.dumps(res, indent=2, ensure_ascii=False) if a.output == "json" else
          (f"route: {res['route']} -> {res.get('skill')}  steps {res.get('steps')}" + (f"\nnote: {res['state_note']}" if res.get("state_note") else "")
           if code == 0 else f"{res['reason']}: " + (res.get("question") or "name the step or the deliverable")))
    sys.exit(code)


if __name__ == "__main__":
    main()
