#!/usr/bin/env bash
# oracle-state-baseline.sh -- WHAT IS IN THE STANDING REFERENCE ORACLE'S LEDGER TODAY, DERIVED.
#
#   bash .softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh
#
# WHY THIS EXISTS
# ---------------
# T352 and T359 each fired probes at the SHARED reference oracle. A journal entry cannot be
# deleted, so both movements are permanent. Both recorded them well -- and both recorded them
# only inside their own capture directory, where the next task to re-derive a count has no
# reason to look. This instrument is the record moved to where a reader will find it, and
# turned from PROSE INTO A DERIVATION.
#
# THE DEFECT IT REFUSES TO REPRODUCE. Every previous attempt to record this state wrote a
# COUNT -- "60/64", "26", "gl 16 -> SIXTEEN". A count is true for an instant. T242 wrote
# SIXTEEN, T352 had to restate it to TWENTY, T359 to TWENTY-ONE, in eight days, and the
# corrections landed in three different files. So this instrument TYPES NO COUNT. It derives
# every figure from the live database on every run, and reads PROBES.tsv only for the two
# things that never rot:
#
#   * a FLOOR expressed as MAX IDs on append-only tables -- "row 64 was the last row before
#     T352" is true forever;
#   * one attribution row per deliberate write above that floor.
#
# WHAT IT GRADES. Not "did the oracle move" -- the oracle is SUPPOSED to move; refusing on
# movement is exactly the fail-closed trap the t305/t327 rigs walked into. It grades
# ATTRIBUTION: is every row above the floor explained by a registered probe? Unexplained
# movement means somebody wrote to the shared oracle without recording it, and THAT is the
# condition worth a red run.
#
# READ-ONLY. Every statement it issues is a SELECT. It fires no HTTP request that writes and
# posts no journal entry. Running it cannot move the thing it measures.
#
# ------------------------------------------------------------------------------------------
# WHY TWO TABLES ARE CLAIMED TO COVER 281, AND WHERE THAT ARGUMENT STOPS.
# [Written down by T371 because T367 found it load-bearing and NOWHERE STATED. Documentation
#  only -- this block changes no behaviour of this instrument.]
#
# THE ARGUMENT. This tenant has 281 base tables [VERIFIED: T371, live]. This instrument
# attributes on 2. The coverage claim is not "nothing else matters"; it is:
#
#     EVERY API-DRIVEN WRITE PASSES THE COMMAND BUS, AND THE COMMAND BUS LANDS AN
#     m_portfolio_command_source ROW -- SO THE COMMAND FLOOR CATCHES A WRITE TO ANY OF THE
#     OTHER 279 TABLES, EVEN THOUGH IT READS NONE OF THEM.
#
# That is sharper than it looks: the row is written by saveInitial BEFORE the handler runs, so
# even a command whose business transaction is ROLLED BACK leaves the audit row behind
# [VERIFIED: T371, SynchronousCommandProcessingService.java:140 then :151, @ 426a23544].
#
# WHERE IT STOPS -- three exception classes, all re-derived live by T371, all still open:
#   (a) a CONSUMED SEQUENCE. The floor is max(id); this script never reads a sequence.
#       acc_gl_closure_id_seq is last_value 1 / is_called t while acc_gl_closure is 0 rows /
#       max id null. This script prints that as pristine -- and reference-oracle.md records
#       that same consumed sequence as PERMANENT movement. Caught only indirectly, via the
#       command-source row a closure create/delete also lands.
#   (b) DIRECT SQL. A statement issued outside the command bus -- psql, a migration, a fixture
#       load -- satisfies none of the argument above.
#   (c) an UPDATE BELOW THE FLOOR. The floor detects appends, not mutations. 8 rows already
#       carry reversed = t, all at or below id 64, and this script never reads that column.
#   (d) THE SCHEDULER — added by T390, and OBSERVED, not theorised. Fineract's in-process
#       Spring Batch scheduler writes journal entries WITHOUT a command-source row, so the
#       coverage argument above ("every API-driven write lands a command-source row") is true
#       and does not reach it. Measured 2026-08-28: job 11 "Add Accrual Transactions"
#       (job_run_history 12721, 16:01:00 UTC = 00:01 Asia/Ulaanbaatar, cron 0 1 0 1/1 * ? *)
#       wrote journal transactions L32/L33/L34, eighteen legs, je ids 96-113, as app user 2
#       `system`, while m_portfolio_command_source stayed at 379. The command floor moved by
#       ZERO and the ledger moved by eighteen rows.
#       WHY THIS ONE WAS CAUGHT ANYWAY: job 11 happens to write to acc_gl_journal_entry, which
#       IS one of the two watched tables, so it starred as UNATTRIBUTED and the operator had to
#       go and find out who did it. A scheduled job touching any of the other 279 tables would
#       be invisible on both floors. Nineteen jobs read is_active = t in this tenant.
#       WHAT NOT TO DO ABOUT IT: do not teach this script to wave through writes by user 2.
#       That converts every future scheduler write into a silent green and is strictly worse
#       than a red somebody has to read. Register the transactions in PROBES.tsv naming the job
#       and its job_run_history id, as T390's block there does.
#       [VERIFIED: T390, live. Evidence under .softhouse/capture/t390-baseline-attribution/out/:
#        q1-je-above-95.txt, q2-command-source-tail.txt, q3-jobs.txt, q4-job-run-history.txt,
#        q5-loan-transactions-8.txt, q7-who-is-user-2.txt.]
#
# The float check is the one place DDL is covered, and it is narrower than it could be: it
# looks at the two ledger tables, while live there are 0 float columns across ALL 281
# [VERIFIED: T371]. Widening it is FU-T367-3 and is deliberately NOT done here.
# ------------------------------------------------------------------------------------------
#
# EXIT CODES -- deliberately parallel to conformance.sh, for the same reason.
#   0  every row above the floor is attributed
#   1  UNATTRIBUTED MOVEMENT -- somebody probed the shared oracle and did not record it
#   2  the oracle's database was UNREACHABLE. This is NOT a verdict about the ledger and must
#      never be read as one, exactly as conformance.sh exit 2 is not a FAIL.
#   3  wrong interpreter -- run it with `bash`, never `sh`.
#
# PostgreSQL is the only database in this program (CLAUDE.md). This script names psql
# explicitly and has no other engine path.

# --- exit 3: wrong interpreter, before anything else ------------------------------------
#
# TESTING `[ -z "$BASH_VERSION" ]` ALONE IS NOT ENOUGH AND THIS WAS MEASURED, NOT ASSUMED.
# That is what this guard said first, and it ADMITTED `sh` on the local fire's host: macOS
# `/bin/sh` IS bash, invoked in POSIX mode, so it sets BASH_VERSION=3.2.57(1)-release and the
# test passes. Driven: `sh -c 'shopt -qo posix; echo rc=$?; echo $BASH_VERSION'` -> `rc=0`,
# `3.2.57(1)-release`; the same under `bash` -> `rc=1`. Transcript: out/RED-3-wrong-interpreter.txt
# (the FAILING first version) and out/RED-3b-wrong-interpreter-fixed.txt (this version).
#
# So the refusal reads POSIX MODE, which is the property that actually differs, and it reads it
# with the non-bash case handled FIRST -- `shopt` does not exist in dash, and a guard whose own
# probe is a syntax error on the shell it exists to reject has refused nothing.
if [ -z "${BASH_VERSION:-}" ]; then
  echo "REFUSING: this is not bash. Run it with 'bash'. No observation was made." >&2
  exit 3
fi
if shopt -qo posix 2>/dev/null; then
  echo "REFUSING: bash is in POSIX mode -- you invoked this as 'sh'. Run it with 'bash'." >&2
  echo "  No observation was made. This is exit 3, NOT an oracle outage (exit 2)." >&2
  exit 3
fi
set -uo pipefail

DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REG="${ORACLE_BASELINE_REGISTRY:-$DIR/PROBES.tsv}"
DBC="${ORACLE_BASELINE_DB_CONTAINER:-fineract-db-1}"
DBUSER="${ORACLE_BASELINE_DB_USER:-root}"
DBNAME="${ORACLE_BASELINE_DB_NAME:-fineract_gerege}"
TENANT=gerege

hr() { printf '%s\n' "------------------------------------------------------------------------"; }

q() { # q <sql> -> tab-separated rows on stdout; non-zero if psql could not run
  docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -At -F$'\t' -c "$1" 2>&1
}

echo "ORACLE STATE BASELINE -- derived, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  container=$DBC  database=$DBNAME  tenant=$TENANT"
echo "  registry=$REG"
echo "  READ-ONLY: every statement below is a SELECT."
hr

[ -f "$REG" ] || { echo "REFUSING: no registry at $REG. Nothing can be attributed." >&2; exit 1; }

PROBE=$(q "SELECT 1")
if [ "$PROBE" != "1" ]; then
  echo "UNREACHABLE: could not read the tenant database. No observation was made."
  echo "  psql said: $PROBE"
  echo "VERDICT: UNREACHABLE (exit 2) -- this is NOT a statement about the ledger."
  exit 2
fi

# --- the floor, read from the registry ---------------------------------------------------
je_floor=$(awk -F'\t' '$1=="floor" && $2=="acc_gl_journal_entry" {print $3}' "$REG" | head -1)
cs_floor=$(awk -F'\t' '$1=="floor" && $2=="m_portfolio_command_source" {print $3}' "$REG" | head -1)
for v in "$je_floor" "$cs_floor"; do
  case "$v" in ''|*[!0-9]*) echo "REFUSING: registry carries no numeric floor." >&2; exit 1;; esac
done
echo "FLOOR (identities, not counts -- an append-only table's max id is true forever)"
echo "  acc_gl_journal_entry       last id before the registered probes : $je_floor"
echo "  m_portfolio_command_source last id before the registered probes : $cs_floor"
hr

# --- live counters, every one derived ----------------------------------------------------
echo "LIVE COUNTERS (derived now; do not transcribe these into prose -- re-run instead)"
q "SELECT 'acc_gl_journal_entry rows/maxid', count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_journal_entry
   UNION ALL SELECT 'acc_gl_journal_entry distinct transaction_id', count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry
   UNION ALL SELECT 'acc_gl_journal_entry distinct currency_code', string_agg(DISTINCT currency_code, ',') FROM acc_gl_journal_entry
   UNION ALL SELECT 'acc_gl_closure rows/maxid', count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_closure
   UNION ALL SELECT 'm_portfolio_command_source rows/maxid', count(*)||'/'||coalesce(max(id)::text,'null') FROM m_portfolio_command_source
   UNION ALL SELECT 'm_loan rows', count(*)::text FROM m_loan
   UNION ALL SELECT 'm_office rows', count(*)::text FROM m_office" | sed 's/^/  /'
hr

# --- the accrual pair, and the accounts the probes touched -------------------------------
# gl 18 and gl 22 are the pair capabilities-ledger.json's ledger.accrual.entry argument rests
# on; that they are STILL ZERO is the load-bearing fact, so it is derived here rather than
# asserted anywhere. The 'at floor' column is derived by SUBTRACTING the registered probe
# transactions -- legitimate only because the ledger is append-only and corrections are
# reversing entries, never deletions.
echo "PER-ACCOUNT LEGS -- 'at floor' is DERIVED by excluding the registered transactions"
TXNS=$(awk -F'\t' '$1=="txn" {printf "%s%s", sep, $2; sep=","}' "$REG")
TXNLIST=$(printf '%s' "$TXNS" | awk -F',' '{for(i=1;i<=NF;i++) printf "%s'\''%s'\''", (i>1?",":""), $i}')
[ -n "$TXNLIST" ] || TXNLIST="''"
q "WITH reg(tid) AS (SELECT unnest(ARRAY[$TXNLIST])),
        acct(a)  AS (SELECT unnest(ARRAY[16,17,18,21,22]))
   SELECT 'gl '||acct.a,
          (SELECT count(*) FROM acc_gl_journal_entry j
             WHERE j.account_id=acct.a AND j.transaction_id NOT IN (SELECT tid FROM reg))::text,
          (SELECT count(*) FROM acc_gl_journal_entry j WHERE j.account_id=acct.a)::text
   FROM acct ORDER BY acct.a" \
  | awk -F'\t' 'BEGIN{printf "  %-8s %10s %10s %s\n","account","at floor","live","moved?"}
                {printf "  %-8s %10s %10s %s\n", $1, $2, $3, ($2==$3 ? "no -- UNMOVED" : "YES +" ($3-$2))}'
hr

# --- movement above the floor, and its attribution ---------------------------------------
rc=0

echo "JOURNAL-ENTRY MOVEMENT above id $je_floor"
je_rows=$(q "SELECT j.transaction_id, count(*)::text, min(j.id)::text, max(j.id)::text,
                    string_agg(DISTINCT j.account_id::text, '+' ORDER BY j.account_id::text),
                    string_agg(DISTINCT j.currency_code, '+')
             FROM acc_gl_journal_entry j
             WHERE j.id > $je_floor GROUP BY j.transaction_id ORDER BY min(j.id)")
if [ -z "$je_rows" ]; then
  echo "  (none -- the ledger has not moved above the floor)"
else
  while IFS=$'\t' read -r tid legs lo hi accts ccy; do
    [ -n "$tid" ] || continue
    who=$(awk -F'\t' -v t="$tid" '$1=="txn" && $2==t {print $3; exit}' "$REG")
    if [ -n "$who" ]; then
      printf '  ok   %-14s legs=%-2s ids %s-%s  gl %-8s %-8s <- %s\n' "$tid" "$legs" "$lo" "$hi" "$accts" "$ccy" "$who"
    else
      printf '  ***  %-14s legs=%-2s ids %s-%s  gl %-8s %-8s UNATTRIBUTED\n' "$tid" "$legs" "$lo" "$hi" "$accts" "$ccy"
      rc=1
    fi
  done <<< "$je_rows"
fi
hr

echo "COMMAND-SOURCE MOVEMENT above id $cs_floor  (a REFUSED post still writes a row here)"
cs_rows=$(q "SELECT id::text, coalesce(idempotency_key,'(null)'), status::text,
                    coalesce(action_name,'')||'/'||coalesce(entity_name,'')
             FROM m_portfolio_command_source WHERE id > $cs_floor ORDER BY id")
if [ -z "$cs_rows" ]; then
  echo "  (none)"
else
  while IFS=$'\t' read -r id key st what; do
    [ -n "$id" ] || continue
    case "$st" in 1) stn="PROCESSED";; 5) stn="ERROR";; 3) stn="REJECTED";; *) stn="status=$st";; esac
    who=$(awk -F'\t' -v k="$key" '$1=="cmd" && $2==k {print $3; exit}' "$REG")
    if [ -n "$who" ]; then
      printf '  ok   %-4s %-30s %-10s %-22s <- %s\n' "$id" "$key" "$stn" "$what" "$who"
    else
      printf '  ***  %-4s %-30s %-10s %-22s UNATTRIBUTED\n' "$id" "$key" "$stn" "$what"
      rc=1
    fi
  done <<< "$cs_rows"
fi
hr

# --- the non-negotiable that a ledger census is the right place to re-assert --------------
echo "NON-NEGOTIABLE CHECKS (derived)"
FLOATCOLS=$(q "SELECT count(*)::text FROM information_schema.columns
               WHERE table_name IN ('acc_gl_journal_entry','acc_gl_closure')
                 AND data_type IN ('double precision','real','money')")
if [ "$FLOATCOLS" = "0" ]; then
  echo "  ok   0 floating-point columns on the ledger tables"
else
  echo "  ***  $FLOATCOLS FLOATING-POINT COLUMNS on the ledger tables -- money is integer minor units"
  rc=1
fi
ENGINE=$(q "SELECT split_part(version(),' on ',1)")
echo "  ok   engine: $ENGINE  (PostgreSQL is the only permitted database)"
hr

if [ "$rc" -eq 0 ]; then
  echo "VERDICT: ALL MOVEMENT ATTRIBUTED (exit 0)."
  echo "  Movement is normal -- the oracle is shared and probes are permanent. What this run"
  echo "  asserts is that every row above the floor names the task that created it."
else
  echo "VERDICT: UNATTRIBUTED MOVEMENT (exit 1)."
  echo "  Somebody wrote to the SHARED reference oracle and did not record it. The rows are"
  echo "  starred above. Do not 'fix' this by widening the floor -- find the task, then add"
  echo "  its rows to $REG."
fi
exit "$rc"
