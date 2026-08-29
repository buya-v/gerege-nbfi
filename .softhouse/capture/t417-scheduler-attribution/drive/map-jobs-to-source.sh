#!/usr/bin/env bash
# map-jobs-to-source.sh -- WHICH OF THE SCHEDULER'S JOBS EXIST, AND WHAT CODE BACKS EACH.
#
# Derives, from the PINNED Fineract checkout, the mapping
#     job table row  ->  JobName enum constant  ->  the main-source class(es) referencing it
# joined against the LIVE `job` table, so the active flag and the last run come from the
# database rather than from anybody's memory.
#
# IT TYPES NO CARDINAL. The job list comes from the database, the enum list from JobName.java,
# the class list from grep. If Fineract adds a job, this map grows on its own.
#
# It is a MAP, NOT A WHITELIST. Nothing in oracle-window-witness.sh consults it: the witness
# measures MOVEMENT over every table and needs no per-job prediction, which is precisely what
# stops it inheriting this map's blind spots. This exists so a reader can answer "which jobs
# could move state a vector depends on" -- and so the residual is NAMED, not assumed empty.
set -uo pipefail
FIN="${FINERACT_SRC:-/Users/buv/fineract}"
PIN="426a23544e8426a38ae43ae404670a0a7e85b9eb"
DBC="${ORACLE_BASELINE_DB_CONTAINER:-fineract-db-1}"
DBUSER="${ORACLE_BASELINE_DB_USER:-root}"
DBNAME="${ORACLE_BASELINE_DB_NAME:-fineract_gerege}"
ENUMF="$FIN/fineract-core/src/main/java/org/apache/fineract/infrastructure/jobs/service/JobName.java"

have=$(git -C "$FIN" rev-parse HEAD 2>/dev/null)
if [ "$have" != "$PIN" ]; then
  echo "REFUSING: $FIN is at ${have:-<not a git repo>}, not the pinned $PIN." >&2
  echo "  A line number read out of an unpinned checkout is not evidence." >&2
  exit 1
fi
[ -f "$ENUMF" ] || { echo "REFUSING: no JobName.java at $ENUMF" >&2; exit 1; }

JOBS=$(docker exec -i "$DBC" psql -v ON_ERROR_STOP=1 -U "$DBUSER" -d "$DBNAME" -At -F$'\t' \
  -c "SELECT id, is_active, coalesce(to_char(previous_run_start_time,'YYYY-MM-DD HH24:MI:SS'),'never'), name FROM job ORDER BY id" 2>&1)
case "$JOBS" in
  ''|*ERROR*|*"could not"*) echo "UNREACHABLE: could not read the job table. psql said: $JOBS" >&2; exit 2;;
esac

# enum display-string -> constant, parsed from the pinned source
ENUMMAP=$(python3 - "$ENUMF" <<'PY'
import re, sys
src = open(sys.argv[1]).read()
body = src.split('public enum JobName {',1)[1]
for k, d in re.findall(r'([A-Z0-9_]+)\s*\(\s*"([^"]*)"\s*\)', body):
    print(k + "\t" + d)
PY
)

matched=0; unmatched=0
echo "# job->source map   pinned fineract $PIN   generated $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "# job rows from the LIVE job table; enum constants from JobName.java; classes from grep"
echo
printf '%-4s %-7s %-20s %-70s %-62s %s\n' "job" "active" "last_run_utc" "display_name" "ENUM" "main-source classes"
while IFS=$'\t' read -r id active last name; do
  [ -n "$id" ] || continue
  konst=$(printf '%s\n' "$ENUMMAP" | awk -F'\t' -v n="$name" '$2==n {print $1; exit}')
  if [ -z "$konst" ]; then
    printf '%-4s %-7s %-20s %-70s %-62s %s\n' "$id" "$active" "$last" "$name" "(NO ENUM CONSTANT)" "-"
    unmatched=$((unmatched+1)); continue
  fi
  # The trailing [^A-Za-z0-9_] is load-bearing. Without it `JobName.ADD_PERIODIC_ACCRUAL_ENTRIES`
  # PREFIX-matches `JobName.ADD_PERIODIC_ACCRUAL_ENTRIES_FOR_SAVINGS_WITH_...` and job 16 is
  # reported as backed by a SAVINGS config. My first attempt did exactly that; the wrong map is
  # kept as out/JOB-SOURCE-MAP-FIRST-ATTEMPT-prefix-bug.txt rather than deleted.
  refs=$(grep -rlE "JobName\.$konst[^A-Za-z0-9_]" --include="*.java" "$FIN" 2>/dev/null \
          | grep '/src/main/java/' | grep -v '/JobName\.java$' \
          | sed "s|^$FIN/||" | sed 's|.*/||' | sort -u | tr '\n' ' ')
  [ -n "$refs" ] || refs="(NO MAIN-SOURCE REFERENCE)"
  printf '%-4s %-7s %-20s %-70s %-62s %s\n' "$id" "$active" "$last" "$name" "$konst" "$refs"
  matched=$((matched+1))
done <<< "$JOBS"

echo
echo "# DERIVED: job rows mapped to an enum constant = $matched ; unmapped = $unmatched"
echo "# DERIVED: enum constants in JobName.java = $(printf '%s\n' "$ENUMMAP" | grep -c .)"
