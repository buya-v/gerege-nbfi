#!/bin/sh
# T40 — self-check of T40's OWN write surface against the project non-negotiables.
# A grep proves absence of a known-bad pattern; it never proves correctness.
set -u
CH=/Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513/.softhouse/capture/charges
fails=0
ok()  { printf '  PASS  %s\n' "$1"; }
bad() { printf '  FAIL  %s\n' "$1" >&2; fails=$((fails+1)); }

# S1 — prohibited database engines. The only permitted engine is PostgreSQL.
# The preconditions script and the attestation generator contain these strings inside
# grep PATTERNS that assert the engines are ABSENT; those two files are excluded by name
# and their assertions are reported separately in the attestation.
h=$(grep -rIl -E 'ojdbc|oracle\.jdbc|:1521|com\.mysql\.cj|mariadb|go-sql-driver' "$CH" 2>/dev/null \
    | grep -v 'bin/preconditions.sh' | grep -v 'bin/attest' | grep -v 'bin/selfcheck.sh')
[ -z "$h" ] && ok "no prohibited-engine token outside the detection patterns" \
  || bad "prohibited-engine token in: $h"

# S2 — no floating-point construction in any T40 analysis code.
h=$(grep -rn -E '\bfloat\(|\bdouble\b|float64|numpy|math\.fsum' "$CH"/bin 2>/dev/null \
    | grep -v 'bin/selfcheck.sh' | grep -v 'parse_float=')
[ -z "$h" ] && ok "no float construction in T40 analysis code" || bad "float in: $h"

# S3 — every analysis script parses JSON numbers straight to Decimal or exact text.
for f in "$CH"/bin/fullcell.py "$CH"/bin/feecols.py "$CH"/bin/invariants.py; do
  grep -q 'parse_float=Decimal' "$f" && ok "$(basename "$f") parses money to Decimal" \
    || bad "$(basename "$f") does not force parse_float=Decimal"
done
grep -q 'parse_float=str' "$CH"/bin/attest-t40.py && ok "attest-t40.py serialises money as exact text" \
  || bad "attest-t40.py does not force parse_float=str"

# S4 — Mongolia name rule.
h=$(grep -rIn -E 'first_name|last_name|firstName|lastName' "$CH" 2>/dev/null | grep -v 'bin/selfcheck.sh')
[ -z "$h" ] && ok "no first_name/last_name anywhere" || bad "name-field violation: $h"

# S5 — never describe savings as insured/protected/guaranteed.
h=$(grep -rIn -iE 'insured|deposit (is|are) (protected|guaranteed)' "$CH" 2>/dev/null | grep -v 'bin/selfcheck.sh')
[ -z "$h" ] && ok "no insured/protected/guaranteed savings language" || bad "$h"

# S6 — no hard-coded UTC offset in place of a zone id.
h=$(grep -rIn -E '\+08:00|\+07:00|UTC\+8|UTC\+7' "$CH" 2>/dev/null | grep -v 'no DST' | grep -v 'is +08')
[ -z "$h" ] && ok "no hard-coded offset (zone ids only)" || bad "hard-coded offset: $h"

# S7 — every capture file in out/fc is an HTTP 200 body, not an error body.
h=$(grep -lI 'httpStatusCode' "$CH"/out/fc/*.json 2>/dev/null)
[ -z "$h" ] && ok "no error body filed as a capture in out/fc" || bad "error body in: $h"

echo
[ "$fails" -eq 0 ] && echo "SELF-CHECK: all pass ($fails failures)." || { echo "SELF-CHECK FAILED: $fails" >&2; exit 1; }
