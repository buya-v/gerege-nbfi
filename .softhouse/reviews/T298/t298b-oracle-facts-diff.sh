#!/usr/bin/env bash
# T298 (resumed) — brief item 5: NO ORACLE FACT WAS DAMAGED.
# `.softhouse/reference-oracle.md` is the file of record for the reference oracle (Fineract)
# connection facts. "The oracle" here is the FINERACT REFERENCE IMPLEMENTATION (test-oracle
# sense) — Oracle Database is PROHIBITED by CLAUDE.md and must appear nowhere.
# Method: diff ONLY what T256 touched — 47b9b5c (pre) vs e6fca83 (post). The current fire's
# appended bring-up section is deliberately NOT in that range, so it cannot contaminate this.
set -u -o pipefail
PRE=47b9b5c
POST=e6fca83
DOC=.softhouse/reference-oracle.md
echo "T298 oracle-fact diff — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "range under review: $PRE (pre-T256) .. $POST (T256 tip).  HEAD = $(git rev-parse --short HEAD)"
echo

echo "1. EXACTLY WHICH LINES DID T256 TOUCH IN THIS FILE?"
git diff "$PRE".."$POST" -- "$DOC" | grep -c '^[+-][^+-]' | sed 's/^/   changed lines: /'
echo "   hunk headers:"
git diff "$PRE".."$POST" -- "$DOC" | grep '^@@' | sed 's/^/     /'
echo

echo "2. THE FACT ROWS — extracted from BOTH revisions and diffed"
FACTS='tenant|fineract_gerege|PostgreSQL|postgres|5432|8443|426a23544|Asia/Ulaanbaatar|docker-compose-postgresql|jdbc|driver|HALF_UP|MathContext|precision|496|fineract-db|actuator/health|mifos|base_?url|BASIC|username|password'
git show "$PRE:$DOC"  | grep -n -iE "$FACTS" | sed 's/^/PRE  /' > /tmp/t298pre.txt
git show "$POST:$DOC" | grep -n -iE "$FACTS" | sed 's/^/POST /' > /tmp/t298post.txt
echo "   fact-bearing lines PRE  = $(wc -l < /tmp/t298pre.txt  | tr -d ' ')"
echo "   fact-bearing lines POST = $(wc -l < /tmp/t298post.txt | tr -d ' ')"
echo "   diff of the fact-bearing TEXT (line numbers stripped, so a pure shift is not noise):"
sed 's/^PRE  *[0-9]*://'  /tmp/t298pre.txt  > /tmp/t298pret.txt
sed 's/^POST *[0-9]*://'  /tmp/t298post.txt > /tmp/t298postt.txt
if diff -u /tmp/t298pret.txt /tmp/t298postt.txt > /tmp/t298factdiff.txt; then
  echo "     IDENTICAL — every fact-bearing line survives T256 byte-for-byte."
else
  echo "     DIFFERENCES:"; sed 's/^/       /' /tmp/t298factdiff.txt
fi
echo

echo "3. NAMED FACTS, asserted one at a time in BOTH revisions (P-70: presence measured, not assumed)"
check() { # label pattern
  local pre post
  pre=$(git show "$PRE:$DOC"  | grep -c -F -- "$2" || true)
  post=$(git show "$POST:$DOC" | grep -c -F -- "$2" || true)
  if [ "$pre" -gt 0 ] && [ "$post" -ge "$pre" ]; then
    printf '   ok       %-42s pre=%-4s post=%-4s\n' "$1" "$pre" "$post"
  elif [ "$pre" -gt 0 ] && [ "$post" -lt "$pre" ]; then
    printf '   *** LOST %-42s pre=%-4s post=%-4s\n' "$1" "$pre" "$post"
  else
    printf '   absent-in-both %-36s pre=%-4s post=%-4s\n' "$1" "$pre" "$post"
  fi
}
check "tenant identifier"            "gerege"
check "database name"                "fineract_gerege"
check "PostgreSQL named"             "PostgreSQL"
check "postgres compose profile"     "docker-compose-postgresql.yml"
check "pinned Fineract commit"       "426a23544"
check "timezone Asia/Ulaanbaatar"    "Asia/Ulaanbaatar"
check "oracle health endpoint"       "actuator/health"
check "https port 8443"              "8443"
check "postgres port 5432"           "5432"
check "rounding mode HALF_UP"        "HALF_UP"
check "MoneyHelper precision 19"     "19"
check "db container fineract-db-1"   "fineract-db-1"
echo

echo "4. THE PROHIBITED PRODUCT — Oracle Database must appear NOWHERE in either revision"
for pat in ojdbc 'oracle.jdbc' 1521 'OracleDialect' 'jdbc:oracle'; do
  a=$(git show "$PRE:$DOC"  | grep -c -F -- "$pat" || true)
  b=$(git show "$POST:$DOC" | grep -c -F -- "$pat" || true)
  printf '   %-16s pre=%s post=%s  %s\n' "$pat" "$a" "$b" "$( [ "$b" -eq 0 ] && echo 'ok (measured zero)' || echo '*** PRESENT — REJECTION' )"
done
echo "   and the forbidden compose profiles:"
for pat in docker-compose-mysql docker-compose-mariadb; do
  b=$(git show "$POST:$DOC" | grep -c -F -- "$pat" || true)
  ctx=$(git show "$POST:$DOC" | grep -n -F -- "$pat" | head -2 | sed 's/^/       /')
  printf '   %-26s post=%s\n%s\n' "$pat" "$b" "$ctx"
done
echo

echo "5. THE build-oracle-image.sh INVOCATION CHANGE — the one T256 made on purpose"
echo "   PRE:"
git show "$PRE:$DOC"  | grep -n -F 'build-oracle-image.sh' | sed 's/^/     /'
echo "   POST:"
git show "$POST:$DOC" | grep -n -F 'build-oracle-image.sh' | sed 's/^/     /'
echo "   does the referenced script still exist at HEAD, and is it executable?"
ls -l .softhouse/bin/build-oracle-image.sh | sed 's/^/     /'
echo "   does the NEW invocation form resolve to it from this worktree?"
P="$(git rev-parse --show-toplevel)/.softhouse/bin/build-oracle-image.sh"
printf '     resolved: %s  -> %s\n' "$P" "$( [ -x "$P" ] && echo 'EXISTS and is executable' || echo '*** MISSING' )"
echo

echo "6. DID T256 TOUCH ANY OTHER FILE OF RECORD?"
git diff --name-only "$PRE".."$POST" | sed 's/^/     /'
echo "END"
