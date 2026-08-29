#!/usr/bin/env bash
# drive-witness.sh -- RED AND GREEN ARMS FOR oracle-window-witness.sh
#
# NOTHING HERE WRITES TO THE SHARED REFERENCE ORACLE. Every statement the instrument issues is
# a SELECT; every red is manufactured by DOCTORING A COPY of a witness file in a scratch
# directory under /tmp, exactly as T390 manufactured its red by deleting a row from a copy of
# the registry. Probing the oracle to make a test go red would leave a permanent casualty in a
# shared, append-only ledger for the sake of a test.
#
# A control that cannot fail and one that refuses everything are the same defect (P-98), so
# every red here is paired with a green that runs the SAME mechanism and passes.
#
# The doctored windows are not invented: they REPLAY the shape of the real 2026-08-28 16:01
# sweep, whose endpoints were measured live [../out/s2-job-run-history.txt,
# ../out/s3-ledger-now.txt] and independently by T409.
set -uo pipefail
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
I="$DIR/instruments/oracle-window-witness.sh"
SCRATCH="${TMPDIR:-/tmp}/t417-drive-$$"
mkdir -p "$SCRATCH/witness"
trap 'rm -rf "$SCRATCH"' EXIT

pass=0; fail=0
arm() { # arm <name> <expected-rc> <cmd...>
  local name="$1" want="$2"; shift 2
  echo "=============================================================================="
  echo "ARM: $name    (expected rc $want)"
  echo "------------------------------------------------------------------------------"
  "$@"
  local got=$?
  echo "------------------------------------------------------------------------------"
  if [ "$got" = "$want" ]; then echo "ARM RESULT: PASS  (rc=$got)"; pass=$((pass+1))
  else echo "ARM RESULT: FAIL  (rc=$got, wanted $want)"; fail=$((fail+1)); fi
  echo
}

# ---------------------------------------------------------------------------------------
# A real witness of the CURRENT oracle, taken once. Every doctored arm below is built from a
# COPY of it, so a red and its green control differ in exactly one respect.
# ---------------------------------------------------------------------------------------
echo "### taking one real witness of the live oracle (READ-ONLY) ###"
ORACLE_WITNESS_DIR="$SCRATCH/witness" bash "$I" open BASE || { echo "cannot take a base witness -- is the oracle up?"; exit 2; }
BASE="$SCRATCH/witness/BASE.open.tsv"
echo

# GREEN 1 -- the same mechanism, undoctored: nothing moved between open and close.
arm "GREEN-1 quiescent window, undoctored witness" 0 \
  env ORACLE_WITNESS_DIR="$SCRATCH/witness" bash "$I" close BASE

# ---------------------------------------------------------------------------------------
# RED 1 -- REPLAY OF THE REAL 16:01 SWEEP.
# The open witness is doctored to claim (a) it was taken at 2026-08-28 16:00:59, one second
# before the sweep, and (b) acc_gl_journal_entry then held 91 rows with a different digest --
# which is what the table actually held before job 11 appended eighteen legs
# [../out/s3-ledger-now.txt: 109 rows now, 91 of them created before 16:00Z].
# Expect: CONTAMINATED, with MANY overlapping runs and attribution REFUSED.
# ---------------------------------------------------------------------------------------
mkdir -p "$SCRATCH/red1"
sed -e 's/^meta\tdb_now_utc\t.*$/meta\tdb_now_utc\t2026-08-28 16:00:59.000000/' \
    -e 's/^tbl\tacc_gl_journal_entry\t[0-9]*\t.*/tbl\tacc_gl_journal_entry\t91\tPRESWEEPDIGEST00000000000000000/' \
    "$BASE" > "$SCRATCH/red1/SWEEP.open.tsv"
arm "RED-1 replay of the real 00:01 sweep: ledger moved, many runs overlap -> REFUSE to name" 1 \
  env ORACLE_WITNESS_DIR="$SCRATCH/red1" bash "$I" close SWEEP

# ---------------------------------------------------------------------------------------
# RED 2 -- A SCHEDULED WRITE ATTRIBUTED CORRECTLY, WITH ONE CANDIDATE.
# Window opens at 16:01:00.100207, the instant job 11's first leg was written. Exactly one job
# run overlaps from there to now? No -- so this arm uses `attribute` on the measured endpoints
# of job 11's eighteen inserts, which is the narrow question the clock CAN answer.
# ---------------------------------------------------------------------------------------
arm "RED-2/GREEN sole-candidate: job 11's insert window names ONE author" 0 \
  bash "$I" attribute '2026-08-28 16:01:00.100207' '2026-08-28 16:01:00.117772'

arm "RED-3 job 9's mutation window: 3 runs overlap, 2 contain -> REFUSES to name one" 1 \
  bash "$I" attribute '2026-08-28 16:01:00.033938' '2026-08-28 16:01:00.039824'

# ---------------------------------------------------------------------------------------
# RED 4 -- CONTENT MOVED AND NO JOB RAN. This is the "somebody wrote to the shared oracle"
# case, and it must NOT be excused. The open witness is doctored only in one table's digest;
# its db_now_utc is left at the real recent instant, so no job run overlaps.
# ---------------------------------------------------------------------------------------
mkdir -p "$SCRATCH/red4"
sed -e 's/^tbl\tm_office\t[0-9]*\t.*/tbl\tm_office\t1\tDOCTOREDDIGEST000000000000000000/' \
    "$BASE" > "$SCRATCH/red4/NOJOB.open.tsv"
arm "RED-4 graded content moved with NO job run -> not the scheduler, and not excused" 1 \
  env ORACLE_WITNESS_DIR="$SCRATCH/red4" bash "$I" close NOJOB

# GREEN 2 -- the SAME mechanism with the doctoring removed. If this failed too, RED-4 would
# prove nothing about the doctoring.
mkdir -p "$SCRATCH/green2"
cp "$BASE" "$SCRATCH/green2/NOJOB.open.tsv"
arm "GREEN-2 control: identical mechanism, undoctored copy" 0 \
  env ORACLE_WITNESS_DIR="$SCRATCH/green2" bash "$I" close NOJOB

# ---------------------------------------------------------------------------------------
# RED 4b -- A JOB WAS IN FLIGHT ACROSS A BOUNDARY. job_run_history is written only when a job
# FINISHES [SchedulerJobListener.java:58,105-108 @ 426a23544], so the run list is INCOMPLETE
# for an in-flight job and the window cannot be certified. Doctored on a COPY: only the
# `meta currently_running` line differs from GREEN-2's copy, which passes.
# ---------------------------------------------------------------------------------------
mkdir -p "$SCRATCH/red4b"
# NOTE: the field is emitted with a leading `jobs`, not `meta`. My first attempt doctored
# `^meta\tcurrently_running` -- which matches NOTHING, so the arm produced a green and read as
# "the refusal does not work". The drive caught it. Kept as
# out/DRIVE-WITNESS-FIRST-ATTEMPT-red4b-failed.txt rather than tidied away: a doctoring that
# silently fails to doctor is exactly how a red arm becomes decorative.
sed -e 's/^jobs\tcurrently_running\t.*$/jobs\tcurrently_running\t1/' \
    "$BASE" > "$SCRATCH/red4b/INFLIGHT.open.tsv"
arm "RED-4b a job was IN FLIGHT across the window boundary -> REFUSED, not certified" 1 \
  env ORACLE_WITNESS_DIR="$SCRATCH/red4b" bash "$I" close INFLIGHT

# ---------------------------------------------------------------------------------------
# RED 5 -- NO OPEN WITNESS. "Did not run" must never read as "clean".
# ---------------------------------------------------------------------------------------
mkdir -p "$SCRATCH/red5"
arm "RED-5 close with no open witness -> refuses; absence is not quiescence" 1 \
  env ORACLE_WITNESS_DIR="$SCRATCH/red5" bash "$I" close NEVER-OPENED

# ---------------------------------------------------------------------------------------
# RED 6 -- SHELF LIFE. `verify` against a witness whose recorded state no longer matches the
# live oracle. This is the vector-rot alarm: a vector citing this witness is graded against a
# state the oracle no longer has.
# ---------------------------------------------------------------------------------------
mkdir -p "$SCRATCH/red6"
sed -e 's/^tbl\tacc_gl_journal_entry\t[0-9]*\t.*/tbl\tacc_gl_journal_entry\t91\tSTALEWITNESSDIGEST00000000000000/' \
    "$BASE" > "$SCRATCH/red6/STALE.open.tsv"
arm "RED-6 shelf life: the oracle has MOVED since the witness -> vector no longer graded" 1 \
  env ORACLE_WITNESS_DIR="$SCRATCH/red6" bash "$I" verify STALE

# GREEN 3 -- verify against an honest witness.
arm "GREEN-3 shelf life control: undoctored witness -> UNMOVED" 0 \
  env ORACLE_WITNESS_DIR="$SCRATCH/witness" bash "$I" verify BASE

# ---------------------------------------------------------------------------------------
# RED 7 -- A WITNESS OVER AN EMPTY GRADED SURFACE MUST REFUSE, NOT PASS. An instrument whose
# population silently became empty would call every window quiescent. Driven by excluding
# every table in a COPY of the instrument, never by editing the shipped one.
# ---------------------------------------------------------------------------------------
ALLTBL=$(docker exec -i "${ORACLE_BASELINE_DB_CONTAINER:-fineract-db-1}" psql -At \
          -U "${ORACLE_BASELINE_DB_USER:-root}" -d "${ORACLE_BASELINE_DB_NAME:-fineract_gerege}" \
          -c "SELECT string_agg(table_name, ' ') FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'" 2>/dev/null)
awk -v all="$ALLTBL" '
  /^EXCLUDED_TABLES=\(/ {print "EXCLUDED_TABLES=("; n=split(all,a," "); for(i=1;i<=n;i++) print "  " a[i]; inblock=1; next}
  inblock && /^\)/ {print ")"; inblock=0; next}
  inblock {next}
  {print}
' "$I" > "$SCRATCH/instrument-empty.sh"
arm "RED-7 empty graded surface -> self-test REFUSES rather than passing everything" 1 \
  bash "$SCRATCH/instrument-empty.sh" --self-test

# GREEN 4 -- the shipped instrument's self-test on the same host.
arm "GREEN-4 shipped self-test: every excluded table is named, graded surface is the rest" 0 \
  bash "$I" --self-test

# ---------------------------------------------------------------------------------------
# RED 8 -- WRONG INTERPRETER. exit 3, and it must not be mistaken for an oracle outage.
# ---------------------------------------------------------------------------------------
arm "RED-8 invoked as sh -> exit 3, NOT exit 2; no observation was made" 3 \
  sh "$I" --self-test

echo "=============================================================================="
echo "DRIVE SUMMARY: $pass passed, $fail failed"
echo "NOTHING WAS WRITTEN TO THE REFERENCE ORACLE BY THIS DRIVE."
[ "$fail" -eq 0 ]
