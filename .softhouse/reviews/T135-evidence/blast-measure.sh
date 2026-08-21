#!/bin/sh
# T135 — BLAST RADIUS, settled from committed evidence rather than by inference.
#
# The three vacuous assertions each read a stream that ALSO feeds a co-located POSITIVE assertion
# in the very same transcript:
#   P5  banned   <- docker inspect Config.Env   ... same dump feeds "driverClassName org.postgresql.Driver"
#                                                   and "JDBC URL is jdbc:postgresql://…"
#   P6  jarhits  <- docker exec unzip -l <jar>  ... same listing feeds "PostgreSQL JDBC driver present in the jar"
#   P11 scp      <- psql on fineract_tenants    ... same join/tenant feeds "tenant schema_server_port = 5432"
# A positive PASS is impossible over an empty stream.  So for any committed transcript carrying the
# witness, the corresponding prohibition scan demonstrably had input, and its 0 means "clean".
set -u
ROOT=${1:-/Users/buv/gerege-nbfi/.softhouse/capture/pathb}
cd "$ROOT" || exit 9
printf '%-46s %-5s %-5s %-5s %s\n' "committed preconditions transcript" "P5w" "P6w" "P11w" "verdict"
n=0; ok=0
for f in $(LC_ALL=C find . -name 'preconditions*.txt' | sort); do
  n=$((n+1))
  p5=0; p6=0; p11=0
  LC_ALL=C grep -qa 'PASS  driverClassName org.postgresql.Driver' "$f" && \
    LC_ALL=C grep -qa 'PASS  JDBC URL is jdbc:postgresql' "$f" && p5=1
  LC_ALL=C grep -qa 'PASS  PostgreSQL JDBC driver present in the jar' "$f" && p6=1
  LC_ALL=C grep -qa 'PASS  tenant schema_server_port = 5432' "$f" && p11=1
  if [ "$p5$p6$p11" = "111" ]; then v="all three scans had input"; ok=$((ok+1)); else v="*** WITNESS MISSING"; fi
  printf '%-46s %-5s %-5s %-5s %s\n' "$(echo "$f" | sed 's|^\./||' | cut -c1-46)" "$p5" "$p6" "$p11" "$v"
done
echo
echo "transcripts examined: $n ; with all three liveness witnesses present: $ok"
