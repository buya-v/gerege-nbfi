#!/bin/bash
# T155 probe (x) — two claims T154 made in prose and did not drive.
#
#  (a) F-6: "a guard that can be REMOVED is not covered by any of this."
#      Delete the census from a scratch copy and see whether anything notices.
#  (b) Blockers/1: fire-program.sh:224's unhardened `grep -v` is FAIL-CLOSED
#      under BSD grep. Simulate a blind grep and check which way it falls.
set -u
POST=/tmp/t155/post
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh

echo "=== (a) can the no-float census simply be DELETED? ==="
S=/tmp/t155/removed
rm -rf "$S"; cp -R "$POST" "$S"
# The minimal deletion a future worker would make: drop the Run call site.
perl -0pi -e 's{\tif census, cerr := ScanGoTreeForFloatingPoint.*?\n\t\}\n}{}s' \
  "$S/nexus/internal/apps/loanschedule/conformance/grade.go"
if LC_ALL=C grep -aq 'ScanGoTreeForFloatingPoint' "$S/nexus/internal/apps/loanschedule/conformance/grade.go"; then
  echo "  APPARATUS: the deletion did not apply; skipping (the probe would be vacuous)"
else
  echo "  the Run call site is gone from grade.go"
  # plant the float literal that the census is the only thing that catches
  printf 'package loanschedule\n\nfunc t155Gone(p int64) int64 { r := 0.036; return p + int64(r) }\n\nvar _ = t155Gone\n' \
    > "$S/nexus/internal/apps/loanschedule/t155_gone.go"
  ( cd "$S/nexus" && go build ./... ) >/dev/null 2>&1; echo "  go build exit=$?"
  ( cd "$S" && bash "$S/.softhouse/conformance.sh" ) > /tmp/t155/out/x-removed.txt 2>&1
  echo "  conformance.sh exit=$?"
  LC_ALL=C grep -aE '^VERDICT|no-float census|probe = ' /tmp/t155/out/x-removed.txt | sed 's/^ */    /'
  echo "  -> if that says PASS, F-6 is real: the guard is deletable and nothing in the harness says so."
  echo "  and does `go test` catch the deletion?"
  ( cd "$S/nexus" && go test -run 'TestNoFloat' ./internal/apps/loanschedule/conformance ) > /tmp/t155/out/x-removed-test.txt 2>&1
  echo "     go test -run TestNoFloat exit=$?  $(tail -2 /tmp/t155/out/x-removed-test.txt | head -1)"
fi
echo

echo "=== (b) fire-program.sh:224 — which way does a BLIND grep -v fall? ==="
# Real BSD grep, real invalid byte, the real pattern.
printf ' M nexus/x.go\n?? \xe2.softhouse/LOCK\n?? .softhouse/LOCK\n' > /tmp/t155/status.txt
echo "  simulated \`git status --porcelain\` (one line carries an invalid byte):"
cat -v /tmp/t155/status.txt | sed 's/^/    /'
DIRTY_UNHARDENED=$(cat /tmp/t155/status.txt | grep -v '^?? \.softhouse/LOCK' || true)
DIRTY_HARDENED=$(cat /tmp/t155/status.txt | LC_ALL=C grep -av '^?? \.softhouse/LOCK' || true)
echo "  unhardened DIRTY lines: $(printf '%s' "$DIRTY_UNHARDENED" | LC_ALL=C grep -ac . )"
echo "  hardened   DIRTY lines: $(printf '%s' "$DIRTY_HARDENED"   | LC_ALL=C grep -ac . )"
echo "  DIRTY non-empty either way => the rescue path runs => FAIL-CLOSED, as T154 argued."
echo "  (the only cost of the blind grep here is a spurious DIRTY, never a skipped rescue.)"
