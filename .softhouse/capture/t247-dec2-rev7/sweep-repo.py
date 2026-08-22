#!/usr/bin/env python3
"""T247 REPO-WIDE sweep for restatements of the banner's false propositions.

P-70's last row is the reason this exists: DEC-2 §8.3's "no guard for either
exists" survived ONE FILE OVER in conformance.sh, and every sweep for it had
been scoped to the ADR. So this one is scoped to the whole tracked tree.

P-75: no `grep`, no `rg`. Population comes from `git ls-files -z` (a list, not a
walker), read as bytes in python. Calibrated on a known POSITIVE and a known
NEGATIVE before anything else is printed; if either arm misbehaves it exits 2.
Single pass over the population: every file is read once and tested against
every concept, so the printed population count IS the population inspected.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../../..")

# Concepts, not sentences (P-26). Each is a way of SAYING the banner's claim.
CONCEPTS = {
    "C1 nothing-grades-the-ledger": rb"(?i)nothing grades (this context|the ledger)|grades? none of them|no grading whatsoever|not one of them is currently checked",
    "C2 zero-ledger-vectors": rb"(?i)(no|zero) `?ledger`? vectors? (exist|is EXPRESSIBLE|are EXPRESSIBLE)|the `?ledger`? context has none",
    "C3 only-two-context-dirs": rb"(?i)(only|exactly two) context director(y|ies)|holds `?loanschedule/?`? and `?_selftest/?`?",
    "C4 no-ledger-PASS": rb"(?i)no such PASS|no `?ledger`? conformance PASS",
    "C5 A2-15-blocked": rb"(?i)A2-15[^\n]{0,80}(stays blocked|cannot start|cannot promote|is blocked)",
    "C6 nine-open-one-landed": rb"(?i)nine open, one landed|nine of the ten|Nine open",
}
RX = {k: re.compile(v) for k, v in CONCEPTS.items()}

# Files that are HISTORY or an independent REGISTER by construction: correcting
# them is out of T247's scope and, for handoffs/runs, would falsify the record.
HISTORY_HINT = ("/.softhouse/handoff/", "/.softhouse/runs/", "/.softhouse/patterns.md",
                "/.softhouse/gates.md", "/.softhouse/capture/", "/.softhouse/tasks.json",
                "/.softhouse/program.json")


def calibrate():
    ok = True
    p = os.path.join(ROOT, "docs/adr/DEC-2-gl-accounting-adapter.md")
    b = open(p, "rb").read()
    if not re.search(rb"NOTHING GRADES THIS CONTEXT", b):
        print("CALIBRATION FAIL: known positive absent", file=sys.stderr)
        ok = False
    if re.search(rb"ZZQQ-T247-KNOWN-NEGATIVE-NEEDLE", b):
        print("CALIBRATION FAIL: known negative present", file=sys.stderr)
        ok = False
    if re.search(rb"\bmain\b", b"bmainb"):
        print("CALIBRATION FAIL: fabricates on word boundary", file=sys.stderr)
        ok = False
    if not re.search(rb"\bmain\b", b"on main today"):
        print("CALIBRATION FAIL: misses a true word-boundary hit", file=sys.stderr)
        ok = False
    # every concept regex must compile AND match its own designed positive
    probes = {
        "C1 nothing-grades-the-ledger": b"NOTHING GRADES THE LEDGER",
        "C2 zero-ledger-vectors": b"Zero `ledger` vectors exist.",
        "C3 only-two-context-dirs": b"The store's only context directories are",
        "C4 no-ledger-PASS": b"Today there is no such PASS to misread.",
        "C5 A2-15-blocked": b"until then `A2-15` (promote GL vectors) stays blocked,",
        "C6 nine-open-one-landed": b"**Nine open, one landed.**",
    }
    for k, probe in probes.items():
        if not RX[k].search(probe):
            print("CALIBRATION FAIL: %s does not match its own probe" % k, file=sys.stderr)
            ok = False
        if RX[k].search(b"ZZQQ nothing here at all ZZQQ"):
            print("CALIBRATION FAIL: %s matched a known negative" % k, file=sys.stderr)
            ok = False
    return ok


def main():
    if not calibrate():
        return 2
    out = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"],
                         check=True, capture_output=True).stdout
    files = [f.decode() for f in out.split(b"\0") if f]
    print("CALIBRATION OK  (known positive found; known negative absent; no word-boundary")
    print("                fabrication; every concept matches its own probe and rejects a negative)")
    print("population = %d tracked file(s), from `git ls-files -z`, read ONCE each" % len(files))
    print("root = %s" % ROOT)
    hits = {k: {"live": [], "hist": []} for k in CONCEPTS}
    skipped_binary = 0
    skipped_unreadable = 0
    for rel in files:
        path = os.path.join(ROOT, rel)
        try:
            data = open(path, "rb").read()
        except (IsADirectoryError, FileNotFoundError, PermissionError, OSError):
            skipped_unreadable += 1
            continue
        if b"\0" in data[:8192]:
            skipped_binary += 1
            continue
        if not any(r.search(data) for r in RX.values()):
            continue
        bucket = "hist" if any(h in "/" + rel for h in HISTORY_HINT) else "live"
        for n, line in enumerate(data.split(b"\n"), 1):
            for k, r in RX.items():
                if r.search(line):
                    hits[k][bucket].append(
                        "%s:%d: %s" % (rel, n, line[:190].decode("utf-8", "replace")))
    print("skipped: %d binary, %d unreadable" % (skipped_binary, skipped_unreadable))
    for name in CONCEPTS:
        print("\n" + "=" * 10 + " " + name)
        live, hist = hits[name]["live"], hits[name]["hist"]
        print("  -- LIVE (in scope for a correction) %d" % len(live))
        for r in live:
            print("     " + r)
        print("  -- HISTORY / INDEPENDENT REGISTER (report only, NOT T247's to edit) %d" % len(hist))
        for r in hist[:15]:
            print("     " + r)
        if len(hist) > 15:
            print("     ... and %d more" % (len(hist) - 15))
    return 0


if __name__ == "__main__":
    sys.exit(main())
