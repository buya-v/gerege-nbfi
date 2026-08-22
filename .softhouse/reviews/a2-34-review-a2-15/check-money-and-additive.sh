#!/bin/bash
# A2-34: (a) money is integer minor units across ALL SIX vectors; (b) the change is purely additive.
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac008956278f2d6ea
cd "$R"

echo "######## (a) MONEY — every JSON scalar in all six ledger vectors, typed"
python3 - "$R" <<'PY'
import json, glob, os, sys
R = sys.argv[1]
bad = []
floats = []
decnum = []
def walk(o, path, raw):
    if isinstance(o, dict):
        for k, v in o.items(): walk(v, f"{path}.{k}", raw)
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(v, f"{path}[{i}]", raw)
    elif isinstance(o, float):
        floats.append((path, o))
for f in sorted(glob.glob(os.path.join(R, ".softhouse/vectors/ledger/*.json"))):
    raw = open(f).read()
    d = json.loads(raw, parse_float=lambda s: ("FLOATTOKEN", s))
    # parse_float returns a tuple for any decimal-pointed / exponent JSON number
    def walk2(o, path):
        if isinstance(o, dict):
            for k, v in o.items(): walk2(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o): walk2(v, f"{path}[{i}]")
        elif isinstance(o, tuple) and o and o[0] == "FLOATTOKEN":
            decnum.append((os.path.basename(f), path, o[1]))
    walk2(d, "$")
    d2 = json.loads(raw)
    walk(d2, "$", raw)
print(f"  decimal-pointed JSON NUMBERS across the six ledger vectors: {len(decnum)}")
for x in decnum: print("   ***", x)
print(f"  python-float-typed values across the six ledger vectors:   {len(floats)}")
for x in floats: print("   ***", x)

print()
print("  every money-bearing field, with its JSON type:")
for f in sorted(glob.glob(os.path.join(R, ".softhouse/vectors/ledger/*.json"))):
    d = json.load(open(f)); cid = d["case_id"]
    for i, l in enumerate(d["expect"].get("legs", [])):
        print(f"    {cid[:34]:34s} expect.legs[{i}].amount_minor      = {l['amount_minor']!r:14s} type={type(l['amount_minor']).__name__}")
        print(f"    {'':34s} expect.legs[{i}].amount_major_text = {l['amount_major_text']!r:18s} type={type(l['amount_major_text']).__name__}")
    for k in ("total_debits_minor", "total_credits_minor"):
        v = d["expect"][k]
        print(f"    {cid[:34]:34s} expect.{k:22s} = {v!r:14s} type={type(v).__name__}")
    for i, l in enumerate(d["request"].get("legs", [])):
        print(f"    {cid[:34]:34s} request.legs[{i}].amount_major_text= {l['amount_major_text']!r:18s} type={type(l['amount_major_text']).__name__}")
    ta = d["request"].get("transaction_amount_major_text")
    print(f"    {cid[:34]:34s} request.transaction_amount_major_text = {ta!r} type={type(ta).__name__}")
PY

echo
echo "######## (a2) Go: any float type / float literal in the new ledger conformance package?"
LC_ALL=C /usr/bin/grep -n -aE 'float32|float64|math/big|big\.Float|ParseFloat|complex' nexus/internal/apps/ledger/conformance/*.go ; echo "  grep -aE float exit=$? (1 = no hits)"
echo "-- amount field declarations in the ledger vector schema:"
LC_ALL=C /usr/bin/grep -n -aF 'AmountMinor' nexus/internal/apps/ledger/conformance/vector.go | head -20
LC_ALL=C /usr/bin/grep -n -aF 'TotalDebitsMinor' nexus/internal/apps/ledger/conformance/vector.go | head -5
echo "-- does the vector schema carry ANY balance field?"
LC_ALL=C /usr/bin/grep -n -aiF 'running_balance' nexus/internal/apps/ledger/conformance/*.go; echo "  exit=$?"
LC_ALL=C /usr/bin/grep -n -aiF 'RunningBalance' nexus/internal/apps/ledger/conformance/*.go; echo "  exit=$?"

echo
echo "######## (b) PURELY ADDITIVE — the A2-15 merge, name-status"
echo "-- merge on main is d76594a (parents a072ecd + 1325e8b). Diff first-parent -> merge:"
git diff --name-status a072ecd d76594a
echo
echo "-- restricted to .softhouse/vectors :"
git diff --name-status a072ecd d76594a -- .softhouse/vectors
echo
echo "######## (b2) SUBTREE HASHES either side"
for p in .softhouse/vectors/loanschedule .softhouse/vectors/_selftest .softhouse/vectors; do
  b=$(git rev-parse "a072ecd:$p" 2>/dev/null || echo "<absent>")
  a=$(git rev-parse "d76594a:$p" 2>/dev/null || echo "<absent>")
  n=$(git rev-parse "HEAD:$p" 2>/dev/null || echo "<absent>")
  same="MOVED"; [ "$b" = "$a" ] && same="IDENTICAL"
  printf "  %-38s before=%s  after=%s  %s   HEAD=%s\n" "$p" "${b:0:12}" "${a:0:12}" "$same" "${n:0:12}"
done
echo
echo "-- count of .json under vectors/loanschedule at both commits:"
echo -n "  before: "; git ls-tree -r --name-only a072ecd -- .softhouse/vectors/loanschedule | LC_ALL=C /usr/bin/grep -c '\.json$'
echo -n "  after : "; git ls-tree -r --name-only d76594a -- .softhouse/vectors/loanschedule | LC_ALL=C /usr/bin/grep -c '\.json$'
echo
echo "######## (b3) contract.go untouched across the merge?"
git diff --stat a072ecd d76594a -- nexus/internal/apps/loanschedule/contract/contract.go; echo "  (empty = untouched)"
echo "######## (b4) DEC-2 untouched across the merge?"
git diff --stat a072ecd d76594a -- docs/adr/DEC-2-gl-accounting-adapter.md; echo "  (empty = untouched)"
git diff --stat a072ecd d76594a -- docs/adr/; echo "  (any ADR touched?)"
