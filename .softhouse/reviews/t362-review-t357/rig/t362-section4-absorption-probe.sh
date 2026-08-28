#!/bin/bash
# T362 — two probes on run-all.sh section 4.
#
#  P1: independently recompute the out/ and req/ byte-identity against the fork sha,
#      rather than trusting verify-manifest-independently.py's own arithmetic. This is
#      the leg behind T357's claim "NO captured oracle observation under out/ or req/
#      has been mutated".
#
#  P2: T357 adjudicates section 4 to RC 1 for DRIFT — but the SAME RC 1 is already being
#      produced by the evidence-integrity arm ("all 430 pre-existing files are
#      byte-identical", currently 428/430), so that arm is SATURATED. Question: if a
#      captured oracle observation under out/ IS mutated, does run-all.sh still say PASS?
#      This is T362 finding F-1.
set -u
# TARGET TREE — passed in, never defaulted; this script MUTATES and reverts. See the
# sibling drive-red script's header for how to build it.
C="${1:?usage: $0 <path to a main+T357 checkout to operate on>}"
[ -d "$C/.git" ] || { echo "REFUSE: $C is not a git checkout" >&2; exit 9; }
A2="$C/.softhouse/reviews/A2-11"
FORK=12a7f8d9a3af4665fd5281a9f9c001d4f1276a53   # LITERAL, pre-A2-7 (P-24), never merge-base
W="$(mktemp -d -t t362-sec4)"
trap 'rm -rf "$W"' EXIT

echo "=== P1. T362's OWN recompute of out/ + req/ integrity vs the fork sha ==="
python3 - "$C" "$FORK" <<'PY'
import hashlib, subprocess, sys
C, FORK = sys.argv[1], sys.argv[2]
CAP = ".softhouse/capture/tierA-a2"
ls = subprocess.run(["git", "-C", C, "ls-tree", "-r", "--name-only", FORK, CAP + "/"],
                    capture_output=True, text=True, check=True).stdout.split()
print("  files under %s at the fork sha: %d" % (CAP, len(ls)))
buckets = {}
for p in ls:
    rel = p[len(CAP) + 1:]
    buckets.setdefault(rel.split("/")[0] if "/" in rel else "<top-level>", []).append(p)
for k in sorted(buckets):
    print("    %-14s %d" % (k, len(buckets[k])))
diff, missing = [], []
for p in ls:
    blob = subprocess.run(["git", "-C", C, "show", "%s:%s" % (FORK, p)],
                          capture_output=True, check=True).stdout
    try:
        disk = open(C + "/" + p, "rb").read()
    except FileNotFoundError:
        missing.append(p)
        continue
    if hashlib.sha256(blob).digest() != hashlib.sha256(disk).digest():
        diff.append(p)
print("  MISSING on disk: %d %s" % (len(missing), missing))
print("  DIFFERING      : %d" % len(diff))
for p in diff:
    print("     ", p)
outreq = [p for p in diff if "/out/" in p or "/req/" in p]
print("  DIFFERING under out/ or req/: %d %s" % (len(outreq), outreq))
print("  => T357's claim 'NO captured oracle observation under out/ or req/ has been "
      "mutated' is %s" % ("CONFIRMED" if not outreq else "*** REFUTED ***"))
PY

echo
echo "=== P2. Mutate a pre-existing captured observation under out/ and see whether"
echo "===     run-all.sh still reports PASS. ==="
VICTIM=$(git -C "$C" ls-tree -r --name-only "$FORK" .softhouse/capture/tierA-a2/out/ | head -1)
echo "  victim (a pre-existing captured oracle observation): $VICTIM"
python3 - "$C/$VICTIM" <<'PY'
import sys
p = sys.argv[1]
b = open(p, 'rb').read()
open(p, 'wb').write(b + b"\nT362-MUTATION-OF-A-CAPTURED-ORACLE-OBSERVATION\n")
print("  appended a mutation marker; file grew from %d to %d bytes" % (len(b), len(b) + 47))
PY

python3 "$A2/verify-manifest-independently.py" > "$W/sec4.txt" 2>&1
echo "  verify-manifest-independently.py rc=$?   (it DOES detect the mutation:)"
grep -n "byte-identical fork-vs-today\|DIFFER  \|DIFF \|current manifest hash agrees" "$W/sec4.txt" | head -12

bash "$A2/run-all.sh" > "$W/runall.txt" 2>&1
RC=$?
echo "  run-all.sh rc=$RC   <-- 0 here means A MUTATED ORACLE OBSERVATION IS ABSORBED"
sed -n '/VERDICT — every section/,$p' "$A2/TRANSCRIPT-A2-11.txt"

git -C "$C" checkout -- .softhouse/capture/ .softhouse/reviews/A2-11/
echo "  reverted; porcelain:"; git -C "$C" status --porcelain | head

echo
if [ "$RC" -eq 0 ]; then
  echo "F-1 CONFIRMED: run-all.sh exits 0 and prints PASS with a captured oracle"
  echo "observation mutated under out/. Section 4's adjudicated RC 1 absorbs it."
else
  echo "F-1 NOT REPRODUCED on this tree: run-all.sh exited $RC."
fi
