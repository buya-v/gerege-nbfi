#!/bin/sh
# guard-precondition.sh -- THE FAIL-CLOSED FENCE OVER THIS RIG'S ONE PROBE.
#
# P-92, the rule this rig exists downstream of, in its own words: "a probe whose safety comes
# from an EXTERNAL PRECONDITION rather than from its own content is a loaded weapon, and the
# danger is highest immediately after the capture SUCCEEDS -- because taking the observation is
# often what removes the precondition. A refusal capture must carry a fail-closed fence that
# re-checks the precondition at fire time, never a comment asserting the refusal, because the
# comment is written when the precondition holds and is not re-read when it stops holding."
#
# So this rig carries TWO fences and this script checks BOTH:
#
#   FENCE 1 -- CONTENT. req/ob-01-openingbalance-after-posted-entries.json is UNBALANCED by
#   exactly one MNT minor unit. checkDebitAndCreditAmounts, reached from
#   validateBusinessRulesForJournalEntries [JournalEntryWritePlatformServiceJpaRepositoryImpl
#   .java:626-651, called from :724], refuses an unbalanced command BEFORE
#   saveAllDebitOrCreditOpeningBalanceEntries is ever called at :742/:745. This fence is
#   clock-independent, state-independent and cannot expire. It is checked below by EXACT
#   INTEGER arithmetic over the raw decimal CHARACTERS in the body -- never by parsing a float.
#
#   FENCE 2 -- STATE. The refusal actually under capture, :717
#   validateJournalEntriesArePostedBefore(contraId) -> :810-816, fires only while
#   findNonContraTransactionIds(contraId) is non-empty. That is a fact about the tenant, and it
#   is exactly the kind of fact that lapses. It is re-measured here, against the live
#   PostgreSQL reference oracle, every time this script runs.
#
# EXIT 0 = both fences hold; the probe refuses and writes nothing.
# EXIT 1 = REFUSED. Any fence that does not hold, any measurement that could not be taken, an
#          unreachable database, a missing file, a body this script cannot classify.
#          FAIL CLOSED: "I could not tell" is a REFUSAL here, never a pass.
#
# PostgreSQL is the only database in this program. This script names psql and has no other
# engine path.
# WHAT-IF ARMS, so this fence can be DRIVEN RED WITHOUT MUTATING THE REFERENCE ORACLE.
# A guard nobody has seen fail is a guard nobody has tested (P-22: a control that cannot fail
# is worse than none). Three overrides exist, each substituting one measured input:
#
#   T294_BODY                     -- path to an alternative probe body (drives FENCE 1)
#   T294_WHATIF_CONTRA_ACCOUNT    -- substitutes the financial-activity-300 resolution (2a)
#   T294_WHATIF_NONCONTRA_COUNT   -- substitutes findNonContraTransactionIds' cardinality (2b)
#
# A WHAT-IF ARM CAN NEVER PRODUCE EXIT 0. If any override is set, this script announces it and
# exits 1 whatever the fences say, so a green under a substituted input cannot be mistaken for
# a green measurement -- which is the only way a debugging affordance stays safe.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"

BODY=${T294_BODY:-"$DIR/req/ob-01-openingbalance-after-posted-entries.json"}
WHATIF=0
if [ -n "${T294_BODY-}" ] || [ -n "${T294_WHATIF_CONTRA_ACCOUNT-}" ] || [ -n "${T294_WHATIF_NONCONTRA_COUNT-}" ]; then
  WHATIF=1
  printf '%s\n' "WHAT-IF ARM -- one or more measured inputs are SUBSTITUTED. The reference oracle was NOT"
  printf '%s\n' "              mutated. This arm exits 1 regardless of the fences below."
fi
rc=0
refuse() { printf 'REFUSE  %s\n' "$*"; rc=1; }
ok()     { printf 'ok      %s\n' "$*"; }

# --- FENCE 1: the body's own content -----------------------------------------------------
if [ ! -f "$BODY" ]; then
  refuse "the probe body $BODY does not exist. A fence over a file that is not there is not a fence."
else
  # json.load with parse_float=str keeps the ORACLE'S OWN CHARACTERS as a string, so no
  # decimal token in this rig is ever routed through a binary float -- not even to check it.
  # The comparison below is int64 minor units produced by string arithmetic.
  fence1=$(python3 - "$BODY" <<'PY'
import json, sys

def minor(text, digits):
    # Exact base-10 string arithmetic. No float, no Decimal, no rounding.
    t = str(text)
    neg = t.startswith('-')
    if neg:
        t = t[1:]
    if '.' in t:
        whole, frac = t.split('.', 1)
    else:
        whole, frac = t, ''
    if len(frac) > digits:
        if frac[digits:].strip('0'):
            raise SystemExit('UNCLASSIFIABLE non-zero residue beyond %d minor digits in %r' % (digits, text))
        frac = frac[:digits]
    frac = frac + '0' * (digits - len(frac))
    v = int((whole or '0') + frac) if (whole or frac) else 0
    return -v if neg else v

with open(sys.argv[1]) as fh:
    body = json.load(fh, parse_float=str, parse_int=str)

debits = sum(minor(l['amount'], 2) for l in body.get('debits', []))
credits = sum(minor(l['amount'], 2) for l in body.get('credits', []))
if not body.get('debits') or not body.get('credits'):
    print('UNBALANCED-UNCLASSIFIABLE 0 0')
elif debits == credits:
    print('BALANCED %d %d' % (debits, credits))
else:
    print('UNBALANCED %d %d' % (debits, credits))
PY
) || fence1="UNCLASSIFIABLE 0 0"
  set -- $fence1
  verdict=${1-UNCLASSIFIABLE}; d=${2-0}; c=${3-0}
  case "$verdict" in
    UNBALANCED)
      ok "FENCE 1 (content): debits $d minor units, credits $c minor units -- the body is UNBALANCED and"
      printf '        %s\n' "checkDebitAndCreditAmounts refuses it at :651 before any write, whatever the tenant state is."
      ;;
    BALANCED)
      refuse "*** FENCE 1 HAS LAPSED: the probe body is BALANCED ($d == $c minor units). ***"
      printf '        %s\n' "Its safety now rests ENTIRELY on FENCE 2. That is the P-92 shape. Do not fire."
      ;;
    *)
      refuse "FENCE 1 could not be evaluated over $BODY ($fence1). Fail closed."
      ;;
  esac
fi

# --- FENCE 2: the tenant state the captured refusal depends on ----------------------------
probe=0
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc 'SELECT 1' >/dev/null 2>&1 || probe=$?
if [ "$probe" -ne 0 ]; then
  refuse "the reference oracle's PostgreSQL ('$DBC' / '$DBNAME') is not reachable (probe rc=$probe),"
  printf '        %s\n' "so FENCE 2 could not be measured at all. Fail closed: an unmeasured fence is a lapsed fence."
else
  contra=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
    "SELECT coalesce((SELECT gl_account_id FROM acc_gl_financial_activity_account WHERE financial_activity_type = 300), 0)")
  [ -n "${T294_WHATIF_CONTRA_ACCOUNT-}" ] && contra=$T294_WHATIF_CONTRA_ACCOUNT
  if [ "$contra" = "0" ]; then
    refuse "financial-activity type 300 is NOT MAPPED on this tenant."
    printf '        %s\n' ":708 findByFinancialActivityTypeWithNotFoundDetection(300) would throw FIRST and the"
    printf '        %s\n' "observation would be a DIFFERENT refusal than the one this rig claims to capture."
  else
    ok "FENCE 2a: financial-activity type 300 maps to GL account $contra (:708-:709 resolves)."
  fi
  n=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
    "SELECT count(*) FROM (SELECT DISTINCT j.transaction_id FROM acc_gl_journal_entry j WHERE j.transaction_id NOT IN (SELECT DISTINCT je.transaction_id FROM acc_gl_journal_entry je WHERE je.account_id = (SELECT gl_account_id FROM acc_gl_financial_activity_account WHERE financial_activity_type = 300))) t")
  [ -n "${T294_WHATIF_NONCONTRA_COUNT-}" ] && n=$T294_WHATIF_NONCONTRA_COUNT
  case "$n" in
    ''|*[!0-9]*)
      refuse "findNonContraTransactionIds could not be measured (got '$n'). Fail closed."
      ;;
    0)
      refuse "*** FENCE 2b HAS LAPSED: findNonContraTransactionIds(contraId) is EMPTY. ***"
      printf '        %s\n' ":810-816 no longer throws. The captured refusal is FALSE of this tenant and the"
      printf '        %s\n' "vector that cites it must be RE-CAPTURED, not exempted."
      ;;
    *)
      ok "FENCE 2b: findNonContraTransactionIds(contraId) returns $n transaction id(s) -- :810-816 throws."
      ;;
  esac
fi

if [ "$WHATIF" -eq 1 ]; then
  printf '%s\n' "WHAT-IF ARM: exiting 1 by construction. A substituted input never yields a green fence."
  exit 1
fi
if [ "$rc" -eq 0 ]; then
  printf '%s\n' "clean: both fences hold. The probe refuses on its own content AND on the tenant state the"
  printf '%s\n' "       captured observation depends on."
else
  printf '%s\n' "REFUSED: at least one fence over this rig's probe does not hold. DO NOT FIRE."
fi
exit "$rc"
