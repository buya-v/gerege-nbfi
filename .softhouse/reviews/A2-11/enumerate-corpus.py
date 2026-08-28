#!/usr/bin/env python3
"""A2-11 (a) — independently re-enumerate the A2 corpus AT A2-7'S FORK POINT.

Tests three of A2-7's claims about what the corpus did and did not contain:
  1. "GET /loanproducts/{id} did not exist anywhere in the corpus — eleven POSTs, zero reads"
  2. "The only four GET /glaccounts/{id} in the corpus (A2-012/013/015/018) are all ASSET"
  3. "24 distinct GL-code-shaped tokens appear in the pre-A2-7 out/ bytes, not four;
      3 are not live accounts; the remaining 21 are exactly A2-150's 21 rows"

P-40 IS THE POINT OF THIS FILE. It reads EVERY blob under out/ at the fork sha, and it
prints, for every category, HOW MANY IT COULD NOT PARSE AND WHICH ONES. There is no
`except: continue` anywhere; an unreadable file is NAMED. The driver's enumerator failed
precisely by not doing this.
"""
import os
import pathlib
import json
import re
import subprocess
import sys
from collections import Counter
from decimal import Decimal

# T357 REPAIR -- was a hard-coded absolute path into the worktree
#   /Users/buv/gerege-nbfi/.claude/worktrees/agent-a3ac3d56d665ff7da
# which was RETIRED, so this script aborted with a traceback in every later checkout
# and the committed transcript stopped being re-derivable from the script that made
# it. Derived from __file__ instead: this file sits three levels below the checkout
# root, under reviews/A2-11, so parents[3] IS that root. In the ORIGINAL worktree it
# resolved to agent-a3ac3d56d665ff7da, so the substitution is OUTPUT-NEUTRAL there --
# it restores the evidence rather than altering it, and that claim is MEASURED in
# .softhouse/capture/t357-a2-11-section1-red/ (BEFORE/AFTER, and a diff against the
# committed transcript), not asserted. A2_11_ROOT overrides for a cross-checkout run.
ROOT = os.environ.get("A2_11_ROOT") or str(pathlib.Path(__file__).resolve().parents[3])
CAP = ".softhouse/capture/tierA-a2"
FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"   # literal, pre-A2-7 (P-24)
fails = []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        fails.append(label)


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, check=True).stdout


paths = [p for p in git("ls-tree", "-r", "--name-only", FORK, "--", CAP + "/out").decode().split("\n") if p]
print("=== corpus at the fork sha %s ===" % FORK[:12])
by_ext = Counter(p.rsplit(".", 1)[-1] if "." in p.rsplit("/", 1)[-1] else "<no-ext>" for p in paths)
print("  %d files under out/, by extension: %s" % (len(paths), dict(by_ext)))

# ---------------------------------------------------------------- claim 1 and 2
http_files = [p for p in paths if p.endswith(".http")]
requests = []
undecodable = []
noreqline = []
for p in http_files:
    raw = git("show", FORK + ":" + p)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:            # NAMED, never dropped (P-40)
        undecodable.append((p, repr(exc)))
        continue
    first = text.split("\n", 1)[0].strip()
    m = re.match(r"^([A-Z]+)\s+(\S+)", first)
    if not m:
        noreqline.append((p, first[:80]))
        continue
    requests.append((p, m.group(1), m.group(2)))

print()
print("=== every HTTP request recorded in the corpus, by method + endpoint family ===")
print("  .http files enumerated : %d" % len(http_files))
print("  undecodable (NAMED)    : %d %s" % (len(undecodable), undecodable))
print("  no request line (NAMED): %d %s" % (len(noreqline), noreqline))
print("  parsed                 : %d" % len(requests))
check("every .http file parsed — nothing was silently skipped",
      len(requests) == len(http_files), "parsed=%d of %d" % (len(requests), len(http_files)))


def family(path):
    p = path.split("?")[0]
    p = re.sub(r"/\d+", "/{id}", p)
    return p


fam = Counter((m, family(u)) for _, m, u in requests)
for (m, f), n in sorted(fam.items()):
    print("    %-6s %-46s %d" % (m, f, n))

lp_posts = [r for r in requests if r[1] == "POST" and family(r[2]) in ("/loanproducts", "loanproducts")]
lp_gets = [r for r in requests if r[1] == "GET" and "loanproducts" in r[2]]
print()
print("  POST .../loanproducts : %d" % len(lp_posts))
print("  GET  .../loanproducts*: %d  %s" % (len(lp_gets), [r[0].rsplit('/', 1)[-1] for r in lp_gets]))
check("CLAIM 1a — the corpus held ELEVEN POST /loanproducts", len(lp_posts) == 11,
      "count=%d: %s" % (len(lp_posts), sorted(r[0].rsplit('/', 1)[-1] for r in lp_posts)))
check("CLAIM 1b — the corpus held ZERO GET on /loanproducts of any form",
      len(lp_gets) == 0, "found %d" % len(lp_gets))

gl_gets = [r for r in requests if r[1] == "GET" and re.search(r"/glaccounts/\d+", r[2])]
print()
print("  GET /glaccounts/{id}  : %d  %s" % (len(gl_gets), sorted(r[0].rsplit('/', 1)[-1].replace('.http', '') for r in gl_gets)))
check("CLAIM 2a — exactly four GET /glaccounts/{id} existed", len(gl_gets) == 4,
      "count=%d" % len(gl_gets))
types = {}
unparsed_bodies = []
for p, _, url in gl_gets:
    body = p[:-5] + ".json"
    raw = git("show", FORK + ":" + body)
    try:
        d = json.loads(raw.decode("utf-8"), parse_float=Decimal)
    except Exception as exc:                     # NAMED (P-40)
        unparsed_bodies.append((body, repr(exc)))
        continue
    types[p.rsplit("/", 1)[-1]] = (d.get("glCode"), d.get("type", {}).get("value"))
for k, v in sorted(types.items()):
    print("      %-40s glCode=%s type=%s" % (k, v[0], v[1]))
print("      bodies that would not parse (NAMED): %d %s" % (len(unparsed_bodies), unparsed_bodies))
check("CLAIM 2b — all four are ASSET",
      len(types) == 4 and all(v[1] == "ASSET" for v in types.values()), str(types))

# ---------------------------------------------------------------- claim 3
print()
print("=== CLAIM 3 — distinct GL-code-shaped tokens across ALL out/ bytes at the fork sha ===")
codes = Counter()
undec = []
for p in paths:
    raw = git("show", FORK + ":" + p)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:            # NAMED (P-40)
        undec.append((p, repr(exc)))
        continue
    for tok in re.findall(r"(?<![0-9.])[0-9]{5}(?![0-9.])", text):
        codes[tok] += 1
print("  files read: %d   undecodable (NAMED): %d %s" % (len(paths), len(undec), undec))
print("  distinct 5-digit tokens: %d -> %s" % (len(codes), sorted(codes)))

dump = git("show", FORK + ":" + CAP + "/out/A2-150-db-final-state.txt").decode()
sect = dump.split("--- acc_gl_account ---")[1].split("--- acc_gl_financial_activity_account ---")[0]
dump_codes = sorted(set(re.findall(r"\|\s*(\d{5})\s*\|", sect)))
print("  A2-150's acc_gl_account gl_code column: %d -> %s" % (len(dump_codes), dump_codes))
check("A2-150 holds exactly 21 gl_code values", len(dump_codes) == 21, str(len(dump_codes)))
extra = sorted(set(codes) - set(dump_codes))
missing = sorted(set(dump_codes) - set(codes))
print("  tokens present in out/ but NOT live accounts: %s" % extra)
print("  live accounts never mentioned in out/ text  : %s" % missing)
check("CLAIM 3 — 24 distinct tokens, 3 of them non-accounts, 21 == the dump's 21 rows",
      len(codes) == 24 and len(extra) == 3 and not missing,
      "tokens=%d extra=%s missing=%s" % (len(codes), extra, missing))

print()
print("FAILURES: %d" % len(fails))
for f in fails:
    print("  - " + f)
sys.exit(1 if fails else 0)
