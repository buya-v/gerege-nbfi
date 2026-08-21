#!/bin/sh
# T151 — SHIP NO GUARD YOU HAVE NOT DRIVEN RED (P-22), applied to the two checks T151 itself adds.
#
# F-T138-7: `prove-guards.sh`'s G-6 and G-7 legs PRINTED their diagnostic through
# `grep … | head -n | sed 's/^/   /'` and never compared it.  Only the exit status was graded, so
# any exit 2 (G-6) or exit 1 (G-7) scored OK — including one produced by a completely different
# failure.  T151 adds a comparison to each.  A comparison that has never failed has not been tested,
# and F-T138-5 is precisely the finding that a claimed-red guard may have no red leg at all.  So
# both new comparisons are driven red here.
#
# THE TWO RED CASES.  Each makes the guarded script exit with the RIGHT CODE for the WRONG REASON,
# which is exactly what the old print-only form could not see:
#   G-6  run-attacks.sh with `assert_mutated` REMOVED and A7's symlink pointed at the SWAP request.
#        It still exits 2 — but for "A7's symlink does not read back as the canonical request",
#        not for "the sed substitution did not take".  This is T138's demonstration, re-driven.
#   G-7  shell-invariance.sh with the one-sided branch relabelled to print `DIFFERS` instead of
#        `MISSING`.  It still exits 1, and the union domain still caught the one-sided name — but
#        the transcript no longer says so, and a reader cannot tell the union fix from a plain
#        content difference.
#
# GREEN is the shipped tree: both comparisons must pass there, or the RED legs prove nothing.
#
# PRE/POST discipline: this driver does not need a baseline — it mutates the tree under test, which
# it resolves as HEAD, and every mutation is applied in python with `assert old in s` so a pattern
# that does not match ABORTS instead of silently leaving the tree healthy.
#
# Destructive: throwaway clones under /tmp only.  prove-guards.sh's G-1 legs contact the oracle
# read-only; nothing here restarts, rebuilds, re-seeds or writes to it.
#
# Usage:  sh t151-drive-g67.sh
# Exit:   0 = every leg behaved as specified; 1 = a leg did not; 2 = the harness could not set up.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
HEAD_SHA=$(cd "$ROOT" && git rev-parse HEAD)
S=/tmp/t151-g67.$$
trap 'rm -rf "$S"' EXIT
mkdir -p "$S"
BAD=0

echo "tree under test = $HEAD_SHA (HEAD)"
echo

build() {  # build <dir>
  rm -rf "$1"
  git clone --quiet --no-hardlinks --shared "$ROOT" "$1" || { echo "ABORT: clone failed" >&2; exit 2; }
  (cd "$1" && git checkout -q -B t151g67 "$HEAD_SHA") || { echo "ABORT: checkout failed" >&2; exit 2; }
}

break_g6() {  # remove the mutation assertion AND redirect A7's symlink -> exit 2 for the wrong reason
  python3 - "$1/.softhouse/capture/t91/run-attacks.sh" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
for old in ('assert_mutated "$O/req-mutated-55.json" 1162502.55\n',
            'assert_mutated "$O/req-crafted-04.json" 1162502.4\n'):
    assert old in s, 'ABORT: %r not found — the mutation would be a no-op' % old
    s = s.replace(old, '')
old = 'ln -s "$CANON" "$O/link-to-canon.json"'
assert old in s, 'ABORT: A7 symlink line not found'
s = s.replace(old, 'ln -s "$SWAP" "$O/link-to-canon.json"')
open(p, 'w').write(s)
PY
  [ $? -eq 0 ] || { echo "ABORT: G-6 mutation did not apply" >&2; exit 2; }
  (cd "$1" && git add -A && git -c user.name=T151 -c user.email=t151@local commit -q -m 'T151 break G-6 reason')
}

break_g7() {  # relabel the one-sided branch -> exit 1 without naming the SH-side absence
  python3 - "$1/.softhouse/capture/t91/shell-invariance.sh" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = 'echo "MISSING  $f  (present under $L-bash only)"'
assert old in s, 'ABORT: the one-sided branch was not found'
open(p, 'w').write(s.replace(old, 'echo "DIFFERS    $(basename "$f")"'))
PY
  [ $? -eq 0 ] || { echo "ABORT: G-7 mutation did not apply" >&2; exit 2; }
  (cd "$1" && git add -A && git -c user.name=T151 -c user.email=t151@local commit -q -m 'T151 break G-7 reason')
}

run() {  # run <dir> <label> <want reason-line for G-6: OK|RED> <want for G-7> <want script exit>
  (cd "$1" && sh .softhouse/capture/t91/prove-guards.sh) > "$1.txt" 2>&1
  rc=$?
  if LC_ALL=C /usr/bin/grep -aq 'G-6 refused for the RIGHT reason' "$1.txt"; then g6=OK; else g6=RED; fi
  if LC_ALL=C /usr/bin/grep -aq 'G-7 named the SH-side absence' "$1.txt"; then g7=OK; else g7=RED; fi
  printf '  %-46s G-6 reason=%-3s (want %-3s)  G-7 reason=%-3s (want %-3s)  exit=%s (want %s)' \
         "$2" "$g6" "$3" "$g7" "$4" "$rc" "$5"
  if [ "$g6" = "$3" ] && [ "$g7" = "$4" ] && [ "$rc" = "$5" ]; then echo "   OK"
  else echo "   *** NOT AS SPECIFIED ***"; BAD=$((BAD+1)); fi
  LC_ALL=C /usr/bin/grep -aE 'G-6 (refused|exited)|G-7 (named|exited)|HARNESS ERROR|^   (MISSING|DIFFERS)' "$1.txt" \
    | head -6 | sed 's/^/       /'
  echo
}

echo "=== GREEN: the shipped tree — both comparisons must pass, or the RED legs prove nothing"
build "$S/green"; run "$S/green" "shipped tree" OK OK 0

echo "=== RED 1: run-attacks.sh exits 2 for the WRONG reason (A7's symlink, not the sed mutation)"
build "$S/red6"; break_g6 "$S/red6"; run "$S/red6" "assert_mutated removed + A7 symlink redirected" RED OK 1

echo "=== RED 2: shell-invariance.sh exits 1 without naming the SH-side absence"
build "$S/red7"; break_g7 "$S/red7"; run "$S/red7" "one-sided branch relabelled DIFFERS" OK RED 1

if [ "$BAD" -eq 0 ]; then
  echo "done — every leg behaved as specified."
  echo "F-T138-7 CLOSED: G-6 and G-7 now compare their diagnostic, and both comparisons are red-driven."
  exit 0
fi
echo "done — $BAD leg(s) did NOT behave as specified."
exit 1
