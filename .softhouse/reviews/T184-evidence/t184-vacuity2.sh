#!/bin/bash
# T184 V1-redo: a capture tree that still HAS lib/ but ZERO request bodies.
# Plus a falsifiability control for V4: does the OLD `grep -q` shape actually invert?
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
cd "$W"
CAP="$W/.softhouse/capture"
STASH=/tmp/t184-capstash
rm -rf "$STASH"; mkdir -p "$STASH"

echo "########## V1b: capture/lib present, every other capture subtree hidden -> ZERO bodies"
for d in "$CAP"/*; do
  b="$(basename "$d")"
  [ "$b" = "lib" ] && continue
  mv "$d" "$STASH/$b"
done
ls "$CAP"
bash .softhouse/conformance.sh > /tmp/t184-v1b.txt 2>&1; echo "EXIT=$?"
grep -n 'CENSUS\|REFUSED\|inspects nothing\|MISSING\|NO CENSUS\|HARD guard\|probe =\|VERDICT' /tmp/t184-v1b.txt
for d in "$STASH"/*; do mv "$d" "$CAP/$(basename "$d")"; done
rmdir "$STASH"
echo "--- restored: $(ls "$CAP" | wc -l) entries under capture/"

echo
echo "########## V4-control: is the P-57 inversion real? Run BOTH grep shapes on 440KB."
python3 - <<'PYEOF' > /tmp/t184-bigout.txt
print('CENSUS wire-float round-trip — stub')
for i in range(4000):
    print('filler line %06d %s' % (i, 'x' * 90))
PYEOF
wc -c /tmp/t184-bigout.txt
bash -c 'set -u -o pipefail
out="$(cat /tmp/t184-bigout.txt)"
if ! printf "%s\n" "$out" | LC_ALL=C grep -aq "^CENSUS "; then
  echo "OLD (grep -q): reports NO CENSUS LINE   <-- INVERTED, the line is line 1"
else
  echo "OLD (grep -q): finds the census line"
fi
n="$(printf "%s\n" "$out" | LC_ALL=C grep -ac "^CENSUS " || true)"
if [ "${n:-0}" -eq 0 ]; then
  echo "NEW (grep -c): reports NO CENSUS LINE   <-- would be a regression"
else
  echo "NEW (grep -c): finds the census line ($n)"
fi'
echo
git status --short
