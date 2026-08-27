#!/bin/sh
# T138 — before prescribing a fix for F-T138-1, drive it red myself (P-22).
# Two changes to prove-guards.sh's G-4:
#   (1) poison BEFORE the match on the same line — the only shape BSD grep fails on;
#   (2) assert the SENTENCE-SPECIFIC verdict, which only c=YES can produce.
set -u
C=${1:?checkout}
SHA=bd59187cf83c7c7161db23668e91d45bd46be2a8

build() { # build <dir> [extra-mutation]
  rm -rf "$1"
  git clone --quiet --no-hardlinks --shared "$C" "$1"
  (cd "$1" && git checkout -q -B g4fix "$SHA")
  P=$1/.softhouse/capture/t91/prove-guards.sh
  # (1) poison position
  LC_ALL=C sed -i.bak \
    -e "s|^j = b.find(b'..n', i)\$|# T138: poison BEFORE the match, same line — T108 shape s01/s06|" \
    -e "s|^open(p, 'wb').write(b\[:j\] + b'..xff..xfe' + b\[j:\])\$|open(p, 'wb').write(b[:i] + b'\\\\xff\\\\xfe' + b[i:])|" "$P"
  # (2) assertion
  LC_ALL=C sed -i.bak2 \
    's|^if LC_ALL=C /usr/bin/grep -aq "\^A2a.\*ADMITS" "\$S/g4.txt"; then$|if LC_ALL=C /usr/bin/grep -aq "^A2a.*ADMITS (printed the HALF_UP certification)" "$S/g4.txt"; then|' "$P"
  rm -f "$P".bak*
  (cd "$1" && git add -A && git -c user.name=T138 -c user.email=t138@local commit -q -m 'T138 proposed G-4 fix')
}

echo "=== the two edits, as applied:"
build /tmp/T138-g4fix
LC_ALL=C sed -n '/^python3 - /,/^PY$/p' /tmp/T138-g4fix/.softhouse/capture/t91/prove-guards.sh | sed 's/^/   /'
LC_ALL=C grep -n 'ADMITS (printed' /tmp/T138-g4fix/.softhouse/capture/t91/prove-guards.sh | sed 's/^/   /'
echo
echo "=== GREEN: healthy tree, fixed G-4"
(cd /tmp/T138-g4fix && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | sed -n '/=== G-4/,/=== G-5/p' | LC_ALL=C grep -aE 'BSD |A2a|G-4')
(cd /tmp/T138-g4fix && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "SCRIPT_EXIT=$?"
echo
echo "=== RED: same tree, sentence scanner BLINDED (c=no always)"
build /tmp/T138-g4fix-blind
V=/tmp/T138-g4fix-blind/.softhouse/capture/t91/verdict.sh
LC_ALL=C sed -i.bak 's|if LC_ALL=C grep -aqF "\$S" "\$f"; then c=YES; else c=no; fi|c=no  # T138 mutation: scanner blinded|' "$V"
rm -f "$V.bak"
(cd /tmp/T138-g4fix-blind && git add -A && git -c user.name=T138 -c user.email=t138@local commit -q -m blind)
(cd /tmp/T138-g4fix-blind && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | sed -n '/=== G-4/,/=== G-5/p' | LC_ALL=C grep -aE 'A2a|G-4')
(cd /tmp/T138-g4fix-blind && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "SCRIPT_EXIT=$?"
echo
echo "=== RED 2: LC_ALL=C removed from verdict.sh's sentence grep (the real regression)"
build /tmp/T138-g4fix-nolc
V=/tmp/T138-g4fix-nolc/.softhouse/capture/t91/verdict.sh
LC_ALL=C sed -i.bak 's|if LC_ALL=C grep -aqF "\$S" "\$f"; then c=YES; else c=no; fi|if LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 /usr/bin/grep -aqF "$S" "$f"; then c=YES; else c=no; fi  # T138: LC_ALL=C removed|' "$V"
rm -f "$V.bak"
LC_ALL=C grep -n 'T138: LC_ALL=C removed' "$V" | sed 's/^/   /'
(cd /tmp/T138-g4fix-nolc && git add -A && git -c user.name=T138 -c user.email=t138@local commit -q -m nolc)
(cd /tmp/T138-g4fix-nolc && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | sed -n '/=== G-4/,/=== G-5/p' | LC_ALL=C grep -aE 'A2a|G-4')
(cd /tmp/T138-g4fix-nolc && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "SCRIPT_EXIT=$?"
echo
echo "=== CONTROL: the SHIPPED G-4 against that same LC_ALL=C-removed verdict.sh"
D=/tmp/T138-g4ship-nolc
rm -rf "$D"; git clone --quiet --no-hardlinks --shared "$C" "$D"
(cd "$D" && git checkout -q -B ship "$SHA")
V=$D/.softhouse/capture/t91/verdict.sh
LC_ALL=C sed -i.bak 's|if LC_ALL=C grep -aqF "\$S" "\$f"; then c=YES; else c=no; fi|if LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 /usr/bin/grep -aqF "$S" "$f"; then c=YES; else c=no; fi  # T138: LC_ALL=C removed|' "$V"
rm -f "$V.bak"
(cd "$D" && git add -A && git -c user.name=T138 -c user.email=t138@local commit -q -m nolc)
(cd "$D" && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | sed -n '/=== G-4/,/=== G-5/p' | LC_ALL=C grep -aE 'A2a|G-4')
(cd "$D" && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "SCRIPT_EXIT=$?"
echo "   ^ if this is 0, the SHIPPED G-4 is green on a tree whose hardening has been removed."
