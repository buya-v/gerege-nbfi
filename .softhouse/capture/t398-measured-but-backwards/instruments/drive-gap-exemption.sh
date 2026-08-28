#!/usr/bin/env bash
# T398 -- drive the register-GAP exemption in BOTH directions.
#
# P-100, which this task filed, says a grading change must be run against at
# least one CORRECT and one DELIBERATELY WRONG input in the same pass, and the
# correct one must pass while the wrong one dies. The one-line change T398 made
# to `check-pnumber-citations.py` IS a grading change, so it owes that drive.
#
#   ARM A  CORRECT INPUT  -- the real tree. P-99 absent, P-100/P-101 defined.
#                            MUST be `gaps=none` and VERDICT PASS.
#   ARM B  WRONG INPUT    -- a disposable clone of patterns.md with a REAL,
#                            UNDECLARED definition deleted (P-97). 97 is not in
#                            NEGATIVE_CONTROL_IDS, so the exemption must NOT
#                            cover it and the checker MUST still go fatal.
#   ARM C  CONTROL ON THE EXEMPTION ITSELF -- same disposable clone, exemption
#                            neutralised in a COPY of the checker. ARM A's input
#                            must then go RED, proving the exemption is what
#                            makes ARM A green rather than something else.
#
# Every arm runs the checker with ROOT anchored to a throwaway worktree copy;
# the repo tree is never mutated.
#
#   bash .softhouse/capture/t398-measured-but-backwards/instruments/drive-gap-exemption.sh <repo-root>
set -uo pipefail
REPO=${1:?usage: <repo-root>}
CHK_REL=.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py
T=$(mktemp -d "${TMPDIR:-/tmp}/t398-gap.XXXXXX") || exit 2
trap 'rm -rf "$T"' EXIT

verdict() { LC_ALL=C grep -aE '^PNUMBER-CITATIONS: (register=|FATAL|VERDICT)' "$1" | sed 's/^/    /'; }

echo "repo    : $REPO"
echo "engine  : $(python3 -VV 2>&1 | head -1)"
echo

echo '=== ARM A: CORRECT INPUT -- the real tree, P-99 reserved-absent, P-100/P-101 defined ==='
( cd "$REPO" && python3 "$CHK_REL" ) > "$T/a.txt" 2>&1
A=$?
verdict "$T/a.txt"
echo "    rc=$A   EXPECT rc=0 and gaps=none"
echo

echo '=== ARM B: WRONG INPUT -- an UNDECLARED hole (P-97 definition deleted) ================='
# A throwaway copy of the whole tree is too expensive; instead copy the repo by
# reference with a rewritten patterns.md, using git worktree-free plumbing: the
# checker anchors ROOT to its own path, so we place a copy of bin/ four levels
# deep inside a scratch root that carries only the files the checker reads.
mkdir -p "$T/b/.softhouse/capture/t282-pnumber-drift/bin"
( cd "$REPO" && git archive HEAD ) | tar -x -C "$T/b" 2>/dev/null
cp "$REPO/$CHK_REL" "$T/b/$CHK_REL"
cp "$REPO/.softhouse/patterns.md" "$T/b/.softhouse/patterns.md"
# delete the P-97 DEFINITION line only -- every citation of P-97 stays, so the
# id becomes genuinely cited-and-undefined AND an interior register gap.
python3 - "$T/b/.softhouse/patterns.md" <<'PY'
import sys, re
p = sys.argv[1]
lines = open(p, encoding="utf-8").read().split("\n")
out, killed = [], 0
for l in lines:
    if l.startswith("**P-97 ") and killed == 0:
        killed = 1
        out.append("**THE RULE FORMERLY KNOWN AS 97 -- definition removed by the T398 RED drive.**")
        continue
    out.append(l)
open(p, "w", encoding="utf-8").write("\n".join(out))
print("    deleted P-97 definition lines:", killed)
PY
( cd "$T/b" && git init -q . >/dev/null 2>&1; git -C "$T/b" add -A >/dev/null 2>&1; \
  git -C "$T/b" -c user.email=t398@local -c user.name=T398 commit -qm scratch >/dev/null 2>&1 )
( cd "$T/b" && python3 "$CHK_REL" ) > "$T/b.txt" 2>&1
B=$?
verdict "$T/b.txt"
echo "    rc=$B   EXPECT rc=1 and REGISTER GAP P-97 -- the exemption must NOT cover an undeclared id"
echo

echo '=== ARM C: CONTROL -- neutralise the exemption, ARM A input must go RED ================'
mkdir -p "$T/c"
( cd "$REPO" && git archive HEAD ) | tar -x -C "$T/c" 2>/dev/null
cp "$REPO/.softhouse/patterns.md" "$T/c/.softhouse/patterns.md"
python3 - "$T/c/$CHK_REL" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = "if n not in reg and n not in NEGATIVE_CONTROL_IDS]"
new = "if n not in reg]"
assert old in s, "exemption line not found -- this control is void"
open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
print("    exemption neutralised in the COPY at", p)
PY
( cd "$T/c" && git init -q . >/dev/null 2>&1; git -C "$T/c" add -A >/dev/null 2>&1; \
  git -C "$T/c" -c user.email=t398@local -c user.name=T398 commit -qm scratch >/dev/null 2>&1 )
( cd "$T/c" && python3 "$CHK_REL" ) > "$T/c.txt" 2>&1
C=$?
verdict "$T/c.txt"
echo "    rc=$C   EXPECT rc=1 and REGISTER GAP P-99 -- proves the exemption is load-bearing"
echo

echo '=== SUMMARY ============================================================================'
printf '  ARM A correct-input    rc=%s  (want 0)\n' "$A"
printf '  ARM B undeclared-gap   rc=%s  (want 1)\n' "$B"
printf '  ARM C exemption-removed rc=%s (want 1)\n' "$C"
if [ "$A" = 0 ] && [ "$B" = 1 ] && [ "$C" = 1 ]; then
  echo '  >>> ALL THREE AS EXPECTED. The exemption is load-bearing, narrow, and does not'
  echo '  >>> silence an undeclared hole. Correct input green, both wrong inputs dead.'
  exit 0
fi
echo '  >>> NOT AS EXPECTED -- do not land the exemption.'
exit 1
