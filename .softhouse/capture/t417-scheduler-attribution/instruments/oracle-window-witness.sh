#!/usr/bin/env bash
# oracle-window-witness.sh -- THE PIN ON THE SCHEDULER.
#
#   bash .../instruments/oracle-window-witness.sh open    <label>
#   bash .../instruments/oracle-window-witness.sh close    <label>
#   bash .../instruments/oracle-window-witness.sh verify   <label>     # shelf-life of a witness
#   bash .../instruments/oracle-window-witness.sh attribute <from-utc> <to-utc>
#   bash .../instruments/oracle-window-witness.sh --self-test
#
# WHY THIS EXISTS
# ---------------
# The reference oracle EDITS ITSELF. Measured, not suspected: at 2026-08-28 16:01:00 UTC
# (00:01 Asia/Ulaanbaatar) Fineract's in-process scheduler inserted eighteen journal-entry
# legs (job 11) AND rewrote ninety-one pre-existing ones (job 9, raw `UPDATE ... WHERE id=?`
# through jdbcTemplate, no command bus). Neither passed the command bus; neither left an
# m_portfolio_command_source row. [T390 live; T409 live; both re-derived by T417 -- see
# ../out/s2-job-run-history.txt and ../out/s3-ledger-now.txt.]
#
# The consequence is not bookkeeping. A CAPTURED VECTOR HAS A SHELF LIFE. The oracle state a
# vector was graded against can move with no task acting, so a shadow-parity divergence may be
# THE CLOCK RATHER THAN THE PORT -- and parity sign-off is a `user` gate that would corrupt.
#
# WHAT THIS PINS, AND WHY IT IS NOT THE OBVIOUS DESIGN
# ----------------------------------------------------
# THE TRAP: attributing scheduler writes by app user id. `created_by = 2 system` looks like a
# scheduler signature and IS NOT ONE.
#   * It is not SUFFICIENT. `system` is an ordinary row of m_appuser (id 2, alongside 1 mifos
#     and 3 interopUser) [../out/s3-ledger-now.txt s3e]. Anything holding those credentials --
#     a human at psql, a fixture loader, a batch API call -- writes rows indistinguishable from
#     the scheduler's.
#   * It is not NECESSARY. Fineract's scheduler runs each job under the tenant's configured
#     identity; a job configured to run as anyone else defeats a user-2 rule the day it is
#     reconfigured, and the rule then reports SILENCE, which reads as "clean".
#   * It is ALREADY FATALLY OVERBROAD. `last_modified_by` is **2 on every single row** of
#     acc_gl_journal_entry [s3d]. A user-2 exemption does not excuse future scheduler writes --
#     it retroactively excuses THE ENTIRE LEDGER, including every probe T352, T359 and T388
#     ever fired. The alarm would be converted into a blanket amnesty.
#   * And it inverts the burden. It answers "who is allowed to have written this" instead of
#     "did anything move while I was looking", which is the question a capture actually needs.
#
# SO THIS INSTRUMENT NEVER READS created_by OR last_modified_by. Not once. It reads only:
#   (1) CONTENT -- a per-table content digest over the graded surface. Order-independent,
#       column-complete, mutation-sensitive. An UPDATE below the floor changes it. A DELETE
#       changes it. A row whose table carries no audit column at all changes it.
#   (2) SEQUENCES -- pg_sequences.last_value, which moves when a sequence is CONSUMED even if
#       the row was never persisted (T371 exception class (a): acc_gl_closure_id_seq).
#   (3) THE SCHEDULER'S OWN BOOKKEEPING -- job_run_history and the job table. This is the
#       WITNESS, never the evidence: it says a job ran, it does not say what it wrote.
#
# COVERAGE -- WHY THIS IS NOT BLIND TO 279 TABLES
# -----------------------------------------------
# The predecessor instrument (oracle-state-baseline.sh) watches 2 tables and argues coverage of
# the other 279 through the command bus. That argument is TRUE and DOES NOT REACH THE SCHEDULER,
# which is how job 11 escaped it -- caught only by the luck that job 11 writes to one of the two
# watched tables. This instrument does not repeat that. Its population is DERIVED from
# information_schema at run time (281 base tables, 254 sequences today; it types no cardinal),
# minus an EXPLICITLY NAMED, GREPPABLE exclusion list of the scheduler's OWN bookkeeping tables
# -- which move every minute by construction and are the witness, not the graded state. Every
# other table is in the digest whether or not anyone knows what writes it, and whether or not it
# carries an audit column. 189 of 281 tables carry NO audit column [../out/s4-*.txt s4a: 92 do],
# so for those this digest is the ONLY way the question can be asked at all.
#
# THE OVER-APPROXIMATION IS DELIBERATE AND IS THE POINT. It measures MOVEMENT, not PERMISSION.
# It needs no per-job table map, so it cannot be defeated by a job doing something its
# documentation did not predict, and it does not silently narrow when Fineract adds a job.
#
# WHY NOT "REFUSE ANY CAPTURE WITH A JOB RUN IN ITS WINDOW" -- MEASURED, NOT ARGUED
# ---------------------------------------------------------------------------------
# Job 36 "Send Asynchronous Events" is `is_active` with cron `0 0/1 * * * ?` and has run 10623
# times; 1440 of those in the last 24h -- EVERY MINUTE, WITHOUT A GAP [../out/s2-*.txt s2c/s2f].
# A blanket refusal on "a job ran inside the window" refuses EVERY capture that takes longer
# than sixty seconds. That is not a pin, it is an outage. So the refusal is keyed on MOVEMENT
# OF GRADED CONTENT, and the run list is reported beside it as the attribution candidate set.
# A window in which jobs ran and nothing graded moved is reported QUIESCENT-WITH-RUNS: proven
# harmless FOR THAT WINDOW, by measurement, rather than by trusting a classification.
#
# IS THE RUN LIST COMPLETE? -- SETTLED FROM SOURCE, WITH ITS ONE HOLE NAMED
# -------------------------------------------------------------------------
# The run list is only worth reading if EVERY execution lands a job_run_history row.
# [VERIFIED from the pinned source @ 426a23544:]
#   * SchedulerJobListener implements Quartz JobListener and is installed with
#     `schedulerFactoryBean.setGlobalJobListeners(jobListeners)`
#     [JobRegisterServiceImpl.java:319,322], for BOTH the cron scheduler [:293] and the
#     temporary scheduler used by a manually triggered execution [:116]. GLOBAL means every
#     job on that scheduler, not a subscribed subset.
#   * `jobWasExecuted` [SchedulerJobListener.java:58] builds a ScheduledJobRunHistory and
#     saves it [:105-108], and it does so on FAILURE too -- `jobException != null` only sets
#     status=FAILED [:79-80]. Confirmed live: job 30 'Update Trial Balance Details' failed
#     with a ClassCastException and STILL has its row, jrh 12718 [../out/s2-*.txt s2e].
#
# THE HOLE, NAMED RATHER THAN GLOSSED: the row is written when the job FINISHES
# (`setEndTime(new Date())` [:106]); `jobToBeExecuted` and `jobExecutionVetoed` are EMPTY
# [:52,:55]. So a job that is IN FLIGHT has NO job_run_history row yet and is invisible in the
# run list. That is why this instrument also reads `job.currently_running` -- set true when the
# job claims itself [SchedularWritePlatformServiceJpaRepositoryImpl.java:159] and false in
# `jobWasExecuted` [:100] -- and REFUSES a window in which any job was in flight at either end.
# A window whose boundary cuts a running job cannot be certified quiescent by a table that has
# not been written yet.
#
# NAMING THE JOB -- AND REFUSING TO GUESS
# ---------------------------------------
# `attribute` lists every job run overlapping a window. If exactly ONE overlaps it is named,
# with its job id and its job_run_history id. If MORE THAN ONE overlaps it REFUSES TO NAME ONE
# and prints them all. This is not caution for its own sake: for the 2026-08-28 mutation window
# [.033938, .039824] THREE runs overlap and TWO contain it, and the true author (job 9) was
# settled from Fineract source, not from the clock [T409 F-T409-1;
# JournalEntryRunningBalanceUpdateServiceImpl.java:72-76,157,163-164,261-266 @ 426a23544].
# A rule that silently picked one would have attributed 91 row-rewrites to a guess.
#
# READ-ONLY. Every statement issued is a SELECT. Running it cannot move what it measures.
#
# EXIT CODES -- parallel to conformance.sh, for the same reason.
#   0  QUIESCENT (or QUIESCENT-WITH-RUNS): nothing on the graded surface moved.
#   1  CONTAMINATED / REFUSED: graded content moved, or the witness is unusable.
#   2  the oracle's database was UNREACHABLE. NOT a verdict about the oracle, exactly as
#      conformance.sh exit 2 is not a FAIL.
#   3  wrong interpreter -- run it with `bash`, never `sh`.
#
# PostgreSQL is the only database in this program (CLAUDE.md). This script names psql
# explicitly and has no other engine path. "The oracle" here is the FINERACT REFERENCE
# IMPLEMENTATION; Oracle Database is a prohibited product and appears nowhere in this stack.

if [ -z "${BASH_VERSION:-}" ]; then
  echo "REFUSING: this is not bash. Run it with 'bash'. No observation was made." >&2; exit 3
fi
if shopt -qo posix 2>/dev/null; then
  echo "REFUSING: bash is in POSIX mode -- you invoked this as 'sh'. Run it with 'bash'." >&2
  echo "  No observation was made. This is exit 3, NOT an oracle outage (exit 2)." >&2; exit 3
fi
set -uo pipefail

DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
WIT="${ORACLE_WITNESS_DIR:-$DIR/witness}"
DBC="${ORACLE_BASELINE_DB_CONTAINER:-fineract-db-1}"
DBUSER="${ORACLE_BASELINE_DB_USER:-root}"
DBNAME="${ORACLE_BASELINE_DB_NAME:-fineract_gerege}"
PIN_COMMIT="426a23544e8426a38ae43ae404670a0a7e85b9eb"

# ---------------------------------------------------------------------------------------
# THE EXCLUSION LIST. Named here, in one place, greppable, with the reason each is excluded.
# These are the SCHEDULER'S OWN BOOKKEEPING. They move every minute because job 36 runs every
# minute; including them would make every window CONTAMINATED and the instrument useless.
# NOTHING ELSE IS EXCLUDED. If you add a name here you are narrowing the graded surface and
# you must say so in a handoff -- an ungraded region nobody has declared ungraded is how a
# program silently stops grading.
#
# Note what is NOT here: m_external_event (job 36's payload table) IS GRADED. Only the batch
# runner's own ledger of itself is excluded, not the business rows any job touches.
# ---------------------------------------------------------------------------------------
EXCLUDED_TABLES=(
  batch_job_execution              # Spring Batch runner bookkeeping
  batch_job_execution_context      # Spring Batch runner bookkeeping
  batch_job_execution_params       # Spring Batch runner bookkeeping
  batch_job_instance               # Spring Batch runner bookkeeping
  batch_step_execution             # Spring Batch runner bookkeeping
  batch_step_execution_context     # Spring Batch runner bookkeeping
  job_run_history                  # THE WITNESS ITSELF -- read separately, below
  job                              # previous_run_start_time / next_run_time tick on every fire
)
# Sequences behind the excluded tables move for the same reason.
EXCLUDED_SEQ_PREFIXES=( batch_job batch_step job_run_history job_id )

hr() { printf '%s\n' "-----------------------------------------------------------------------------"; }
say() { printf '%s\n' "$*"; }

q() { # q <sql> -> tab-separated rows; rc non-zero if psql could not run
  docker exec -i "$DBC" psql -v ON_ERROR_STOP=1 -U "$DBUSER" -d "$DBNAME" -At -F$'\t' -c "$1" 2>&1
}

reachable() {
  local p; p=$(q "SELECT 1")
  if [ "$p" != "1" ]; then
    say "UNREACHABLE: could not read the tenant database. No observation was made."
    say "  psql said: $p"
    say "VERDICT: UNREACHABLE (exit 2) -- this is NOT a statement about the oracle."
    return 1
  fi
  return 0
}

sql_excluded_list() { # -> 'a','b','c'
  local out="" t
  for t in "${EXCLUDED_TABLES[@]}"; do out="${out:+$out,}'$t'"; done
  printf '%s' "$out"
}
sql_excluded_seq_pred() { # -> a NOT LIKE chain
  local out="TRUE" p
  for p in "${EXCLUDED_SEQ_PREFIXES[@]}"; do out="$out AND sequencename NOT LIKE '${p}%'"; done
  printf '%s' "$out"
}

# ---- the three readings -----------------------------------------------------------------

read_tables() { # tbl <name> <rows> <md5>
  # The digest is order-independent (string_agg over a sorted per-row md5) and
  # column-complete (r::text renders every column). An UPDATE, a DELETE and an INSERT all
  # change it. Empty tables digest to the literal EMPTY so "no rows" is distinguishable
  # from "could not read".
  q "SELECT 'tbl', s.table_name, s.rows::text, s.digest FROM (
       SELECT t.table_name,
              (xpath('/row/c/text()', query_to_xml(
                 format('SELECT count(*) AS c FROM %I.%I', t.table_schema, t.table_name),
                 false, true, '')))[1]::text::bigint AS rows,
              coalesce((xpath('/row/c/text()', query_to_xml(
                 format('SELECT md5(string_agg(h, '''' ORDER BY h)) AS c FROM (SELECT md5(r::text) AS h FROM %I.%I r) z',
                        t.table_schema, t.table_name),
                 false, true, '')))[1]::text, 'EMPTY') AS digest
       FROM information_schema.tables t
       WHERE t.table_schema='public' AND t.table_type='BASE TABLE'
         AND t.table_name NOT IN ($(sql_excluded_list))
     ) s ORDER BY s.table_name"
}

read_sequences() { # seq <name> <last_value>
  q "SELECT 'seq', sequencename, coalesce(last_value::text,'unset')
     FROM pg_sequences
     WHERE schemaname='public' AND $(sql_excluded_seq_pred)
     ORDER BY sequencename"
}

read_scheduler() { # jrh/job/meta rows -- the witness
  # job_run_history.start_time/end_time are `timestamp WITHOUT time zone` holding UTC;
  # now() is timestamptz. The conversion is written out explicitly rather than left to the
  # session TimeZone, and the session TimeZone is PRINTED so a reader can check it.
  q "SELECT 'meta', 'db_now_utc', to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD HH24:MI:SS.US')
     UNION ALL SELECT 'meta','session_timezone', current_setting('TimeZone')
     UNION ALL SELECT 'meta','engine', split_part(version(),' on ',1)
     UNION ALL SELECT 'jrh','max_id', coalesce(max(id)::text,'none') FROM job_run_history
     UNION ALL SELECT 'jrh','rows', count(*)::text FROM job_run_history
     UNION ALL SELECT 'jrh','max_start_time', coalesce(to_char(max(start_time),'YYYY-MM-DD HH24:MI:SS.US'),'none') FROM job_run_history
     UNION ALL SELECT 'jrh','max_end_time', coalesce(to_char(max(end_time),'YYYY-MM-DD HH24:MI:SS.US'),'none') FROM job_run_history
     UNION ALL SELECT 'jobs','total', count(*)::text FROM job
     UNION ALL SELECT 'jobs','active', count(*) FILTER (WHERE is_active)::text FROM job
     UNION ALL SELECT 'jobs','currently_running', count(*) FILTER (WHERE currently_running)::text FROM job"
}

read_job_table() { # job <id> <active> <cron> <prev> <next>
  q "SELECT 'job', id::text, is_active::text, coalesce(cron_expression,''),
            coalesce(to_char(previous_run_start_time,'YYYY-MM-DD HH24:MI:SS.US'),'never'),
            coalesce(to_char(next_run_time,'YYYY-MM-DD HH24:MI:SS.US'),'none'),
            name
     FROM job ORDER BY id"
}

emit_witness() { # emit_witness <phase> <label>
  local phase="$1" label="$2"
  printf '# oracle-window-witness v1\n'
  printf 'meta\tlabel\t%s\n' "$label"
  printf 'meta\tphase\t%s\n' "$phase"
  printf 'meta\thost_utc\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'meta\tfineract_commit\t%s\n' "$PIN_COMMIT"
  printf 'meta\tdatabase\t%s\n' "$DBNAME"
  printf 'meta\tcontainer\t%s\n' "$DBC"
  read_scheduler
  read_job_table
  read_sequences
  read_tables
}

rollup() { # rollup <witness-file> -> one md5 over the whole graded surface
  grep -E '^(tbl|seq)	' "$1" | LC_ALL=C sort | md5_of_stdin
}
md5_of_stdin() { if command -v md5 >/dev/null 2>&1; then md5 -q; else md5sum | awk '{print $1}'; fi; }

counts_of() { # counts_of <witness-file>
  printf 'graded_tables=%s graded_sequences=%s\n' \
    "$(grep -c '^tbl	' "$1")" "$(grep -c '^seq	' "$1")"
}

# ---- job-run attribution over a window ---------------------------------------------------

runs_overlapping() { # runs_overlapping <from-utc-naive> <to-utc-naive>
  q "SELECT h.id::text, h.job_id::text, j.name, to_char(h.start_time,'YYYY-MM-DD HH24:MI:SS.US'),
            to_char(h.end_time,'YYYY-MM-DD HH24:MI:SS.US'), h.status,
            CASE WHEN h.start_time <= timestamp '$1' AND h.end_time >= timestamp '$2'
                 THEN 'CONTAINS' ELSE 'overlaps' END
     FROM job_run_history h LEFT JOIN job j ON j.id = h.job_id
     WHERE h.start_time <= timestamp '$2' AND coalesce(h.end_time, h.start_time) >= timestamp '$1'
     ORDER BY h.start_time, h.id"
}

# RUNS_TEXT / RUNS_N are set by print_runs. The window is read ONCE per call site: calling
# runs_overlapping twice would ask the database two different questions, because a job can
# start between the two calls -- the exact hazard this instrument exists to detect.
RUNS_TEXT=""; RUNS_N=0
RUNS_PRINT_CAP="${ORACLE_WITNESS_RUNS_CAP:-40}"
print_runs() { # print_runs <from> <to>; sets RUNS_N
  local rows n=0 shown=0
  rows=$(runs_overlapping "$1" "$2")
  if [ -n "$rows" ]; then
    printf '  %-7s %-6s %-9s %-26s %-26s %s\n' "jrh" "job" "kind" "start (UTC)" "end (UTC)" "name"
    while IFS=$'\t' read -r id jid nm st en stat kind; do
      [ -n "$id" ] || continue
      n=$((n+1))
      # The COUNT is exact and drives the verdict; only the PRINTING is capped. A window of
      # hours contains hundreds of per-minute runs and an uncapped list buries the verdict.
      if [ "$shown" -lt "$RUNS_PRINT_CAP" ]; then
        shown=$((shown+1))
        printf '  %-7s %-6s %-9s %-26s %-26s %s [%s]\n' "$id" "$jid" "$kind" "$st" "$en" "$nm" "$stat"
      fi
    done <<< "$rows"
    [ "$n" -gt "$shown" ] && printf '  ... and %s more run(s) not printed (cap %s; the COUNT below is exact)\n' \
        "$((n-shown))" "$RUNS_PRINT_CAP"
  fi
  printf '  RUNS OVERLAPPING WINDOW = %s\n' "$n"
  RUNS_N="$n"
  return 0
}

# ---- the commands ------------------------------------------------------------------------

cmd_open() {
  local label="$1"
  mkdir -p "$WIT"
  reachable || return 2
  emit_witness open "$label" > "$WIT/$label.open.tsv"
  local rc_rows; rc_rows=$(grep -c '^tbl	' "$WIT/$label.open.tsv")
  if [ "$rc_rows" -lt 1 ]; then
    say "REFUSING: the graded-table population came back EMPTY. A witness over nothing"
    say "  would pass every window. This is a refusal, not a quiescent oracle."
    return 1
  fi
  say "WITNESS OPEN  label=$label"
  say "  $(counts_of "$WIT/$label.open.tsv")  excluded_tables=${#EXCLUDED_TABLES[@]}"
  say "  graded rollup = $(rollup "$WIT/$label.open.tsv")"
  say "  db now (UTC)  = $(awk -F'\t' '$2=="db_now_utc"{print $3}' "$WIT/$label.open.tsv")"
  say "  jrh max id    = $(awk -F'\t' '$2=="max_id"{print $3}' "$WIT/$label.open.tsv")"
  say "  jobs in flight= $(awk -F'\t' '$2=="currently_running"{print $3}' "$WIT/$label.open.tsv")  (job.currently_running)"
  say "  witness       -> $WIT/$label.open.tsv"
  return 0
}

cmd_close() {
  local label="$1"
  local open="$WIT/$label.open.tsv"
  local close="$WIT/$label.close.tsv"
  if [ ! -f "$open" ]; then
    say "REFUSING: no open witness at $open. A capture with no opening witness cannot be"
    say "  shown to have been taken against a still oracle. Absence is not quiescence."
    return 1
  fi
  reachable || return 2
  emit_witness close "$label" > "$close"

  local from to
  from=$(awk -F'\t' '$2=="db_now_utc"{print $3}' "$open")
  to=$(awk -F'\t' '$2=="db_now_utc"{print $3}' "$close")

  say "WITNESS CLOSE label=$label"
  say "  window (UTC, database clock): $from  ->  $to"
  say "  $(counts_of "$close")  excluded_tables=${#EXCLUDED_TABLES[@]}"
  hr
  say "SCHEDULER RUNS INSIDE THE WINDOW (the witness -- says a job RAN, not what it WROTE)"
  print_runs "$from" "$to"
  local nruns="$RUNS_N"
  hr

  # --- the graded surface --------------------------------------------------------------
  local movedfile; movedfile=$(mktemp "${TMPDIR:-/tmp}/witness-moved.XXXXXX")
  LC_ALL=C join -t$'\t' -j2 -o 0,1.3,1.4,2.3,2.4 \
      <(grep -E '^(tbl|seq)	' "$open"  | LC_ALL=C sort -t$'\t' -k2,2) \
      <(grep -E '^(tbl|seq)	' "$close" | LC_ALL=C sort -t$'\t' -k2,2) \
    | awk -F'\t' '$2!=$4 || $3!=$5' > "$movedfile"

  # appearances / disappearances -- a DROP or CREATE is movement too
  local onlyopen onlyclose
  onlyopen=$(LC_ALL=C comm -23 <(grep -E '^(tbl|seq)	' "$open"  | cut -f2 | LC_ALL=C sort) \
                               <(grep -E '^(tbl|seq)	' "$close" | cut -f2 | LC_ALL=C sort))
  onlyclose=$(LC_ALL=C comm -13 <(grep -E '^(tbl|seq)	' "$open"  | cut -f2 | LC_ALL=C sort) \
                                <(grep -E '^(tbl|seq)	' "$close" | cut -f2 | LC_ALL=C sort))

  local nmoved; nmoved=$(wc -l < "$movedfile" | tr -d ' ')
  say "GRADED SURFACE -- content digest over EVERY base table and sequence except the ${#EXCLUDED_TABLES[@]} named"
  if [ "$nmoved" = "0" ] && [ -z "$onlyopen" ] && [ -z "$onlyclose" ]; then
    say "  ok   nothing moved. rollup open == close == $(rollup "$open")"
  else
    while IFS=$'\t' read -r nm r1 d1 r2 d2; do
      [ -n "$nm" ] || continue
      say "  ***  $nm  rows $r1 -> $r2   digest ${d1:0:12} -> ${d2:0:12}   MOVED"
    done < "$movedfile"
    [ -n "$onlyopen" ]  && while read -r n; do say "  ***  $n  DISAPPEARED between open and close"; done <<< "$onlyopen"
    [ -n "$onlyclose" ] && while read -r n; do say "  ***  $n  APPEARED between open and close"; done <<< "$onlyclose"
  fi
  hr
  rm -f "$movedfile"

  # IN-FLIGHT REFUSAL. job_run_history is written only when a job FINISHES, so a job running
  # across either boundary is absent from the run list above. `job.currently_running` is the
  # only in-flight signal there is, and a window that cuts a running job cannot be certified.
  local inflight_open inflight_close
  inflight_open=$(awk -F'\t' '$2=="currently_running"{print $3}' "$open")
  inflight_close=$(awk -F'\t' '$2=="currently_running"{print $3}' "$close")
  if [ "${inflight_open:-0}" != "0" ] || [ "${inflight_close:-0}" != "0" ]; then
    say "IN FLIGHT: job.currently_running = $inflight_open at open, $inflight_close at close."
    say "VERDICT: REFUSED (exit 1). A job was RUNNING across a boundary of this window. Its"
    say "  job_run_history row is not written until it finishes, so the run list above is"
    say "  INCOMPLETE by construction and this window cannot be certified quiescent."
    say "  Re-take the witness when no job is in flight."
    return 1
  fi

  if [ "$nmoved" = "0" ] && [ -z "$onlyopen" ] && [ -z "$onlyclose" ]; then
    if [ "${nruns:-0}" = "0" ]; then
      say "VERDICT: QUIESCENT (exit 0). No job ran inside the window and no graded content moved."
    else
      say "VERDICT: QUIESCENT-WITH-RUNS (exit 0). $nruns job run(s) overlapped the window and"
      say "  NOTHING ON THE GRADED SURFACE MOVED. They are proven harmless FOR THIS WINDOW by"
      say "  measurement -- not waved through by a classification, and not by who they ran as."
    fi
    say "  A capture taken inside this window is reproducible against this oracle state."
    return 0
  fi

  say "VERDICT: CAPTURE CONTAMINATED (exit 1). The oracle MOVED while the capture was open."
  say "  Anything captured inside this window may be a photograph of a moving target. Do not"
  say "  promote it to a vector: re-capture inside a window this instrument calls QUIESCENT."
  if [ "${nruns:-0}" = "1" ]; then
    say "  ATTRIBUTION: exactly ONE job run overlaps this window; it is named above and is the"
    say "  sole candidate author. Confirm from Fineract source before recording it as the author."
  elif [ "${nruns:-0}" = "0" ]; then
    say "  ATTRIBUTION: NO job run overlaps this window. The scheduler did not do this. Something"
    say "  else wrote to the SHARED reference oracle -- find it, and register it."
  else
    say "  ATTRIBUTION: REFUSED. $nruns job runs overlap this window, so the clock CANNOT name"
    say "  one author. This is not caution for its own sake: for the 2026-08-28 mutation window"
    say "  three runs overlapped and TWO contained it, and the author (job 9) was settled from"
    say "  Fineract source, not from the clock. Settle it from source; do not pick one."
  fi
  return 1
}

cmd_verify() { # has the oracle moved since a witness was taken? -- the vector SHELF-LIFE check
  local label="$1"
  local ref="$WIT/$label.close.tsv"
  [ -f "$ref" ] || ref="$WIT/$label.open.tsv"
  if [ ! -f "$ref" ]; then
    say "REFUSING: no witness for label '$label' under $WIT."; return 1
  fi
  reachable || return 2
  local nowf; nowf=$(mktemp "${TMPDIR:-/tmp}/witness-now.XXXXXX")
  emit_witness verify "$label" > "$nowf"
  local a b; a=$(rollup "$ref"); b=$(rollup "$nowf")
  say "SHELF-LIFE CHECK  label=$label"
  say "  witness taken   : $(awk -F'\t' '$2=="host_utc"{print $3}' "$ref")  rollup $a"
  say "  oracle right now: $(date -u +%Y-%m-%dT%H:%M:%SZ)  rollup $b"
  if [ "$a" = "$b" ]; then
    say "VERDICT: UNMOVED (exit 0). Every graded table and sequence is byte-identical to the"
    say "  witness. A vector captured against this witness is still graded against this oracle."
    rm -f "$nowf"; return 0
  fi
  say "  MOVED since the witness:"
  LC_ALL=C join -t$'\t' -j2 -o 0,1.3,1.4,2.3,2.4 \
      <(grep -E '^(tbl|seq)	' "$ref"  | LC_ALL=C sort -t$'\t' -k2,2) \
      <(grep -E '^(tbl|seq)	' "$nowf" | LC_ALL=C sort -t$'\t' -k2,2) \
    | awk -F'\t' '$2!=$4 || $3!=$5 {printf "  ***  %s  rows %s -> %s  digest %.12s -> %.12s\n",$1,$2,$4,$3,$5}'
  say "VERDICT: ORACLE HAS MOVED SINCE THE WITNESS (exit 1). Any vector whose provenance cites"
  say "  this witness is now graded against a state the oracle no longer has. A shadow-parity"
  say "  divergence against it may be THE CLOCK RATHER THAN THE PORT. Re-capture, or record"
  say "  explicitly which of the moved tables the vector does not read."
  say "  Candidate authors, over the interval since the witness:"
  print_runs "$(awk -F'\t' '$2=="db_now_utc"{print $3}' "$ref")" \
             "$(awk -F'\t' '$2=="db_now_utc"{print $3}' "$nowf")"
  rm -f "$nowf"; return 1
}

cmd_attribute() {
  reachable || return 2
  say "JOB RUNS OVERLAPPING [$1 .. $2]  (UTC, job_run_history is naive UTC)"
  print_runs "$1" "$2"
  local n="$RUNS_N"
  if [ "$n" = "1" ]; then
    say "SOLE CANDIDATE. Named above. Confirm from Fineract source @ $PIN_COMMIT before recording."
    return 0
  elif [ "$n" = "0" ]; then
    say "NO CANDIDATE. The scheduler did not run in this window."
    return 0
  fi
  say "REFUSING TO NAME ONE AUTHOR: $n runs overlap. The clock cannot resolve this."
  return 1
}

usage() {
  say "usage: oracle-window-witness.sh open|close|verify <label>"
  say "       oracle-window-witness.sh attribute <from-utc> <to-utc>   # 'YYYY-MM-DD HH:MM:SS'"
  say "       oracle-window-witness.sh --self-test"
}

case "${1:-}" in
  open)      [ $# -eq 2 ] || { usage; exit 1; }; cmd_open "$2"; exit $?;;
  close)     [ $# -eq 2 ] || { usage; exit 1; }; cmd_close "$2"; exit $?;;
  verify)    [ $# -eq 2 ] || { usage; exit 1; }; cmd_verify "$2"; exit $?;;
  attribute) [ $# -eq 3 ] || { usage; exit 1; }; cmd_attribute "$2" "$3"; exit $?;;
  --self-test)
    # Cheap structural self-test that contacts the oracle once. It proves the population is
    # non-empty and the exclusion list is a strict subset -- a witness over an empty or
    # accidentally-total exclusion list passes every window and grades nothing.
    reachable || exit 2
    tot=$(q "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")
    graded=$(read_tables | wc -l | tr -d ' ')
    say "SELF-TEST  base_tables=$tot  graded=$graded  excluded_named=${#EXCLUDED_TABLES[@]}"
    if [ "$graded" -lt 1 ]; then say "REFUSING: graded population is EMPTY."; exit 1; fi
    if [ "$graded" -ge "$tot" ]; then
      say "REFUSING: graded ($graded) >= base tables ($tot) -- the exclusion list did not apply,"
      say "  so the witness would report the scheduler's own bookkeeping as contamination."; exit 1
    fi
    if [ $((tot - graded)) -ne ${#EXCLUDED_TABLES[@]} ]; then
      say "REFUSING: $((tot-graded)) tables excluded but ${#EXCLUDED_TABLES[@]} names are listed --"
      say "  the exclusion list does not match reality. Every excluded table must be NAMED."; exit 1
    fi
    say "SELF-TEST OK: every excluded table is named, and the graded surface is everything else."
    exit 0;;
  *) usage; exit 1;;
esac
