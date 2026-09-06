#!/usr/bin/env bash
# t553-failclosed.sh <repo> <old-guard> <new-guard>
# T552 MAJOR-2: every path that can leave the guard BEFORE a verdict is reached
# must exit 2 (REFUSE), never 1 (which the call site logs as
# "**RED — THAT PRODUCER IS NOT ADVANCING THE MIGRATION**"). Drives the whole
# prologue on both guards. Exit 1 in the AFTER column would be a bug.
set -uo pipefail
REPO="$1"; OLD="$2"; NEW="$3"
cd "$REPO"
case_rc() {  # case_rc <label> <guard> <env...> -- <args...>
  local label="$1" guard="$2"; shift 2
  local envs=() ; while [ "$1" != "--" ]; do envs+=("$1"); shift; done; shift
  env "${envs[@]}" "$guard" "$@" >/dev/null 2>&1
  printf '%s' "$?"
}
row() {  # row <label> <env...> -- <args...>
  local label="$1"; shift
  local o n
  o="$(case_rc "$label" "$OLD" "$@")"
  n="$(case_rc "$label" "$NEW" "$@")"
  local verdict="ok"
  [ "$n" = 2 ] || verdict="**LEAKS $n**"
  printf '%-46s before_rc=%s  after_rc=%s  %s\n' "$label" "$o" "$n" "$verdict"
}
echo "# T553 — fail-closed sweep of the SHELL PROLOGUE (T552 MAJOR-2)"
echo "# rc=1 is a VERDICT about the producer; only rc=2 is 'no verdict'."
echo
row "--streak with no value"                 -- --producer local --ref origin/main --no-fetch --streak
row "--ref with no value"                    -- --producer local --no-fetch --ref
row "--explain with no value"                -- --producer local --ref origin/main --no-fetch --explain
row "--producer with no value"               -- --no-fetch --producer
row "--now with no value"                    -- --producer local --ref origin/main --no-fetch --now
row "--min-subst-lines with no value"        -- --producer local --ref origin/main --no-fetch --min-subst-lines
row "--lookback-days with no value"          -- --producer local --ref origin/main --no-fetch --lookback-days
row "--silence-hours with no value"          -- --producer local --ref origin/main --no-fetch --silence-hours
row "--earned-silence-hours with no value"   -- --producer local --ref origin/main --no-fetch --earned-silence-hours
row "unwritable TMPDIR (mktemp fails)"       TMPDIR=/nonexistent-dir-xyz -- --producer local --ref origin/main --no-fetch --quiet
row "NOFS_PAYLOAD_CAP=abc (cap disabled)"    NOFS_PAYLOAD_CAP=abc -- --producer local --ref origin/main --no-fetch --quiet
row "NOFS_PAYLOAD_CAP=0"                     NOFS_PAYLOAD_CAP=0 -- --producer local --ref origin/main --no-fetch --quiet
row "NOFS_PAYLOAD_CAP=-5"                    NOFS_PAYLOAD_CAP=-5 -- --producer local --ref origin/main --no-fetch --quiet
row "--min-subst-lines 0 (floor would be off)" -- --producer local --ref origin/main --no-fetch --quiet --min-subst-lines 0
row "unknown argument"                       -- --wat
row "unknown producer"                       -- --producer martian --ref origin/main --no-fetch
row "ref that does not exist"                -- --producer local --ref no/such/ref --no-fetch
row "bad NOFS_SURFACE_RE (analyser crash)"   NOFS_SURFACE_RE='(' -- --producer local --ref origin/main --no-fetch
row "bad NOFS_BOOKKEEPING_RE (analyser crash)" NOFS_BOOKKEEPING_RE='*' -- --producer local --ref origin/main --no-fetch
row "--now not-a-date (analyser crash)"      -- --producer local --ref origin/main --no-fetch --now not-a-date
row "--streak xyz (analyser crash)"          -- --producer local --ref origin/main --no-fetch --streak xyz
echo
echo "# NOTE: 'NOFS_PAYLOAD_CAP=' (empty) is NOT listed: \${NOFS_PAYLOAD_CAP:-200}"
echo "# substitutes the default for an EMPTY value as well as an unset one, so the"
echo "# empty case never reaches awk. T552 MINOR-5's 'abc' half reproduces; its"
echo "# empty-string half does not — measured, both guards, see the handoff."
