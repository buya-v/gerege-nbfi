#!/usr/bin/env python3
"""Compare the reference oracle's pass-3f observation against the prediction
committed BEFORE the capture ran.

The predicted values below are transcribed from `PREDICTION.md`, which is in git
one commit earlier than the capture artefact. Both are re-read from disk here so
the comparison is mechanical rather than narrated.

Money is int64 minor units. The wire text is converted by exact integer string
manipulation; a significant digit beyond the currency scale is an ERROR, never a
rounding opportunity (T17-F5).

    python3 .softhouse/capture/t61-halfeven/check-prediction.py
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CAP = os.path.join(ROOT, ".softhouse/capture/out/capture-prod3f-raw.json")

# (principal_minor, interest_minor, outstanding_minor) per REPAYMENT row,
# transcribed from PREDICTION.md, committed before the capture.
PREDICTED = {
    "T61-HE-A": [(15940901, 1800975, 84113249), (16227838, 1514038, 67885411),
                 (16519939, 1221937, 51365472), (16817298, 924578, 34548174),
                 (17120009, 621867, 17428165), (17428165, 313707, 0)],
    "T61-HE-B": [(15933110, 1800095, 84072140), (16219906, 1513299, 67852234),
                 (16511865, 1221340, 51340369), (16809078, 924127, 34531291),
                 (17111642, 621563, 17419649), (17419649, 313554, 0)],
    "T61-HE-C": [(15933700, 1800161, 84075250), (16220506, 1513355, 67854744),
                 (16512476, 1221385, 51342268), (16809700, 924161, 34532568),
                 (17112275, 621586, 17420293), (17420293, 313565, 0)],
}

# The counterfactual a HALF_EVEN port produces, measured on a scratch copy of the
# port. DERIVED, never observed. Only the cells that move are listed.
HALF_EVEN_COUNTERFACTUAL = {
    "T61-HE-A": {(1, "principal"): 15940900, (1, "outstanding"): 84113250,
                 (2, "principal"): 16227837, (2, "outstanding"): 67885413,
                 (3, "principal"): 16519938, (3, "outstanding"): 51365475},
    "T61-HE-B": {(1, "interest"): 1800094,
                 (2, "principal"): 16219905, (2, "outstanding"): 67852235,
                 (3, "principal"): 16511864, (3, "outstanding"): 51340371,
                 (4, "principal"): 16809077},
    "T61-HE-C": {(1, "principal"): 15933699, (1, "outstanding"): 84075251,
                 (2, "principal"): 16220505, (2, "outstanding"): 67854746,
                 (3, "principal"): 16512475, (3, "outstanding"): 51342271},
}


def minor(text):
    """Exact major-unit decimal text -> int64 minor units. No float, ever."""
    neg = text.startswith("-")
    t = text.lstrip("-")
    whole, _, frac = t.partition(".")
    if len(frac) > 2 and set(frac[2:]) != {"0"}:
        raise SystemExit("OVER-SCALED wire text %r: a significant digit beyond the "
                         "currency scale is a finding, not a rounding opportunity" % text)
    frac = (frac + "00")[:2]
    v = int(whole) * 100 + int(frac)
    return -v if neg else v


def main():
    caps = {c["id"]: c for c in json.load(open(CAP))["captures"]}
    total = bad = 0
    for cid, rows in PREDICTED.items():
        obs = [p for p in caps[cid]["observed"]["periods"] if p["type"] == "REPAYMENT"]
        if len(obs) != len(rows):
            sys.exit("%s: %d observed repayment rows, %d predicted" % (cid, len(obs), len(rows)))
        print("== %s" % cid)
        for i, (pp, pi, po) in enumerate(rows):
            o = obs[i]
            got = {"principal": minor(o["principal"]),
                   "interest": minor(o["interest"]),
                   "outstanding": minor(o["balance"])}
            for name, want in (("principal", pp), ("interest", pi), ("outstanding", po)):
                total += 1
                if got[name] != want:
                    bad += 1
                    print("   p%-2d %-12s predicted %-12d OBSERVED %-12d *** MISMATCH ***"
                          % (i + 1, name, want, got[name]))
                elif (i + 1, name) in HALF_EVEN_COUNTERFACTUAL[cid]:
                    cf = HALF_EVEN_COUNTERFACTUAL[cid][(i + 1, name)]
                    print("   p%-2d %-12s predicted = OBSERVED %-12d   HALF_EVEN port would emit %-12d  margin %d"
                          % (i + 1, name, want, cf, abs(want - cf)))
    print("\ncells compared against the pre-registered prediction: %d   mismatches: %d" % (total, bad))
    if bad:
        sys.exit(1)
    print("THE ORACLE CONFIRMED THE PREDICTION ON EVERY CELL.")


if __name__ == "__main__":
    main()
