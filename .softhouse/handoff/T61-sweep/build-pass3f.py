#!/usr/bin/env python3
"""Construct capture pass 3f MECHANICALLY from pass 3e.

Pass 3f is pass 3e's rig with a new case list and a FOURTH rig calibration --
exactly the relationship pass 3c has to pass 3b (`README-pass3c.md`). Building it
by transformation rather than by hand is deliberate: it makes "not one
precondition was weakened" a property of the construction instead of a claim in a
comment. The script asserts that every substitution it makes actually matched.

    python3 .softhouse/handoff/T61-sweep/build-pass3f.py
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, ".softhouse/capture/src")


def sub1(text, old, new, what):
    if text.count(old) < 1:
        sys.exit("BUILD FAILED: anchor not found (%s)" % what)
    return text.replace(old, new)


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

open(os.path.join(SRC, "Capture3f.java"), "w").write(java)

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

open(os.path.join(SRC, "run-pass3f.sh"), "w").write(sh)
os.chmod(os.path.join(SRC, "run-pass3f.sh"), 0o755)

print("built .softhouse/capture/src/Capture3f.java and run-pass3f.sh from pass 3e")
