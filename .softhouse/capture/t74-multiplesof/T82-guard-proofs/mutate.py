#!/usr/bin/env python3
"""T82 — build the inputs that SHOULD make each rewritten guard go red.

    python3 mutate.py <mode> <run-pass3i.sh> <capture.json> <out-script> <out-capture>

Writes a mutated COPY of the script and/or of the capture. Never writes to the originals.

Every mutation is a plausible FUTURE EDIT rather than a contrived one, because a guard is only worth
what it catches in the edit somebody will actually make:

  add-unregistered-case   somebody adds a case to the harness and to EXPECTED_IDS and forgets the
                          precision table
  restore-old-table       the pre-T82 self-constructing table, so the same edit can be run through
                          the OLD guard and shown to sail past it
  add-stale-entry         somebody removes a case but leaves its table entry behind
  wrong-precision         a case runs at a precision its table entry forbids
  unnamed-probe           somebody registers a NON-`-p12` case at precision 12 — a discrimination
                          probe with a parity candidate's name
  both-arms-half-down     both counterfactual arms at a non-ratified rounding mode (E-3's hole)
  one-arm-half-down       one arm at a non-ratified rounding mode

Money is never touched: no mutation here alters a principal, an interest figure, a balance or a
total. These edit ids, precisions and rounding-mode labels only.
"""
import json
import shutil
import sys


def load(p):
    return json.load(open(p, encoding="utf-8"))


def dump(doc, p):
    json.dump(doc, open(p, "w", encoding="utf-8"), indent=2)


def case(doc, cid):
    for c in doc["captures"]:
        if c["id"] == cid:
            return c
    raise SystemExit("no such case %r" % cid)


NEW_ID = "T82-PROOF-UNREGISTERED-CASE"
STALE_ID = "T82-PROOF-STALE-ENTRY"

OLD_TABLE_START = "CASE_PRECISION = {"
OLD_TABLE = """CASE_PRECISION = {'P-CAL': 12}
for _id in EXPECTED_IDS:
    if _id not in CASE_PRECISION:
        CASE_PRECISION[_id] = 12 if _id.endswith('-p12') else 19
_unregistered = [i for i in EXPECTED_IDS if i not in CASE_PRECISION]
if _unregistered:
    sys.exit("RUN FAILED: no expected MathContext precision registered for %r" % _unregistered)
"""


def replace_table(text, replacement):
    """Swap the whole CASE_PRECISION block (dict literal + the two checks after it)."""
    start = text.index(OLD_TABLE_START)
    end = text.index("# --- 16. ADDED BY PASS 3i: FIELD SEPARATION", start)
    return text[:start] + replacement + "\n" + text[end:]


def main(mode, script, capture, out_script, out_capture):
    text = open(script, encoding="utf-8").read()
    doc = load(capture)

    if mode == "add-unregistered-case":
        # 1. the script gains the id in EXPECTED_IDS and NOTHING in CASE_PRECISION
        old = "'T74-E-P6940', 'T74-E-P6940-p12']"
        assert text.count(old) == 1, "anchor not unique in EXPECTED_IDS"
        text = text.replace(old, "'T74-E-P6940', 'T74-E-P6940-p12',\n                '%s']" % NEW_ID)
        # 2. the capture gains that case, so check 8 (the id list) still passes and the run reaches
        #    guard 17. Cloned from an existing case; not one money cell is edited.
        clone = json.loads(json.dumps(case(doc, "T74-E-P4")))
        clone["id"] = NEW_ID
        doc["captures"].append(clone)
        print("script:  EXPECTED_IDS += %r  (CASE_PRECISION deliberately NOT updated)" % NEW_ID)
        print("capture: appended a clone of T74-E-P4 under id %r, money untouched" % NEW_ID)

    elif mode == "restore-old-table":
        text = replace_table(text, OLD_TABLE)
        print("script:  CASE_PRECISION reverted to the pre-T82 self-constructing form")
        print("         (the id-suffix default: endswith('-p12') -> 12, else 19)")

    elif mode == "add-stale-entry":
        anchor = "    'T74-E-P6940-p12':           12,\n"
        assert text.count(anchor) == 1, "anchor not unique in CASE_PRECISION"
        text = text.replace(anchor, anchor + "    '%s':    19,\n" % STALE_ID)
        print("script:  CASE_PRECISION += %r, an id this run does not capture" % STALE_ID)

    elif mode == "wrong-precision":
        c = case(doc, "T74-E-P4")
        c["inputs"]["mathContextPrecision"] = 12
        print("capture: T74-E-P4 mathContextPrecision 19 -> 12 "
              "(CASE_PRECISION registers it at 19); money untouched")

    elif mode == "unnamed-probe":
        anchor = "    'T74-A0-DP0-NONE':           19,\n"
        assert text.count(anchor) == 1, "anchor not unique in CASE_PRECISION"
        text = text.replace(anchor, "    'T74-A0-DP0-NONE':           12,\n")
        c = case(doc, "T74-A0-DP0-NONE")
        c["inputs"]["mathContextPrecision"] = 12
        print("script:  CASE_PRECISION['T74-A0-DP0-NONE'] 19 -> 12")
        print("capture: T74-A0-DP0-NONE mathContextPrecision 19 -> 12, money untouched")
        print("         so guard 17 is SATISFIED and guard 18 is the one that must catch it")

    elif mode in ("both-arms-half-down", "one-arm-half-down"):
        arms = ["T74-E-P4-p12"] if mode == "one-arm-half-down" else ["T74-E-P4", "T74-E-P4-p12"]
        for cid in arms:
            c = case(doc, cid)
            c["inputs"]["mathContextRoundingMode"] = "HALF_DOWN"
            c["inputs"]["mathContextRoundingModeOrdinal"] = 5
        print("capture: rounding mode HALF_UP -> HALF_DOWN on %r; money untouched" % arms)

    else:
        raise SystemExit("unknown mode %r" % mode)

    if text == open(script, encoding="utf-8").read():
        shutil.copyfile(script, out_script)
    else:
        open(out_script, "w", encoding="utf-8").write(text)
    dump(doc, out_capture)


if __name__ == "__main__":
    main(*sys.argv[1:6])
