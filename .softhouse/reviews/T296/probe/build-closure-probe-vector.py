#!/usr/bin/env python3
"""T296 review probe — builds a CLOSURE-FAMILY refusal vector from T287's REAL raw
capture and points it at the capability row T294 flipped.

IT IS NOT A VECTOR FOR THE STORE and it is never written under .softhouse/vectors.
Its single purpose is to measure ONE thing: does the capability gate refuse a
vector for a shape `ledger.opening.balance.and.closure` names but this store has
never observed?  Two arms are run against it -- the merged registry
(in_graded_domain true) and a copy with the flip reverted -- and the difference
is the finding.

The provenance is REAL: capture_ref / request_capture_ref point at T287's
committed A1-01 artefacts and the sha256s are recomputed from those bytes, so the
vector clears provenance verification on its own merits rather than by exemption.
Nothing here fires a probe at the oracle. Nothing here is committed to the store.
"""
import hashlib
import json
import os

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
SRC = os.path.join(W, ".softhouse/vectors/ledger/"
                      "LDG-REFUSE-03-openingbalance-after-posted-entries.json")
CAP = os.path.join(W, ".softhouse/capture/t287-closure-refusals/out/A1-01-future-far.json")
REQ = os.path.join(W, ".softhouse/capture/t287-closure-refusals/out/A1-01-future-far.req")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "LDG-REFUSE-04-PROBE-future-dated-entry.json")


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    with open(SRC) as fh:
        v = json.load(fh)

    v["case_id"] = "LDG-REFUSE-04-PROBE-future-dated-entry"
    v["title"] = (
        "T296 REVIEW PROBE, NEVER FOR THE STORE. A CLOSURE-FAMILY refusal (the "
        "future-dated entry, one of the three shapes ledger.opening.balance.and.closure "
        "names) built from T287's REAL raw capture A1-01. Its only purpose is to measure "
        "whether the capability gate still refuses an UNOBSERVED shape after T294's flip."
    )
    v["_note"] = "T296 review probe. Not a promoted vector. Measured, then discarded."
    v["provenance"] = {
        "kind": "capture",
        "capture_ref": ".softhouse/capture/t287-closure-refusals/out/A1-01-future-far.json",
        "capture_sha256": sha(CAP),
        "capture_case_id": "A1-01-future-far",
        "request_capture_ref": ".softhouse/capture/t287-closure-refusals/out/A1-01-future-far.req",
        "request_capture_sha256": sha(REQ),
        "request_capture_case_id": "A1-01-future-far",
        "rerun_invariant": "T296 PROBE ONLY -- this vector is never promoted and never re-run.",
        "citation": "T296 review probe over T287's committed raw A1-01 artefacts.",
    }
    # A closure-family refusal is a PLAIN CREATE, so none of T294's three new
    # opening-balance inputs may be set (admit.go refuses them off that path).
    v["request"]["command"] = ""
    v["request"]["contra_gl_account_id"] = 0
    v["request"]["posted_non_contra_transaction_ids"] = []
    v["request"]["legs"] = [
        {"gl_account_id": 4, "entry_side": "DEBIT", "amount_major_text": "1000000.00"},
        {"gl_account_id": 2, "entry_side": "CREDIT", "amount_major_text": "1000000.00"},
    ]
    v["expect"]["refusal"] = {
        "http_status": 403,
        "code": "error.msg.glJournalEntry.invalid.future.date",
        "message": "The journal entry cannot be made for a future date",
    }
    # DELIBERATELY EMPTY: the point is that this vector names no kill of its own
    # and free-rides on LDG-REFUSE-03's coverage of the same capability row.
    v["graded_against"] = []

    with open(OUT, "w") as fh:
        fh.write(json.dumps(v, indent=2) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
