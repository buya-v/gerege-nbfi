#!/bin/sh
# T138 — r14 attempt 1 applied edit (1) with a `sed` whose pattern did not match, so the
# python block was COPIED unchanged.  That is V-C's own lesson landing on me, and I only
# noticed because the script echoed the block back.  Recorded, then redone with python.
set -u
C=${1:?checkout}
SHA=bd59187cf83c7c7161db23668e91d45bd46be2a8

build() { # build <dir> <do-poison-fix yes|no> <do-assert-fix yes|no>
  rm -rf "$1"
  git clone --quiet --no-hardlinks --shared "$C" "$1"
  (cd "$1" && git checkout -q -B g4 "$SHA")
  P=$1/.softhouse/capture/t91/prove-guards.sh
  if [ "$2" = yes ]; then
    python3 - "$P" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = "open(p, 'wb').write(b[:j] + b'\\xff\\xfe' + b[j:])"
new = "open(p, 'wb').write(b[:i] + b'\\xff\\xfe' + b[i:])   # T138: BEFORE the match (T108 s01/s06)"
assert old in s, 'ABORT: poison line not found — the edit would have been a no-op'
s = s.replace(old, new)
open(p, 'w').write(s)
print('   poison-position edit APPLIED (asserted, not assumed)')
PY
  fi
  if [ "$3" = yes ]; then
    python3 - "$P" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = 'if LC_ALL=C /usr/bin/grep -aq "^A2a.*ADMITS" "$S/g4.txt"; then'
new = 'if LC_ALL=C /usr/bin/grep -aq "^A2a.*ADMITS (printed the HALF_UP certification)" "$S/g4.txt"; then'
assert old in s, 'ABORT: assertion line not found — the edit would have been a no-op'
open(p, 'w').write(s.replace(old, new))
print('   assertion edit APPLIED (asserted, not assumed)')
PY
  fi
  (cd "$1" && git add -A && git -c user.name=T138 -c user.email=t138@local commit -q -m 'T138 G-4 fix')
}

blind() { # blind <dir> <mode: scanner|nolc>
  V=$1/.softhouse/capture/t91/verdict.sh
  python3 - "$V" "$2" <<'PY'
import sys
p, mode = sys.argv[1], sys.argv[2]
s = open(p).read()
old = 'if LC_ALL=C grep -aqF "$S" "$f"; then c=YES; else c=no; fi'
assert old in s, 'ABORT: scanner line not found'
new = ('c=no  # T138: scanner blinded' if mode == 'scanner'
       else 'if LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 /usr/bin/grep -aqF "$S" "$f"; then c=YES; else c=no; fi  # T138: LC_ALL=C removed')
open(p, 'w').write(s.replace(old, new))
print('   verdict.sh mutated: %s' % mode)
PY
  (cd "$1" && git add -A && git -c user.name=T138 -c user.email=t138@local commit -q -m "mutate $2")
}

run() { # run <dir> <label>
  echo "--- $2"
  (cd "$1" && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | sed -n '/=== G-4/,/=== G-5/p' \
      | LC_ALL=C grep -aE 'BSD +-?a?qF|^A2a|\[G-4\]')
  (cd "$1" && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "    SCRIPT_EXIT=$?"
  echo
}

echo "############ the SHIPPED G-4 (baseline)"
build /tmp/T138b-ship no no;      run /tmp/T138b-ship "healthy tree"
build /tmp/T138b-ship-nolc no no; blind /tmp/T138b-ship-nolc nolc
run /tmp/T138b-ship-nolc "LC_ALL=C REMOVED from verdict.sh's scanner  <-- the regression G-4 exists to catch"

echo "############ with BOTH T138 edits"
build /tmp/T138b-fix yes yes;      run /tmp/T138b-fix "healthy tree (must stay GREEN)"
build /tmp/T138b-fix-nolc yes yes; blind /tmp/T138b-fix-nolc nolc
run /tmp/T138b-fix-nolc "LC_ALL=C REMOVED  <-- must now go RED"
build /tmp/T138b-fix-blind yes yes; blind /tmp/T138b-fix-blind scanner
run /tmp/T138b-fix-blind "scanner fully blinded  <-- must go RED"

echo "############ each edit alone, to show BOTH are needed"
build /tmp/T138b-p yes no; blind /tmp/T138b-p nolc
run /tmp/T138b-p "poison-position edit ONLY, LC_ALL=C removed"
build /tmp/T138b-a no yes; blind /tmp/T138b-a nolc
run /tmp/T138b-a "assertion edit ONLY, LC_ALL=C removed"
