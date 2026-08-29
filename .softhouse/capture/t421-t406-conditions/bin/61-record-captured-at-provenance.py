#!/usr/bin/env python3
"""T421 / F-T406-1 second half -- say IN THE VECTOR where oracle.captured_at came
from, so the next reader does not have to reconstruct it from a handoff.

Exact-count byte replacement, same discipline as 60-.
"""
import os

VEC = ".softhouse/vectors/ledger"
SRC = {
    "LDG-ACC-01-accrual-six-slots-runaccruals-trigger": ("T391-A01-je-L29.http", "2026-08-28T17:10:23Z"),
    "LDG-ACC-02-accrual-six-slots-minor-unit-residue":  ("T391-A02-je-L30.http", "2026-08-28T17:10:28Z"),
    "LDG-ACC-03-accrual-six-slots-scheduled-job":       ("T391-A04-je-L32.http", "2026-08-28T17:10:28Z"),
}
ANCHOR = "HOW THE TRANSACTION CAME TO EXIST:"

for name, (http, ts) in SRC.items():
    path = os.path.join(VEC, name + ".json")
    text = open(path).read()
    ins = ("WHERE oracle.captured_at COMES FROM [T421, closing T406's F-T406-1]: it is the "
           "captured-at-utc header of " + http + ", the digest-pinned request record this "
           "vector already names as provenance.request_capture_ref -- " + ts + ", the instant "
           "the observation was ACTUALLY taken, and T421 re-verified that record's sha256 "
           "against the digest cited here before reading the header out of it. T391 carried "
           "2026-08-29T09:00:00Z in this field: a round hour about sixteen hours AFTER the "
           "capture it described, still in the FUTURE when T406 read it, and the only "
           "round-hour captured_at in the entire vector store. It was a stamped value, not an "
           "observed one. Provenance metadata is held to the same rule as money here, because "
           "provenance is the whole reason a later reader trusts the money beside it. ")
    n = text.count(ANCHOR)
    if n != 1:
        raise SystemExit("ABORT %s: anchor occurs %d times" % (path, n))
    if "WHERE oracle.captured_at COMES FROM" in text:
        raise SystemExit("ABORT %s: already annotated" % path)
    open(path, "w").write(text.replace(ANCHOR, ins + ANCHOR))
    print("captured_at provenance recorded in", name)
