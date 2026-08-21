#!/bin/sh
# T138 — drive the V-B assertion I prescribe in §4 before prescribing it (P-22):
# it must be a NO-OP on every committed transcript set and RED on a dead oracle.
set -u
W=${1:?workdir}
S='PASS  effective rounding mode canary'

echo "=== is the certification sentence present in every committed transcript dir?"
for tree in pre post; do
  for d in "$W/$tree"/.softhouse/capture/t91/out/*/; do
    b=$(basename "$d"); [ "$b" = happy ] && continue
    ls "$d"/A*.txt >/dev/null 2>&1 || continue
    n=$(LC_ALL=C grep -alF "$S" "$d"/A*.txt 2>/dev/null | wc -l | tr -d ' ')
    printf '   %-28s transcripts carrying the sentence: %s\n' "$tree/$b" "$n"
  done
done
echo
echo "=== the proposed assertion, applied to a copy of the shipped verdict.sh"
V=/tmp/T138-vbfix.sh
python3 - "$W/post/.softhouse/capture/t91/verdict.sh" "$V" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
anchor = '[ "$files" = "$n" ] || echo "WARNING:'
assert anchor in s, 'ABORT: anchor not found'
block = '''# T138 (V-B).  Nothing in the table asserts the oracle ANSWERED: NEVER forbids the certification
# sentence and PINNED merely permits it.  Resistance to a dead oracle rested entirely on A4c/A7/A8
# being CLEAN rows -- an accident of the data.  Make it deliberate.
if ! LC_ALL=C grep -alF "$S" "$D"/A*.txt >/dev/null 2>&1; then
  echo "ERROR: not one transcript contains the rounding-mode certification sentence -- the suite" >&2
  echo "       never reached a live oracle.  Scoring it would grade an outage as a clean sweep." >&2
  exit 3
fi
'''
open(dst, 'w').write(s.replace(anchor, block + anchor))
print('   assertion inserted (anchor asserted, not assumed)')
PY
echo
echo "=== NO-OP check: every committed transcript dir, shipped vs patched scorer"
for tree in pre post; do
  for d in "$W/$tree"/.softhouse/capture/t91/out/*/; do
    b=$(basename "$d"); [ "$b" = happy ] && continue
    ls "$d"/A*.txt >/dev/null 2>&1 || continue
    t=/tmp/T138-vb-$tree-$b; rm -rf "$t"; cp -R "$d" "$t"; chmod -R u+w "$t"
    sh "$W/post/.softhouse/capture/t91/verdict.sh" "$t" >/dev/null 2>&1; a=$?
    sh "$V" "$t" >/dev/null 2>&1; c=$?
    s=SAME; [ "$a" = "$c" ] || s='*** CHANGED ***'
    printf '   %-28s shipped exit=%s   patched exit=%s   %s\n' "$tree/$b" "$a" "$c" "$s"
  done
done
echo
echo "=== RED check: the 13 dead-oracle transcripts from r13"
sh "$W/post/.softhouse/capture/t91/verdict.sh" /tmp/T138-vb/dead >/dev/null 2>&1; echo "   shipped exit=$?  (accidental: 3 CLEAN rows)"
sh "$V" /tmp/T138-vb/dead 2>&1 | tail -3 | sed 's/^/   /'
sh "$V" /tmp/T138-vb/dead >/dev/null 2>&1; echo "   patched exit=$?  (deliberate)"
echo
echo "=== RED check 2: dead oracle AND all three CLEAN rows retyped to BREACH"
P=/tmp/T138-vbfix-allbreach.sh
python3 - "$V" "$P" <<'PY'
import sys
s = open(sys.argv[1]).read()
for r in ('A4c-decoy-variable.txt', 'A7-symlinked-canary.txt', 'A8-foreign-cwd.txt'):
    old = r + '|CLEAN|'
    assert old in s, 'ABORT: ' + r
    s = s.replace(old, r + '|BREACH|')
open(sys.argv[2], 'w').write(s)
print('   three CLEAN rows retyped to BREACH')
PY
sh "$P" /tmp/T138-vb/dead 2>&1 | tail -3 | sed 's/^/   /'
sh "$P" /tmp/T138-vb/dead >/dev/null 2>&1; echo "   patched+retyped exit=$?  (was 0 before the assertion)"
