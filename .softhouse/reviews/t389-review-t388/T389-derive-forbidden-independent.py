#!/usr/bin/env python3
"""
T389 -- INDEPENDENT derivation of the GL accounts read by the promoted vector store.

Deliberately BROADER than T388's rule (which matched only keys whose name ENDS IN
'gl_account_id'). This walks every scalar in every JSON file under .softhouse/vectors,
including _selftest (which T388's "67 files" excluded), and flags a value as a candidate
GL reference under ANY of five independent rules, so that a miss requires all five to fail:

  R1  key name, lowercased and stripped of '_', ENDS IN 'glaccountid'
  R2  key name, lowercased and stripped of '_', CONTAINS 'glaccount'  (camelCase-safe:
      glAccountId, gl_account_id, contra_gl_account_id, glAccountCode, glAccountName ...)
  R3  key name, lowercased and stripped of '_', CONTAINS 'account' AND value is an int
  R4  key name, lowercased and stripped of '_', CONTAINS 'gl' AND value is an int
  R5  the ENCLOSING key path contains 'slot' or 'unposted' and the value is an int
      (catches capabilities-ledger.json's unposted_slots-style structures where the id may
      sit in a bare list rather than under a named key)

Non-integer candidates (codes, names) are reported SEPARATELY, because a vector that pins
an account by CODE or NAME is just as contaminable as one that pins it by id, and no
id-only scan would ever see it.

Instance-space split is by provenance.capture_ref (throwaway rigs stand up their own
id space and must NOT be merged with the standing oracle's).
"""
import json, os, sys, re
from collections import defaultdict

ROOT = sys.argv[1] if len(sys.argv) > 1 else ".softhouse/vectors"

def norm(k):
    return re.sub(r'[^a-z0-9]', '', str(k).lower())

def walk(node, path, out):
    """out: list of (jsonpath, key, value)"""
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, path + [str(k)], out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + ["[%d]" % i], out)
    else:
        key = None
        for seg in reversed(path):
            if not seg.startswith("["):
                key = seg
                break
        out.append((".".join(path), key, node))

def classify(jsonpath, key, val):
    """return list of rule names that fire"""
    hits = []
    nk = norm(key)
    npath = norm(jsonpath)
    isint = isinstance(val, int) and not isinstance(val, bool)
    if nk.endswith("glaccountid"):
        hits.append("R1")
    if "glaccount" in nk:
        hits.append("R2")
    if "account" in nk and isint:
        hits.append("R3")
    if "gl" in nk and isint:
        hits.append("R4")
    if ("slot" in npath or "unposted" in npath) and isint:
        hits.append("R5")
    return hits

files = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    for fn in sorted(filenames):
        if fn.endswith(".json"):
            files.append(os.path.join(dirpath, fn))
files.sort()

per_file_ids = {}
per_file_nonint = {}
rule_only = defaultdict(set)      # rule -> ids found by that rule
instance_of = {}
all_rows = []

for f in files:
    with open(f, encoding="utf-8") as fh:
        doc = json.load(fh)
    prov = doc.get("provenance", {}) if isinstance(doc, dict) else {}
    cref = prov.get("capture_ref", "") if isinstance(prov, dict) else ""
    inst = "throwaway" if ("t305" in str(cref) or "t327" in str(cref)) else "standing-oracle"
    instance_of[f] = (inst, cref)
    scalars = []
    walk(doc, [], scalars)
    ids = set()
    nonint = set()
    for jp, key, val in scalars:
        hits = classify(jp, key, val)
        if not hits:
            continue
        if isinstance(val, int) and not isinstance(val, bool):
            ids.add(val)
            for h in hits:
                rule_only[h].add((inst, val))
            all_rows.append((f, inst, jp, key, val, ",".join(hits)))
        else:
            nonint.add((jp, key, str(val)))
    per_file_ids[f] = ids
    per_file_nonint[f] = nonint

print("T389 -- INDEPENDENT DERIVATION of GL accounts read by the promoted vector store")
print("root       :", os.path.abspath(ROOT))
print("json files :", len(files), " (T388 reported 67; this scan includes _selftest)")
print()
print("%-11s %-70s %s" % ("instance", "file", "candidate gl ids"))
print("-" * 130)
for f in files:
    inst, cref = instance_of[f]
    ids = per_file_ids[f]
    print("%-11s %-70s %s" % (inst, os.path.relpath(f, ROOT), sorted(ids) if ids else "-"))

standing = set()
throwaway = set()
for f in files:
    inst, _ = instance_of[f]
    (standing if inst == "standing-oracle" else throwaway).add(0)
    for i in per_file_ids[f]:
        (standing if inst == "standing-oracle" else throwaway).add(i)
standing.discard(0); throwaway.discard(0)

print()
print("FORBIDDEN ON THE STANDING ORACLE (T389 independent):", sorted(standing))
print("THROWAWAY-INSTANCE ID SPACE, deliberately NOT merged:", sorted(throwaway))
print()
print("Which rule contributed which standing-oracle id (a value found ONLY by R2-R5 is one")
print("T388's ENDS-IN-gl_account_id rule R1 would have MISSED):")
for r in ["R1", "R2", "R3", "R4", "R5"]:
    got = sorted(v for (i, v) in rule_only[r] if i == "standing-oracle")
    print("  %s: %s" % (r, got))
r1 = set(v for (i, v) in rule_only["R1"] if i == "standing-oracle")
extra = standing - r1
print()
print("STANDING ids NOT reachable by R1 alone (T388's stated rule):", sorted(extra))
print()
print("NON-INTEGER account references (code/name pins -- no id scan would see these):")
any_ni = False
for f in files:
    for jp, key, val in sorted(per_file_nonint[f]):
        any_ni = True
        print("  %-55s %s = %r" % (os.path.relpath(f, ROOT), jp, val))
if not any_ni:
    print("  (none)")
