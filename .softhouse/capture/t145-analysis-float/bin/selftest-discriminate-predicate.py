#!/usr/bin/env python3
"""T145 RED/GREEN battery for the calibration predicate at
`.softhouse/capture/actualactual/analysis/discriminate.py:159-160`.

WHAT IS UNDER TEST.  Two implementations of "did the capture reproduce Fineract's own
shipped literal?", driven side by side on the same planted rows:

  ORIG  -- transcribed CHARACTER FOR CHARACTER from discriminate.py:159-160 at rev
           817d2b53.  The literal file is read by `json.load(fh)` with NO parse_float=,
           so every bare JSON number is a binary double before the predicate runs:
               want = [str(x) for x in row]
               if [float(g) for g in got] != [float(w) for w in want]:
           On no mismatch the caller prints "ALL n PERIODS REPRODUCED DIGIT FOR DIGIT".

  NEW   -- T145 R1+R2.  `json.load(fh, parse_float=Decimal)`, then TWO predicates:
               DIGIT : got == want          (exact source text -- the banner's own claim)
               VALUE : Decimal(got) == Decimal(want)

NO MONEY VALUE IS CARRIED IN A FLOAT BY THIS INSTRUMENT.  The `float()` calls inside ORIG
are the SIMULATED DEFECT -- they are the thing being measured, in the sense T207's ruling
and check_wire_float_roundtrip.py's docstring both use.  Every amount this file asserts on
is a Decimal built from exact text, and every planted literal is written as text.

EXIT 0 iff every arm behaves as PREDICTED. A RED arm that fails to go red is a dead arm.
"""
import json
import sys
from decimal import Decimal


def orig_predicate(literal_json_text, got):
    """discriminate.py:159-160, verbatim, including its json.load with no parse_float."""
    row = json.loads(literal_json_text)                       # <-- the doubles are born here
    want = [str(x) for x in row]                              # :159
    mism = [float(g) for g in got] != [float(w) for w in want]  # :160
    return (not mism), want


def new_predicate(literal_json_text, got):
    """T145 R1 + R2."""
    row = json.loads(literal_json_text, parse_float=Decimal)  # R1
    want = [str(x) for x in row]
    digit_ok = got == want                                   # R2 -- the banner's own claim
    value_ok = [Decimal(g) for g in got] == [Decimal(w) for w in want]
    return digit_ok, value_ok, want


ARMS = [
    # (name, literal row as SOURCE TEXT, captured cells as exact text,
    #  predicted ORIG verdict, predicted NEW digit, predicted NEW value, why)
    ("GREEN  real S1 row 0",
     "[1713.21, 80.53, 1632.68, 8367.32]",
     ["1713.21", "80.53", "1632.68", "8367.32"],
     True, True, True,
     "the honest case: text, value and the banner all agree"),

    ("RED-A  real S1 FINAL row -- ORIG's own `want` is not digit-identical",
     "[1713.18, 13.69, 1699.49, 0.00]",
     ["1713.18", "13.69", "1699.49", "0.00"],
     True, True, True,
     "ORIG passes and prints DIGIT FOR DIGIT, but its own want list holds '0.0' while the "
     "capture holds '0.00'. The banner asserts a text identity ORIG never checked and which "
     "was FALSE of the strings it actually held. R1 restores the scale, so NEW's DIGIT "
     "predicate is true ON THE EXACT TEXT rather than true by accident."),

    ("RED-B  VALUE LOSS -- two different amounts, one double",
     "[9007199254740993.00, 13.69, 1699.49, 0.00]",
     ["9007199254740992.00", "13.69", "1699.49", "0.00"],
     True, False, False,
     "2**53+1 vs 2**53: the amounts differ by a whole unit and ORIG says they match. THIS IS "
     "THE MONEY KILL -- ORIG prints 'REPRODUCED DIGIT FOR DIGIT' over a one-unit discrepancy."),

    ("RED-C  SCALE LOSS -- DECIMAL(19,6) shape vs a 1-place literal",
     "[1200.0, 13.69, 1699.49, 0.00]",
     ["1200.000000", "13.69", "1699.49", "0.00"],
     True, False, True,
     "the oracle's own scale-6 emission (T186 rule A4). Value intact, text not identical. "
     "ORIG prints DIGIT FOR DIGIT anyway; NEW says EQUAL IN VALUE, NOT digit for digit."),

    # PREDICTION REFUTED AND CORRECTED, recorded rather than quietly rewritten.
    # T145's FIRST RED-D was [10000000000000.01] vs "10000000000000.02" -- ~10 trillion at
    # scale 2 -- predicted to collide in binary64. IT DOES NOT: that is 16 significant
    # digits and binary64 separates it (measured: float('10000000000000.01') !=
    # float('10000000000000.02')). The arm printed "!! WRONG" and the battery exited 1.
    # The corrected arm below uses Fineract's OWN DECIMAL(19,6) scale, where 10 billion MNT
    # at six decimals is 17 significant digits and the collision is real.
    ("RED-D  DECIMAL(19,6) money at 17 significant digits",
     "[10000000000.000001, 13.69, 1699.49, 0.00]",
     ["10000000000.000002", "13.69", "1699.49", "0.00"],
     True, False, False,
     "10,000,000,000 MNT at Fineract's own numeric(19,6) scale, differing by one unit in "
     "the last place the SCHEMA can represent. binary64 cannot separate them, so ORIG "
     "reports DIGIT FOR DIGIT. This is not a contrived magnitude: it is in-schema."),
]


def main():
    print("T145 -- RED/GREEN battery for discriminate.py:159-160")
    print("SELECTOR: predicate text transcribed from")
    print("          .softhouse/capture/actualactual/analysis/discriminate.py:159-160 @ 817d2b53")
    print("python: %s" % sys.version.split()[0])
    print()
    bad = 0
    for name, lit, got, p_orig, p_digit, p_value, why in ARMS:
        o_ok, o_want = orig_predicate(lit, got)
        n_digit, n_value, n_want = new_predicate(lit, got)
        ok = (o_ok == p_orig) and (n_digit == p_digit) and (n_value == p_value)
        # the banner ORIG would print, reconstructed from discriminate.py:161-163
        banner = ("ALL %d PERIODS REPRODUCED DIGIT FOR DIGIT" % 1) if o_ok else "MISMATCH"
        print("%-8s %s" % ("AS PRED." if ok else "!! WRONG", name))
        print("           literal source text : %s" % lit)
        print("           captured exact text : %s" % got)
        print("           ORIG want (post-double) : %s" % o_want)
        print("           NEW  want (post-Decimal): %s" % n_want)
        print("           ORIG says match=%-5s -> it prints: %s" % (o_ok, banner))
        print("           NEW  DIGIT=%-5s  VALUE=%-5s" % (n_digit, n_value))
        print("           why: %s" % why)
        print()
        if not ok:
            bad += 1
    # the headline claim, asserted rather than narrated
    orig_b, _ = orig_predicate(ARMS[2][1], ARMS[2][2])
    _, new_v, _ = new_predicate(ARMS[2][1], ARMS[2][2])
    print("HEADLINE  on RED-B (amounts differ by a whole unit):")
    print("          ORIG reaches 'REPRODUCED DIGIT FOR DIGIT' : %s" % orig_b)
    print("          NEW  VALUE predicate holds                : %s" % new_v)
    assert orig_b is True and new_v is False, "RED-B did not go red -- the arm is dead"
    print()
    print("ARMS: %d   AS PREDICTED: %d   WRONG: %d" % (len(ARMS), len(ARMS) - bad, bad))
    if bad:
        print("BATTERY FAILED")
        return 1
    print("BATTERY PASS -- every arm behaved as predicted")
    return 0


sys.exit(main())
