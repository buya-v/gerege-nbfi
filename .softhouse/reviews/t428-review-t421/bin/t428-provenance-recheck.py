#!/usr/bin/env python3
"""T428 -- INDEPENDENT re-derivation of T421's captured_at provenance.

Unlike T421's emitter, this script hard-codes NO digest. For each ledger vector
that carries a provenance.request_capture_ref, it:

  1. reads the digest the VECTOR ITSELF cites (provenance.request_capture_sha256),
  2. hashes the referenced .http record,
  3. ASSERTS EQUALITY BEFORE parsing a single header out of that record,
  4. only then reads `captured-at-utc:` out of it,
  5. compares it, as a STRING, with oracle.captured_at in the vector.

No value is parsed as a number anywhere: json is decoded with parse_float=str and
parse_int=str, and every comparison below is a string comparison.
"""
import json, hashlib, os, sys

ROOT = sys.argv[1]
VDIR = os.path.join(ROOT, ".softhouse/vectors/ledger")

rows = []
for name in sorted(os.listdir(VDIR)):
    if not name.endswith(".json"):
        continue
    path = os.path.join(VDIR, name)
    with open(path) as fh:
        d = json.load(fh, parse_float=str, parse_int=str)
    prov = d.get("provenance") or {}
    ref = prov.get("request_capture_ref")
    cited = prov.get("request_capture_sha256")
    cap = (d.get("oracle") or {}).get("captured_at")
    if not ref or not cited:
        rows.append((name, "NO request_capture_ref", cap, "-", "-", "-"))
        continue
    hp = os.path.join(ROOT, ref)
    if not os.path.exists(hp):
        rows.append((name, "MISSING " + ref, cap, cited, "-", "FAIL-missing"))
        continue
    with open(hp, "rb") as fh:
        raw = fh.read()
    got = hashlib.sha256(raw).hexdigest()
    digest_ok = (got == cited)
    if not digest_ok:
        # DO NOT read the header out of a record whose digest does not match.
        rows.append((name, ref, cap, cited, got, "FAIL-digest"))
        continue
    hdr = None
    for line in raw.decode("utf-8", "replace").splitlines():
        if line.startswith("captured-at-utc:"):
            hdr = line.split(":", 1)[1].strip()
            break
    verdict = "MATCH" if (hdr is not None and cap == hdr) else "MISMATCH"
    rows.append((name, ref, cap, "digest OK", hdr, verdict))

print("T428 PROVENANCE RE-DERIVATION -- hash first, read second")
print("root:", ROOT)
print()
bad = 0
for name, ref, cap, cited, hdr, verdict in rows:
    print("%-56s" % name)
    print("    oracle.captured_at   %s" % cap)
    print("    request_capture_ref  %s" % ref)
    print("    digest               %s" % cited)
    print("    captured-at-utc      %s" % hdr)
    print("    VERDICT              %s" % verdict)
    if verdict.startswith("FAIL") or verdict == "MISMATCH":
        bad += 1
print()
print("VECTORS CHECKED %d   FAILURES %d" % (len(rows), bad))
sys.exit(1 if bad else 0)
