#!/usr/bin/env python3
"""T175 RED PROBE -- t55-analyse.py:352 (invariant I6, "every money cell is at most 2 dp").

P-22: ship no guard you have not personally driven RED.  P-50: drive BOTH halves -- show the
successor REFUSES the input the original swallows, AND show it still PASSES the clean corpus.

Five legs:
  A  ORIGINAL vs CLEAN corpus            -> I6 ok           (baseline: it is not simply broken)
  B  ORIGINAL vs PARSEABLE 3-dp plant    -> I6 VIOLATED     (control: it catches what it parses)
  C  ORIGINAL vs UNPARSEABLE 3-dp plant  -> I6 ok  <-- THE DEFECT, demonstrated not asserted
  D  SUCCESSOR vs UNPARSEABLE 3-dp plant -> exits 1 and NAMES the cell
  E  SUCCESSOR vs CLEAN corpus           -> exits 0, 1236 money cells inspected, 0 swallowed
  F  SUCCESSOR vs an EMPTY corpus        -> exits 1 (zero inspected is an ERROR, P-35)

The committed `../out/` corpus and the committed `../t55-analyse.py` are never written to.
Only `decimal.Decimal`; no float is constructed anywhere in this probe.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ANALYSIS = os.path.abspath(os.path.join(HERE, os.pardir))
ORIGINAL = os.path.join(ANALYSIS, "t55-analyse.py")
SUCCESSOR = os.path.join(ANALYSIS, "t55-invariants-v2.py")
PLANT = os.path.join(HERE, "plant.py")

rc = 0


def check(label, expected, actual):
    global rc
    if str(expected) == str(actual):
        print("  AS PREDICTED      %s: %s" % (label, actual))
    else:
        print("  NOT AS PREDICTED  %s: expected %s, got %s" % (label, expected, actual))
        rc = 1


def load_original(out_dir):
    """Fresh import of the ORIGINAL, pointed at a scratch corpus.  `sidecars()` is never
    called -- it is the only function in that module that writes, and it writes to OUT."""
    spec = importlib.util.spec_from_file_location("t55_original_probe", ORIGINAL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.OUT = out_dir
    del m.fails[:]
    return m


def original_i6(out_dir, cid):
    """Run the ORIGINAL's own invariants() and return its I6 row verbatim."""
    m = load_original(out_dir)
    for name, ok, det in m.invariants(cid):
        if name.startswith("I6"):
            return ok, det
    raise AssertionError("the original emitted no I6 row")


def plant(scratch, mode):
    out = subprocess.run([sys.executable, PLANT, scratch, mode],
                         capture_output=True, text=True)
    sys.stdout.write("".join("    | " + ln + "\n" for ln in out.stdout.strip().splitlines()))
    if out.returncode:
        sys.stdout.write(out.stderr)
        raise SystemExit(9)
    return scratch


def run_successor(out_dir):
    env = dict(os.environ, T175_OUT=out_dir)
    return subprocess.run([sys.executable, SUCCESSOR], capture_output=True, text=True, env=env)


def main():
    tmp = tempfile.mkdtemp(prefix="t175-red-")
    try:
        cid = "LB-LEAPIN-p7"

        print("\n======== LEG A -- ORIGINAL vs the CLEAN corpus (baseline) ========")
        clean = plant(os.path.join(tmp, "clean"), "clean")
        ok, det = original_i6(clean, cid)
        check("ORIGINAL I6 on the clean corpus (ok = no breach present)", "True", ok)
        print("        detail: %s" % det)

        print("\n======== LEG B -- ORIGINAL vs a PARSEABLE 3-dp plant (control) ========")
        pars = plant(os.path.join(tmp, "parseable"), "parseable-3dp")
        ok, det = original_i6(pars, cid)
        check("ORIGINAL I6 on a PARSEABLE three-decimal money cell (must VIOLATE)", "False", ok)
        print("        detail: %s" % det)
        print("        -> the original's I6 is NOT simply broken. It catches a 3-dp breach")
        print("           whenever the text happens to parse. That is what makes leg C damning.")

        print("\n======== LEG C -- ORIGINAL vs an UNPARSEABLE 3-dp plant (THE DEFECT) ========")
        unp = plant(os.path.join(tmp, "unparseable"), "unparseable-3dp")
        ok, det = original_i6(unp, cid)
        check("ORIGINAL I6 on an UNPARSEABLE three-decimal money cell (defect => ok)",
              "True", ok)
        print("        detail: %s" % det)
        print("        -> `1,200,000.000` is THREE decimal places in a 2-minor-unit currency,")
        print("           i.e. a real breach of the first non-negotiable in CLAUDE.md. The")
        print("           original reports I6=ok and prints NOTHING about having skipped it.")
        print("        -> field-census.py enumerates the whole money surface of this capture:")
        print("           24 of 32 cell plants are swallowed exactly like this one, 8 crash on")
        print("           an unguarded Decimal() elsewhere, and 0 are reported BY I6.")
        m = load_original(unp)
        allres = m.invariants(cid)
        n_ok = sum(1 for _n, o, _d in allres if o)
        check("ORIGINAL's whole invariant row for %s (all seven still 'ok')" % cid,
              "7", n_ok)

        print("\n======== LEG D -- SUCCESSOR vs the SAME unparseable plant ========")
        r = run_successor(unp)
        check("SUCCESSOR exit status (must REFUSE)", "1", r.returncode)
        named = "1,200,000.000" in r.stdout
        check("SUCCESSOR NAMES the planted cell's exact text", "True", named)
        check("SUCCESSOR names the cell key", "True",
              "plan.totalRepaymentExpected" in r.stdout)
        # PREDICTION CORRECTED ON MEASUREMENT.  The first draft of this probe predicted ONE
        # swallowed item and measured THREE.  Three is right and the prediction was wrong:
        # LB-LEAPIN-p7 is the `p7` leg of two pairs (p7-vs-p4 and p7-vs-p3), so the same
        # planted cell is ALSO an uncomputable money delta in each of them -- which is the
        # t55-analyse.py:167 swallow, the second site, firing on the same input.  Recorded
        # rather than quietly relabelled: a probe that adjusts its prediction to its result
        # without saying so is the thing this task exists to stop.
        check("SUCCESSOR's SKIP REGISTER item count (1 x I6 + 2 x worst-delta)", "3",
              r.stdout.count("SKIP REGISTER -- 3 swallowed item(s)") * 3)
        check("...of which I6 entries", "1", len([l for l in r.stdout.splitlines()
                                                  if l.strip().startswith("[I6]")]))
        check("...of which worst-delta entries", "2",
              len([l for l in r.stdout.splitlines()
                   if l.strip().startswith("[worst-delta]")]))
        print("        --- the SUCCESSOR's verdict lines:")
        for ln in r.stdout.splitlines():
            if ("FAIL" in ln or ln.strip().startswith("[I6]")
                    or "money cells I6 SWALLOWED" in ln
                    or "money cells I6 INSPECTED" in ln):
                print("        | " + ln.strip())

        print("\n======== LEG E -- the OTHER half (P-50): SUCCESSOR vs the CLEAN corpus ========")
        r = run_successor(clean)
        check("SUCCESSOR exit status on the clean corpus", "0", r.returncode)
        for ln in r.stdout.splitlines():
            if ("money cells I6" in ln or "money deltas" in ln or "captures loaded" in ln
                    or ln.startswith("T175 SUCCESSOR:")
                    or "dropped by cells()" in ln):
                print("        | " + ln.strip())
        check("SUCCESSOR reports a NON-ZERO I6 denominator", "True",
              "money cells I6 INSPECTED   : 1236" in r.stdout)

        print("\n======== LEG F -- SUCCESSOR vs an EMPTY corpus (zero inspected is an ERROR) ========")
        empty = os.path.join(tmp, "empty")
        os.makedirs(empty)
        r = run_successor(empty)
        check("SUCCESSOR exit status on an empty corpus", "1", r.returncode)
        check("SUCCESSOR calls zero-captures an ERROR (P-35)", "True",
              "ZERO captures loaded" in r.stdout)
        check("SUCCESSOR calls zero-money-cells an ERROR (P-35)", "True",
              "I6 is VACUOUS" in r.stdout)
        print("        --- and for contrast, the ORIGINAL on the same empty corpus:")
        try:
            ok, det = original_i6(empty, cid)
            print("        | ORIGINAL I6 = %s  %s" % (ok, det))
        except Exception as exc:
            print("        | ORIGINAL raises %s: %s  (it has no empty-corpus handling at all;"
                  % (type(exc).__name__, exc))
            print("        |  the file-not-found happens to be loud, but that is the LOADER,")
            print("        |  not the invariant -- :352 stays silent on every cell it drops.)")

        print("\n======== VERDICT ========")
        print("  ALL LEGS AS PREDICTED" if rc == 0 else "  SOME LEG NOT AS PREDICTED")
        return rc
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
