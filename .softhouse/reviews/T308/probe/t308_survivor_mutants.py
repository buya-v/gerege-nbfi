#!/usr/bin/env python3
"""T308 -- ATTACK THE CALIBRATION.  Plant defects T292 DID NOT PLANT and run T292's OWN
adversary, unmodified, against each.

T292's calibration argument is: "plant the lineage's defect and the same counter reports 28
across 12 fixtures, so `LOST REFUSALS: 0` is a measurement."  The brief's question is whether
the counter is sensitive to the RIGHT thing -- a counter can be sensitive to the planted
defect and blind to a different one.

Every mutant here re-introduces T259's FOUNDING defect shape -- **the refusal is PRINTED in
the body and the exit code stays GREEN** -- at a guard T292 did not mutate.  T292's own
mutant suite (probe/mutants_t292.py) plants 8 kill targets, and every one of them attacks
either COVERAGE (M1/M2/M3), READ INTEGRITY (M4/M5/M10/M6), the EXIT PROTOCOL (M7) or
DETECTION BREADTH (M9).  Not one of them attacks the GATE -- the disjunction in `main` that
turns counted refusals into exit 1.

A mutant that SURVIVES here is a hole in the adversary, and therefore a zero the headline
number cannot see.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent.parent          # repo root
CAP = ROOT / ".softhouse" / "capture" / "t286-t268-retry"
RULE = CAP / "check_verdict_predicate_agreement_t292.py"
ADV = CAP / "probe" / "adversary_t292.py"
T256 = ROOT / ".softhouse" / "capture" / "t256-verdict-predicate"

# (id, why, [(find, replace)], expected)
MUTANTS = [
    ("N1-unacknowledged-disagreement-printed-but-not-COUNTED",
     "T259's FOUNDING defect, one guard over: the body prints 'NO ACKNOWLEDGEMENT ... do not "
     "summarise past it' and the process exits 0 GREEN. The witness is non-empty, so the "
     "post-condition cannot see it and PROP-C reclassifies it as an adjudicated WIDENING.",
     [("                    rep.unacknowledged += 1\n", "\n")]),

    ("N2-mute-refutation-G6-printed-but-not-COUNTED",
     "Same shape at G6: a refuted record with no readable disposition prints REFUSED and the "
     "run exits GREEN.",
     [("        if false_predicates and not vclasses:\n            rep.mute_refutations += 1",
       "        if false_predicates and not vclasses:\n            pass")]),

    ("N3-void-acknowledgement-printed-but-not-COUNTED",
     "Same shape at G4: the acknowledgement block is void (evidence edited after it was "
     "written), the body says so, the exit code says GREEN. T114/T176.",
     [("            rep.void_acks += 1\n", "\n")]),

    ("N4-unclassified-verdict-word-printed-but-not-COUNTED",
     "Same shape at G1.",
     [("                rep.unclassified_verdicts += 1\n", "\n")]),

    ("N5-unclassified-boolean-key-printed-but-not-COUNTED",
     "Same shape at G2 -- the guard T259 exists for.",
     [("                rep.unclassified_keys += 1\n", "\n")]),

    ("N6-CONTROL-gate-drops-nil-coverage--EXPECTED-KILLED",
     "POSITIVE CONTROL. Dropping `nil` from the same disjunction IS covered, because the "
     "post-condition independently re-checks nil_files. If this survives the harness is broken.",
     [("    refused = bool(rep.unacknowledged or rep.unclassified_keys "
       "or rep.unclassified_verdicts\n                   or rep.void_acks "
       "or rep.mute_refutations or nil)",
       "    refused = bool(rep.unacknowledged or rep.unclassified_keys "
       "or rep.unclassified_verdicts\n                   or rep.void_acks "
       "or rep.mute_refutations)")]),
]

# EVERY mutant here is a KILL TARGET.  A survivor is a HOLE in T292's adversary, so this probe
# exits NON-ZERO when one survives -- fail-closed.  (Pass 1 of this probe expressed the same
# result with the exit code inverted, because the author had PREDICTED the survivals and wrote
# the prediction into the gate.  A gate that passes when the defect is present is the lineage's
# own founding shape; recorded in out/t308-survivor-mutants-pass1.txt rather than tidied away.)
KILL_TARGETS = {"N1", "N2", "N3", "N4", "N5", "N6"}

# One executable reproduction per mutant: a document the SHIPPED rule refuses.
DEMOS = {
    "N1": {"cells": [{"id": "c1", "P2_x": False, "verdict": "AS PREDICTED"}]},
    "N2": {"cells": [{"id": "c1", "P2_x": False, "conclusion": "everything is fine"}]},
    "N3": None,     # a VOID ack needs the ack'd path AND different bytes; not reproduced here
    "N4": {"cells": [{"id": "c1", "P2_x": True, "verdict": "WOBBLY"}]},
    "N5": {"cells": [{"id": "c1", "P2_x": True, "someBool": True,
                      "verdict": "AS PREDICTED"}]},
    "N6": {"cells": []},
}


def build(mid, edits, tmp):
    src = RULE.read_text(encoding="utf-8")
    for find, repl in edits:
        n = src.count(find)
        if n != 1:
            raise SystemExit("ERROR: mutant %s anchor occurs %d times, expected exactly 1:\n%r"
                             % (mid, n, find[:160]))
        src = src.replace(find, repl)
    p = tmp / (mid + ".py")
    p.write_text(src, encoding="utf-8")
    return p


def viable(rule):
    """A mutant must still MEASURE: probe line present on the real committed evidence."""
    real = ROOT / ".softhouse" / "capture" / "t229-g8-site3" / "out" / "classify-t229.json"
    r = subprocess.run([sys.executable, str(rule),
                        "--register", str(T256 / "boolean-key-register.json"),
                        "--acknowledgements", str(T256 / "acknowledged.json"), str(real)],
                       capture_output=True, text=True, timeout=120)
    probe = [l for l in r.stdout.splitlines() if l.startswith("T259-VPA:")]
    return bool(probe), r.returncode


def demonstrate(rule, doc, tmp, name):
    """Drive ONE document through a rule and return (rc, probe, body_says_refused)."""
    p = tmp / (name + ".json")
    p.write_text(json.dumps(doc), encoding="utf-8")
    r = subprocess.run([sys.executable, str(rule),
                        "--register", str(T256 / "boolean-key-register.json"),
                        "--acknowledgements", str(T256 / "acknowledged.json"), str(p)],
                       capture_output=True, text=True, timeout=120)
    probe = [l for l in r.stdout.splitlines() if l.startswith("T259-VPA:")]
    return r.returncode, (probe[-1] if probe else None), ("REFUSED " in r.stdout)


A10 = {"cells": [{"id": "c1", "P2_x": False, "verdict": "AS PREDICTED"}]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix=".t308-mut-", dir=str(HERE.parent)))
    rows = []
    try:
        print("T308 -- MUTANTS T292 DID NOT PLANT, GRADED BY T292'S OWN UNMODIFIED ADVERSARY")
        print("=" * 96)
        print("  rule     %s" % RULE.name)
        print("  adversary %s (unmodified), --seeds %d" % (ADV.name, args.seeds))
        print()
        # baseline: the shipped rule on A10
        rc, probe, said = demonstrate(RULE, A10, tmp, "A10-baseline")
        print("  BASELINE shipped rule on A10 (genuine unacknowledged disagreement):")
        print("     rc=%s body-prints-REFUSED=%s" % (rc, said))
        print("     %s" % probe)
        print()
        for mid, why, edits in MUTANTS:
            mp = build(mid, edits, tmp)
            ok_probe, vrc = viable(mp)
            if not ok_probe:
                rows.append((mid, "NON-VIABLE", "", why))
                print("  NON-VIABLE %s (rc=%s on the real evidence)" % (mid, vrc))
                continue
            r = subprocess.run([sys.executable, str(ADV), "--rule", str(mp),
                                "--seeds", str(args.seeds),
                                "--legs-out", str(tmp / (mid + "-legs.json"))],
                               capture_output=True, text=True, timeout=3600)
            killed = r.returncode != 0
            legs = json.loads((tmp / (mid + "-legs.json")).read_text(encoding="utf-8"))
            lost = len(legs["lost_refusals"])
            widen = len(legs["widenings"])
            failed = [l for l in legs["legs"] if not l["ok"] and not l["skipped"]]
            demo = DEMOS.get(mid.split("-")[0])
            if demo is None:
                srepr = mrepr = "(no reproduction document for this guard)"
                mrc = msaid = "-"
            else:
                src, sprobe, ssaid = demonstrate(RULE, demo, tmp, mid + "-demo-shipped")
                mrc, mprobe, msaid = demonstrate(mp, demo, tmp, mid + "-demo-mutant")
                srepr = "SHIPPED rc=%s body-prints-REFUSED=%s" % (src, ssaid)
                mrepr = "MUTANT  rc=%s body-prints-REFUSED=%s" % (mrc, msaid)
            rows.append((mid, "KILLED" if killed else "SURVIVED",
                         "lost=%d widenings=%d failing-legs=%d | %s vs %s"
                         % (lost, widen, len(failed), srepr, mrepr), why))
            print("  %-9s %-58s adversary exit %d" % ("KILLED" if killed else "SURVIVED",
                                                      mid, r.returncode))
            print("            LOST REFUSALS: %d   ADJUDICATED WIDENINGS: %d   failing legs: %d"
                  % (lost, widen, len(failed)))
            # LABEL THE DOCUMENT THAT WAS ACTUALLY DRIVEN. Pass 2 of this probe printed
            # "A10 driven through the mutant" beside a number produced by the PER-GUARD demo
            # document, because the label was left behind when the demo table was added. A
            # mislabelled cardinal is the defect this whole directory is about; fixed, and the
            # pass-2 transcript is kept at out/t308-survivor-mutants-pass2-stale-label.txt.
            print("            reproduction %-22s SHIPPED %s | MUTANT   %s"
                  % (mid.split("-")[0], srepr, mrepr))
            if demo is not None and mprobe:
                print("            %s" % mprobe)
            for l in failed[:4]:
                print("              FAILED [%s] %s -- %s" % (l["prop"], l["name"],
                                                              l["detail"][:110]))
            print("            why it matters: %s" % why)
            print()
        print("=" * 96)
        surv = [r for r in rows if r[1] == "SURVIVED"]
        print("SUMMARY: %d mutants, %d KILLED, %d SURVIVED, %d NON-VIABLE"
              % (len(rows), sum(1 for r in rows if r[1] == "KILLED"), len(surv),
                 sum(1 for r in rows if r[1] == "NON-VIABLE")))
        for r in rows:
            print("  %-9s %s" % (r[1], r[0]))
        # A SURVIVOR IS A HOLE. Print the survivors again, loudly, and never above the list.
        if surv:
            print()
            print("SURVIVORS -- each is a defect T292's adversary CANNOT SEE:")
            for r in surv:
                print("  %s" % r[0])
                print("     %s" % r[2])
        bad = [r for r in rows
               if r[0].split("-")[0] in KILL_TARGETS and r[1] != "KILLED"]
        print()
        print("EXIT %d   (non-zero if ANY kill target survived -- a survivor is a hole)"
              % (1 if bad else 0))
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
