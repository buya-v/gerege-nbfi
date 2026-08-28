#!/usr/bin/env python3
"""T397 -- re-drive T387's SIXTEEN authoring attacks against the T397 tree.

Every attack is T387's own, reconstructed from its committed instruments
(.softhouse/reviews/t387-review-t360/instruments/attack{,2,3,4,_capture}.py) and
re-pointed at THIS worktree. Each is planted on the real committed store, driven
through the real conformance binary at full store, and then reverted with
`git checkout --` before the next one is planted.

WHAT COUNTS AS "STILL REFUSED", stated so it cannot be softened later:
  * the run must NOT exit 0, AND
  * the divergence vector must be reported INADMISSIBLE (or, for A5, some vector
    must be), AND
  * the refusal reason T387 recorded must still be among the reasons printed.
A run that merely went red is not a pass here -- a vector that FAILED grading
instead of being REFUSED ADMISSION would mean the default-deny had been lost and
the corpus was relying on the comparator, which is the exact P-45 shape this task
exists to remove from one place.

A16 IS EXPECTED TO GAIN A REASON. T387 built A16 ON TOP of the F-T387-2 hole --
it truncates the request legs to "100.12" precisely because bytes.Contains
accepted the prefix -- so after T397 it is refused by the NEW boundary rule as
well as by the pre-existing date/outcome conflict rule. Both are asserted.
"""

import copy
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
OUT = os.path.join(ROOT, ".softhouse", "capture", "t397-t387-conditions", "out", "attacks")
VEC = os.path.join(ROOT, ".softhouse", "vectors", "ledger",
                   "LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json")
LDG01 = os.path.join(ROOT, ".softhouse", "vectors", "ledger",
                     "LDG-01-manual-je-3leg-minor-units.json")
CAP = os.path.join(ROOT, ".softhouse", "capture", "t352-a2-next-tranche", "out",
                   "T352-A09-residue-3dp-readback-cited.json")
BIN = sys.argv[1] if len(sys.argv) > 1 else "/tmp/t397-conf"


def git_restore():
    subprocess.check_call(["git", "checkout", "--", ".softhouse/vectors/",
                           ".softhouse/capture/t352-a2-next-tranche/"], cwd=ROOT)


def write(path, doc):
    with open(path, "w") as f:
        f.write(json.dumps(doc, indent=2) + "\n")


def load(path):
    with open(path) as f:
        return json.load(f)


# --- the sixteen plants -----------------------------------------------------

def a1(d):
    d["expect"]["legs"] = [
        {"gl_account_id": 16, "entry_side": "DEBIT", "amount_minor": "10013",
         "amount_major_text": "100.125000", "gl_account_code": "10300"},
        {"gl_account_id": 21, "entry_side": "CREDIT", "amount_minor": "10013",
         "amount_major_text": "100.125000", "gl_account_code": "99008"}]
    write(VEC, d)


def a2(d):
    d["expect"]["total_debits_minor"] = "10013"
    d["expect"]["total_credits_minor"] = "10013"
    write(VEC, d)


def a3(d):
    d["expect"]["refusal"] = {"http_status": 422, "code": "error.msg.residue",
                              "message": "residue"}
    write(VEC, d)


def a4(d):
    d["expect"]["http_status"] = 422
    write(VEC, d)


def a5(_d):
    p = load(LDG01)
    p["oracle_accepted"] = {"http_status": 200,
                            "observed_amount_texts": ["100.125000"],
                            "why_unrepresentable": "smuggled by T387, re-driven by T397",
                            "gate": "G-19"}
    write(LDG01, p)


def a6(d):
    d["oracle_accepted"]["observed_amount_texts"] = ["100.125001"]
    write(VEC, d)


def a7(d):
    d["oracle_accepted"]["observed_amount_texts"] = ["100.120000"]
    write(VEC, d)


def a8(d):
    d["expect"]["port_refusal"]["marker"] = "residue"
    write(VEC, d)


def a9(d):
    # The capture artefact itself is mutated by ONE digit AND the vector's sha
    # pin is refreshed, so the digest cannot be what catches it. The verbatim
    # check must fire on its own.
    with open(CAP, "rb") as f:
        raw = f.read()
    assert raw.count(b"100.125000") >= 1
    mut = raw.replace(b"100.125000", b"100.125001")
    with open(CAP, "wb") as f:
        f.write(mut)
    d["provenance"]["capture_sha256"] = hashlib.sha256(mut).hexdigest()
    write(VEC, d)


def a10(d):
    d["class"] = "parity"
    write(VEC, d)


def a11(d):
    d["class"] = "oracle-refusal"
    write(VEC, d)


def a12(d):
    d["expect"]["kind"] = "journal-entry"
    write(VEC, d)


def a13(d):
    d["expect"]["port_refusal"]["marker"] = "carries sub-minor-unit residue at scale 7"
    write(VEC, d)


def a14(d):
    d["oracle_accepted"]["gate"] = ""
    write(VEC, d)


def a15(d):
    d["request"]["legs"][0]["gl_account_id"] = 99
    d["request"]["accounts"] = [a for a in d["request"]["accounts"] if a["id"] != 99]
    d["expect"]["port_refusal"]["marker"] = "which the vector's chart does not carry"
    d["expect"]["port_refusal"]["observed_text"] = (
        "leg 0 points at GL account 99, which the vector's chart does not carry")
    write(VEC, d)


def a16(d):
    for leg in d["request"]["legs"]:
        leg["amount_major_text"] = "100.12"
    d["request"]["business_date"] = "2026-06-01"
    d["request"]["transaction_date"] = "2026-06-02"
    d["expect"]["port_refusal"]["marker"] = "cannot be made for a future date"
    d["expect"]["port_refusal"]["observed_text"] = (
        "The journal entry cannot be made for a future date")
    write(VEC, d)


ATTACKS = [
    ("A1-expect-legs-10013", a1, ["NEITHER SYSTEM PRODUCED"]),
    ("A2-totals-minor", a2, ["the port posted nothing to total"]),
    ("A3-expect-refusal", a3, ["the oracle did not refuse"]),
    ("A4-expect-http-status", a4, ["this port produces no HTTP response at all"]),
    ("A5-oracle-accepted-on-parity", a5, ["oracle_accepted"]),
    ("A6-one-digit-mutated", a6, ["DO NOT OCCUR in provenance.capture_ref"]),
    ("A7-representable", a7, ["belongs in the PARITY class"]),
    ("A8-short-marker", a8, ["contained in almost any refusal text"]),
    ("A9-capture-digit-mutated-sha-refreshed", a9,
     ["DO NOT OCCUR in provenance.capture_ref"]),
    ("A10-divergence-relabelled-parity", a10, ["DIVERGENCE POPULATION 0, PINNED 1"]),
    ("A11-divergence-relabelled-oracle-refusal", a11, ["DIVERGENCE POPULATION 0, PINNED 1"]),
    ("A12-divergence-with-journal-entry-kind", a12, ["INADMISSIBLE"]),
    ("A13-marker-not-in-observed-text", a13, ["was never cut from it"]),
    ("A14-gate-empty", a14, ["gate"]),
    ("A15-refusal-for-an-unrelated-reason", a15, ["INADMISSIBLE"]),
    # A16 must now ALSO trip the new boundary rule, because T387 built it on the
    # F-T387-2 hole.
    ("A16-graded-on-an-unrelated-refusal", a16,
     ["ONLY GLUED TO A LONGER NUMBER", "INADMISSIBLE"]),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    git_restore()
    rows = []
    for name, plant, wants in ATTACKS:
        plant(load(VEC))
        proc = subprocess.run([BIN, "-oracle-probe", "up"], cwd=ROOT,
                              capture_output=True, text=True)
        log = proc.stdout + proc.stderr
        with open(os.path.join(OUT, name + ".log"), "w") as f:
            f.write(log)
            f.write("\nexit=%d\n" % proc.returncode)
        inadmissible = ("INADMISSIBLE" in log) or ("DIVERGENCE POPULATION" in log)
        missing = [w for w in wants if w not in log]
        ok = proc.returncode != 0 and inadmissible and not missing
        rows.append((name, proc.returncode, inadmissible, missing, ok))
        git_restore()

    dirty = subprocess.run(["git", "status", "--porcelain",
                            ".softhouse/vectors/", ".softhouse/capture/t352-a2-next-tranche/"],
                           cwd=ROOT, capture_output=True, text=True).stdout.strip()

    lines = ["T397 -- re-drive of T387's SIXTEEN authoring attacks, after the T397 change", ""]
    for name, rc, inad, missing, ok in rows:
        lines.append("%-46s exit=%-2d refused=%-5s %s%s" % (
            name, rc, inad, "REFUSED" if ok else "*** NOT REFUSED ***",
            "" if not missing else "  MISSING REASON: %r" % missing))
    refused = sum(1 for r in rows if r[4])
    lines += ["", "%d of %d attacks REFUSED" % (refused, len(rows)),
              "store clean after the drive: %s" % ("YES" if dirty == "" else "NO -- " + dirty)]
    report = "\n".join(lines) + "\n"
    with open(os.path.join(OUT, "SUMMARY.txt"), "w") as f:
        f.write(report)
    print(report)
    if refused != len(rows) or dirty != "":
        sys.exit(1)


if __name__ == "__main__":
    main()
