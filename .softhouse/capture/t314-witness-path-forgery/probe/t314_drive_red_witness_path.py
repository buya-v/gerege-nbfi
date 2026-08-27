#!/usr/bin/env python3
"""T314 -- DRIVE F-T308-6 RED, THEN SHOW IT DEAD.  PRE = T292, POST = T314.

F-T308-6 was RAISED BY T308 and ESTABLISHED BY CONSTRUCTION.  This file does NOT re-derive it.
It re-runs T308's own two attacks verbatim as arms, adds two of mine, and reads the SAME arm
against the two rules side by side:

    PRE   .softhouse/capture/t286-t268-retry/check_verdict_predicate_agreement_t292.py
          COMMITTED EVIDENCE.  Read, never written.  Every PRE row below must show the attack
          LANDING; a PRE row that does not land means the arm is vacuous and this probe FAILS.
    POST  .softhouse/capture/t314-witness-path-forgery/check_verdict_predicate_agreement_t314.py

ARMS
  CTRL  the legitimate document.  Must stay GREEN, witness=1, on BOTH rules.  If it does not,
        the fix broke the thing it was protecting and this probe FAILS.
  A1    T308's COLLISION.  A top-level key literally named `cells[0]`.
        PRE: prints a witness line BYTE-IDENTICAL to CTRL's.        POST: must differ from CTRL's.
  A2    T308's INJECTION.  A container key containing a NEWLINE.
        PRE: 3 printed witness lines against a reported count of 1. POST: exactly 1 line.
  A3    MINE -- THE DIGEST.  Two documents grading DIFFERENT (key, value) multisets -- two facts
        versus one -- made to share a `coverageDigest`, by putting the canon's own separators
        `;` and `=` inside a key that auto-classifies.  This is the half A1 only LOOKED like:
        A1's two documents grade the SAME facts, so their shared digest is container-blindness
        working as designed, and escaping the printer would not have moved it either way.
        PRE: digests EQUAL across different fact sets.  POST: digests DIFFER.
  A4    MINE -- THE PATH IS NOT COSMETIC.  T292 recovers the census OWNER by splitting the
        rendered path (`spath.rsplit(".", 1)[0]`), so a top-level key containing a `.` is read
        as a nested path and its owner resolves onto a DIFFERENT, witnessed object -- steering a
        SET MEMBERSHIP TEST, not a line of output.  PRE: the census line is SUPPRESSED relative
        to its own control.  POST: it fires.
  CORP  the committed real corpus -- classify-t229.json and classify-t219.json.  Every GATING
        counter must be identical under PRE and POST.  `coverageDigest` MUST move (the canon
        changed); nothing else may.

EXIT 0 means every PRE row landed AND every POST row is dead AND the legitimate arms are
unchanged.  Exit 1 means a row did not behave as this file claims.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAPDIR = HERE.parent
ROOT = CAPDIR.parent.parent.parent
PRE = ROOT / ".softhouse" / "capture" / "t286-t268-retry" / "check_verdict_predicate_agreement_t292.py"
POST = CAPDIR / "check_verdict_predicate_agreement_t314.py"
T256 = ROOT / ".softhouse" / "capture" / "t256-verdict-predicate"
REG = T256 / "boolean-key-register.json"
ACK = T256 / "acknowledged.json"
CORPUS = [ROOT / ".softhouse" / "capture" / "t229-g8-site3" / "out" / "classify-t229.json",
          ROOT / ".softhouse" / "capture" / "t219-g8-residual" / "out" / "classify-t219.json"]

FAILURES = []


def check(cond, what):
    if not cond:
        FAILURES.append(what)
    return cond


def run(rule: Path, target: Path):
    r = subprocess.run([sys.executable, str(rule), "--register", str(REG),
                        "--acknowledgements", str(ACK), str(target)],
                       capture_output=True, text=True, timeout=120)
    probe = None
    for ln in r.stdout.splitlines():
        if ln.startswith("T259-VPA:"):
            probe = ln
    return r.returncode, probe, r.stdout


def f(probe, name):
    """Read a field of the probe line.  P-84 -- 'EXIT 2 WITH NO PROBE LINE IS THE GUARD WORKING;
    READ THE ABSENCE, NOT THE VALUE.'  So: absence is reported as None and every caller that
    compares a value first asserts the line is PRESENT."""
    if not probe:
        return None
    for t in probe.split():
        if t.startswith(name + "="):
            return t.split("=", 1)[1]
    return None


def witness_block(stdout):
    """The lines the rule prints as the witness listing -- the NAMING, verbatim."""
    out, grabbing = [], False
    for ln in stdout.splitlines():
        if ln.strip().startswith("WITNESS -- predicate reads"):
            grabbing = True
            continue
        if grabbing:
            if ln.strip().startswith("disagreements found"):
                break
            out.append(ln)
    return [l for l in out if l.strip()]


def census_lines(stdout):
    return [l.strip() for l in stdout.splitlines() if "HEADER AFFIRMATION" in l]


def write(tmp, name, doc):
    p = tmp / name
    p.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return p


def hdr(t):
    print()
    print(t)
    print("-" * len(t))


def main():
    print("T314 -- F-T308-6 DRIVEN RED (PRE=T292) AND SHOWN DEAD (POST=T314)")
    print("=" * 100)
    for p in (PRE, POST, REG, ACK, *CORPUS):
        if not p.exists():
            print("ERROR: missing input %s" % p, file=sys.stderr)
            return 2
    print("PRE   %s" % PRE.relative_to(ROOT))
    print("POST  %s" % POST.relative_to(ROOT))

    tmp = Path(tempfile.mkdtemp(prefix=".t314-drive-", dir=str(CAPDIR)))
    try:
        # ------------------------------------------------------------------ CTRL
        hdr("CTRL  the legitimate document -- must be untouched by the fix")
        ctrl_doc = {"cells": [{"P1_principalAmortizesToZero": True, "verdict": "AS PREDICTED"}]}
        pc = write(tmp, "ctrl.json", ctrl_doc)
        rc_c_pre, pb_c_pre, so_c_pre = run(PRE, pc)
        rc_c_post, pb_c_post, so_c_post = run(POST, pc)
        wb_c_pre, wb_c_post = witness_block(so_c_pre), witness_block(so_c_post)
        print("  PRE   rc=%s  probe line PRESENT: %s" % (rc_c_pre, pb_c_pre is not None))
        for l in wb_c_pre:
            print("        |%s" % l)
        print("  POST  rc=%s  probe line PRESENT: %s" % (rc_c_post, pb_c_post is not None))
        for l in wb_c_post:
            print("        |%s" % l)
        check(pb_c_pre is not None and pb_c_post is not None,
              "CTRL: a probe line was ABSENT (P-84: that is a failed guard, not an outage)")
        check(rc_c_pre == 0 and rc_c_post == 0, "CTRL: a legitimate document stopped passing")
        check(f(pb_c_pre, "witness") == "1" and f(pb_c_post, "witness") == "1",
              "CTRL: witness count moved")
        check(len(wb_c_post) == 1, "CTRL: POST printed %d witness lines, expected 1" % len(wb_c_post))
        print("  => a legitimate document still passes on BOTH rules, witness=1: %s"
              % ("YES" if rc_c_pre == rc_c_post == 0 else "NO"))

        # ------------------------------------------------------------------ A1
        hdr("A1  T308's COLLISION -- a top-level key literally named `cells[0]`")
        a1_doc = {"cells[0]": {"P1_principalAmortizesToZero": True, "verdict": "AS PREDICTED"}}
        p1 = write(tmp, "a1.json", a1_doc)
        rc1p, pb1p, so1p = run(PRE, p1)
        rc1q, pb1q, so1q = run(POST, p1)
        wb1p, wb1q = witness_block(so1p), witness_block(so1q)
        print("  PRE   rc=%s  line: %s" % (rc1p, wb1p[0].strip() if wb1p else "<none>"))
        print("        CTRL line: %s" % (wb_c_pre[0].strip() if wb_c_pre else "<none>"))
        pre_collides = wb1p == wb_c_pre
        print("        BYTE-IDENTICAL TO CTRL: %s   <- the attack LANDS"
              % ("YES" if pre_collides else "no"))
        print("  POST  rc=%s  line: %s" % (rc1q, wb1q[0].strip() if wb1q else "<none>"))
        print("        CTRL line: %s" % (wb_c_post[0].strip() if wb_c_post else "<none>"))
        post_collides = wb1q == wb_c_post
        print("        BYTE-IDENTICAL TO CTRL: %s   <- the attack is DEAD"
              % ("YES" if post_collides else "NO"))
        check(pre_collides, "A1: PRE did not collide -- the arm is vacuous")
        check(not post_collides, "A1: POST STILL COLLIDES -- the forgery is still unnameable")
        check(rc1q == 0, "A1: POST changed the verdict; naming is not supposed to gate")
        print("  NOTE ON THE DIGEST, deliberately NOT 'fixed': PRE=%s POST-ctrl=%s POST-a1=%s."
              % (f(pb1p, "coverageDigest"), f(pb_c_post, "coverageDigest"),
                 f(pb1q, "coverageDigest")))
        print("        A1's two documents grade the SAME (key, value) multiset, so an identical")
        print("        digest is container-blindness working AS DESIGNED -- the digest excludes")
        print("        the path on purpose. Adding the path back would break the property the")
        print("        digest exists to have. The real digest defect is A3, below.")
        check(f(pb_c_post, "coverageDigest") == f(pb1q, "coverageDigest"),
              "A1: POST digest split on a container-only difference -- container-blindness lost")

        # ------------------------------------------------------------------ A2
        hdr("A2  T308's INJECTION -- a container key carrying a NEWLINE and a fabricated line")
        inj_key = "z\n      $.cells[0].P7_reconciledAgainstOracle = true\n      x"
        a2_doc = {inj_key: {"P1_principalAmortizesToZero": True, "verdict": "AS PREDICTED"}}
        p2 = write(tmp, "a2.json", a2_doc)
        rc2p, pb2p, so2p = run(PRE, p2)
        rc2q, pb2q, so2q = run(POST, p2)
        wb2p, wb2q = witness_block(so2p), witness_block(so2q)
        fabricated = "$.cells[0].P7_reconciledAgainstOracle = true"
        print("  PRE   rc=%s  reported witness COUNT=%s, printed LINES=%d"
              % (rc2p, f(pb2p, "witness"), len(wb2p)))
        for l in wb2p:
            print("        |%s" % l)
        pre_injects = (len(wb2p) > int(f(pb2p, "witness") or 0)
                       and any(l.strip() == fabricated for l in wb2p))
        print("        A FABRICATED LINE NAMING AN UNGRADED PREDICATE IS PRESENT: %s   <- LANDS"
              % ("YES" if pre_injects else "no"))
        print("  POST  rc=%s  reported witness COUNT=%s, printed LINES=%d"
              % (rc2q, f(pb2q, "witness"), len(wb2q)))
        for l in wb2q:
            print("        |%s" % l)
        post_injects = any(l.strip() == fabricated for l in wb2q)
        post_count_ok = len(wb2q) == int(f(pb2q, "witness") or -1)
        print("        fabricated line present: %s ; printed LINES == reported COUNT: %s   <- DEAD"
              % ("YES" if post_injects else "NO", "YES" if post_count_ok else "NO"))
        check(pre_injects, "A2: PRE did not inject -- the arm is vacuous")
        check(not post_injects, "A2: POST STILL INJECTS a fabricated witness line")
        check(post_count_ok, "A2: POST printed a number of lines != the reported witness count")

        # ------------------------------------------------------------------ A3
        hdr("A3  MINE -- THE DIGEST. Different graded FACTS, one `coverageDigest`.")
        print("  T292's canon: \";\".join(sorted(\"%s=%s\" %% (k, \"1\" if v else \"0\") ...)) --")
        print("  `;` and `=` are the separators AND are legal inside a JSON member name.")
        a3_two = {"cells": [{"P1_x": True, "P2_y": True, "verdict": "AS PREDICTED"}]}
        a3_one = {"cells": [{"P1_x=1;P2_y": True, "verdict": "AS PREDICTED"}]}
        p3a = write(tmp, "a3-two-facts.json", a3_two)
        p3b = write(tmp, "a3-one-fact.json", a3_one)
        rows = {}
        for tag, rule in (("PRE", PRE), ("POST", POST)):
            r_two = run(rule, p3a)
            r_one = run(rule, p3b)
            rows[tag] = (r_two, r_one)
            for nm, (rc, pb, _so) in (("two facts", r_two), ("one fact", r_one)):
                check(pb is not None, "A3/%s/%s: probe line ABSENT (P-84)" % (tag, nm))
                print("  %-4s %-9s rc=%s witness=%s coverageDigest=%s"
                      % (tag, nm, rc, f(pb, "witness"), f(pb, "coverageDigest")))
            d_two = f(r_two[1], "coverageDigest")
            d_one = f(r_one[1], "coverageDigest")
            same = d_two is not None and d_two == d_one
            print("       witness counts DIFFER (%s vs %s) but digests %s"
                  % (f(r_two[1], "witness"), f(r_one[1], "witness"),
                     "COLLIDE  <- the attack LANDS" if same else "DIFFER  <- the attack is DEAD"))
        pre_dig_collide = (f(rows["PRE"][0][1], "coverageDigest")
                           == f(rows["PRE"][1][1], "coverageDigest"))
        post_dig_collide = (f(rows["POST"][0][1], "coverageDigest")
                            == f(rows["POST"][1][1], "coverageDigest"))
        check(pre_dig_collide, "A3: PRE digests did not collide -- the arm is vacuous")
        check(not post_dig_collide, "A3: POST DIGESTS STILL COLLIDE across different graded facts")
        check(f(rows["PRE"][0][1], "witness") != f(rows["PRE"][1][1], "witness"),
              "A3: the two documents did not actually grade different numbers of facts")

        # ------------------------------------------------------------------ A4
        hdr("A4  MINE -- THE PATH IS NOT COSMETIC: it steers a SET MEMBERSHIP TEST")
        print("  T292: `owner = spath.rsplit('.', 1)[0]` then `if owner not in witnessed_objects`.")
        print("  A top-level key containing a `.` is therefore read as a NESTED path whose owner")
        print("  is a DIFFERENT object -- one that IS witnessed -- so the census line is lost.")
        a4_ctrl = {"a": {"P1_principalAmortizesToZero": True, "verdict": "AS PREDICTED"},
                   "note": "AS PREDICTED"}
        a4_atk = {"a": {"P1_principalAmortizesToZero": True, "verdict": "AS PREDICTED"},
                  "a.note": "AS PREDICTED"}
        p4c = write(tmp, "a4-ctrl.json", a4_ctrl)
        p4a = write(tmp, "a4-attack.json", a4_atk)
        res4 = {}
        for tag, rule in (("PRE", PRE), ("POST", POST)):
            rc_c, pb_c, so_c = run(rule, p4c)
            rc_a, pb_a, so_a = run(rule, p4a)
            check(pb_c is not None and pb_a is not None, "A4/%s: probe line ABSENT (P-84)" % tag)
            hc, ha = f(pb_c, "headerAffirmations"), f(pb_a, "headerAffirmations")
            res4[tag] = (hc, ha)
            print("  %-4s control key `note`   headerAffirmations=%s   %s"
                  % (tag, hc, (census_lines(so_c) or ["<none>"])[0]))
            print("  %-4s attack  key `a.note` headerAffirmations=%s   %s"
                  % (tag, ha, (census_lines(so_a) or ["<none>"])[0]))
            print("       census SUPPRESSED by the key's content: %s"
                  % ("YES  <- the attack LANDS" if hc != ha else "NO  <- the attack is DEAD"))
        check(res4["PRE"][0] != res4["PRE"][1],
              "A4: PRE census was not steered -- the arm is vacuous")
        check(res4["POST"][0] == res4["POST"][1],
              "A4: POST census is STILL steered by key content")
        print("  This one gates NOTHING today (headerAffirmations is a census counter, by")
        print("  T292's own design). It is here to refute 'the path is only printed' -- it is")
        print("  also an IDENTITY, and an ambiguous identity is a bug wherever it is read.")

        # ------------------------------------------------------------------ CORP
        hdr("CORP  the committed real corpus -- the fix must move NOTHING but the digest")
        gating = ["files", "rows", "predicates", "disagreements", "acknowledged", "unacknowledged",
                  "unclassifiedKeys", "unclassifiedVerdicts", "nilCoverage", "witness", "nilFiles",
                  "muteRefutations", "voidAcks", "headerAffirmations"]
        for doc in CORPUS:
            rc_p, pb_p, _ = run(PRE, doc)
            rc_q, pb_q, _ = run(POST, doc)
            check(pb_p is not None and pb_q is not None,
                  "CORP/%s: probe line ABSENT (P-84)" % doc.name)
            same = [g for g in gating if f(pb_p, g) == f(pb_q, g)]
            moved = [g for g in gating if f(pb_p, g) != f(pb_q, g)]
            print("  %s" % doc.relative_to(ROOT))
            print("     PRE  rc=%s %s" % (rc_p, pb_p))
            print("     POST rc=%s %s" % (rc_q, pb_q))
            print("     gating counters identical: %d/%d   moved: %s"
                  % (len(same), len(gating), moved or "none"))
            print("     coverageDigest PRE=%s POST=%s  (MUST differ -- the canon changed)"
                  % (f(pb_p, "coverageDigest"), f(pb_q, "coverageDigest")))
            check(rc_p == rc_q, "CORP/%s: verdict changed" % doc.name)
            check(not moved, "CORP/%s: gating counters moved: %s" % (doc.name, moved))
            check(f(pb_p, "coverageDigest") != f(pb_q, "coverageDigest"),
                  "CORP/%s: digest did NOT move, so the canon did not actually change" % doc.name)

        # ------------------------------------------------------------------ verdict
        print()
        print("=" * 100)
        if FAILURES:
            print("FAIL -- %d row(s) did not behave as this file claims:" % len(FAILURES))
            for x in FAILURES:
                print("   * %s" % x)
            return 1
        print("PASS -- every PRE row LANDED (the arms are not vacuous), every POST row is DEAD,")
        print("        the legitimate document and the committed corpus are unchanged except for")
        print("        the coverageDigest, which had to move because its canon was the defect.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
