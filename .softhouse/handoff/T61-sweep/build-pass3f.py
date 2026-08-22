#!/usr/bin/env python3
"""Construct capture pass 3f MECHANICALLY from pass 3e.

Pass 3f is pass 3e's rig with a new case list and a FOURTH rig calibration --
exactly the relationship pass 3c has to pass 3b (`README-pass3c.md`). Building it
by transformation rather than by hand is deliberate: it makes "not one
precondition was weakened" a property of the construction instead of a claim in a
comment. The script asserts that every substitution it makes actually matched.

    python3 .softhouse/handoff/T61-sweep/build-pass3f.py
"""
import os, re, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, ".softhouse/capture/src")


def sub1(text, old, new, what):
    if text.count(old) < 1:
        sys.exit("BUILD FAILED: anchor not found (%s)" % what)
    return text.replace(old, new)


# HARDENED BY T206 (22 August 2026) - P-22, P-48 rule 4.  T203's backlog named
# this file's three write sites (then :147/:215/:216, unchanged by this fix's
# line count above them) as CAPTURE-tagged unguarded mutations, not a
# vector-store rewrite -- so T203's `t203_store_guard.py` does not apply as-is
# (it requires a `.json` target and speaks of "the live golden-vector store";
# neither is true of `Capture3f.java` / `run-pass3f.sh`).  MEASURED, NOT
# ASSERTED (T206-evidence/RED-b-prefix.txt): both `open(path, "w").write(...)`
# calls are bare O_TRUNC with no existence check, and the trailing
# `os.chmod(path, 0o755)` runs unconditionally regardless of what (if
# anything) is at that path -- against a scratch mirror seeded with sentinels
# at BOTH already-built targets, the pre-fix bytes destroyed both canaries and
# silently widened run-pass3f.sh's mode from 0600 to 0755, exit 0.
# `Capture3f.java` and `run-pass3f.sh` are themselves ALREADY COMMITTED build
# outputs of a prior run of this exact script (`ls .softhouse/capture/src/`),
# so re-running it today is not a hypothetical -- it would truncate them in
# place. `guarded_create` below is T203's/T178's core rule -- THE TARGET MUST
# NOT EXIST; no override -- applied locally rather than through the shared
# vector-store module, because the target here is a build artefact, not a
# vector, and forcing it through a `.json`-only, vector-store-worded guard
# would be a second lie layered on the first. It performs the identical
# mkstemp/fchmod/fsync/os.replace/fsync-dir sequence as
# `t203_store_guard._atomic_create`, so no interruption between the first
# byte and the fsync'd replace can leave a partial or half-permissioned file,
# and the `os.chmod` follow-up call is eliminated entirely -- the mode is set
# on the temp file, atomically, before it becomes the target, so there is no
# window where the finished file exists with the wrong mode and no third
# call left to forget a guard on.
def guarded_create(path, data, what, mode=None):
    """Create `path` with `data` (bytes or str), or refuse if it already
    exists.  No flag lifts the refusal: this script's whole job is to BUILD
    pass 3f from pass 3e, and a rebuild after a prior build already ran must
    be a deliberate `rm` in a reviewable commit, never an implicit
    overwrite -- exactly T203's rule for the vector store, applied here to a
    committed capture-harness artefact instead of a `.json` vector."""
    if os.path.lexists(path):
        sys.exit("BUILD FAILED: %s already exists at %r; refusing to overwrite it "
                  "(O_TRUNC would destroy it before the replacement exists). "
                  "Delete it deliberately in a reviewable commit first if this "
                  "pass is genuinely being rebuilt." % (what, path))
    data = data.encode("utf-8") if isinstance(data, str) else data
    target_dir = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=target_dir, prefix=".build-pass3f-", suffix=".tmp")
    try:
        if mode is not None:
            os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)
    dfd = os.open(target_dir, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


# --------------------------------------------------------------------------
# 1. Capture3f.java = Capture3e.java, renamed, with a new case list.
# --------------------------------------------------------------------------
java = open(os.path.join(SRC, "Capture3e.java")).read()

HEADER_OLD_START = java.index("/*")
HEADER_OLD_END = java.index("*/") + 2
NEW_HEADER = '''/*
 * Golden-vector capture harness, PASS 3f — gerege-nbfi Fineract→Go migration, Tier 0.
 *
 * PASS 3f IS PASS 3e's RIG WITH A NEW CASE LIST. Every precondition, attestation field, column
 * and emission rule is preserved byte-for-byte; only the case list differs, and NOT ONE check was
 * weakened. All three of pass 3e's rig calibrations are carried over unchanged and a FOURTH is
 * added.
 *
 * WHY THIS PASS EXISTS — task T61, pattern P-3. The Go port was mutated into thirteen named wrong
 * implementations and each was run against the REAL harness at 29 promoted parity vectors. One of
 * the survivors moves money on ordinary MNT loans:
 *
 *   M7  MONEY-QUANTIZATION-HALF-EVEN — a port that applies HALF_EVEN where the oracle applies the
 *       tenant's ratified HALF_UP at the currency quantization [Money.java:52]. Buyan ratified
 *       HALF_UP (RoundingMode ordinal 4) on 2026-08-18; HALF_EVEN is the oracle's own STOCK
 *       DEFAULT, so a port that inherits the default rather than reading the tenant pin lands
 *       exactly here. It passes all 29 promoted vectors, exit 0.
 *
 * HALF_UP and HALF_EVEN differ only on an EXACT TIE, and only when the truncated value is even.
 * On an on-lattice FIXED_30_360 monthly loan at 21.6% the period-1 rate factor is exactly 0.018,
 * so period-1 interest in minor units is 18*B/1000 for a principal of B minor units — an exact
 * tie when B == 250 (mod 500). The three candidates below are chosen from that algebra and were
 * confirmed separating by a 40,001-shape sweep of the port against the mutant.
 *
 * FOUR CALIBRATIONS AND THREE PARITY CANDIDATES:
 *
 *   P-CAL         RIG CALIBRATION at (12, HALF_UP), inputs identical to pass 3b's P-CAL.
 *   P-CAL-P00     RIG CALIBRATION at PRODUCTION (19, HALF_UP), inputs identical to pass 3b's P-00.
 *   P-CAL-EMI6    RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT, inputs identical to pass
 *                 3c's P-EMI-6-1M014632 — already a promoted parity vector.
 *   P-CAL-LATQ0a  RIG CALIBRATION ADDED BY THIS PASS: inputs identical to pass 3e's P-LAT-Q0a —
 *                 the on-lattice MNT control at 2024-01-01, 6 x 21.6%, already a promoted parity
 *                 vector. It is the SAME QUESTION as the three candidates below in every field but
 *                 the principal, so the calibration covers the exact lattice, term and rate the
 *                 promotion will rest on.
 *   T61-HE-A/B/C  three parity candidates; ordinary on-lattice MNT loans differing from
 *                 P-LAT-Q0a ONLY in the principal.
 *
 * None of the four calibrations is a parity vector and P-CAL is on PIN.json's never-promotable
 * list.
 *
 * It asserts nothing and predicts nothing — every value printed is what the oracle emitted. No
 * expected value is ever synthesised here. In particular this harness does NOT know which tie rule
 * it is testing, does NOT compute a HALF_EVEN counterfactual and does NOT decide whether a shape
 * separates: it prints the oracle's schedule and stops. The prediction lives, timestamped by git,
 * in .softhouse/capture/t61-halfeven/PREDICTION.md and was committed BEFORE this ran.
 *
 * PRODUCTION SETTINGS. Buyan ratified the tenant parameters on 2026-08-18: rounding mode HALF_UP,
 * licence NBFI. Precision is not a choice — MoneyHelper.PRECISION = 19 is a compile-time constant and
 * getMathContext() returns new MathContext(19, tenantRoundingMode) [MoneyHelper.java:35, 91-93]. So the
 * PRODUCTION MathContext is (19, HALF_UP).
 *
 * PostgreSQL remains the only permitted database for this program; this seam opens no database
 * connection at all. "The oracle" here is the Fineract reference implementation, never Oracle
 * Database (a prohibited product).
 */'''
java = NEW_HEADER + java[HEADER_OLD_END:]
java = sub1(java, "public class Capture3e {", "public class Capture3f {", "class decl")
java = sub1(java, "Capture3e.class", "Capture3f.class", "self reference")
java = sub1(java, "/cap/src/Capture3e.java", "/cap/src/Capture3f.java", "attest sources default")
java = sub1(java, "capture-prod3e-classpath-sha256.txt", "capture-prod3f-classpath-sha256.txt", "classpath out default")

# The case list, between the two markers pass 3e itself uses.
start = java.index("        // ---- RIG CALIBRATIONS")
end = java.index("        StringBuilder sb = new StringBuilder();")
NEW_CASES = '''        // ---- RIG CALIBRATIONS — reproduce values ALREADY OBSERVED in the committed corpus ------
        // Inputs below are byte-identical to the passes they repeat, TENANT ID INCLUDED, so the
        // whole observed block of each must equal the committed entry of the same shape. If any
        // one differs, nothing else from this run is trustworthy and run-pass3f.sh refuses it.
        cases.add(prod("P-CAL", "RIG CALIBRATION at (12, HALF_UP) — inputs identical to pass 3b P-CAL; must reproduce it digit for digit; NOT a parity vector",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, null, false, "usd", "cap_p_cal"));

        cases.add(prod("P-CAL-P00", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) — inputs identical to pass 3b P-00; must reproduce it digit for digit at the precision the parity candidates run at; NOT a parity vector",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 19, null, false, "usd", "cap_p_00"));

        cases.add(prod("P-CAL-EMI6", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3c P-EMI-6-1M014632; must reproduce it digit for digit; NOT a parity vector",
                new BigDecimal("1014632"), 6, new BigDecimal("7.0"), 19, null, false, "MNT", "cap_p_emi_6"));

        // ---- FOURTH CALIBRATION, ADDED BY PASS 3f ------------------------------------------------
        // Inputs byte-identical to pass 3e's P-LAT-Q0a, tenant id included. That case is ALREADY a
        // promoted parity vector, and it is the SAME QUESTION as the three candidates below in
        // every field but the principal: same lattice date, same term, same rate, same currency,
        // same MathContext. A rig that reproduces it is calibrated on exactly the arithmetic the
        // promotion rests on, not merely on something nearby.
        cases.add(prodDates("P-CAL-LATQ0a", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3e P-LAT-Q0a, the on-lattice control the three candidates differ from ONLY in principal; must reproduce it digit for digit; NOT a parity vector",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1200000"), 6, new BigDecimal("21.6"), "cap_lat_q0a"));

        // ---- PARITY CANDIDATES — three on-lattice MNT loans that land the currency -------------
        // ---- quantization on an EXACT TIE ------------------------------------------------------
        // Strictly inside the graded domain and identical to the promoted P-LAT-Q0a in every field
        // except the principal: single disbursement ON the schedule start date, RepaymentEvery 1
        // MONTHS, DECLINING_BALANCE, DAYS_30/DAYS_360, no down payment, no installment rounding,
        // MNT 2 decimals, (19, HALF_UP).
        //
        // The principals are chosen from source algebra, not searched for: at 21.6% on this
        // lattice the period-1 rate factor is exactly 0.018, so period-1 interest in minor units
        // is 18*B/1000, an exact tie when B == 250 (mod 500). T61-HE-B is the clean case
        // (B = 100005250: 18*B/1000 = 1800094.5, and 1800094 is even, so the two tie rules
        // disagree). A and C were confirmed separating by sweep.
        cases.add(prodDates("T61-HE-A", "TIE AT THE CURRENCY QUANTIZATION: MNT 1,000,541.50 / 6 x 21.6% on the 2024-01-01 lattice — widest HALF_UP vs HALF_EVEN separation found in 2,001 consecutive principals",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1000541.50"), 6, new BigDecimal("21.6"), "cap_t61_he_a"));

        cases.add(prodDates("T61-HE-B", "TIE AT THE CURRENCY QUANTIZATION: MNT 1,000,052.50 / 6 x 21.6% — period-1 interest is exactly 18000.945, the tie the sharp prediction names",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1000052.50"), 6, new BigDecimal("21.6"), "cap_t61_he_b"));

        cases.add(prodDates("T61-HE-C", "TIE AT THE CURRENCY QUANTIZATION: MNT 1,000,089.50 / 6 x 21.6% — a third, independent principal separating the two tie rules",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1000089.50"), 6, new BigDecimal("21.6"), "cap_t61_he_c"));

'''
java = java[:start] + NEW_CASES + java[end:]
java = sub1(java, '"{\\n  \\"pass\\": \\"3e\\",\\n"', '"{\\n  \\"pass\\": \\"3f\\",\\n"', "pass id")
java = sub1(java, '\\"harness\\": \\"Capture3e.java\\"', '\\"harness\\": \\"Capture3f.java\\"', "harness name")
old_extends = re.search(r'sb\.append\("  \\"extends\\": .*?\);\n', java, re.S).group(0)
java = java.replace(old_extends,
    'sb.append("  \\"extends\\": \\"Capture3e.java / capture-prod3e-raw.json — same rig, same columns, same attestation, same emission rules, all three calibrations carried over unchanged plus a FOURTH (P-CAL-LATQ0a, inputs identical to pass 3e P-LAT-Q0a); a NEW case list of three on-lattice MNT loans that land the currency quantization on an exact tie, so that a port applying HALF_EVEN where the tenant pins HALF_UP is separated in a payable amount.\\",\\n");\n')

guarded_create(os.path.join(SRC, "Capture3f.java"), java, "Capture3f.java")

# --------------------------------------------------------------------------
# 2. run-pass3f.sh = run-pass3e.sh with the new ids and a fourth calibration.
# --------------------------------------------------------------------------
sh = open(os.path.join(SRC, "run-pass3e.sh")).read()

sh = sh.replace("PASS 3e", "PASS 3f").replace("pass 3e", "pass 3f")
sh = sh.replace("Capture3e.java", "Capture3f.java").replace("Capture3e", "Capture3f")
sh = sh.replace("capture-prod3e-", "capture-prod3f-")
sh = sh.replace("run-pass3e.sh", "run-pass3f.sh")
sh = sh.replace("pass3e-", "pass3f-")

# the fourth calibration reference: pass 3e's own committed artefact
sh = sub1(sh,
    'REF3C_JSON="${REF3C_JSON:-.softhouse/capture/out/capture-prod3c-raw.json}"',
    'REF3C_JSON="${REF3C_JSON:-.softhouse/capture/out/capture-prod3c-raw.json}"\n'
    '# The FOURTH calibration reference, added by pass 3f: pass 3e\'s own committed artefact, from\n'
    '# which the eight P-DRIFT, four P-ME and two P-LAT parity vectors were transcribed.\n'
    'REF3E_JSON="${REF3E_JSON:-.softhouse/capture/out/capture-prod3e-raw.json}"',
    "ref3e decl")
sh = sub1(sh,
    'EXPECTED_REF3C_SHA="cae566d3ba99c69704fdb5dca21e247b3ec7d20c2e5ccc4e50b97721e8c92dec"',
    'EXPECTED_REF3C_SHA="cae566d3ba99c69704fdb5dca21e247b3ec7d20c2e5ccc4e50b97721e8c92dec"\n'
    'EXPECTED_REF3E_SHA="8822699cc4505236c12ddd1f8156b273e0a88eaffb1ef73f73f409fc05104fc0"',
    "ref3e sha")

# precondition 11, third arm
anchor = ('[ "$ACTUAL_REF3C_SHA" = "$EXPECTED_REF3C_SHA" ] \\\n'
          '  || fail "calibration reference $REF3C_JSON is sha256 $ACTUAL_REF3C_SHA, expected $EXPECTED_REF3C_SHA'
          ' — these are not the bytes the two P-EMI parity vectors were transcribed from"')
sh = sub1(sh, anchor, anchor + '\n\n'
    '[ -f "$REF3E_JSON" ] || fail "calibration reference $REF3E_JSON not found; pass 3f cannot prove the rig reproduces the on-lattice MNT control its candidates differ from only in principal"\n'
    'ACTUAL_REF3E_SHA=$(shasum -a 256 "$REF3E_JSON" | cut -d\' \' -f1)\n'
    '[ "$ACTUAL_REF3E_SHA" = "$EXPECTED_REF3E_SHA" ] \\\n'
    '  || fail "calibration reference $REF3E_JSON is sha256 $ACTUAL_REF3E_SHA, expected $EXPECTED_REF3E_SHA — these are not the bytes the sixteen pass-3e parity vectors were transcribed from"',
    "precondition 11 third arm")

sh = sub1(sh, '        "$REF3C_JSON" "$ACTUAL_REF3C_SHA" <<\'PY\'',
              '        "$REF3C_JSON" "$ACTUAL_REF3C_SHA" "$REF3E_JSON" "$ACTUAL_REF3E_SHA" <<\'PY\'',
          "python argv")
sh = sub1(sh, " rawp, ref3b, ref3b_sha, ref3c, ref3c_sha) = sys.argv[1:18]",
              " rawp, ref3b, ref3b_sha, ref3c, ref3c_sha, ref3e, ref3e_sha) = sys.argv[1:20]",
          "python argv unpack")

sh = sub1(sh, """EXPECTED_IDS = ['P-CAL', 'P-CAL-P00', 'P-CAL-EMI6',
                'P-DRIFT-A', 'P-DRIFT-B', 'P-DRIFT-C', 'P-DRIFT-D',
                'P-DRIFT-E', 'P-DRIFT-F', 'P-DRIFT-G', 'P-DRIFT-H',
                'P-ME-A', 'P-ME-B', 'P-ME-C', 'P-ME-D',
                'P-LAT-Q0a', 'P-LAT-MID']""",
    """EXPECTED_IDS = ['P-CAL', 'P-CAL-P00', 'P-CAL-EMI6', 'P-CAL-LATQ0a',
                'T61-HE-A', 'T61-HE-B', 'T61-HE-C']""", "expected ids")

sh = sub1(sh, """CALIBRATIONS = {
    'P-CAL':      (ref3b, ref3b_sha, 'P-CAL'),
    'P-CAL-P00':  (ref3b, ref3b_sha, 'P-00'),
    'P-CAL-EMI6': (ref3c, ref3c_sha, 'P-EMI-6-1M014632'),
}
CAL_PRECISION = {'P-CAL': 12, 'P-CAL-P00': 19, 'P-CAL-EMI6': 19}""",
    """CALIBRATIONS = {
    'P-CAL':        (ref3b, ref3b_sha, 'P-CAL'),
    'P-CAL-P00':    (ref3b, ref3b_sha, 'P-00'),
    'P-CAL-EMI6':   (ref3c, ref3c_sha, 'P-EMI-6-1M014632'),
    'P-CAL-LATQ0a': (ref3e, ref3e_sha, 'P-LAT-Q0a'),
}
CAL_PRECISION = {'P-CAL': 12, 'P-CAL-P00': 19, 'P-CAL-EMI6': 19, 'P-CAL-LATQ0a': 19}""",
    "calibrations")

guarded_create(os.path.join(SRC, "run-pass3f.sh"), sh, "run-pass3f.sh", mode=0o755)

print("built .softhouse/capture/src/Capture3f.java and run-pass3f.sh from pass 3e")
