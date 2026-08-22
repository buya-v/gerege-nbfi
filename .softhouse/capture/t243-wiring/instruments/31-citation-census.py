#!/usr/bin/env python3
"""T243 — where PART TWO of every ledger capture citation actually resolves.

INDEPENDENT OF THE GO CODE ON PURPOSE. admit.go's citationMode is the thing
under test; a census that called it would agree with it by construction, which
is the shape of every tautological check this task exists to remove. This
re-implements the three branches from T233's rule as stated in prose and reports
where each of the twelve citations lands.

ENGINE: python3 `str.__contains__` over bytes read from disk. No grep, no rg
(P-75: in an agent shell `grep` is a function that execs ugrep with
`--ignore-files` prepended, and `rg` does not exist inside a script at all).

CALIBRATION, both directions, run before any result is printed:
  known POSITIVE — the case id must be found in an artefact that contains it;
  known NEGATIVE — a case id that is nowhere must be found nowhere.
A failure of either aborts with exit 2 rather than reporting a census.
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
if not ROOT or not os.path.isdir(ROOT):
    print("CENSUS ABORT (2): not inside a git work tree", file=sys.stderr)
    sys.exit(2)
os.chdir(ROOT)

LEDGER = os.path.join(".softhouse", "vectors", "ledger")
files = sorted(f for f in os.listdir(LEDGER) if f.endswith(".json"))
if not files:
    print("CENSUS ABORT (2): zero ledger vectors; censusing nothing proves nothing (P-35)",
          file=sys.stderr)
    sys.exit(2)


def where(ref, case_id):
    """The three branches of part two, in the order admit.go tries them."""
    if not ref or not case_id or os.path.isabs(ref):
        return "UNRESOLVED", None
    abs_ = os.path.join(ROOT, ref)
    try:
        raw = open(abs_, "rb").read()
    except OSError:
        return "UNRESOLVED", None
    if case_id.encode() in raw:
        return "ARTEFACT-BYTES", hashlib.sha256(raw).hexdigest()
    base = os.path.splitext(abs_)[0]
    if base.endswith(".req"):
        base = base[:-4]
    side = base + ".http"
    if os.path.exists(side) and case_id.encode() in open(side, "rb").read():
        return "HTTP-SIDECAR", hashlib.sha256(raw).hexdigest()
    if case_id in os.path.basename(abs_):
        return "FILE-NAME-ONLY", hashlib.sha256(raw).hexdigest()
    return "UNRESOLVED", hashlib.sha256(raw).hexdigest()


# --- CALIBRATION (P-72, both directions) ------------------------------------
probe = os.path.join(".softhouse", "capture", "tierA-a2", "out",
                     "A2-390-db-ledger-state-a2-15.json")
pos, _ = where(probe, "A2-390-db-ledger-state-a2-15")
neg, _ = where(probe, "A2-000-THIS-CASE-ID-EXISTS-NOWHERE")
if pos != "ARTEFACT-BYTES":
    print("CENSUS ABORT (2): known POSITIVE did not resolve in bytes (%s)" % pos, file=sys.stderr)
    sys.exit(2)
if neg != "UNRESOLVED":
    print("CENSUS ABORT (2): known NEGATIVE resolved as %s — the matcher fabricates" % neg,
          file=sys.stderr)
    sys.exit(2)
print("  CALIBRATE+ known positive resolves ARTEFACT-BYTES; "
      "CALIBRATE- known negative resolves UNRESOLVED. Matcher trusted.")

tally = {}
rows = 0
for f in files:
    v = json.load(open(os.path.join(LEDGER, f), encoding="utf-8"))
    p = v["provenance"]
    for field, ref, cid, want_sha in (
            ("capture_ref", p.get("capture_ref"), p.get("capture_case_id"),
             p.get("capture_sha256")),
            ("request_capture_ref", p.get("request_capture_ref"),
             p.get("request_capture_case_id"), p.get("request_capture_sha256"))):
        mode, sha = where(ref, cid)
        tally[mode] = tally.get(mode, 0) + 1
        rows += 1
        agree = "sha OK" if sha and want_sha and sha.lower() == want_sha.lower() else "SHA MISMATCH"
        print("  %-46s %-20s %-15s %s" % (v["case_id"][:46], field, mode, agree))
print("  ---")
print("  %d citations over %d vectors: %s" % (
    rows, len(files), ", ".join("%s %d" % (k, tally[k]) for k in sorted(tally))))
