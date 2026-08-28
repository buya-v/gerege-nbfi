#!/bin/sh
# T353 / CONDITION 1. Is `/bin/date -j -f` BSD-only?
#
# The claim under test (the driver marked it UNVERIFIED): `date -j` is a BSD/macOS flag,
# GNU coreutils has no `-j`, therefore `lock_started_age` in `.softhouse/bin/fire-program.sh`
# returns EMPTY on any GNU host, therefore arms 3 (CEILING) and 5 (both-stale) can never
# fire there. Run this on the host and inside containers; POSIX sh so busybox can run it.
echo "=== uname ==="
uname -a
echo "=== /bin/date --version ==="
/bin/date --version 2>&1 | head -2
echo "=== ls -l /bin/date ==="
ls -l /bin/date 2>&1
echo "=== PROBE A: the BSD form the shipped code uses (stderr VISIBLE) ==="
out=$(TZ=UTC /bin/date -j -f "%Y-%m-%dT%H:%M:%SZ" "2026-08-28T00:00:00Z" +%s 2>&1); rc=$?
echo "rc=$rc out=[$out]"
echo "=== PROBE A2: exactly as shipped (2>/dev/null) ==="
out=$(TZ=UTC /bin/date -j -f "%Y-%m-%dT%H:%M:%SZ" "2026-08-28T00:00:00Z" +%s 2>/dev/null); rc=$?
echo "rc=$rc out=[$out]"
if [ -z "$out" ]; then
  echo "VERDICT: EMPTY -> lock_started_age returns empty -> ARMS 3 AND 5 CANNOT FIRE on this host"
else
  echo "VERDICT: parsed -> arms 3 and 5 are live on this host"
fi
echo "=== PROBE B: the GNU form ==="
out=$(/bin/date -u -d "2026-08-28T00:00:00Z" +%s 2>&1); rc=$?
echo "rc=$rc out=[$out]"
echo "=== PROBE C: python3 as a portable parser ==="
if command -v /usr/bin/python3 >/dev/null 2>&1; then
  /usr/bin/python3 -c 'import sys,datetime;print(int(datetime.datetime.strptime(sys.argv[1],"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()))' "2026-08-28T00:00:00Z" 2>&1
else
  echo "no /usr/bin/python3"
fi
echo "=== PROBE D: pure-shell ISO shape check + epoch (no date, no python) ==="
# what T353 actually ships: shape by zsh glob, epoch by days-from-civil in integer arithmetic.
echo "(driven separately by epoch-parity.zsh)"
