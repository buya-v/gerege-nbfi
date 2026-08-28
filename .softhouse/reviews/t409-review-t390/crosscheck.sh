#!/usr/bin/env bash
# T409 crosscheck.sh -- INDEPENDENT re-derivation of PROBES.tsv attribution.
#
#   bash .softhouse/reviews/t409-review-t390/crosscheck.sh <registry.tsv>
#
# It does NOT use oracle-state-baseline.sh's matcher, and it asks BOTH directions, which the
# instrument does not: live-not-registered (the instrument's own question) AND
# registered-not-live (a registry that over-claims, which the instrument can never notice).
# Section F asks the question no max(id) floor can express at all: were rows AT OR BELOW the
# floor mutated?
#
# READ-ONLY: every statement is a SELECT.
set -uo pipefail
REG="${1:?usage: crosscheck.sh <registry.tsv>}"
W="${2:-/tmp/t409/crosscheck-work}"
mkdir -p "$W"
psqlq() { docker exec -i fineract-db-1 psql -U root -d fineract_gerege -At -c "$1"; }

echo "T409 INDEPENDENT ATTRIBUTION CROSS-CHECK -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "registry: $REG"
echo "registry sha256: $(shasum -a 256 "$REG" | awk '{print $1}')"
echo

awk -F'\t' '$1=="txn"{print $2}' "$REG" | sort > "$W/reg-txn"
awk -F'\t' '$1=="txn"{print $2"\t"$3}' "$REG" | sort > "$W/reg-txn-full"
psqlq "SELECT DISTINCT transaction_id FROM acc_gl_journal_entry WHERE id > 64 ORDER BY 1" | sort > "$W/live-txn"

echo "== registry txn rows (key -> task) =="
sed 's/^/  /' "$W/reg-txn-full"
echo
echo "== live txn ids above je floor 64: $(grep -c . "$W/live-txn") =="
sed 's/^/  /' "$W/live-txn"
echo
echo "== A. LIVE but NOT in registry  (the instrument's own question) =="
comm -23 "$W/live-txn" "$W/reg-txn" | sed 's/^/  UNATTRIBUTED: /'
echo "  count = $(comm -23 "$W/live-txn" "$W/reg-txn" | grep -c .)"
echo
echo "== B. REGISTRY but NOT live  (over-claim; the instrument NEVER checks this) =="
comm -13 "$W/live-txn" "$W/reg-txn" | sed 's/^/  STALE-CLAIM: /'
echo "  count = $(comm -13 "$W/live-txn" "$W/reg-txn" | grep -c .)"
echo
echo "== C. registry txn rows with an EMPTY task field =="
awk -F'\t' '$1=="txn" && $3=="" {print "  EMPTY-TASK: "$0}' "$REG"
echo "  (end)"
echo
echo "== D. duplicate txn keys in the registry =="
uniq -d "$W/reg-txn" | sed 's/^/  DUP: /'
echo "  (end)"
echo
echo "== E. command keys above cs floor 352 =="
psqlq "SELECT coalesce(idempotency_key,'(null)') FROM m_portfolio_command_source WHERE id > 352 ORDER BY id" | sort > "$W/live-cmd"
awk -F'\t' '$1=="cmd"{print $2}' "$REG" | sort > "$W/reg-cmd"
echo "  live=$(grep -c . "$W/live-cmd")  registered=$(grep -c . "$W/reg-cmd")"
echo "  live-not-registered:"
comm -23 "$W/live-cmd" "$W/reg-cmd" | sed 's/^/    /'
echo "  registered-not-live:"
comm -13 "$W/live-cmd" "$W/reg-cmd" | sed 's/^/    /'
echo
echo "== F. what the registry cannot express: MUTATION of rows at or below the floor =="
psqlq "SELECT '  je rows AT/BELOW floor 64 modified since 2026-08-28 16:00Z: '||count(*) FROM acc_gl_journal_entry WHERE id <= 64 AND last_modified_on_utc >= TIMESTAMPTZ '2026-08-28 16:00:00+00'"
psqlq "SELECT '  je rows ABOVE floor 64 modified since 2026-08-28 16:00Z: '||count(*) FROM acc_gl_journal_entry WHERE id > 64 AND last_modified_on_utc >= TIMESTAMPTZ '2026-08-28 16:00:00+00'"
psqlq "SELECT '  distinct last_modified_by over the whole ledger table: '||string_agg(DISTINCT last_modified_by::text,',') FROM acc_gl_journal_entry"
