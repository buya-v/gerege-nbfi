#!/bin/sh
# T305 -- THE ACCEPTING-SIDE CAPTURE GATE.  FAIL-CLOSED.  READ-ONLY.
#
# WHAT THIS IS FOR. T296 arm A measured that a port refusing EVERY defineOpeningBalance --
# including on an empty ledger, where the reference oracle ACCEPTS
# (JournalEntryWritePlatformServiceJpaRepositoryImpl.java:810-816, the fall-through when
# findNonContraTransactionIds is empty) -- is GREEN on the whole ledger corpus. The only
# thing that kills arm A is an ACCEPTING-side observation. T305 was sent to decide whether
# that observation can be taken safely and concluded IT CANNOT, TODAY, ON THIS RIG.
#
# P-89: "PROSE DOES NOT FIRE ON THE NEXT FIRE -- a limit written into a handoff, a review,
# or a `## Backlog` heading is invisible to the scheduler." A refusal recorded only in
# FINDING.md is exactly that. So the refusal is THIS SCRIPT, and any future task briefed to
# take the accepting capture must run it FIRST and must not fire while it exits non-zero.
#
# P-92: "a probe whose safety comes from an EXTERNAL PRECONDITION rather than from its own
# content is a loaded weapon, and the danger is highest immediately after the capture
# SUCCEEDS -- because taking the observation is often what removes the precondition."
# THE ACCEPTING CAPTURE IS THE PURE FORM OF THAT SHAPE, and worse than the refusals P-92 was
# written about: an accepted opening balance POSTS JOURNAL ENTRIES, a posted journal entry
# has NO DELETE PATH IN FINERACT AT ALL (verified: no @DELETE anywhere in
# fineract-provider/.../accounting/, and JournalEntriesApiResource exposes only @GET and
# @POST), and the entries it posts are precisely what makes findNonContraTransactionIds
# non-empty -- so THE CAPTURE DESTROYS ITS OWN PRECONDITION, ON THAT TENANT, FOREVER.
# There is no content fence for an accepting probe. A body that cannot post is not an
# accept. That is why this gate is about the TENANT and not about the body.
#
# WHAT IT CHECKS, per registered tenant, and why each one:
#   C1 rounding-mode = 4 (HALF_UP)     CLAUDE.md ratified; a capture at any other mode is a
#                                      discrimination probe, not a parity vector -- CLAUDE.md
#                                      says so in those words about C-00/D-01..D-04.
#   C2 timezone in {Asia/Ulaanbaatar,  CLAUDE.md permits exactly two zones and no others.
#      Asia/Hovd}
#   C3 findNonContraTransactionIds     the accepting side of :812. NON-EMPTY => the oracle
#      is EMPTY                        refuses, and only the refusal T294 already has is
#                                      available.
#   C4 type-300 mapping resolves to    :708 must not throw and :764-769 must not throw, or
#      an EQUITY account               the answer is a DIFFERENT refusal, not an accept.
#   C5 an explicit DISPOSABILITY       NOT MEASURABLE. C1-C4 can all pass and the capture
#      attestation                     still be wrong to take, because the question "may this
#                                      tenant be permanently mutated" is a fact about the rig,
#                                      not about the database. Supplied by file, never by
#                                      inference, and its ABSENCE REFUSES.
#
# EXIT CODES.  0 = a tenant qualifies on all five and the capture MAY be planned (it still
# needs its own task and its own review).  1 = REFUSED, with the measured reason.  2 = the
# guard could not measure (unreachable database, unparseable output, missing file) --
# INDISTINGUISHABLE FROM REFUSED for the purpose of firing, and deliberately so.
set -u
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"

say() { printf '%s\n' "$*"; }
QUALIFIED=0
MEASURED_TENANTS=0

say "T305 accepting-side capture gate -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say ""

# ---- reachability first, so a refusal is never confused with an outage -----------------
if ! docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME_STORE" -Atc 'SELECT 1' >/dev/null 2>&1; then
  say "CANNOT MEASURE: container '$DBC' / database '$DBNAME_STORE' is not reachable."
  say "  This is EXIT 2, not a refusal and not a pass. Nothing was observed."
  exit 2
fi

TENANTS=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME_STORE" -At -F'|' \
  -c "SELECT t.identifier, t.timezone_id, c.schema_name FROM tenants t JOIN tenant_server_connections c ON c.id = t.oltp_id ORDER BY t.id" 2>/dev/null)
if [ -z "$TENANTS" ]; then
  say "CANNOT MEASURE: the tenant registry returned nothing. Fail-closed."
  exit 2
fi

for row in $TENANTS; do
  ID=$(printf '%s' "$row" | cut -d'|' -f1)
  TZ=$(printf '%s' "$row" | cut -d'|' -f2)
  DB=$(printf '%s' "$row" | cut -d'|' -f3)
  [ -n "$ID" ] && [ -n "$TZ" ] && [ -n "$DB" ] || { say "CANNOT MEASURE: unparseable registry row '$row'. Fail-closed."; exit 2; }

  say "tenant '$ID'  timezone=$TZ  database=$DB"
  MEASURED_TENANTS=$((MEASURED_TENANTS + 1))
  FAIL=""

  # C1 -- rounding mode. java.math.RoundingMode ordinals: HALF_UP=4, HALF_EVEN=6.
  RM=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DB" -Atc \
        "SELECT coalesce(value::text,'NULL') FROM c_configuration WHERE name = 'rounding-mode'" 2>/dev/null)
  case "$RM" in
    4) say "  ok    C1 rounding-mode = 4 (HALF_UP), the ratified production mode." ;;
    6) say "  REFUSE C1 rounding-mode = 6 (HALF_EVEN). CLAUDE.md ratifies HALF_UP=4 for MNT; a"
       say "         capture here is a DISCRIMINATION PROBE, not a parity vector."; FAIL="y" ;;
    "") say "  CANNOT MEASURE C1: no rounding-mode row read from $DB. Fail-closed."; exit 2 ;;
    *) say "  REFUSE C1 rounding-mode = $RM, not 4 (HALF_UP)."; FAIL="y" ;;
  esac

  # C2 -- time zone. CLAUDE.md: "Two time zones, no DST -- Asia/Ulaanbaatar (+08) and Asia/Hovd (+07)."
  case "$TZ" in
    Asia/Ulaanbaatar|Asia/Hovd) say "  ok    C2 timezone $TZ is one of the two CLAUDE.md permits." ;;
    *) say "  REFUSE C2 timezone $TZ is NOT one of Asia/Ulaanbaatar or Asia/Hovd."; FAIL="y" ;;
  esac

  # C3 -- the accepting side of :812.
  NC=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DB" -Atc \
        "SELECT count(*) FROM (SELECT DISTINCT j.transaction_id FROM acc_gl_journal_entry j WHERE j.transaction_id NOT IN (SELECT DISTINCT je.transaction_id FROM acc_gl_journal_entry je WHERE je.account_id = (SELECT gl_account_id FROM acc_gl_financial_activity_account WHERE financial_activity_type = 300))) t" 2>/dev/null)
  case "$NC" in
    "") say "  CANNOT MEASURE C3 on $DB. Fail-closed."; exit 2 ;;
    0)  say "  ok    C3 findNonContraTransactionIds is EMPTY -- :812 falls through and the oracle ACCEPTS." ;;
    *)  say "  REFUSE C3 findNonContraTransactionIds has $NC id(s) -- :812 THROWS. Only the refusal"
        say "         T294 already captured (LDG-REFUSE-03) is available on this tenant."; FAIL="y" ;;
  esac

  # C4 -- :708 resolves and :764-769 does not throw.
  FA=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DB" -Atc \
        "SELECT coalesce((SELECT a.id || ':' || a.classification_enum FROM acc_gl_financial_activity_account f JOIN acc_gl_account a ON a.id = f.gl_account_id WHERE f.financial_activity_type = 300), 'UNMAPPED')" 2>/dev/null)
  if [ -z "$FA" ]; then
    say "  CANNOT MEASURE C4 on $DB. Fail-closed."; exit 2
  elif [ "$FA" = "UNMAPPED" ]; then
    say "  REFUSE C4 financial-activity type 300 is UNMAPPED. :708"
    say "         findByFinancialActivityTypeWithNotFoundDetection(300) throws FIRST, so the answer"
    say "         would be a DIFFERENT refusal, not an accept."; FAIL="y"
  else
    CLS=$(printf '%s' "$FA" | cut -d':' -f2)
    if [ "$CLS" = "3" ]; then
      say "  ok    C4 type 300 -> GL $(printf '%s' "$FA" | cut -d':' -f1), classification_enum 3 (EQUITY)."
    else
      say "  REFUSE C4 type 300 maps to a NON-EQUITY account (classification_enum $CLS). :764-769"
      say "         throws error.msg.configuration.opening.balance.contra.account.value.is.invalid.account.type."; FAIL="y"
    fi
  fi

  # C5 -- disposability. A FACT ABOUT THE RIG, never inferred from the database.
  ATT="$DIR/attest/$ID.disposable"
  if [ -f "$ATT" ]; then
    say "  ok    C5 a disposability attestation exists at attest/$ID.disposable -- READ IT before firing."
  else
    say "  REFUSE C5 NO disposability attestation at attest/$ID.disposable."
    say "         An accepted opening balance is a POSTED JOURNAL ENTRY and there is NO delete path"
    say "         for one. On any tenant this program intends to KEEP, this capture is IRREVERSIBLE."
    FAIL="y"
  fi

  if [ -z "$FAIL" ]; then
    say "  --> tenant '$ID' QUALIFIES on all five."
    QUALIFIED=$((QUALIFIED + 1))
  else
    say "  --> tenant '$ID' REFUSED."
  fi
  say ""
done

say "measured $MEASURED_TENANTS tenant(s); $QUALIFIED qualify."
if [ "$QUALIFIED" -eq 0 ]; then
  say ""
  say "REFUSED: no registered tenant can carry an accepting-side opening-balance capture."
  say "  The accepting side of :812 remains UNOBSERVED and T296 arm A remains UNKILLED."
  say "  Recorded in .softhouse/vectors/capabilities-ledger.json under"
  say "  ledger.opening.balance.and.closure, which is where the next reader hits it."
  say "  DO NOT close this hole by promoting a weaker refusal vector: every refusal capture"
  say "  in this corpus AGREES with arm A, so no number of them can kill it (T296 §4)."
  exit 1
fi
say "PASS: an accepting-side capture MAY be planned. It still needs its own task and review."
exit 0
