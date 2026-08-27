#!/bin/sh
# T138 — mutation-test T115's two headline new guards: revert the FIX each one
# protects and confirm the guard goes RED.  A guard that stays green when its own
# fix is reverted is the P-22 defect one level up.
set -u
C=${1:?checkout}
SHA=bd59187cf83c7c7161db23668e91d45bd46be2a8

mut() { # mut <tag> <file> <sed-expr...>
  tag=$1; shift; f=$1; shift
  D=/tmp/T138-mut-$tag
  rm -rf "$D"
  git clone --quiet --no-hardlinks --shared "$C" "$D"
  (cd "$D" && git checkout -q -B m "$SHA")
  LC_ALL=C sed -i.bak "$@" "$D/$f"
  rm -f "$D/$f.bak"
  (cd "$D" && git add -A && git -c user.name=T138 -c user.email=t138@local commit -q -m "mutation $tag")
  echo "$D"
}

echo "=================================================================="
echo "MUTATION — revert V-A: put verdict.sh's failure channel back in \$D"
echo "=================================================================="
D=$(mut va .softhouse/capture/t91/verdict.sh \
  -e 's|^FAILS=\$FAILDIR/score-fail$|FAILS=$D/.score-fail  # T138 mutation: V-A reverted|')
LC_ALL=C grep -n 'T138 mutation' "$D/.softhouse/capture/t91/verdict.sh" | sed 's/^/   /'
(cd "$D" && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | sed -n '/=== G-5/,/=== G-6/p' | grep -E 'exit=|VACUOUS|OK      \[G-5\]')
(cd "$D" && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "SCRIPT_EXIT=$?"
echo

echo "=================================================================="
echo "MUTATION — revert V-E: shell-invariance.sh iterates the sh side only"
echo "=================================================================="
D=$(mut ve .softhouse/capture/t91/shell-invariance.sh \
  -e 's|^NAMES=.*$|NAMES=$( ls "$A"/A*.txt 2>/dev/null \| while read -r p; do basename "$p"; done \| sort -u )  # T138 mutation: V-E reverted|')
LC_ALL=C grep -n 'T138 mutation' "$D/.softhouse/capture/t91/shell-invariance.sh" | sed 's/^/   /'
(cd "$D" && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | sed -n '/=== G-7/,/=== VERDICT/p' | grep -E 'exit=|MISSING')
(cd "$D" && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "SCRIPT_EXIT=$?"
echo

echo "=================================================================="
echo "MUTATION — revert V-F: scratch back into \$O"
echo "=================================================================="
D=$(mut vf .softhouse/capture/t91/shell-invariance.sh \
  -e 's|^  norm "\$f" > "\$INVDIR/.inv-a"; norm "\$b" > "\$INVDIR/.inv-b"$|  norm "$f" > "$O/.inv-a"; norm "$b" > "$O/.inv-b"  # T138 mutation: V-F reverted|' \
  -e 's|diff -q "\$INVDIR/.inv-a" "\$INVDIR/.inv-b"|diff -q "$O/.inv-a" "$O/.inv-b"|' \
  -e 's|diff "\$INVDIR/.inv-a" "\$INVDIR/.inv-b"|diff "$O/.inv-a" "$O/.inv-b"|')
LC_ALL=C grep -n 'T138 mutation' "$D/.softhouse/capture/t91/shell-invariance.sh" | sed 's/^/   /'
(cd "$D" && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | sed -n '/=== G-7/,/=== VERDICT/p' | grep -E 'exit=')
(cd "$D" && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "SCRIPT_EXIT=$?"
echo "   -> V-F has NO guard: no leg of prove-guards.sh exercises a read-only \$O for"
echo "      shell-invariance.sh.  Reverting V-F leaves every leg green."
echo

echo "=================================================================="
echo "MUTATION — revert MF-1's SHAPE test (keep T107's value test only)"
echo "=================================================================="
D=$(mut mf1 .softhouse/capture/t91/verdict.sh \
  -e 's|^    EXIT=\*) shape=ok ;;$|    *) shape=ok ;;  # T138 mutation: shape test reverted|' \
  -e 's|^    \*)      shape=bad ;;$|    EXIT=*) shape=ok ;;|')
LC_ALL=C grep -n 'T138 mutation' "$D/.softhouse/capture/t91/verdict.sh" | sed 's/^/   /'
(cd "$D" && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "SCRIPT_EXIT=$? (guards do not cover the shape test)"
echo "   -> MF-1's shape test likewise has no leg in prove-guards.sh; it is driven only"
echo "      by t115-drive-mf1.sh."
