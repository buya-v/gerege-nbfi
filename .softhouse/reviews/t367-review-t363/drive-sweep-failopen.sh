#!/usr/bin/env bash
# T367 -- DRIVE the fail-open shape in T363's casualty-sweep.sh sel().
#
# THE CLAIM UNDER TEST. casualty-sweep.sh's whole thesis is P-66/P-70: "not found" is a
# statement about the SEARCH, never about the world, so the script must be the statement.
# Its sel() is:
#
#     all=$(git grep "$@" -- .softhouse/ 2>/dev/null)
#
# `git grep` exits 0 on a hit, 1 on no hit, and >=2 on a BAD PATTERN or a usage error. This
# line discards stderr AND never reads the exit status, so all three collapse to "0 hits".
# A selector that never ran is reported identically to a selector that ran and found nothing --
# which is exactly the T232 defect the file's own header cites as its reason for existing.
#
# READ-ONLY. This is a grep. It touches no database and no network.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 2

sel_asshipped() { # verbatim from casualty-sweep.sh:34-45, trimmed to the counting lines
  local label="$1"; shift
  local all live arch
  all=$(git grep "$@" -- .softhouse/ 2>/dev/null)
  live=$(printf '%s' "$all" | grep -v -E '(/out/|\.softhouse/handoff/)')
  arch=$(printf '%s' "$all" | grep -c -E '(/out/|\.softhouse/handoff/)')
  printf '  %-46s total=%-5s archived=%-5s LIVE=%s\n' "$label" \
    "$(printf '%s' "$all" | grep -c .)" "$arch" "$(printf '%s' "$live" | grep -c .)"
}

echo "A) a selector that IS valid and DOES hit"
sel_asshipped "-F 'acc_gl_journal_entry'" -n -F 'acc_gl_journal_entry'

echo
echo "B) a selector that IS valid and genuinely finds nothing"
sel_asshipped "-F 'zzz-no-such-string-t367'" -n -F 'zzz-no-such-string-t367'

echo
echo "C) a selector that is MALFORMED and never ran -- indistinguishable from B"
sel_asshipped "-E 'gl (16|17' (unbalanced paren)" -n -E 'gl (16|17'

echo
echo "D) the same malformed selector with the exit status the script throws away:"
git grep -n -E 'gl (16|17' -- .softhouse/ >/dev/null 2>&1
echo "     git grep rc for the MALFORMED pattern = $?"
git grep -n -F 'zzz-no-such-string-t367' -- .softhouse/ >/dev/null 2>&1
echo "     git grep rc for the EMPTY-RESULT pattern = $?"
git grep -n -F 'acc_gl_journal_entry' -- .softhouse/ >/dev/null 2>&1
echo "     git grep rc for the HITTING pattern      = $?"
echo
echo "  If rc for MALFORMED differs from rc for EMPTY-RESULT, the information needed to"
echo "  distinguish B from C exists and casualty-sweep.sh discards it."

echo
echo "E) does the shipped script read that status anywhere?"
n=$(grep -c 'git grep' .softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh 2>/dev/null \
    || git show softhouse/T363-oracle-baseline:.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh | grep -c 'git grep')
echo "     'git grep' occurrences in the shipped sweep: $n"
git show softhouse/T363-oracle-baseline:.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh \
  | grep -nE 'rc=|\$\?|exit [0-9]' | sed 's/^/     /'
echo "     (nothing above means: no exit status of git grep is ever inspected)"
