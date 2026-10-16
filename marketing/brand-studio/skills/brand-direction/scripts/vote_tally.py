#!/usr/bin/env python3
"""vote_tally.py — turn a shapes-dynamic vote into a verdict, without letting noise decide.

In a shapes dynamic the client reacts to 20-30 items (roughs, drafts, market references, inspirations)
and says what each shape means to them. The value is in the output: one clear direction for the team
that finalises the mark. This tool counts the votes and refuses to over-read them.

Scale (editable with --scale): no = -1, maybe = 0, yes = +1, favorite = +3. At most one favorite per voter.
Votes are weighted by voter weight (default 1).

Rules:
  BAD_ITEM        BLOCK  an item has no visible type (rough, draft, market_ref, inspiration)
  TWO_FAVORITES   BLOCK  a voter marked more than one favorite
  UNKNOWN_VOTE    BLOCK  a vote or item id that does not exist
  VETADO_WINS     BLOCK  with --state: the leading item matches a locked vetado (non-leading matches are flagged in the notes)
  COUNT_MISMATCH  BLOCK  the two independent counts disagree (counted twice, as the process demands)
  QUORUM          exit 3 fewer than the required voters voted on at least 80% of the items; no verdict is given
Verdict:
  NEW_DIRECTION  the top score is zero or below: the candidates do not work
  GREEN_LIGHT    the top item leads the second by the margin (default 2.0) and is a rough or a draft
  ADJUST         anything else, including when a market reference or an inspiration leads: translate its quality,
                 never present the reference as the proposal

Also prints the finalisation brief skeleton: keep, add (with the client's words), eliminate, must convey.

Exit codes: 0 verdict given | 1 input error | 3 no quorum | 4 blocked
Stdlib only. No network. Deterministic.
"""

import argparse
import collections
import json
import os
import re
import sys

TYPES = ("rough", "draft", "market_ref", "inspiration")
SCALE = {"no": -1.0, "maybe": 0.0, "yes": 1.0, "favorite": 3.0}
STOP = {"para", "como", "mais", "muito", "isso", "that", "this", "with", "feels", "very", "uma", "dele", "dela"}


GENERIC = {"symbol", "literal", "category", "mark", "brand", "pack", "field", "cliche", "logo", "shape", "form", "pictorial"}


def vetado_hits(items, vetados):
    """Items whose path or meaning shares a distinctive word (5+ letters) with a locked vetado."""
    def toks(t):
        return {w for w in re.findall(r"[a-z\u00e0-\u00ff]{5,}", t.lower())} - GENERIC
    out = {}
    for i in items.values():
        it = toks(i.get("path", "") + " " + " ".join(i.get("meaning", [])))
        for v in vetados:
            if it & toks(v):
                out[i["id"]] = v
    return out


def tally(data, scale, margin, quorum, vetados=()):
    items = {i["id"]: i for i in data["items"]}
    voters = data["voters"]
    blocks = []
    for i in items.values():
        if i.get("type") not in TYPES:
            blocks.append(("BAD_ITEM", f"{i['id']} has no visible type (use {', '.join(TYPES)})"))
    covered = 0
    for v in voters:
        votes = v.get("votes", {})
        unknown = [k for k in votes if k not in items]
        if unknown:
            blocks.append(("UNKNOWN_VOTE", f"{v['name']} voted on unknown item(s): {', '.join(unknown)}"))
        bad = [k for k, x in votes.items() if x not in scale]
        if bad:
            blocks.append(("UNKNOWN_VOTE", f"{v['name']} used a vote not in the scale for: {', '.join(bad)}"))
        if sum(1 for x in votes.values() if x == "favorite") > 1:
            blocks.append(("TWO_FAVORITES", f"{v['name']} marked more than one favorite"))
        if len(votes) >= 0.8 * len(items):
            covered += 1
    if blocks:
        return {"blocks": blocks}
    # count one: voter by voter
    by_voter = collections.Counter()
    for v in voters:
        for iid, x in v.get("votes", {}).items():
            by_voter[iid] += scale[x] * v.get("weight", 1)
    # count two: item by item, an independent traversal
    by_item = {}
    for iid in items:
        by_item[iid] = sum(scale[v["votes"][iid]] * v.get("weight", 1) for v in voters if iid in v.get("votes", {}))
    if any(abs(by_voter[i] - by_item[i]) > 1e-9 for i in items):
        return {"blocks": [("COUNT_MISMATCH", "the two independent counts disagree; recount by hand")]}
    need = quorum if quorum is not None else len(voters)
    if covered < need:
        return {"no_quorum": f"{covered} of {need} required voters covered 80% of the items"}
    ranking = sorted(items, key=lambda i: (-by_item[i], i))
    hits = vetado_hits(items, vetados)
    if ranking[0] in hits:
        return {"blocks": [("VETADO_WINS", f"{ranking[0]} leads the vote but matches a locked vetado: '{hits[ranking[0]]}'. "
                                           "A vetado is a path we will not take; remove it and re-run the round")]}
    top, second = ranking[0], (ranking[1] if len(ranking) > 1 else None)
    lead = by_item[top] - (by_item[second] if second else 0)
    ttype = items[top].get("type")
    if by_item[top] <= 0:
        verdict = "NEW_DIRECTION"
    elif lead >= margin and ttype in ("rough", "draft"):
        verdict = "GREEN_LIGHT"
    else:
        verdict = "ADJUST"
    notes = [f"{i} matches a locked vetado ('{v}'): remove it from the batch before the next round" for i, v in hits.items()]
    if ttype in ("market_ref", "inspiration"):
        notes.append(f"{top} is a {ttype}, not a proposal: translate what the client liked in it, do not copy it")
    split = [i for i in items if any(v.get("votes", {}).get(i) == "no" for v in voters) and any(v.get("votes", {}).get(i) in ("yes", "favorite") for v in voters)]
    words = collections.Counter(w for i in ranking[:3] for w in re.findall(r"[a-zà-ÿ]{4,}", " ".join(items[i].get("meaning", [])).lower()) if w not in STOP)
    return {
        "verdict": verdict, "scores": {i: by_item[i] for i in ranking}, "top": top, "lead": lead, "notes": notes,
        "decisors_split_on": split,
        "finalisation_brief": {
            "verdict_in_one_sentence": f"{verdict}: {top} leads with {by_item[top]:g} points ({lead:g} ahead).",
            "keep": [top],
            "add": [{"item": i, "from": [v["name"] for v in voters if v.get("votes", {}).get(i) == "favorite"],
                     "contested_by": [v["name"] for v in voters if v.get("votes", {}).get(i) == "no"],
                     "client_words": items[i].get("meaning", [])}
                    for i in ranking[1:] if any(v.get("votes", {}).get(i) == "favorite" for v in voters)],
            "eliminate": [i for i in items if by_item[i] < 0],
            "must_convey": [w for w, _ in words.most_common(6)]}}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Tally a shapes-dynamic vote into a verdict.")
    ap.add_argument("--input", help="votes JSON (see assets/example_votes.json)")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--margin", type=float, default=2.0, help="points the top item must lead by for GREEN_LIGHT")
    ap.add_argument("--state", help="brand-state.json: items matching a locked vetado are flagged, and block if they win")
    ap.add_argument("--quorum", type=int, help="voters required to cover 80%% of the items (default: all voters)")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_votes.json") if a.sample else a.input
    if not path:
        ap.error("provide --input or --sample")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        vet = []
        if a.state:
            with open(a.state, encoding="utf-8") as sf:
                vet = [x["text"] for x in json.load(sf)["fio"]["vetados"]]
        r = tally(data, SCALE, a.margin, a.quorum, vet)
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if "blocks" in r:
        print("BLOCKED:\n  " + "\n  ".join(f"{c}: {m}" for c, m in r["blocks"]))
        sys.exit(4)
    if "no_quorum" in r:
        print(f"NO QUORUM: {r['no_quorum']}. No verdict is given.")
        sys.exit(3)
    if a.output == "json":
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print(f"Verdict: {r['verdict']}   top: {r['top']}   lead: {r['lead']:g}")
        print("Scores: " + ", ".join(f"{k} {v:g}" for k, v in r["scores"].items()))
        for n in r["notes"]:
            print("  NOTE: " + n)
        if r["decisors_split_on"]:
            print("  Decisors split (yes vs no) on: " + ", ".join(r["decisors_split_on"]))
        b = r["finalisation_brief"]
        print("Finalisation brief:\n  " + b["verdict_in_one_sentence"])
        print("  keep: " + ", ".join(b["keep"]))
        for x in b["add"]:
            print(f"  add: {x['item']} (favorite of {', '.join(x['from'])}"
                  + (f"; CONTESTED by {', '.join(x['contested_by'])}" if x["contested_by"] else "")
                  + f"); client words: {', '.join(x['client_words'])}")
        print("  eliminate: " + (", ".join(b["eliminate"]) or "none"))
        print("  must convey: " + ", ".join(b["must_convey"]))
    sys.exit(0)


if __name__ == "__main__":
    main()
