#!/usr/bin/env python3
"""asset_name_checker.py — keep the project's files findable: names, versions, and what may be delivered.

Naming standard (the default; change it with --pattern): {SIGLA}_{Name}_V{NN}_{DDMMAA}
  example  SFI_Guidelines_V03_151026.pdf      final form: {SIGLA}_{Name}_Final_{DDMMAA}

Input is a manifest of files with a status: [{"path": "Marca/Exportados/SFI_Logo_V02_101026.svg", "status": "approved"}].

Rules:
  EXPORT_NOT_APPROVED  BLOCK  a file under a folder named Exportados is not approved (Exportados is the final delivery to the client)
  BAD_NAME             WARN   the file name does not match the pattern
  BAD_DATE             WARN   the DDMMAA part is not a real date
  DUPLICATE_VERSION    WARN   two files share name and version
  VERSION_GAP          WARN   V01 and V03 exist with no V02 for the same name
  TEMP_MARKER          WARN   (1), copy, copia, final_final, novo, ~, .tmp in the name
  WRONG_SIGLA          WARN   the name starts with a different project code

Exit codes: 0 CLEAN | 1 input error | 2 WARNINGS | 4 BLOCKED
Stdlib only. No network. Deterministic.
"""

import argparse
import collections
import datetime
import json
import os
import re
import sys

TEMP = re.compile(r"\(\d+\)|copy|copia|cópia|final_final|\bnovo\b|~|\.tmp$", re.I)


def pattern(sigla):
    s = re.escape(sigla)
    return (re.compile(rf"^{s}_(?P<name>[A-Za-z0-9\-]+)_V(?P<v>\d{{2}})_(?P<d>\d{{6}})(?:\.[A-Za-z0-9]+)?$"),
            re.compile(rf"^{s}_(?P<name>[A-Za-z0-9\-]+)_Final_(?P<d>\d{{6}})(?:\.[A-Za-z0-9]+)?$"))


def check(files, sigla):
    ver, fin = pattern(sigla)
    out, seen = [], collections.defaultdict(list)
    add = lambda lvl, code, p, msg: out.append({"level": lvl, "code": code, "path": p, "message": msg})
    for f in files:
        p, st = f["path"], f.get("status", "")
        base = os.path.basename(p)
        if "exportados" in [x.lower() for x in p.replace("\\", "/").split("/")[:-1]] and st != "approved":
            add("BLOCK", "EXPORT_NOT_APPROVED", p, f"status is '{st or 'none'}'; only approved files go to Exportados")
        if TEMP.search(base):
            add("WARN", "TEMP_MARKER", p, "looks like a copy or temporary file")
        m = ver.match(base) or fin.match(base)
        if not m:
            if re.match(r"^[A-Z]{2,5}_", base) and not base.startswith(sigla + "_"):
                add("WARN", "WRONG_SIGLA", p, f"does not start with {sigla}_")
            else:
                add("WARN", "BAD_NAME", p, f"expected {sigla}_Name_VNN_DDMMAA or {sigla}_Name_Final_DDMMAA")
            continue
        d = m.group("d")
        try:
            datetime.date(2000 + int(d[4:6]), int(d[2:4]), int(d[0:2]))
        except ValueError:
            add("WARN", "BAD_DATE", p, f"'{d}' is not a valid DDMMAA date")
        if "v" in m.groupdict() and m.group("v"):
            seen[m.group("name")].append((int(m.group("v")), p))
    for name, items in seen.items():
        nums = [n for n, _ in items]
        for n in sorted({x for x in nums if nums.count(x) > 1}):
            add("WARN", "DUPLICATE_VERSION", name, f"V{n:02d} appears {nums.count(n)} times")
        top = max(nums)
        missing = [n for n in range(1, top) if n not in nums]
        if missing:
            add("WARN", "VERSION_GAP", name, "missing " + ", ".join(f"V{n:02d}" for n in missing))
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Check file names, versions and delivery status of project assets.")
    ap.add_argument("--input", help="manifest JSON list of {path, status}")
    ap.add_argument("--sigla", default="SFI", help="project code (default SFI)")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_manifest.json") if a.sample else a.input
    if not path:
        ap.error("provide --input or --sample")
    try:
        with open(path, encoding="utf-8") as fh:
            files = json.load(fh)
        if not isinstance(files, list):
            raise ValueError("manifest must be a JSON list")
        res = check(files, a.sigla.upper())
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    code = 4 if any(r["level"] == "BLOCK" for r in res) else (2 if res else 0)
    verdict = {0: "CLEAN", 2: "WARNINGS", 4: "BLOCKED"}[code]
    if a.output == "json":
        print(json.dumps({"verdict": verdict, "findings": res}, indent=2, ensure_ascii=False))
    else:
        print(f"Verdict: {verdict}   files: {len(files)}   findings: {len(res)}")
        for r in res:
            print(f"  [{r['level']}] {r['code']}: {r['path']} :: {r['message']}")
    sys.exit(code)


if __name__ == "__main__":
    main()
