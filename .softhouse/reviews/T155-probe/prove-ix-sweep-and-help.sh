#!/bin/bash
# T155 probe (ix) — the sweep claim, and that the sweep did not break anything.
#   * every grep invocation in conformance.sh carries BOTH tokens
#   * no aliased spelling (egrep/fgrep/zgrep) slipped past a lexical sweep
#   * --help still works (the sentinel search at :449 was one of the swept sites)
#   * the whole .softhouse tree, so the "24 sites" claim can be sized
set -u
POST=/tmp/t155/post
PRE=/tmp/t155/pre
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh

count_invocations() { # $1 file — grep invocations, comments excluded
  LC_ALL=C grep -anE '(^|[;|&(]|[[:space:]])(LC_ALL=C[[:space:]]+)?(e|f|z|r)?grep[[:space:]]' "$1" \
    | LC_ALL=C grep -av '^[0-9]*: *#' | wc -l | tr -d ' '
}
echo "conformance.sh grep invocation sites:  PRE=$(count_invocations "$PRE/.softhouse/conformance.sh")  POST=$(count_invocations "$POST/.softhouse/conformance.sh")"
echo
echo "POST sites WITHOUT both tokens (must be empty):"
LC_ALL=C grep -anE '(^|[;|&(]|[[:space:]])(e|f|z|r)?grep[[:space:]]' "$POST/.softhouse/conformance.sh" \
  | LC_ALL=C grep -av 'LC_ALL=C grep -a' | LC_ALL=C grep -av '^[0-9]*: *#' | sed 's/^/  MISSED /'
echo "  (end)"
echo
echo "aliased spellings anywhere in .softhouse (egrep/fgrep/zgrep):"
LC_ALL=C grep -arnE '\b(e|f|z)grep\b' "$POST/.softhouse/conformance.sh" "$POST/.softhouse/bin" | sed 's/^/  /'
echo "  (end)"
echo
echo "unhardened greps left in .softhouse/bin (T154 disclosed exactly one):"
LC_ALL=C grep -rnE '(^|[;|&(]|[[:space:]])grep[[:space:]]' "$POST/.softhouse/bin" | LC_ALL=C grep -av 'LC_ALL=C grep -a' | sed 's/^/  /'
echo "  (end)"
echo
echo "=== --help still exits 0 and prints the help, not raw shell ==="
( cd "$POST" && bash "$POST/.softhouse/conformance.sh" --help ) > /tmp/t155/out/ix-help.txt 2>&1
echo "exit=$?  lines=$(wc -l < /tmp/t155/out/ix-help.txt | tr -d ' ')"
echo "first line: $(head -1 /tmp/t155/out/ix-help.txt)"
echo "leaked raw shell? $(LC_ALL=C grep -ac 'set -u -o pipefail\|SCRIPT_DIR=' /tmp/t155/out/ix-help.txt) lines (want 0)"
echo "sentinel leaked?  $(LC_ALL=C grep -ac '#=END-OF-HELP=' /tmp/t155/out/ix-help.txt) lines (want 0)"
echo
echo "=== the sweeper is idempotent (re-running it must change nothing) ==="
cp "$POST/.softhouse/conformance.sh" /tmp/t155/sweep-before.sh
cp "$POST/.softhouse/conformance.sh" /tmp/t155/sweep-test.sh
perl "$POST/.softhouse/capture/t154-nofloat/sweep-harden-greps.pl" /tmp/t155/sweep-test.sh 2>&1 | sed 's/^/  /'
if diff -q /tmp/t155/sweep-before.sh /tmp/t155/sweep-test.sh >/dev/null; then
  echo "  IDEMPOTENT: re-running the sweeper on the swept file changes nothing"
else
  echo "  *** NOT IDEMPOTENT — the sweeper would double-harden:"
  diff /tmp/t155/sweep-before.sh /tmp/t155/sweep-test.sh | head -10 | sed 's/^/    /'
fi
