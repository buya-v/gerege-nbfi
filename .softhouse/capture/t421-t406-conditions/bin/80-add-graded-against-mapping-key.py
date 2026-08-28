#!/usr/bin/env python3
"""T421 / F-T406-6 -- add the ledger-wrong-mapping-key-ignored graded_against row
to the three ACC vectors.

The row is inserted as TEXT, immediately after the opening `[` of the
"graded_against" array, so the rest of the file's bytes and its hand-authored
formatting are untouched. Exact-count discipline: the anchor must occur exactly
once or the script aborts.

The cell list and the margin were READ OUT of the arm transcript
out/T421-W02-arm-mapping-key-ignored.txt, which this script re-reads and
re-counts rather than trusting -- so the row cannot claim a kill the run did not
produce.
"""
import json, os, re, sys

VEC = ".softhouse/vectors/ledger"
ARM = ".softhouse/capture/t421-t406-conditions/out/T421-W02-arm-mapping-key-ignored.txt"

NAMES = {
    "LDG-ACC-01": "LDG-ACC-01-accrual-six-slots-runaccruals-trigger",
    "LDG-ACC-02": "LDG-ACC-02-accrual-six-slots-minor-unit-residue",
    "LDG-ACC-03": "LDG-ACC-03-accrual-six-slots-scheduled-job",
}

# --- re-count the arm's cell differences, per cell name ---------------------
arm = open(ARM).read()
diffs = re.findall(r"legs\[\d+\]\.([a-z_]+): want ", arm)
counts = {}
for d in diffs:
    counts[d] = counts.get(d, 0) + 1
total = len(re.findall(r": want .*, got ", arm))
print("ARM CELL DIFFERENCES, re-counted from the transcript:", counts, " total lines:", total)
if set(counts) != {"gl_account_id", "gl_account_code"}:
    raise SystemExit("ABORT: the arm moved cells other than the two claimed: %r" % counts)
if counts["gl_account_id"] != 18 or counts["gl_account_code"] != 18 or total != 36:
    raise SystemExit("ABORT: expected 18 + 18 = 36, measured %r / %d" % (counts, total))

ROW = '''
    {
      "impl": "ledger-wrong-mapping-key-ignored",
      "kind": "structural",
      "margin_minor": "0",
      "divergent_cells": [
        "legs[].gl_account_id",
        "legs[].gl_account_code"
      ],
      "note": "THE KILL THAT MAKES THE ACCOUNT AN OUTPUT. This vector's headline structural claim is that expect.legs[].gl_account_id and expect.legs[].gl_account_code are RESOLVED by the port and are no longer inputs the vector hands it -- 'a port that resolves slot 8 to the wrong account now differs from the expectation; before this field existed it could not'. T406 measured that NO registered wrong implementation demonstrated that: ledger-wrong-code-ignored blanks the code on every vector including the manual ones, so it says nothing about RESOLUTION, and ledger-wrong-slot-family-blind deliberately gets every account RIGHT because being blind to the FAMILY is its whole point. So the claim was TRUE and graded by nothing that had ever been watched to fail. This implementation is the measurement: it resolves every accounting-path leg to the FIRST row of the product's mapping table instead of keying that table by the leg's slot code, so all six legs land on account 35 / T388-1000 while legs[].slot_name, every side, the leg order and every money cell stay CORRECT. It is the exact mirror image of ledger-wrong-slot-family-blind -- right slot, wrong account, where that one is right account, wrong slot -- and between them the two pin down that the slot and the account are independently graded. MEASURED BY T421 on this corpus: ledger parity PASS 7 FAIL 3, oracle-refusal PASS 6 FAIL 0, divergence PASS 1 FAIL 0, so all FOURTEEN vectors that predate T391 are untouched; 36 cell differences in the entire run, 18 gl_account_id and 18 gl_account_code, and not one other cell of any kind. NOT A MONEY KILL: margin_minor is 0 because no money cell moves. (T406's review reported this shape as '12 account-id cells and 12 code cells'; T421 re-ran it rather than inheriting the number and counted 18 and 18 -- three vectors of six legs each. The kill is the same; the cardinal was wrong.)"
    },'''


for short, name in NAMES.items():
    path = os.path.join(VEC, name + ".json")
    text = open(path).read()
    if "ledger-wrong-mapping-key-ignored" in text:
        raise SystemExit("ABORT %s: already has the row" % path)
    anchor = '"graded_against": ['
    if text.count(anchor) != 1:
        raise SystemExit("ABORT %s: graded_against anchor occurs %d times"
                         % (path, text.count(anchor)))
    text = text.replace(anchor, anchor + ROW)
    open(path, "w").write(text)
    # re-parse to prove the file is still valid JSON, without floating anything
    doc = json.load(open(path), parse_float=str, parse_int=str)
    impls = [g["impl"] for g in doc["graded_against"]]
    print("%s graded_against -> %s" % (short, impls))

sys.exit(0)
