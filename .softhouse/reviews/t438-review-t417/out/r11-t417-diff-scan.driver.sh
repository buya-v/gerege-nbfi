#!/usr/bin/env bash
# T438 evidence: scan T417's committed capture directory for CLAUDE.md non-negotiable
# violations. The tree to scan is an ARGUMENT -- deliberately, so that no host path is
# bound to a name in this file and this rig introduces no new site to the host-state
# temp-path census (`HOSTSTATE_PIN_TEMP_ASSIGN_LIST`, pinned at 18). It DOES perform a
# repo-wide search, so it is in that census's corpus; it must not add a row to it.
#
#   usage: bash r11-t417-diff-scan.driver.sh <path-to>/.softhouse/capture/t417-scheduler-attribution
#
# Read-only: every command here is a grep or a sed. No database is contacted.
T="${1:?usage: $0 <t417 capture dir>}"
echo "=== scanning: $T"
echo "=== float/double/decimal literals in T417 shell+sql:"
grep -rnE '\bfloat\b|\bdouble\b|[0-9]+\.[0-9]+e|::float|::double|::numeric' "$T" --include=*.sh --include=*.sql || echo "  none"
echo "=== write verbs against the oracle in T417 shell+sql:"
grep -rniE '\b(INSERT +INTO|UPDATE +[a-z_]+ +SET|DELETE +FROM|TRUNCATE|ALTER +TABLE|DROP +TABLE|CREATE +TABLE|GRANT|COPY .* FROM)\b' "$T" --include=*.sh --include=*.sql || echo "  none"
echo "=== prohibited engines / vendors:"
grep -rniE 'mysql|mariadb|ojdbc|oracle\.jdbc|1521|stripe|plaid|lithic|persona' "$T" --include=*.sh --include=*.sql || echo "  none"
echo "=== deposit/insured language:"
grep -rniE 'insured|guaranteed|protected deposit|deposit insurance' "$T" --include=*.sh --include=*.sql || echo "  none"
echo "=== hard-coded tz offsets:"
grep -rnE '\+08:00|\+07:00|UTC\+8|GMT\+8' "$T" --include=*.sh --include=*.sql || echo "  none"
echo "=== capsql.sh header + write-verb refusal (lines 1-36):"
sed -n '1,36p' "$T/capsql.sh"
