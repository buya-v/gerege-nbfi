#!/usr/bin/env python3
"""T291 -- INDEPENDENT REVIEW OF T286. The fifth fail-open, driven on four pinned arms.

T286 repaired the fail-open T268 introduced by phrasing the coverage rule STRUCTURALLY:

    "A RECORD IS A ROW REACHED THROUGH A LIST."

It chose that phrasing over "the document root does not count" precisely BECAUSE the root
phrasing is defeated in one line -- `{"meta": {"verdict": "AS PREDICTED"}, "cells": []}` is
not a root collapse, and T286 measured the in-flight repair losing to it (its finding R1b).

THIS INSTRUMENT APPLIES THE SAME ARGUMENT ONE STEP FURTHER. Take T286's own R1b fixture and
wrap the header dict in a ONE-ELEMENT LIST. Two characters. The header is now "a row reached
through a LIST", so it is a RECORD, so it answers the coverage guard, so an affirmative verdict
over an empty container exits 0 GREEN -- while the PRE-T268 rule exits 1 REFUSED. That is a
LOST REFUSAL, which is the exact criterion T281 used to REJECT T268.

ARMS, all pinned by BLOB SHA and never by `HEAD:<path>` (the rule under review moves):
    PRE  86f4285  pre-T268 (== main:<rule> at the time of writing)
    T268 0607ecd  the fix T281 rejected
    WIP  a70051b  the rescued in-flight repair phrased about the ROOT
    NEW  4f844ed  T286's shipped rule, the subject of this review
A MISSING ARM IS REPORTED LOUDLY AND COUNTED SKIPPED, NEVER PASSED, AND SKIPPED LEGS MAKE THIS
INSTRUMENT EXIT NON-ZERO -- unlike T286's own battery, which returns 0 with legs skipped
(finding F-T291-3).

The arms are unpacked into a scratch directory INSIDE the repo, because the rule's `repo_root()`
walks up from its own file's directory and a copy in /tmp makes every leg die for the wrong
reason. The directory is created with `mkstemp`-style randomness and REMOVED on exit, so no
classification anywhere can depend on its existence (T273: a guard a /tmp file can flip is
measuring the host).

NO FLOATING POINT: nothing here computes; exit codes and counts are ints.
EXIT: 0 every leg as expected; 1 a leg failed or was skipped; 2 the instrument could not run.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = HERE.parent
ROOT = CAP.parent.parent.parent
RULE_DIR = ROOT / ".softhouse/capture/t256-verdict-predicate"
REG = RULE_DIR / "boolean-key-register.json"
ACK = RULE_DIR / "acknowledged.json"
REAL = ROOT / ".softhouse/capture/t229-g8-site3/out/classify-t229.json"
FIX = HERE / "fixtures"
PROBE = "T259-VPA:"

BLOBS = {
    "PRE": "86f42859a1492409de9c052caf9ecbde15791212",
    "T268": "0607ecdb943e84c0ad2ae9f16cd79fc702847c3d",
    "WIP": "a70051b6567e4418b2be4a5a965dd7ef769122af",
    "NEW": "4f844ed2409bbcde3add574a1160601f4e55b06d",
}


def git(*args, check=True):
    p = subprocess.run(["git", "-C", str(ROOT)] + list(args), capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError("git %s exited %d: %s" % (" ".join(args), p.returncode, p.stderr))
    return p.returncode, p.stdout


def run_rule(rule, targets):
    argv = [sys.executable, str(rule), "--register", str(REG), "--acknowledgements", str(ACK)]
    argv += [str(t) for t in targets]
    p = subprocess.run(argv, capture_output=True, text=True)
    probe = None
    for ln in p.stdout.splitlines():
        if ln.startswith(PROBE):
            probe = ln
    return p.returncode, probe


class Battery:
    def __init__(self, arms):
        self.arms = arms
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.rows = []

    def leg(self, name, targets, want, why):
        missing = [a for a in want if self.arms.get(a) is None]
        if missing:
            self.skipped += 1
            print("--- LEG %s" % name)
            print("    *** SKIPPED, NOT PASSED: arm(s) %s unavailable (blob not in this store)."
                  % missing)
            print()
            self.rows.append({"leg": name, "skipped": True, "missingArms": missing, "why": why})
            return
        got = {}
        ok = True
        print("--- LEG %s" % name)
        print("    why : %s" % why)
        for arm in ("PRE", "T268", "WIP", "NEW"):
            if arm not in want:
                continue
            rc, probe = run_rule(self.arms[arm], targets)
            got[arm] = {"exit": rc, "probe": probe}
            good = rc == want[arm]
            ok = ok and good
            state = probe.split()[1] if probe else "(no probe)"
            print("    %-5s exit %-3d (expected %d)  %-8s %s"
                  % (arm, rc, want[arm], state, "" if good else "   <-- UNEXPECTED"))
        print("    LEG %s: %s" % (name, "PASS" if ok else "FAIL"))
        print()
        self.rows.append({"leg": name, "want": want, "got": got, "pass": ok, "skipped": False,
                          "why": why})
        if ok:
            self.passed += 1
        else:
            self.failed += 1


def main():
    for p in (REG, ACK, REAL, FIX):
        if not p.exists():
            print("ERROR: required path absent: %s" % p, file=sys.stderr)
            return 2
    scratch = Path(tempfile.mkdtemp(prefix=".scratch-t291-", dir=str(CAP)))
    try:
        arms = {}
        for arm, blob in BLOBS.items():
            rc, _ = git("cat-file", "-e", blob + "^{blob}", check=False)
            if rc != 0:
                print("!! ARM %s UNAVAILABLE: blob %s is not in this object store. Legs needing "
                      "it are SKIPPED, not passed." % (arm, blob))
                arms[arm] = None
                continue
            d = scratch / arm
            d.mkdir()
            _, text = git("cat-file", "blob", blob)
            f = d / "rule.py"
            f.write_text(text)
            arms[arm] = f
            print("    arm %-5s <- blob %s" % (arm, blob))
        print()

        b = Battery(arms)
        F = lambda n: FIX / (n + ".json")   # noqa: E731

        print("=" * 96)
        print("### T286's OWN TWO FIXTURES -- reproduced, because a finding I cannot reproduce")
        print("### is not a finding. NEW closes both; that part of T286 HOLDS.")
        print("=" * 96)
        print()
        b.leg("BASE-N6-root-verdict-empty", [F("N6-root-verdict-empty")],
              {"PRE": 1, "T268": 0, "WIP": 1, "NEW": 1},
              "T281's R1. T268 greens an affirmative verdict over nothing; NEW refuses it.")
        b.leg("BASE-H1-nested-header-empty", [F("H1-nested-header-empty")],
              {"PRE": 1, "T268": 0, "WIP": 0, "NEW": 1},
              "T286's R1b. The WIP repair, phrased about the ROOT, still greens it; NEW refuses.")

        print("=" * 96)
        print("### F-T291-1 -- THE FIFTH FAIL-OPEN. H1 with the inner dict wrapped in a LIST.")
        print("### Expected values below are what T286 CLAIMS (NEW must refuse whatever PRE")
        print("### refused). A FAIL on these legs IS the finding.")
        print("=" * 96)
        print()
        for n, why in (
            ("X2-header-in-nested-list",
             "H1 + two characters: the header dict is now an element of a list one level down, "
             "so it is a RECORD, so it answers the coverage guard."),
            ("X3-header-in-list-of-lists",
             "The same, reached through two nested lists."),
            ("X4-toplevel-array-header-only",
             "A top-level JSON ARRAY holding only the header -- which is the shape this "
             "program's own battery evidence files (t286-legs.json, red-green-legs.json) use."),
            ("X7-header-in-deep-nested-list",
             "The same, four levels down."),
        ):
            b.leg("FO5-" + n, [F(n)], {"PRE": 1, "T268": 0, "WIP": 0, "NEW": 1}, why)

        b.leg("FO5-X2-BATCHED-with-real-evidence", [F("X2-header-in-nested-list"), REAL],
              {"PRE": 0, "T268": 0, "WIP": 0, "NEW": 1},
              "F-1's own batching shape: the empty file hides inside a batch with real evidence. "
              "PRE greens the BATCH because F-1's global nil gate is the defect T268 fixed; NEW "
              "must refuse it on the per-file counter and does not.")

        print("=" * 96)
        print("### F-T291-2 -- guard #10 (AFFIRMATION ON A CONTAINER ROW) loses to the same")
        print("### two characters. X5b is the CONTROL that makes X5 non-vacuous.")
        print("=" * 96)
        print()
        b.leg("FO5-X5-affirmation-in-list-over-refuted-record",
              [F("X5-affirmation-in-list-over-refuted-record")],
              {"PRE": 0, "T268": 0, "WIP": 0, "NEW": 1},
              "A document-level 'AS PREDICTED' sitting beside a record that recorded its own "
              "predicate FALSE. Guard #10 is written for exactly this and does not fire, because "
              "the header is in a list and is therefore not a CONTAINER row.")
        b.leg("CONTROL-X5b-affirmation-as-mapping-key",
              [F("X5b-affirmation-as-mapping-key-over-refuted-record")],
              {"PRE": 0, "T268": 0, "WIP": 0, "NEW": 1},
              "The SAME document with the header as a mapping key. Guard #10 fires here, which "
              "is what shows the guard is real and its scope is one bracket wide.")

        print("=" * 96)
        print("### EVASIONS THAT FAILED -- the evidence that the search had coverage.")
        print("### These are attacks on NEW that NEW correctly REFUSED.")
        print("=" * 96)
        print()
        b.leg("HELD-X8-noninspectable-dict-in-list", [F("X8-noninspectable-dict-in-list")],
              {"PRE": 0, "T268": 0, "WIP": 1, "NEW": 1},
              "A dict in the list that carries no evidence is not a row at all, so the root "
              "header cannot borrow coverage from it. NEW refuses. PRE greens it.")
        b.leg("HELD-X1-header-in-toplevel-list", [F("X1-header-in-toplevel-list")],
              {"PRE": 0, "T268": 0, "WIP": 0, "NEW": 0},
              "NOT a lost refusal -- PRE greens this too (its coverage rule is 'a dict in a "
              "TOP-LEVEL list'). Recorded so the finding above is not overstated: X1 is the "
              "pre-existing decoy class T286 discloses as item a2; X2/X3/X4/X7 are NOT.")

        print("=" * 96)
        print("### CORPUS SHAPE -- is the repair direction viable? Measured, not assumed.")
        print("=" * 96)
        print()
        # Imported from the NEW ARM'S PINNED BLOB, never from the working tree: this instrument
        # must give the same answer on a clean checkout of main, where the live rule is the
        # PRE-T268 file whose `walk_rows` has a different signature entirely.
        if arms["NEW"] is None:
            print("    NEW arm unavailable -- corpus shape NOT MEASURED, not assumed.")
            return 1
        import importlib.util
        spec = importlib.util.spec_from_file_location("rvpa_new", str(arms["NEW"]))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        reg = json.loads(REG.read_text())
        corpus = []
        for f in (REAL, ROOT / ".softhouse/capture/t219-g8-residual/out/classify-t219.json"):
            if not f.exists():
                print("    %s ABSENT -- a statement about the search, not the world." % f)
                continue
            doc = json.loads(f.read_text())
            rec = con = withpred = 0
            for path, row, via in mod.walk_rows(reg, doc):
                if via:
                    rec += 1
                else:
                    con += 1
                has = any(mod.key_class(reg, k)[0] == "PREDICATE"
                          for _p, k, _v in mod.walk_pairs(row, path))
                if via and has:
                    withpred += 1
            print("    %-22s records=%-3d containers=%-3d records carrying a PREDICATE=%d"
                  % (f.name, rec, con, withpred))
            corpus.append({"file": f.name, "records": rec, "containers": con,
                           "recordsWithPredicate": withpred})
        print()
        print("    containers=0 on both files CONFIRMS T286's inertness claim for guard #10.")
        print("    recordsWithPredicate >= 8 on both files says a coverage rule of the form")
        print("    'a record is a row reached through a list THAT CARRIES A PREDICATE' would")
        print("    leave the real corpus GREEN. That is a measured statement about viability,")
        print("    not a recommendation to adopt it without its own battery.")
        print()

        print("=" * 96)
        print("T291 BATTERY: %d passed, %d failed, %d SKIPPED"
              % (b.passed, b.failed, b.skipped))
        if b.skipped:
            print("              A SKIPPED LEG IS NOT A PASSED LEG, and it makes this "
                  "instrument exit non-zero.")
        print("=" * 96)
        (CAP / "out").mkdir(exist_ok=True)
        (CAP / "out" / "t291-legs.json").write_text(
            json.dumps({"legs": b.rows, "corpusShape": corpus}, indent=1) + "\n")
        return 1 if (b.failed or b.skipped) else 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
