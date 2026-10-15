#!/usr/bin/env python3
"""brand_state.py — the project memory and gatekeeper of a branding process.

A branding project fails less from one bad step than from lost coherence between steps:
a client change lands after the palette was approved and nobody re-checks the manual.
This tool is a JSON-backed state machine that makes the dependency between steps explicit.

Steps (a dependency graph, not a list):
  1 Briefing -> 2 Kick-off -> 3 Research -> 4 Direction -> 5 Shapes dynamic -> 6 Brand & identity
  -> 6.5 Team guidelines -> 7 Pieces -> 8 Manual
Status: not_started, in_progress, in_review, with_client, approved, reopened, stale.

Hard rules (each refusal exits 4):
  start     needs every prerequisite step approved (not stale, not reopened)
  submit    needs every gate item checked with evidence
  review    a release needs --lint-exit (0 or 2; 4 is HELD and refused; 'na' needs a reason)
  send/approve  need a review verdict of released or released_with_caveats
  reopen    marks every approved/in-flight downstream step STALE, transitively
  revalidate  a stale step returns to where it was (approved, or back to in_progress if it was never approved)
              only with a note and only if its prerequisites are approved
  lock      pétreos (non-negotiable truths) and vetados (paths we will not take) live in one place

change requests are logged verbatim, triaged against locked decisions and the dependency graph,
and resolved as accept / negotiate / defend by a person. The tool suggests; it never decides.

Exit codes: 0 ok | 1 usage or input error | 4 refused by a rule
Stdlib only. No network. Atomic writes.
"""

import argparse
import datetime
import json
import os
import re
import sys
import tempfile

STEPS = ["1", "2", "3", "4", "5", "6", "6.5", "7", "8"]
NAMES = {"1": "Briefing", "2": "Kick-off", "3": "Research and immersion", "4": "Creative and visual direction",
         "5": "Shapes dynamic", "6": "Brand and identity presentation", "6.5": "Team guidelines",
         "7": "Graphic pieces", "8": "Brand manual"}
DEPS = {"1": [], "2": ["1"], "3": ["1", "2"], "4": ["1", "2", "3"], "5": ["4"], "6": ["4", "5"],
        "6.5": ["6"], "7": ["6", "6.5"], "8": ["1", "2", "3", "4", "5", "6", "6.5", "7"]}
GATES = {
    "1": ["facts_sourced", "hypotheses_marked", "scope_matches_contract", "dates_coherent", "gaps_listed", "kickoff_agenda_ready"],
    "2": ["extraction_validated", "purpose_and_attributes_defined", "ideal_client_drafted", "territories_listed", "baseline_inputs_captured"],
    "3": ["competitors_sourced_and_dated", "colours_measured", "icp_hypotheses_marked", "registries_dated", "white_space_linked_to_attributes"],
    "4": ["petreos_and_vetados_have_origin", "naming_and_registries_flagged", "anatomy_candidates_present", "colour_contrast_computed",
          "fonts_licensed", "client_taste_handled", "graphic_elements_direction_set"],
    "5": ["every_item_has_visible_type", "references_not_presented_as_proposals", "votes_counted_twice", "verdict_explicit", "finalisation_brief_written"],
    "6": ["concept_one_sentence", "anatomy_final", "construction_and_versions", "usage_and_minimum_size", "colour_tokens_and_pairs",
          "typography_hierarchy", "graphic_elements_closed", "voice_guidelines_final"],
    "6.5": ["signatures_published", "technical_rules_complete", "no_story_or_concept_inside", "approved_by_lead"],
    "7": ["pieces_follow_guidelines", "print_specs_present", "approved_pieces_only_in_exports"],
    "8": ["every_approved_step_reflected", "manual_matches_guidelines", "version_history_present", "client_and_internal_versions_in_sync"],
}
TOUCH_STEPS = {
    "scope": ["1", "2", "3", "4", "5", "6", "6.5", "7", "8"], "audience": ["3", "4", "6", "8"],
    "name": ["4", "6", "6.5", "7", "8"], "anatomy": ["4", "6", "6.5", "8"], "symbol": ["4", "5", "6", "6.5", "7", "8"],
    "colour": ["4", "6", "6.5", "7", "8"], "type": ["4", "6", "6.5", "7", "8"], "elements": ["4", "6", "6.5", "7", "8"],
    "voice": ["4", "6", "8"], "pieces": ["7", "8"],
}
VERDICTS = ("released", "released_with_caveats", "held")


class Refusal(Exception):
    pass


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def downstream(step):
    out, frontier = set(), {step}
    while frontier:
        nxt = {s for s in STEPS if any(d in frontier for d in DEPS[s])} - out
        out |= nxt
        frontier = nxt
    return [s for s in STEPS if s in out]


def new_state(client, sigla, decisors):
    return {"project": {"client": client, "sigla": sigla.upper(), "decisors": decisors, "created": now()},
            "steps": {s: {"name": NAMES[s], "status": "not_started", "gate": {}, "verdict": None,
                          "approved_at": None, "approved_by": None, "stale_reason": None} for s in STEPS},
            "fio": {"petreos": [], "vetados": []}, "changes": [], "history": []}


def log(st, msg):
    st["history"].append({"at": now(), "event": msg})


def blockers(st, step):
    return [d for d in DEPS[step] if st["steps"][d]["status"] != "approved"]


def need_step(step):
    if step not in STEPS:
        raise Refusal(f"unknown step '{step}'. Steps: {', '.join(STEPS)}")


def start(st, step):
    need_step(step)
    s = st["steps"][step]
    if s["status"] not in ("not_started", "reopened"):
        raise Refusal(f"step {step} is {s['status']}, not startable")
    b = blockers(st, step)
    if b:
        raise Refusal(f"step {step} needs approved prerequisites: " + ", ".join(f"{d} ({st['steps'][d]['status']})" for d in b))
    s["status"] = "in_progress"
    log(st, f"start {step}")
    return f"step {step} {NAMES[step]} started"


def check(st, step, item, evidence):
    need_step(step)
    s = st["steps"][step]
    if s["status"] != "in_progress":
        raise Refusal(f"step {step} is {s['status']}; gate items are checked while in_progress")
    if item not in GATES[step]:
        raise Refusal(f"'{item}' is not a gate item of step {step}. Items: {', '.join(GATES[step])}")
    if len((evidence or "").strip()) < 3:
        raise Refusal("evidence is required: say where the proof is (document, link, number)")
    s["gate"][item] = {"evidence": evidence.strip(), "at": now()}
    log(st, f"check {step}:{item}")
    return f"step {step}: {len(s['gate'])}/{len(GATES[step])} gate items checked"


def submit(st, step):
    need_step(step)
    s = st["steps"][step]
    if s["status"] != "in_progress":
        raise Refusal(f"step {step} is {s['status']}, not in_progress")
    missing = [g for g in GATES[step] if g not in s["gate"]]
    if missing:
        raise Refusal(f"step {step} gate incomplete, missing: {', '.join(missing)}")
    s["status"], s["verdict"] = "in_review", None
    log(st, f"submit {step}")
    return f"step {step} is in review"


def review(st, step, verdict, note, lint_exit=None):
    need_step(step)
    s = st["steps"][step]
    if verdict not in VERDICTS:
        raise Refusal(f"verdict must be one of {', '.join(VERDICTS)}")
    if s["status"] != "in_review":
        raise Refusal(f"step {step} is {s['status']}; a review verdict applies to a step in_review")
    if verdict != "held":
        # A release must rest on the mechanical layer: the exit code of deliverable_linter.py for this deliverable.
        if lint_exit not in ("0", "2", "na"):
            raise Refusal("a release needs --lint-exit: the exit code of deliverable_linter.py (0 or 2), or 'na' with a note "
                          "saying why no text deliverable applies. Exit 4 means HELD: fix the deliverable first")
        if lint_exit == "na" and len((note or "").strip()) < 8:
            raise Refusal("--lint-exit na needs a note saying why the linter does not apply")
    if verdict == "held":
        s["status"] = "in_progress"
    s["verdict"] = {"value": verdict, "note": note or "", "lint_exit": lint_exit, "at": now()}
    log(st, f"review {step}: {verdict}")
    return f"step {step} review: {verdict}" + (" (back to in_progress)" if verdict == "held" else "")


def verdict_ok(s):
    return bool(s["verdict"]) and s["verdict"]["value"] in ("released", "released_with_caveats")


def send(st, step):
    need_step(step)
    s = st["steps"][step]
    if s["status"] != "in_review" or not verdict_ok(s):
        raise Refusal(f"step {step} cannot go to the client: it must be in_review with a released verdict")
    s["status"] = "with_client"
    log(st, f"send {step}")
    return f"step {step} is with the client"


def approve(st, step, by):
    need_step(step)
    s = st["steps"][step]
    if s["status"] not in ("in_review", "with_client") or not verdict_ok(s):
        raise Refusal(f"step {step} cannot be approved: it needs a released review verdict first (status {s['status']})")
    b = blockers(st, step)
    if b:
        raise Refusal(f"step {step} depends on unapproved step(s): {', '.join(b)}")
    if not (by or "").strip():
        raise Refusal("say who approved (--by)")
    s.update(status="approved", approved_at=now(), approved_by=by.strip(), stale_reason=None)
    log(st, f"approve {step} by {by.strip()}")
    return f"step {step} approved by {by.strip()}"


def reopen(st, step, reason):
    need_step(step)
    if len((reason or "").strip()) < 5:
        raise Refusal("give the reason for reopening (a client request, an error found)")
    s = st["steps"][step]
    if s["status"] == "not_started":
        raise Refusal(f"step {step} has not started")
    s.update(status="reopened", verdict=None, approved_at=None, approved_by=None, gate={})
    hit = []
    for d in downstream(step):
        ds = st["steps"][d]
        if ds["status"] in ("approved", "with_client", "in_review", "in_progress"):
            ds.update(was=ds["status"] if ds["status"] != "stale" else ds.get("was", "approved"), status="stale",
                      stale_reason=f"step {step} reopened: {reason.strip()}")
            hit.append(d)
    log(st, f"reopen {step}: {reason.strip()}; stale: {','.join(hit) or 'none'}")
    return f"step {step} reopened; stale downstream: {', '.join(hit) or 'none'}"


def revalidate(st, step, note):
    need_step(step)
    s = st["steps"][step]
    if s["status"] != "stale":
        raise Refusal(f"step {step} is {s['status']}, not stale")
    if len((note or "").strip()) < 8:
        raise Refusal("explain why the step still holds (what you re-checked and what stayed the same)")
    b = blockers(st, step)
    if b:
        raise Refusal(f"step {step} cannot be revalidated while prerequisite(s) are not approved: {', '.join(b)}")
    if s.get("was") == "approved":
        s.update(status="approved", stale_reason=None)
        msg = f"step {step} revalidated and approved again"
    else:
        s.update(status="in_progress", stale_reason=None, verdict=None)
        msg = f"step {step} was not approved before it went stale, so it is back in_progress (re-check the gate)"
    log(st, f"revalidate {step}: {note.strip()}")
    return msg


def lock(st, kind, text, origin):
    if kind not in ("petreo", "vetado"):
        raise Refusal("kind must be petreo or vetado")
    if len((text or "").strip()) < 4 or len((origin or "").strip()) < 3:
        raise Refusal("a locked decision needs its text and a traceable origin")
    lst = st["fio"]["petreos" if kind == "petreo" else "vetados"]
    lst.append({"text": text.strip(), "origin": origin.strip(), "at": now()})
    log(st, f"lock {kind}: {text.strip()}")
    note = " (more than 5 is a list, not a spine)" if len(lst) > 5 else ""
    return f"{kind} locked ({len(lst)} total){note}"


NOISE = {"that", "this", "with", "from", "have", "want", "wants", "would", "should", "because", "please", "more", "than", "they",
         "their", "there", "make", "looks", "look", "like", "into", "also", "para", "como", "mais", "porque", "quer", "querem",
         "symbol", "mark", "brand", "logo", "pack", "shape", "form", "literal", "category", "cliche", "pictorial", "field"}


def toks(s):
    return {w for w in re.findall(r"[a-z0-9\u00e0-\u00ff]+", s.lower()) if len(w) >= 4} - NOISE


def triage(st, text, touches):
    bad = [t for t in touches if t not in TOUCH_STEPS]
    if bad:
        raise Refusal(f"unknown --touches value(s): {', '.join(bad)}. Use: {', '.join(TOUCH_STEPS)}")
    affected = sorted({s for t in touches for s in TOUCH_STEPS[t]}, key=STEPS.index)
    reopen_these = [s for s in affected if st["steps"][s]["status"] in ("approved", "with_client", "in_review")]
    tk = toks(text)
    conflicts = [{"kind": k, "text": x["text"], "shared_words": sorted(tk & toks(x["text"]))}
                 for k, lst in (("petreo", st["fio"]["petreos"]), ("vetado", st["fio"]["vetados"]))
                 for x in lst if tk & toks(x["text"])]
    if any(c["kind"] == "petreo" for c in conflicts):
        suggestion = "DEFEND_OR_NEGOTIATE"
    elif conflicts or reopen_these:
        suggestion = "NEGOTIATE"
    else:
        suggestion = "ACCEPT"
    return {"affected_steps": affected, "would_reopen": reopen_these, "conflicts_with_locked": conflicts, "suggestion": suggestion}


def add_change(st, text, origin, touches):
    if len((text or "").strip()) < 5 or len((origin or "").strip()) < 3:
        raise Refusal("log the request verbatim and where it came from")
    t = triage(st, text, touches)
    cid = f"CH{len(st['changes']) + 1:02d}"
    st["changes"].append({"id": cid, "text": text.strip(), "origin": origin.strip(), "touches": touches, "triage": t,
                          "status": "open", "resolution": None, "at": now()})
    log(st, f"change {cid} logged")
    return (f"{cid} logged. Suggestion: {t['suggestion']}. Would reopen: {', '.join(t['would_reopen']) or 'nothing approved'}. "
            "Possible overlap with locked decisions (judge each by the shared words): "
            + ("; ".join(f"{c['kind']} '{c['text']}' [shared: {', '.join(c['shared_words'])}]" for c in t["conflicts_with_locked"]) or "none")
            + ". A person resolves it with the resolve command.")


def resolve(st, cid, cls, by):
    ch = next((c for c in st["changes"] if c["id"] == cid), None)
    if not ch:
        raise Refusal(f"no change request {cid}")
    if ch["status"] != "open":
        raise Refusal(f"{cid} is already {ch['status']}")
    if cls not in ("accept", "negotiate", "defend") or not (by or "").strip():
        raise Refusal("resolve needs --class accept|negotiate|defend and --by NAME")
    ch.update(status="resolved", resolution={"class": cls, "by": by.strip(), "at": now()})
    log(st, f"change {cid} resolved as {cls}")
    todo = ""
    if cls == "accept" and ch["triage"]["would_reopen"]:
        todo = f" Next: reopen step {ch['triage']['would_reopen'][0]} (earliest affected) with this request as the reason."
    return f"{cid} resolved: {cls}.{todo}"


def next_action(st):
    S = st["steps"]
    for s in STEPS:
        if S[s]["status"] == "reopened":
            return f"Rework step {s} {NAMES[s]} (reopened)."
    for s in STEPS:
        if S[s]["status"] == "stale":
            return f"Revalidate or rework step {s} {NAMES[s]} (stale: {S[s]['stale_reason']})."
    for s in STEPS:
        if S[s]["status"] in ("in_progress", "in_review", "with_client"):
            return f"Continue step {s} {NAMES[s]} ({S[s]['status']})."
    for s in STEPS:
        if S[s]["status"] == "not_started" and not blockers(st, s):
            return f"Start step {s} {NAMES[s]}."
    open_changes = [c["id"] for c in st["changes"] if c["status"] == "open"]
    return "All steps approved." + (f" Open change requests: {', '.join(open_changes)}." if open_changes else "")


def render_status(st):
    p = st["project"]
    lines = [f"{p['client']} [{p['sigla']}]  decisors: {', '.join(p['decisors']) or 'none'}"]
    for s in STEPS:
        x = st["steps"][s]
        extra = f"  gate {len(x['gate'])}/{len(GATES[s])}" if x["status"] in ("in_progress", "reopened") else ""
        extra += f"  verdict {x['verdict']['value']}" if x["verdict"] else ""
        extra += f"  STALE: {x['stale_reason']}" if x["status"] == "stale" else ""
        lines.append(f"  {s:<4} {NAMES[s]:<34} {x['status']}{extra}")
    lines.append(f"  petreos {len(st['fio']['petreos'])}, vetados {len(st['fio']['vetados'])}, "
                 f"open changes {sum(1 for c in st['changes'] if c['status'] == 'open')}")
    lines.append("  Next: " + next_action(st))
    return "\n".join(lines)


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"error: cannot read state {path}: {exc}. Run init first.", file=sys.stderr)
        sys.exit(1)


def save(path, st):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".brand-state-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def sample(as_json=False):
    st = new_state("Serra Fina (fictional)", "SFI", ["Ana (owner)", "Beto (marketing)"])
    script = [
        ("start 2 before 1 (must refuse)", lambda: start(st, "2")),
        ("start 1", lambda: start(st, "1")),
        ("submit 1 with no gate (must refuse)", lambda: submit(st, "1")),
    ]
    for item in GATES["1"]:
        script.append((f"check 1:{item}", lambda i=item: check(st, "1", i, "briefing-v1 doc, section by section")))
    script += [("submit 1", lambda: submit(st, "1")),
               ("approve 1 without review (must refuse)", lambda: approve(st, "1", "Ana")),
               ("review 1 without the linter result (must refuse)", lambda: review(st, "1", "released", "")),
               ("review 1 after a clean lint", lambda: review(st, "1", "released", "", "0")), ("approve 1", lambda: approve(st, "1", "Ana")),
               ("reopen 1", lambda: reopen(st, "1", "client changed the contract scope"))]
    out = []
    for label, fn in script:
        try:
            out.append(f"> {label}: {fn()}")
        except Refusal as e:
            out.append(f"> {label}: REFUSED. {e}")
    out.append(render_status(st))
    print(json.dumps(out, indent=2, ensure_ascii=False) if as_json else "\n".join(out))


def main():
    ap = argparse.ArgumentParser(description="State machine and gatekeeper for a branding process.")
    ap.add_argument("--state", default="brand-state.json", help="state file (default ./brand-state.json)")
    ap.add_argument("--sample", action="store_true", help="walk a scripted scenario in memory, including refusals")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("init"); p.add_argument("--client", required=True); p.add_argument("--sigla", required=True)
    p.add_argument("--decisors", default=""); p.add_argument("--force", action="store_true")
    for name in ("status", "next", "log"):
        sub.add_parser(name)
    for name in ("start", "submit", "send"):
        p = sub.add_parser(name); p.add_argument("step")
    p = sub.add_parser("check"); p.add_argument("step"); p.add_argument("item"); p.add_argument("--evidence", default="")
    p = sub.add_parser("review"); p.add_argument("step"); p.add_argument("--verdict", required=True); p.add_argument("--note", default="")
    p.add_argument("--lint-exit", default=None, help="exit code of deliverable_linter.py for this deliverable: 0, 2, or na (with a note)")
    p = sub.add_parser("approve"); p.add_argument("step"); p.add_argument("--by", default="")
    p = sub.add_parser("reopen"); p.add_argument("step"); p.add_argument("--reason", default="")
    p = sub.add_parser("revalidate"); p.add_argument("step"); p.add_argument("--note", default="")
    p = sub.add_parser("lock"); p.add_argument("--kind", required=True); p.add_argument("--text", required=True); p.add_argument("--origin", required=True)
    p = sub.add_parser("change"); p.add_argument("--text", required=True); p.add_argument("--origin", required=True)
    p.add_argument("--touches", default="", help="comma list: " + ",".join(TOUCH_STEPS))
    p = sub.add_parser("resolve"); p.add_argument("id"); p.add_argument("--class", dest="cls", default=""); p.add_argument("--by", default="")
    a = ap.parse_args()
    if a.sample:
        sample(a.output == "json")
        return
    if not a.cmd:
        ap.error("give a command or --sample")
    if a.cmd == "init":
        if os.path.exists(a.state) and not a.force:
            print(f"refused: {a.state} exists. Use --force to overwrite.", file=sys.stderr)
            sys.exit(4)
        st = new_state(a.client, a.sigla, [d.strip() for d in a.decisors.split(",") if d.strip()])
        save(a.state, st)
        print(f"state created at {a.state}")
        return
    st = load(a.state)
    try:
        if a.cmd == "status":
            print(json.dumps(st, indent=2, ensure_ascii=False) if a.output == "json" else render_status(st))
            return
        if a.cmd == "next":
            print(next_action(st)); return
        if a.cmd == "log":
            for h in st["history"]:
                print(f"{h['at']}  {h['event']}")
            return
        touches = [t.strip() for t in getattr(a, "touches", "").split(",") if t.strip()]
        msg = {"start": lambda: start(st, a.step), "check": lambda: check(st, a.step, a.item, a.evidence),
               "submit": lambda: submit(st, a.step), "review": lambda: review(st, a.step, a.verdict, a.note, getattr(a, "lint_exit", None)),
               "send": lambda: send(st, a.step), "approve": lambda: approve(st, a.step, a.by),
               "reopen": lambda: reopen(st, a.step, a.reason), "revalidate": lambda: revalidate(st, a.step, a.note),
               "lock": lambda: lock(st, a.kind, a.text, a.origin),
               "change": lambda: add_change(st, a.text, a.origin, touches),
               "resolve": lambda: resolve(st, a.id, a.cls, a.by)}[a.cmd]()
    except Refusal as e:
        print(f"refused: {e}", file=sys.stderr)
        sys.exit(4)
    save(a.state, st)
    print(msg)


if __name__ == "__main__":
    main()
