#!/bin/sh
# T36 — re-capture the four Path B sets against a PRODUCTION-SETTINGS tenant.  Closes T22 P0-6.
# HARDENED by T80 after T77 P0-T77-2.  See "the two properties" below.
#
# Tenant `gerege`: timezone Asia/Ulaanbaatar (+08, no DST — the ZONE is asserted, never an offset),
# c_configuration.rounding-mode = 4 (HALF_UP), MoneyHelper.PRECISION = 19 (deployed bytecode).
# Effective MathContext therefore (19, HALF_UP) — the ratified production setting.
#
# Additive only.  Creates no tenant, restarts nothing, drops nothing: another worker may be running
# captures against this same server for the whole fire.  Products 1-4 already exist in `gerege` from
# the committed byte-verbatim payloads (t22-audit/fresh-tenant.sh); this run reuses them so the calc
# requests can be sent BYTE-VERBATIM from req/, productId included.
#
# ---------------------------------------------------------------------------------------------
# THE TWO PROPERTIES THIS SCRIPT MUST HAVE.  Both were false until T80; both are now proved by an
# attack transcript in ../t80/out/, not asserted here.
#
#  1. PRECONDITIONS ARE FAIL-THE-RUN.  Until T80 this was a comment, not a fact: preconditions.sh
#     writes every FAIL to STDERR, and this script tee'd only STDOUT and then grepped the tee'd
#     file for '^  FAIL'.  The count was therefore ALWAYS 0 and the ABORT was UNREACHABLE.  T77 ran
#     `TENANT=default sh recapture.sh` and got five breached preconditions — including a canary that
#     404'd, i.e. the rounding mode in force was never established at all — no abort, all four
#     captures taken, exit 0.  The gate now tests the EXIT STATUS of preconditions.sh (the signal
#     the script actually emits) and, independently, greps a transcript that now contains BOTH
#     streams.  Two operands, either of which aborts.  `attest.py:96-101` already did it this way;
#     this is the same shape, deliberately.
#
#  2. A CAPTURE IS FILED UNDER THE TENANT IT WAS TAKEN FROM, STRUCTURALLY.  Until T80 the output
#     directory was the hard-coded literal `out/recapture-gerege` while the tenant was a variable,
#     so T77's `default` run wrote default-tenant bytes into a directory named for `gerege` — and
#     the four response bodies are byte-identical across modes, so NOTHING downstream could tell.
#     The directory now DERIVES from $TENANT; an explicit RECAPTURE_OUT override must still be
#     named for the tenant in use; and the run drops a provenance stamp that a later run of a
#     different tenant refuses to overwrite.
# ---------------------------------------------------------------------------------------------
#
# Usage:   sh recapture.sh                 # tenant gerege -> out/recapture-gerege
#          TENANT=x sh recapture.sh        # tenant x      -> out/recapture-x
#          RECAPTURE_OUT=<dir> sh …        # explicit dir, which must be named for $TENANT
# Exit:    0 = every precondition held and all four captures returned HTTP 200
#          1 = anything else, and in that case NOTHING was captured
set -u

D=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$D/.." && pwd)

die() { printf 'ABORT: %s\n' "$1" >&2; exit 1; }

TENANT=${TENANT:-gerege}
# A tenant identifier becomes a directory name below, so it is validated as one path segment.
case "$TENANT" in
  '' | *[!a-z0-9_-]* ) die "TENANT='$TENANT' is not a valid tenant identifier (expected [a-z0-9_-]+)." ;;
esac

# --- property 2: the output directory derives from the tenant actually used ---------------------
# T99 CORRECTION.  Until now this compared BASENAMES:
#     Obase=$(basename "$O"); case "$Obase" in "$TENANT" | *-"$TENANT" ) : ;; * ) die ...
# so `RECAPTURE_OUT=$D/out/recapture-default/sub-gerege TENANT=gerege` passed — leaf `sub-gerege`
# matches `*-gerege` — and filed a gerege capture INSIDE the default tenant's capture directory.
# The hazard T80 closed at the top level survived exactly ONE DIRECTORY DOWN.  Reproduced against
# main's bytes in t99/out/f1-prefix-*: guard admitted, directory created, stamp written 'gerege'
# under `recapture-default/`.
#
# The guard now decides on the RESOLVED path (symlinks and `..` collapsed, relative forms made
# absolute) and on its SHAPE, not on its leaf.  Three operands, each of which alone refuses the
# nested attack:
#   (a) CONTAINMENT — the resolved path is inside this Path B evidence tree.
#   (b) SHAPE — relative to that tree it is exactly `<task>/out/<name>`, three components, with
#       `<task>` matching t[0-9]*.  A bounded depth is what makes "one directory down" impossible;
#       an enumeration of bad ancestor names would only ever be as good as the enumerator (P-18).
#   (c) LEAF — `<name>` is the tenant id or ends in `-<tenant id>`, as before.
# and a fourth, semantic operand:
#   (d) NO NESTING INSIDE A CAPTURE — no ancestor directory may itself carry a CAPTURED-FROM-TENANT
#       stamp.  A capture set never lives inside another capture set, whatever it is called.
O=${RECAPTURE_OUT:-$D/out/recapture-$TENANT}

# Resolve a directory that need not exist yet: the deepest EXISTING ancestor is resolved with
# `cd`+`pwd -P`, which collapses symlinks and `..`; the remainder is appended and refused if it
# still contains a `.` or `..` component.
resolve_dir() {
  rp=$1
  case "$rp" in /*) ;; *) rp=$PWD/$rp ;; esac
  rtail=''
  while [ ! -d "$rp" ] && [ "$rp" != "/" ] && [ -n "$rp" ]; do
    rb=$(basename "$rp"); rp=$(dirname "$rp")
    rtail=$rb${rtail:+/$rtail}
  done
  rhead=$(cd "$rp" 2>/dev/null && pwd -P) || return 1
  [ -n "$rtail" ] || { printf '%s\n' "$rhead"; return 0; }
  case "/$rtail/" in *"/./"* | *"/../"* ) return 1 ;; esac
  printf '%s\n' "$rhead/$rtail"
}

Wr=$(resolve_dir "$W") || die "cannot resolve the Path B evidence root '$W'"
Or=$(resolve_dir "$O") || die "output directory '$O' cannot be resolved to a concrete path (a '.' or '..' component below a directory that does not exist)."

# (a) containment
case "$Or/" in
  "$Wr"/* ) : ;;
  * ) die "output directory '$O' resolves to '$Or', which is OUTSIDE the Path B evidence tree '$Wr'. A capture is filed inside the tree it belongs to, so that the provenance index at $Wr/PROVENANCE-INDEX.tsv can account for it." ;;
esac
rel=${Or#"$Wr"/}
[ "$rel" != "$Or" ] || die "output directory '$O' resolves to the Path B evidence root itself ('$Or'), which is not a capture directory."

# (b) shape: exactly <task>/out/<name>
oldifs=$IFS; IFS=/; set -f
# shellcheck disable=SC2086
set -- $rel
set +f; IFS=$oldifs
[ "$#" -eq 3 ] || die "output directory '$O' resolves to '$Or'; relative to the evidence tree that is '$rel', which has $# path component(s). A capture directory is exactly <task>/out/<name> — three components. Nesting a capture one level down inside another tenant's capture directory is the same mis-filing hazard the leaf check was written to stop, and a fixed depth is what makes it impossible."
Otask=$1; Omid=$2; Oleaf=$3
case "$Otask" in
  t[0-9]* ) : ;;
  * ) die "output directory '$Or': the task component is '$Otask', which is not a t<NN> task directory. Expected <task>/out/<name> below '$Wr'." ;;
esac
[ "$Omid" = "out" ] || die "output directory '$Or': the middle component is '$Omid', expected literally 'out'. Expected <task>/out/<name> below '$Wr'."

# (c) leaf
case "$Oleaf" in
  "$TENANT" | *-"$TENANT" ) : ;;
  * ) die "output directory '$O' is not named for tenant '$TENANT'. A capture must be filed under the tenant it was taken from; refusing to write '$TENANT' bytes into a directory called '$Oleaf'." ;;
esac

# (d) no capture set inside another capture set
anc=$Or
while [ "$anc" != "$Wr" ] && [ "$anc" != "/" ]; do
  anc=$(dirname "$anc")
  if [ -f "$anc/CAPTURED-FROM-TENANT" ]; then
    die "output directory '$Or' is nested inside '$anc', which is itself a capture set (it carries $anc/CAPTURED-FROM-TENANT, tenant '$(head -1 "$anc/CAPTURED-FROM-TENANT" | tr -d '\r')'). A capture set is never written inside another capture set."
  fi
done

# From here on the output directory is the RESOLVED one, so nothing downstream can be handed a
# path that the guard did not adjudicate.
O=$Or

STAMP=$O/CAPTURED-FROM-TENANT
if [ -f "$STAMP" ]; then
  prev=$(head -1 "$STAMP" | tr -d '\r')
  [ "$prev" = "$TENANT" ] || die "'$O' already holds a capture set taken from tenant '$prev' (see $STAMP); refusing to overwrite it with a '$TENANT' capture."
fi
mkdir -p "$O" || die "cannot create output directory '$O'"
printf '%s\n' "$TENANT" > "$STAMP"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T="Fineract-Platform-TenantId: $TENANT"
CT='Content-Type: application/json'

echo "### tenant '$TENANT'  ->  output directory $O"
echo
echo "### preconditions (T22 P0-4) — a breach ABORTS before any capture"
prestatus=0
CANARY_REQ="$W/t22-audit/req/calc-pmode2-gerege.json" \
  sh "$D/preconditions.sh" "$TENANT" > "$O/preconditions.txt" 2>&1 || prestatus=$?
cat "$O/preconditions.txt"
# Operand 1: the exit status preconditions.sh actually emits.
# Operand 2: FAIL lines in a transcript that now captures BOTH streams (the bug T77 found was that
# it captured only stdout, where a FAIL line never appears).  Either one aborts.
# LC_ALL=C: BSD grep in a UTF-8 locale silently fails to match ANY line in a file containing an
# invalid multibyte sequence, so a transcript with one stray byte would make this operand return 0
# on a breached run.  That is precisely the silent-zero this gate exists to stop; operand 1 (the
# exit status) would still abort, but an operand that can go blind is not a second operand.
prefails=$(LC_ALL=C grep -ac '^  FAIL' "$O/preconditions.txt" || true)
if [ "$prestatus" -ne 0 ] || [ "$prefails" != "0" ]; then
  echo >&2
  die "preconditions breached — exit status $prestatus, $prefails FAIL line(s) in $O/preconditions.txt. NOTHING WAS CAPTURED. Any file already in '$O' is from an earlier run and is NOT an observation of this environment."
fi

echo
echo "### product persistence read-back, from PostgreSQL rows not from the create response"
SCHEMA=$(docker exec fineract-db-1 psql -U root -d fineract_tenants -At \
  -c "select c.schema_name from tenants t join tenant_server_connections c on c.id=t.oltp_id where t.identifier='$TENANT';" | tr -d '\r')
[ -n "$SCHEMA" ] || die "no schema_name for tenant '$TENANT' — cannot read the product rows back."
docker exec fineract-db-1 psql -U root -d "$SCHEMA" -At \
  -c "select to_jsonb(t) from m_product_loan t where id in (1,2,3,4) order by id;" > "$O/products-asrow.jsonl"
docker exec fineract-db-1 psql -U root -d "$SCHEMA" -At \
  -c "select id, coalesce(installment_amount_in_multiples_of::text,'NULL'), coalesce(days_in_year_custom_strategy,'NULL') from m_product_loan where id in (1,2,3,4) order by id;"

echo
echo "### captures — explicit filenames, HTTP status checked, non-200 fails the run"
set -e
for pair in "01:calc-B-01-baseline:B-01-baseline" \
            "02:calc-B-02-multiplesof100:B-02-multiplesof100" \
            "03:calc-B-03-diycs-fullleapyear:B-03-diycs-fullleapyear" \
            "04:calc-B-04-diycs-feb29only:B-04-diycs-feb29only"; do
  n=${pair%%:*}; rest=${pair#*:}; req=${rest%%:*}; outname=${rest#*:}
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" \
              -H "$A" -H "$T" -H "$CT" -d @"$W/req/$req.json" \
              -o "$O/$outname-raw.json" -w '%{http_code}')
  echo "B-$n  HTTP $code  -> $O/$outname-raw.json"
  if [ "$code" != "200" ]; then
    echo "CAPTURE FAILED: B-$n returned HTTP $code — the file is an ERROR BODY, not a capture." >&2
    exit 1
  fi
done

echo
# T99: the digests printed into this transcript are evidence, so they are computed by the hardened
# instrument (absolute-path tools, known-answer tested, two implementations required to agree) and
# not by a bare `shasum` that $PATH decides the meaning of.  A refusal prints REFUSED and fails the
# run rather than printing a digest nobody can stand behind.
. "$D/sha256.sh"
if ! sha256_init; then
  echo "REFUSED: cannot digest the captures — $SHA256_ERROR" >&2
  exit 1
fi
echo "# sha256 by $SHA256_TOOLS"
for f in "$O"/B-0*-raw.json; do
  if sha256_file "$f"; then
    printf '%s  %s\n' "$SHA256_RESULT" "$f"
  else
    echo "REFUSED: $SHA256_ERROR" >&2
    exit 1
  fi
done
echo
echo "captured from tenant '$TENANT' (stamped in $STAMP)"
