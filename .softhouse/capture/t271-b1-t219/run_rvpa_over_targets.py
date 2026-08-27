#!/usr/bin/env python3
"""T271 -- run R-VPA over a COMMITTED TARGET LIST, so that adding a file to the rule's remit is an
edit to evidence and not a second contended edit to `.softhouse/conformance.sh`.

This is T268's recommendation, adopted by the driver, implemented and driven red/green here so
that T269 can install it rather than write it. **T271 does not install it**: `conformance.sh` is
held by a sibling this fire, and `t256-verdict-predicate/` is held by T268, so both the target
list and this runner sit in T271's own directory, read by nothing. T269 should move this file and
`targets-proposed-for-T269.json` into `t256-verdict-predicate/` and call this from the guard.

WHY IT MERGES THE ACKNOWLEDGEMENT REGISTERS INSTEAD OF ASKING FOR ONE FILE
    `check_verdict_predicate_agreement.py` takes a single `--acknowledgements` path. There are two
    registers and there must stay two: T259's is pinned to t229's bytes, T271's to t219's, and
    copying either into a shared file would create a second copy of a pinned record that must not
    drift (P-80). So this runner CONCATENATES their `acknowledgements` blocks into a scratch file
    that is never committed, and passes that. **The rule is not modified**, which is the whole
    point: it is being rewritten on another branch. As of T271 that rewrite (T268) has been
    REJECTED by T281 at `b4272ff` and the retry is T286, so the rule's `--acknowledgements`
    interface may still move. This runner depends on exactly one property of it -- a single
    `--acknowledgements` path and a `T259-VPA:` probe line carrying `files=` -- and refuses
    loudly if that property is absent, rather than assuming it.

FAIL-CLOSED, and each direction closes something specific:
    * a target named in the list that is not on disk is an ERROR (2), never a pass;
    * an acknowledgement file named in the list that is not on disk is an ERROR (2);
    * an EMPTY target list is a REFUSAL (1) -- a runner that inspects nothing passes everything;
    * if the rule reports fewer `files=` than the list names, that is a REFUSAL (1): the runner
      must not be able to report green over a file it silently failed to hand over;
    * the rule's own exit code is passed through unchanged, so 1 stays a measured refusal and 2
      stays an error (P-80).

PROBE LINE. The rule's own `T259-VPA:` line is printed verbatim, and this runner adds
    T271-TARGETS: <STATE> targets=.. inspected=.. ruleExit=..
as its last line. Test PRESENCE before VALUE (P-83).

EXIT: 0 green; 1 a real measured refusal; 2 error. Never conflated.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T271-TARGETS:"
VPA_RE = re.compile(r"^T259-VPA: (?P<state>\S+) .*?\bfiles=(?P<files>\d+)\b", re.M)


def repo_root(start: Path) -> Path:
    p = start
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise SystemExit(2)


def load_json(path: Path):
    return json.loads(path.read_text(), parse_float=Decimal)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="run R-VPA over a committed target list")
    ap.add_argument("--targets", default=str(HERE / "targets-proposed-for-T269.json"))
    ap.add_argument("--rule", default=None)
    args = ap.parse_args(argv)

    root = repo_root(HERE)
    rule = Path(args.rule) if args.rule else (
        root / ".softhouse" / "capture" / "t256-verdict-predicate"
        / "check_verdict_predicate_agreement.py")
    tpath = Path(args.targets)

    if not rule.exists():
        print(f"ERROR: the R-VPA rule is absent: {rule}", file=sys.stderr)
        return 2
    if not tpath.exists():
        print(f"ERROR: the target list is absent: {tpath}", file=sys.stderr)
        return 2
    try:
        doc = load_json(tpath)
        targets = doc["targets"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: target list unreadable: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    files, acks = [], []
    for t in targets:
        f = root / t["file"]
        if not f.exists():
            print(f"ERROR: target named in {tpath.name} is not on disk: {t['file']}",
                  file=sys.stderr)
            return 2
        files.append(f)
        for a in t.get("acknowledgements", []):
            ap_ = root / a
            if not ap_.exists():
                print(f"ERROR: acknowledgement register named in {tpath.name} is not on disk: {a}",
                      file=sys.stderr)
                return 2
            if ap_ not in acks:
                acks.append(ap_)

    print("T271 -- R-VPA over the committed target list")
    print("=" * 78)
    print(f"  target list : {tpath}")
    print(f"  rule        : {rule}")
    for t in targets:
        print(f"  target      : {t['file']}   (added by {t.get('addedBy', '?')})")
    for a in acks:
        print(f"  register    : {a.relative_to(root)}")
    print()

    if not files:
        print("  REFUSED: the target list names no file. A runner that inspects nothing passes")
        print("           everything.")
        print(f"{PROBE} REFUSED targets=0 inspected=0 ruleExit=-")
        return 1

    merged = {"_about": ["DERIVED, NEVER COMMITTED. Concatenation of the registers named in the "
                         "target list, built at run time so neither register is copied."],
              "acknowledgements": []}
    for a in acks:
        try:
            merged["acknowledgements"].extend(load_json(a).get("acknowledgements", []))
        except (OSError, ValueError) as exc:
            print(f"ERROR: register unreadable: {a}: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(merged, fh, default=str)
        merged_path = Path(fh.name)

    cmd = [sys.executable, str(rule), "--acknowledgements", str(merged_path)] + \
          [str(f) for f in files]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(root))
    merged_path.unlink()
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)

    m = VPA_RE.search(proc.stdout)
    if not m:
        print()
        print("  REFUSED: the rule printed NO probe line (exit "
              f"{proc.returncode}). It died before it measured, and an exit code alone cannot")
        print("           tell a refusal from a crash (P-83).")
        print(f"{PROBE} REFUSED targets={len(files)} inspected=? ruleExit={proc.returncode}")
        return 1 if proc.returncode == 1 else 2

    inspected = int(m.group("files"))
    print()
    if inspected != len(files):
        print(f"  REFUSED: the list names {len(files)} file(s), the rule inspected {inspected}.")
        print("           A green over a file that was never handed over is the defect this whole")
        print("           instrument exists to refuse.")
        print(f"{PROBE} REFUSED targets={len(files)} inspected={inspected} "
              f"ruleExit={proc.returncode}")
        return 1

    state = {0: "GREEN", 1: "REFUSED"}.get(proc.returncode, "ERROR")
    print(f"{PROBE} {state} targets={len(files)} inspected={inspected} "
          f"ruleExit={proc.returncode}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
