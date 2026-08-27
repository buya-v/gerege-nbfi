#!/usr/bin/env python3
"""T185 INDEPENDENT RED PROBE of t55-invariants-v2.py.

Plants the value shapes T175 explicitly listed as NOT SWEPT and therefore NOT CLAIMED
(handoff: "unparseable values of other shapes (empty string, `"null"`, a Unicode minus)"),
plus a bare JSON number and a nested object -- the `cells()` narrowing class.

Scratch corpora only (mktemp). The committed corpus is COPIED, never written.
Predicts, for each plant: the successor must NOT print `T175 SUCCESSOR: PASS` with exit 0.
Either it reports a VIOLATION, or it names the cell in the SKIP REGISTER and fails,
or it counts it as dropped-by-cells() and fails. A silent `ok` is the defect class.
"""
import json, os, shutil, subprocess, sys, tempfile

W = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac71271ab074115ac"
ANALYSIS = os.path.join(W, ".softhouse/capture/leapboundary/analysis")
SUCC = os.path.join(ANALYSIS, "t55-invariants-v2.py")
ORIG = os.path.join(ANALYSIS, "t55-analyse.py")
OUT = os.path.join(W, ".softhouse/capture/leapboundary/out")
TARGET = "LB-LEAPIN-p7-exact.json"
FIELD = "totalRepaymentExpected"

# value shapes T175 did NOT sweep, plus the parseable control
PLANTS = [
    ("CONTROL parseable 3dp (T175 leg B)", "1200000.000"),
    ("T175's own unparseable plant",       "1,200,000.000"),
    ("EMPTY STRING",                        ""),
    ("the STRING 'null'",                   "null"),
    ("UNICODE MINUS U+2212",                "−1200000.00"),
    ("NBSP thousands sep",                  "1 200 000.000"),
    ("full-width digits",                   "１２０００００.０００"),
    ("BARE JSON NUMBER 3dp (cells() class)", 1200000.000),
    ("JSON null (cells() class)",            None),
    ("NESTED OBJECT (cells() class)",       {"v": "1200000.000"}),
    ("Decimal-legal exponent form 3dp",     "1.200000000E+6"),
]


def build(scratch, value, plant):
    os.makedirs(scratch, exist_ok=True)
    n = 0
    for fn in sorted(os.listdir(OUT)):
        if fn.endswith("-exact.json"):
            shutil.copy2(os.path.join(OUT, fn), os.path.join(scratch, fn))
            n += 1
    if plant:
        p = os.path.join(scratch, TARGET)
        with open(p) as fh:
            doc = json.load(fh, parse_float=str, parse_int=str)  # T185: no binary float
        assert FIELD in doc, "target field vanished: " + FIELD
        doc[FIELD] = value
        with open(p, "w") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
            fh.write("\n")
    return n


def run(script, scratch):
    env = dict(os.environ, T175_OUT=scratch)
    r = subprocess.run([sys.executable, script], capture_output=True, text=True, env=env,
                       cwd=ANALYSIS)
    return r.returncode, r.stdout + r.stderr


def run_orig_i6(scratch):
    """Call the ORIGINAL's own invariants() in-process against the scratch corpus.

    NEVER runs its main(): main() calls sidecars(), which WRITES ../out/*-exact.json, and
    t55-analyse.py has no output-dir env override (only T55_NEG_PREC / _ROUND / _DOCTOR).
    Writing there would be a write to committed evidence -- forbidden by T114's ruling.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("t55_orig_t185", ORIG)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.OUT = scratch                      # redirect reads only
    cid = TARGET[:-len("-exact.json")]
    try:
        res = m.invariants(cid)
    except Exception as exc:
        return "CRASHED %s: %s" % (type(exc).__name__, str(exc)[:60])
    for name, ok, det in res:
        if name.startswith("I6"):
            return "I6 %s  detail=%s" % ("ok" if ok else "VIOLATED", str(det)[:60])
    return "I6 not returned"


def main():
    bad = 0
    base = tempfile.mkdtemp(prefix="t185-t55-")
    try:
        # ---- P-50 other half first: clean copy must PASS
        clean = os.path.join(base, "clean")
        n = build(clean, None, False)
        rc, out = run(SUCC, clean)
        print("======== LEG 0 -- CLEAN copy of the committed corpus (%d sidecars)" % n)
        print("  successor exit = %d   (predicted 0)" % rc)
        for line in out.splitlines():
            if "SUCCESSOR:" in line or "money cells inspected" in line or "captures loaded" in line:
                print("    " + line.strip())
        if rc != 0:
            print("  *** NOT AS PREDICTED: clean corpus does not pass"); bad += 1

        # ---- each plant
        for label, value in PLANTS:
            d = os.path.join(base, "p%d" % PLANTS.index((label, value)))
            build(d, value, True)
            orig_i6 = run_orig_i6(d)
            rc_s, out_s = run(SUCC, d)
            succ_pass = "T175 SUCCESSOR: PASS" in out_s
            verdict = "SILENTLY ACCEPTED" if (succ_pass and rc_s == 0) else "CAUGHT"
            print()
            print("======== PLANT: %s   value=%r" % (label, value))
            print("  ORIGINAL   : %s" % orig_i6)
            print("  SUCCESSOR  : exit=%d  -> %s" % (rc_s, verdict))
            for line in out_s.splitlines():
                s = line.strip()
                if s.startswith("FAIL ") or "VIOLATED" in s or "SWALLOWED" in s.upper() \
                   or s.startswith("T175 SUCCESSOR:"):
                    print("      " + s[:150])
            if verdict == "SILENTLY ACCEPTED":
                print("  *** NOT AS PREDICTED: the successor passed an input of the swallowed class")
                bad += 1
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print()
    print("######## T185 RESULT: %d plant(s) silently accepted by the successor" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
