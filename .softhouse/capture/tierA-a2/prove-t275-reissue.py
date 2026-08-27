#!/usr/bin/env python3
"""T275 -- PROVE the recipes this task added actually re-issue, and prove the proof can fail.

  python3 prove-t275-reissue.py            run every leg
  exit 0  every leg held;  exit 1  at least one leg failed

WHY THIS FILE EXISTS
--------------------
DEFECTS-FOUND-BY-REVIEW.md D-1: ten `attempt1-*` recipes in this directory are PROVABLY
FALSE. Each `.http` record says `body-file: req/foo.json`, and `mkreq2.py` later OVERWROTE
that file, so the recipe names a body that is not the body which produced the recorded
response. Nothing went red. The corpus carried ten lies for a day.

T275's standing instruction was: do not add an eleventh. That cannot be discharged by
saying "my recipes are fine". It needs a CHECK, the check needs to be capable of failing,
and the failure has to be demonstrated against real bytes rather than asserted.

THREE LEGS, and each says something different:

  LEG 1  STALENESS. For every capture, is the request the recipe NAMES still byte-identical
         to the request that was actually SENT? cap8.sh commits the wire bytes as
         out/NAME.req and their digest as `body-sha256:`, so this is decidable. It is
         decidable for capsql.sh's SQL captures the same way (out/NAME.sql).
         Three outcomes, and UNVERIFIABLE is NOT a pass:
           VERIFIED     the named file, the committed wire bytes and the recorded digest
                        all agree -- the recipe re-issues the same request today
           STALE        they disagree -- this is the D-1 defect, live
           UNVERIFIABLE the capture predates the wire-byte record (cap.sh era). Nothing
                        can be concluded. All 10 attempt1-* recipes land here, which is
                        the honest statement about them: they are not "fine", they are
                        BEYOND THE REACH OF ANY CHECK.

  LEG 2  FAILABILITY, driven against real bytes. LEG 1 is re-run over a scratch COPY of the
         tree in which exactly one request body has had one byte changed. If LEG 1 does not
         go STALE on precisely that capture and stay VERIFIED on the others, LEG 1 is a
         guard that cannot fail (P-22) and this script exits 1.

  LEG 3  ACTUAL RE-ISSUE. The IDEMPOTENT captures -- the read-only GET and the SQL
         snapshots -- are SENT AGAIN, right now, through the committed instruments
         (cap8.sh / capsql.sh) running against a scratch out/ directory, and the returned
         bytes are compared with the committed bytes. This is the only leg that observes
         the oracle rather than reasoning about files.

WHAT THIS SCRIPT DELIBERATELY DOES NOT CLAIM
--------------------------------------------
The MUTATING captures (every PUT and POST T275 took) CANNOT re-issue to the same response,
and no honest proof can say they do. A2-502 re-pointed a mapping; sending it again finds the
mapping already re-pointed. A2-522 created product 56; sending it again is refused for a
duplicate short name. Their re-issuability is a statement about the REQUEST, not the
response, and about a stated PRECONDITION -- both of which LEG 1 checks and this script
prints explicitly rather than glossing. Claiming byte-identical replay for a mutating call
would be the same class of overstatement A2-5 had to correct in CAPTURE-PLAN.md §6.

Numbers are compared as TEXT. Nothing here parses a monetary value at all, and no float
appears in any comparison.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DIR, "out")

# The captures T275 took. Split by whether re-issuing them is even meaningful.
IDEMPOTENT_HTTP = [
    ("A2-521-loanproduct23-after-channel-repoint", "GET", "/loanproducts/23"),
    ("A2-523-prod-charge-mappings-readback", "GET", "/loanproducts/56"),
]

# READ-ONLY BUT SUPERSEDED, and the distinction is not pedantry.
#
# A2-501 and A2-512 are GETs -- they wrote nothing. The FIRST draft of this script
# classified them as idempotent on that basis and LEG 3 FAILED THEM, which is the guard
# working: a GET is only replayable while the state it reads still exists, and this fire's
# OWN writes moved product 23 between A2-501, A2-512 and A2-521. Loosening the check to
# make them pass would have been the exact move that produced D-1 -- declaring a recipe
# reproducible because it looked like it ought to be.
#
# So they are re-issued too, and the assertion is INVERTED and made specific: a fresh read
# today must DIFFER from each superseded snapshot and must EQUAL the current-state one.
# That distinguishes "the state moved, as this fire's own captures say it did" from "the
# instrument is nondeterministic", which a bare mismatch could not.
SUPERSEDED_READ = [
    ("A2-501-loanproduct23-before", "GET", "/loanproducts/23"),
    ("A2-512-loanproduct23-final", "GET", "/loanproducts/23"),
]
CURRENT_FOR_SUPERSEDED = "A2-521-loanproduct23-after-channel-repoint"
IDEMPOTENT_SQL = [
    ("A2-544-db-mapping-after-reason-probes", "sql/q8-t275-mapping-ids.sql"),
    ("A2-520-db-fixtures", "sql/q9-t275-fixture-state.sql"),
]
MUTATING = [
    "A2-502-p23-repoint-fundsource", "A2-505-p23-add-channel",
    "A2-508-p23-description-only", "A2-510-p23-channel-empty",
    "A2-514-p23-channel-readd", "A2-516-p23-channel-resend-identical",
    "A2-518-p23-channel-repoint",
    "A2-522-prod-charge-mappings", "A2-524-prod-fee-charge-not-attached",
    "A2-525-prod-penalty-mapping-on-fee-charge",
    "A2-526-prod-fee-income-expense-account", "A2-527-prod-duplicate-fee-charge",
    "A2-540-prod-writeoff-reason-dangling",
    "A2-541-prod-writeoff-reason-dangling-nonexpense",
    "A2-542-prod-chargeoff-reason-dangling",
    "A2-543-prod-chargeoff-reason-dangling-nonexpense",
]

fails = []


def ok(msg):
    print(f"  PASS  {msg}")


def bad(msg):
    print(f"  FAIL  {msg}", file=sys.stderr)
    fails.append(msg)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def kv(path):
    """Parse a .http / .psql record into a dict of its `key: value` lines."""
    d = {}
    with open(path) as f:
        for line in f:
            if ": " in line:
                k, _, v = line.partition(": ")
                d.setdefault(k.strip(), v.rstrip("\n"))
    return d


# --------------------------------------------------------------------------------- LEG 1
def staleness(root, names):
    """Return {name: (verdict, detail)} for each capture under `root`."""
    res = {}
    for name in names:
        http = os.path.join(root, "out", name + ".http")
        psql = os.path.join(root, "out", name + ".psql")
        if os.path.exists(http):
            rec = kv(http)
            named = rec.get("body-file")
            wire = os.path.join(root, "out", name + ".req")
            digest = rec.get("body-sha256")
            if named is None:
                res[name] = ("VERIFIED", "no body -- a GET; nothing to go stale")
                continue
            if not os.path.exists(wire) or digest is None:
                res[name] = ("UNVERIFIABLE", "no wire-byte artefact (cap.sh era)")
                continue
            named_path = os.path.join(root, named)
            if not os.path.exists(named_path):
                res[name] = ("STALE", f"{named} no longer exists")
                continue
            a, b = sha256(named_path), sha256(wire)
            if a != b:
                res[name] = ("STALE", f"{named} {a[:16]} != wire {b[:16]}")
            elif b != digest:
                res[name] = ("STALE", f"wire {b[:16]} != recorded body-sha256 {digest[:16]}")
            else:
                res[name] = ("VERIFIED", f"{named} == wire == recorded digest {b[:16]}")
        elif os.path.exists(psql):
            rec = kv(psql)
            named = rec.get("query-file")
            wire = os.path.join(root, "out", name + ".sql")
            digest = rec.get("query-sha256")
            named_path = os.path.join(root, named) if named else None
            if not named_path or not os.path.exists(named_path) or not os.path.exists(wire):
                res[name] = ("STALE", f"{named} or its committed query bytes are missing")
                continue
            a, b = sha256(named_path), sha256(wire)
            if a != b:
                res[name] = ("STALE", f"{named} {a[:16]} != executed {b[:16]}")
            elif b != digest:
                res[name] = ("STALE", f"executed {b[:16]} != recorded query-sha256 {digest[:16]}")
            else:
                res[name] = ("VERIFIED", f"{named} == executed == recorded digest {b[:16]}")
        else:
            res[name] = ("STALE", "no .http and no .psql record at all")
    return res


def t275_names():
    names = [n for n, _, _ in IDEMPOTENT_HTTP] + [n for n, _, _ in SUPERSEDED_READ] + MUTATING
    names += [n for n, _ in IDEMPOTENT_SQL]
    names += [n for n in os.listdir(OUT)
              if n.endswith(".psql") and n.startswith("A2-5")]
    names = sorted({n[:-5] if n.endswith(".psql") else n for n in names})
    return names


print("== LEG 1: is any T275 recipe already STALE (the D-1 defect, live)? ==")
NAMES = t275_names()
verdicts = staleness(DIR, NAMES)
n_ver = sum(1 for v, _ in verdicts.values() if v == "VERIFIED")
for name in NAMES:
    v, d = verdicts[name]
    print(f"    {v:<12} {name:<50} {d}")
if len(NAMES) == 0:
    bad("LEG 1 inspected ZERO captures -- a check that inspects nothing is not a check (P-22)")
elif n_ver == len(NAMES):
    ok(f"all {len(NAMES)} T275 captures VERIFIED: every recipe names the bytes that were sent")
else:
    for name in NAMES:
        v, d = verdicts[name]
        if v != "VERIFIED":
            bad(f"LEG 1 {v} on {name}: {d}")

print("\n== LEG 1b: the same check over the 10 attempt1-* recipes D-1 declared false ==")
a1 = sorted(n[:-5] for n in os.listdir(OUT)
            if n.startswith("attempt1-") and n.endswith(".http"))
a1v = staleness(DIR, a1)
if not a1:
    bad("no attempt1-* recipes found -- the D-1 control is missing")
else:
    for name in a1:
        v, d = a1v[name]
        print(f"    {v:<12} {name:<50} {d}")
    if all(v == "UNVERIFIABLE" for v, _ in a1v.values()):
        ok(f"all {len(a1)} attempt1-* recipes are UNVERIFIABLE, not VERIFIED -- "
           "this check cannot launder them")
    else:
        bad("an attempt1-* recipe reached a verdict other than UNVERIFIABLE")

print("\n== LEG 1c: D-1 demonstrated from committed bytes alone, no trust required ==")
# The visible symptom D-1 names: a recorded 400 saying `isInterestRecalculationEnabled` is
# mandatory, paired with a body that CONTAINS it. Both files are committed; this reads them.
demo = "attempt1-A2-prod-069-accrual-complete"
dj = os.path.join(OUT, demo + ".json")
rec = kv(os.path.join(OUT, demo + ".http"))
body = os.path.join(DIR, rec.get("body-file", ""))
if os.path.exists(dj) and os.path.exists(body):
    resp = open(dj).read()
    with open(body) as f:
        b = json.load(f, parse_float=str)
    says_mandatory = "isInterestRecalculationEnabled" in resp and "mandatory" in resp
    contains = "isInterestRecalculationEnabled" in b
    print(f"    recorded response demands isInterestRecalculationEnabled : {says_mandatory}")
    print(f"    the body the recipe names CONTAINS it                    : {contains}")
    if says_mandatory and contains:
        ok("D-1 reproduced from committed bytes: the recipe cannot have produced that response")
    else:
        bad("could not reproduce D-1's stated symptom -- do not cite it as demonstrated here")
else:
    bad(f"the D-1 demonstration inputs are missing ({demo})")

# --------------------------------------------------------------------------------- LEG 2
print("\n== LEG 2: drive LEG 1 RED by changing ONE BYTE of one request body ==")
scratch = tempfile.mkdtemp(prefix="t275-red-")
try:
    copy = os.path.join(scratch, "tierA-a2")
    shutil.copytree(DIR, copy)
    victim_name = "A2-502-p23-repoint-fundsource"
    victim_body = kv(os.path.join(copy, "out", victim_name + ".http"))["body-file"]
    vp = os.path.join(copy, victim_body)
    with open(vp, "rb") as f:
        raw = f.read()
    # one byte: a trailing newline -> a trailing space. Semantically nothing; byte-wise
    # everything, which is the point -- D-1 was invisible precisely because the CONTENT
    # still looked plausible.
    with open(vp, "wb") as f:
        f.write(raw[:-1] + b" ")
    red = staleness(copy, NAMES)
    got = red[victim_name][0]
    others = [n for n in NAMES if n != victim_name and red[n][0] != "VERIFIED"]
    print(f"    mutated {victim_body} by exactly 1 byte ({len(raw)} bytes, unchanged length)")
    print(f"    LEG 1 verdict on the victim: {got} -- {red[victim_name][1]}")
    if got != "STALE":
        bad(f"LEG 1 did NOT go red on a mutated body (said {got}) -- it is a guard that cannot fail")
    elif others:
        bad(f"LEG 1 went red on unrelated captures too: {others} -- it is not specific")
    else:
        ok("LEG 1 goes STALE on exactly the mutated capture and stays VERIFIED on the other "
           f"{len(NAMES) - 1} -- it is failable AND specific")
finally:
    shutil.rmtree(scratch, ignore_errors=True)

# --------------------------------------------------------------------------------- LEG 3
print("\n== LEG 3: RE-ISSUE the idempotent captures against the live oracle, right now ==")
scratch = tempfile.mkdtemp(prefix="t275-reissue-")
try:
    copy = os.path.join(scratch, "tierA-a2")
    shutil.copytree(DIR, copy)
    shutil.rmtree(os.path.join(copy, "out"))
    os.makedirs(os.path.join(copy, "out"))

    for name, method, path in IDEMPOTENT_HTTP:
        r = subprocess.run(["sh", os.path.join(copy, "cap8.sh"), name, method, path],
                           capture_output=True, text=True)
        fresh = os.path.join(copy, "out", name + ".json")
        if r.returncode != 0 or not os.path.exists(fresh):
            bad(f"LEG 3 could not re-issue {name}: {r.stderr.strip()[:200]}")
            continue
        a, b = sha256(os.path.join(OUT, name + ".json")), sha256(fresh)
        if a == b:
            ok(f"{name} re-issued BYTE-IDENTICAL ({a[:16]})")
        else:
            bad(f"{name} re-issued DIFFERENT bytes: committed {a[:16]} vs now {b[:16]}")

    # The superseded reads: a fresh read must DIFFER from each and EQUAL the current one.
    cur = sha256(os.path.join(OUT, CURRENT_FOR_SUPERSEDED + ".json"))
    for name, method, path in SUPERSEDED_READ:
        r = subprocess.run(["sh", os.path.join(copy, "cap8.sh"), name, method, path],
                           capture_output=True, text=True)
        fresh_p = os.path.join(copy, "out", name + ".json")
        if r.returncode != 0 or not os.path.exists(fresh_p):
            bad(f"LEG 3 could not re-issue {name}: {r.stderr.strip()[:200]}")
            continue
        old, fresh = sha256(os.path.join(OUT, name + ".json")), sha256(fresh_p)
        if old == fresh:
            bad(f"{name} re-issued IDENTICAL bytes, but this fire's writes should have "
                f"moved that state -- one of the two observations is wrong")
        elif fresh != cur:
            bad(f"{name} re-issued bytes matching NEITHER the snapshot nor the current-state "
                f"capture {CURRENT_FOR_SUPERSEDED} -- the instrument may be nondeterministic")
        else:
            ok(f"{name} correctly SUPERSEDED: differs from its own snapshot ({old[:16]}) "
               f"and equals the current-state capture ({fresh[:16]})")

    for name, qf in IDEMPOTENT_SQL:
        r = subprocess.run(["sh", os.path.join(copy, "capsql.sh"), name, qf],
                           capture_output=True, text=True)
        fresh = os.path.join(copy, "out", name + ".txt")
        if r.returncode != 0 or not os.path.exists(fresh):
            bad(f"LEG 3 could not re-issue {name}: {r.stderr.strip()[:200]}")
            continue
        a, b = sha256(os.path.join(OUT, name + ".txt")), sha256(fresh)
        if a == b:
            ok(f"{name} re-issued BYTE-IDENTICAL ({a[:16]})")
        else:
            bad(f"{name} re-issued DIFFERENT bytes: committed {a[:16]} vs now {b[:16]}")
finally:
    shutil.rmtree(scratch, ignore_errors=True)

# ------------------------------------------------------------------------------ statement
print("\n== The MUTATING captures, and what is and is not claimed about them ==")
print(f"    {len(MUTATING)} captures write state. NONE of them can re-issue to the same")
print("    RESPONSE, and this script does not claim they can. What LEG 1 proves about each")
print("    is that the REQUEST is re-issuable: the body the recipe names is byte-identical")
print("    to the body that went over the wire. Their PRECONDITION is the oracle state")
print("    recorded in out/A2-500-db-mapping-before.txt (product 23 mapping ids 12-21, the")
print("    generic FUND_SOURCE row id 12 -> GL 2, no payment-channel row, acc_product_mapping")
print("    max(id) 94, m_product_loan max(id) 55). Replaying them on a tenant not in that")
print("    state reproduces the BEHAVIOUR and not the IDS -- CAPTURE-PLAN.md §6's standing")
print("    warning, which applies to this batch exactly as it applies to the original one.")

print()
if fails:
    print(f"FAIL -- {len(fails)} leg(s) failed", file=sys.stderr)
    sys.exit(1)
print("PASS -- every leg held.")
