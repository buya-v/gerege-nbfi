#!/bin/zsh
# T280 — item 5: arm 3 (CEILING) vs arm 4 (LIVE), and whether ORDER is load-bearing.
#
# SKILL.md STEP 0 asserts: "The arms are written to be mutually exclusive, not merely
# first-match-wins, so reading them out of order cannot change the answer."
# The wrapper's lock_decide() is a chain of EARLY RETURNS. This script tests the claim
# against the implementation by building a copy with arms 3 and 4 TRANSPOSED and nothing
# else changed, then running the real case measure-f2 cites: a 105 h lock, a 2.99 h tip.
set -uo pipefail
W="$1"
T=$(mktemp -d /tmp/t280-order.XXXXXX)
cp "$W" "$T/swapped.sh"

python3 - "$T/swapped.sh" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p).read()
arm3 = """  if [[ "$sage" == <0-> ]] && (( sage >= LOCK_CEILING_SECS )); then
    print -r -- TAKE-ceiling; return 0                                             # arm 3
  fi
"""
arm4 = """  if [[ "$tage" == <0-> ]] && (( tage < LOCK_MAX_AGE_SECS )); then
    print -r -- HELD-live; return 0                                                # arm 4
  fi
"""
assert arm3 in s and arm4 in s, "arm text not found verbatim"
assert s.index(arm3) < s.index(arm4), "arm 3 is not before arm 4"
s = s.replace(arm3 + arm4, arm4 + arm3, 1)
open(p, "w").write(s)
print("  transposed arms 3 and 4; nothing else changed")
PY

STARTED_105H=378000     # 105 h, the lock measure-f2.py reports at fire-20260827-230001
TIP_299H=10764          # 2.99 h
print -r -- ""
print -r -- "=== the case T279 cites: lock 105 h old, tip 2.99 h old, pid not judgeable ==="
printf '  %-34s -> %s\n' "SHIPPED order (3 before 4)"  "$(zsh "$W" --lock-decide 1 '' $STARTED_105H $TIP_299H absent)"
printf '  %-34s -> %s\n' "TRANSPOSED order (4 before 3)" "$(zsh "$T/swapped.sh" --lock-decide 1 '' $STARTED_105H $TIP_299H absent)"
print -r -- ""
print -r -- "=== sweep: how many of the 192 states change verdict when 3 and 4 are swapped? ==="
python3 - "$W" "$T/swapped.sh" <<'PY'
import subprocess, sys, itertools
W, S = sys.argv[1], sys.argv[2]
SEC_S = {"lt6":"3600","b6_24":"43200","ge24":"90000","unreadable":""}
SEC_T = {"lt6":"3600","ge6":"43200","unreadable":""}
diff = []
for lock, rel, st, tip, pid in itertools.product(
        ("present","absent"),("null","set"),SEC_S,SEC_T,
        ("alive_here","dead_here","absent","other_host")):
    a = ["1" if lock=="present" else "0",
         "2026-08-28T00:00:00Z" if rel=="set" else "",
         SEC_S[st], SEC_T[tip], pid]
    g1 = subprocess.run(["zsh",W,"--lock-decide",*a],capture_output=True,text=True).stdout.strip()
    g2 = subprocess.run(["zsh",S,"--lock-decide",*a],capture_output=True,text=True).stdout.strip()
    if g1 != g2:
        diff.append((lock,rel,st,tip,pid,g1,g2))
print(f"  states whose verdict CHANGES under the transposition: {len(diff)}")
for d in diff:
    print(f"    lock={d[0]} released={d[1]} started={d[2]} tip={d[3]} pid={d[4]}"
          f"   shipped={d[5]}  transposed={d[6]}")
PY
print -r -- ""
print -r -- "scratch: $T"
