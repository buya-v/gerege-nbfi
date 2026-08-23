#!/bin/sh
# guard-probe-expiry.sh -- ADDED BY T289 (independent review of T287). FAIL-CLOSED.
#
# WHY THIS EXISTS
# ---------------
# Every one of the four refusal probes in this rig is an OTHERWISE PERFECTLY VALID,
# BALANCED, POSTABLE MANUAL JOURNAL ENTRY. Their only defect is a PRECONDITION that lives
# in the ORACLE, not in the request body:
#
#   req/a1-01-future-far.json          2026-12-31  refused ONLY WHILE business date < 2026-12-31
#   req/a1-02-future-boundary-plus1.json 2026-08-24 refused ONLY WHILE business date < 2026-08-24
#   req/a2-01-preclosure-on-date.json  2026-01-31  refused ONLY WHILE a GLClosure at office 1
#   req/a2-02-preclosure-before.json   2026-01-15    has closingDate >= that date
#
# When the precondition lapses the request does NOT stop being interesting quietly -- it
# BECOMES A SUCCESSFUL WRITE. `validateBusinessRulesForJournalEntries` is the only thing
# standing between these bodies and `saveAllDebitOrCreditEntries`
# [JournalEntryWritePlatformServiceJpaRepositoryImpl.java:157, :626-640, pinned 426a23544].
# GL 4 and GL 2 are both manual_journal_entries_allowed=t, disabled=f, account_usage=1
# (DETAIL) on tenant `gerege`, and debits equal credits, so nothing else refuses them.
#
# AND JOURNAL ENTRIES CANNOT BE DELETED. Unlike the GLClosure T287 created and removed,
# a posted journal entry is reversible only by posting MORE entries. A mis-fire here is
# PERMANENT contamination of the reference oracle every vector in this program is graded
# against.
#
# T287 disclosed that a1-02 "stops being a refusal on 2026-08-24" and called it "not a
# re-runnable assertion". That understates it in the one direction that matters: the
# recipe does not become useless, it becomes DESTRUCTIVE. And T287 did not note that the
# a2-* probes are ALREADY in that state -- it deleted the closure that made them refuse,
# so as of that delete both a2 probes post cleanly.
#
# WHAT THIS DOES
# --------------
# Refuses (exit 1) unless EVERY probe's oracle-side precondition currently holds.
# Fail-closed by construction: an unrecognised req/*.json is a REFUSAL, not a pass, so a
# probe added later cannot slip through unfenced.
#
# WHAT THIS IS NOT
# ----------------
# NOTHING RUNS THIS AUTOMATICALLY. It is not called by conformance.sh (contended, and T289
# was barred from touching it) and not called by cap.sh (owned by T287's branch; editing it
# here would be an add/add merge conflict). It fires only when invoked. That is a P-89
# exposure and it is STATED, not hidden -- see .softhouse/handoff/.../T289.md, F-T289-3.
#
# USAGE
#   sh guard-probe-expiry.sh          # check against the live oracle
#   T289_BUSINESS_DATE=2026-08-24 sh guard-probe-expiry.sh   # what-if, no oracle mutation
#
# No floating point anywhere: ISO-8601 dates compared as strings (lexicographic order is
# chronological order for yyyy-MM-dd) and integer row counts. No money is computed here.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"

fail=0
note() { printf '%s\n' "$*"; }

# ---- 1. business date -------------------------------------------------------------
# Derived exactly as BusinessDateReadPlatformServiceImpl does: when `enable-business-date`
# is off or m_business_date is empty, BUSINESS_DATE is seeded with
# DateUtils.getLocalDateOfTenant() = today in the TENANT zone. Never a hard-coded offset
# (CLAUDE.md: two zones, no DST) -- the zone name is passed to date(1).
TZNAME=Asia/Ulaanbaatar

if [ "${T289_BUSINESS_DATE-}" != "" ]; then
  BD=$T289_BUSINESS_DATE
  note "business date: $BD  (OVERRIDE via T289_BUSINESS_DATE -- what-if only, oracle not consulted for this value)"
else
  if ! docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc 'SELECT 1' >/dev/null 2>&1; then
    note "REFUSED: oracle database '$DBNAME' in container '$DBC' is unreachable."
    note "  Cannot establish the preconditions, so NOTHING may be fired. Fail-closed."
    exit 1
  fi
  ENABLED=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
    "SELECT enabled FROM c_configuration WHERE name='enable-business-date'" 2>/dev/null || echo "")
  PINNED=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
    "SELECT date FROM m_business_date WHERE type='BUSINESS_DATE'" 2>/dev/null || echo "")
  if [ "$ENABLED" = "t" ] && [ -n "$PINNED" ]; then
    BD=$PINNED
    note "business date: $BD  (PINNED -- enable-business-date=t, m_business_date row present)"
  else
    BD=$(TZ=$TZNAME date +%F)
    note "business date: $BD  (DERIVED -- enable-business-date='$ENABLED', m_business_date rows: $([ -n "$PINNED" ] && echo 1 || echo 0); today in $TZNAME)"
  fi
fi

# ---- 2. closure state -------------------------------------------------------------
if [ "${T289_LATEST_CLOSURE-}" != "" ]; then
  LC=$T289_LATEST_CLOSURE
  note "latest GLClosure at office 1: $LC  (OVERRIDE via T289_LATEST_CLOSURE)"
else
  LC=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
    "SELECT max(closing_date) FROM acc_gl_closure WHERE office_id=1" 2>/dev/null || echo "")
  if [ -z "$LC" ]; then
    note "latest GLClosure at office 1: NONE (acc_gl_closure has no row for office 1)"
  else
    note "latest GLClosure at office 1: $LC"
  fi
fi
note ""

# ---- 3. fence every request body --------------------------------------------------
for f in "$DIR"/req/*.json; do
  base=$(basename "$f")
  td=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("transactionDate",""))' "$f")

  case "$base" in
    a1-*-future-*)
      if [ -z "$td" ]; then
        note "REFUSE  $base  -- classified FUTURE_DATE probe but carries no transactionDate."
        fail=1
      elif [ "$td" \> "$BD" ]; then
        note "ok      $base  FUTURE_DATE probe, transactionDate $td > business date $BD -- still refuses."
      else
        note "REFUSE  $base  *** transactionDate $td is NOT after business date $BD ***"
        note "        DateUtils.isDateInTheFuture() = isAfterBusinessDate() is STRICT, so this"
        note "        request NO LONGER TRIPS THE GUARD. Firing it POSTS 2 JOURNAL ENTRIES into"
        note "        the reference oracle, PERMANENTLY. Journal entries cannot be deleted."
        fail=1
      fi
      ;;
    a2-*-preclosure-*)
      if [ -z "$td" ]; then
        note "REFUSE  $base  -- classified ACCOUNTING_CLOSED probe but carries no transactionDate."
        fail=1
      elif [ -z "$LC" ]; then
        note "REFUSE  $base  *** NO GLClosure EXISTS at office 1 ***"
        note "        transactionDate $td is in the past, so the FUTURE_DATE guard does not fire"
        note "        either. Firing this POSTS 2 JOURNAL ENTRIES into the reference oracle,"
        note "        PERMANENTLY. Create the closure first (req/a2-00-create-closure.json),"
        note "        and remember the next closure gets id=2, not 1."
        fail=1
      elif [ "$td" \> "$LC" ]; then
        note "REFUSE  $base  *** transactionDate $td is AFTER latest closing date $LC ***"
        note "        The boundary is INCLUSIVE (refuses transactionDate <= closingDate), so a"
        note "        date strictly after it is ACCEPTED and WRITES."
        fail=1
      else
        note "ok      $base  ACCOUNTING_CLOSED probe, transactionDate $td <= closingDate $LC -- still refuses (INCLUSIVE boundary)."
      fi
      ;;
    a2-00-create-closure.json)
      note "NOTE    $base  MUTATION recipe, not a probe. Firing it CREATES a GLClosure in the"
      note "        reference oracle. T287 created and deleted one; the sequence is now"
      note "        is_called=t, so the next one is id=2. Delete it in the same fire."
      ;;
    *)
      note "REFUSE  $base  -- UNCLASSIFIED. This guard fails closed: a request body it does not"
      note "        recognise is not certified safe to fire. Classify it here first."
      fail=1
      ;;
  esac
done

note ""
if [ "$fail" -ne 0 ]; then
  note "REFUSED: at least one probe would WRITE to the reference oracle if fired now."
  exit 1
fi
note "clean: every probe's oracle-side precondition holds; each still refuses and writes nothing."
exit 0
