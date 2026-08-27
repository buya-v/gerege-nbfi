#!/usr/bin/env bash
# T261 RED-DRIVE B -- ATTACK the T250 tamper-detector with shapes it was NOT
# designed around (P-76: re-running the author's arms is reading, not reviewing).
#
# T250's arm set was: sidecar edit, record edit, record deleted, legacy sidecar,
# body swapped, Content-Length mismatch, whole-set forgery.  NONE of the shapes
# below appear in it.
#
# Every attack starts from a REAL capture taken against the LIVE reference oracle
# in this run.  Nothing is synthesised.  Each attack reports DETECTED / MISSED,
# and the harness itself is calibrated: attack 0 is an untouched positive control
# that MUST verify, and if it does not the run ABORTS rather than scoring the
# rest against a broken baseline.
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../../.." && pwd)
EV="$ROOT/.softhouse/reviews/t261-tenant-attestation/evidence/redB"
# --- T304 FAIL-CLOSED GUARD (FU-T284-3) ---------------------------------------------
# This instrument rebuilds its evidence directory from scratch on every run, and that
# directory holds 107 TRACKED files. T114 binds: committed evidence is named and
# SUPERSEDED by a scratch copy, never rewritten in place. Documenting the hazard in a
# handoff enforces nothing (P-45: "A test-only guard is not a guard ... verify the path
# that actually executes ... calls it, not merely that a test does") -- so the refusal
# is here, on the executing path, ahead of the destruction.
#   run for a NEW answer:  T304_EVIDENCE_SCRATCH="$(mktemp -d)" bash "$0"
#   read the OLD answer :  do not run it; the corpus is at the path above.
. "$(git rev-parse --show-toplevel)/.softhouse/capture/t304-evidence-destruction/instruments/refuse-if-tracked.sh"
EV="$(t304_evidence_root "$EV")" || exit 2
# --- end T304 guard -----------------------------------------------------------------
LIB="$ROOT/.softhouse/capture/lib"   # the library under review, in place
WA="$LIB/wire_attestation.py"
BASE="https://localhost:8443/fineract-provider/api/v1"
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
CT='Content-Type: application/json'

rm -rf "$EV"; mkdir -p "$EV/src" "$EV/req"
printf '%s' '{"name":"T261 probe","openingDate":"01 January 2026","dateFormat":"dd MMMM yyyy","locale":"en","parentId":1}' > "$EV/req/office.json"

capture() {   # capture NAME METHOD PATH [BODY] [EXTRA_HEADER...]
  cname=$1; cmethod=$2; cpath=$3; cbody=${4:-}
  shift 4 2>/dev/null || shift $#
  mkdir -p "$EV/src/$cname"
  OS_BASE="$BASE"; OS_OUTDIR="$EV/src/$cname"; OS_LIB_DIR="$LIB"
  OS_HEADERS="$A
Fineract-Platform-TenantId: default
$CT"
  for h in "$@"; do OS_HEADERS="$OS_HEADERS
$h"; done
  export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
  # shellcheck disable=SC1091
  . "$LIB/oracle_send.sh"
  oracle_send "$cname" "$cmethod" "$cpath" ${cbody:+"$cbody"}
}

verify() {    # verify DIR NAME [--req]
  vd=$1; vn=$2; vreq=${3:-}
  if [ -n "$vreq" ]; then
    python3 "$WA" verify --sidecar "$vd/$vn.http" --headers "$vd/$vn.reqhdr" --req "$vd/$vn.req" >"$vd/$vn.vout" 2>"$vd/$vn.verr"
  else
    python3 "$WA" verify --sidecar "$vd/$vn.http" --headers "$vd/$vn.reqhdr" >"$vd/$vn.vout" 2>"$vd/$vn.verr"
  fi
  echo $?
}

PASS=0; MISS=0; N=0
score() {     # score LABEL EXPECT_RC GOT_RC DIR NAME
  slabel=$1; sexp=$2; sgot=$3; sdir=$4; sname=$5
  N=$((N+1))
  if [ "$sgot" = "$sexp" ]; then
    printf '  [%-8s] %-58s rc=%s (expected %s)\n' DETECTED "$slabel" "$sgot" "$sexp"
    PASS=$((PASS+1))
  else
    printf '  [%-8s] %-58s rc=%s (expected %s)  <-- GAP\n' "MISSED" "$slabel" "$sgot" "$sexp"
    MISS=$((MISS+1))
  fi
  if [ -s "$sdir/$sname.verr" ]; then sed 's/^/            /' "$sdir/$sname.verr"; fi
}

echo "T261 RED-DRIVE B -- attacking the detector"
echo "oracle: $BASE   curl: $(curl --version | head -1 | cut -d' ' -f1-2)"
echo ""

# ---------------------------------------------------------------------- capture
echo "capturing base artefacts from the LIVE oracle ..."
capture post POST /offices "$EV/req/office.json"          || echo "  (post capture rc=$?)"
capture dup  GET  /offices "" "Fineract-Platform-TenantId: gerege" || echo "  (dup capture rc=$?)"
capture colon GET /offices "" 'X-T261-Note: alpha: beta; gamma' || echo "  (colon capture rc=$?)"
capture kcoll GET /offices "" 'body-bytes: 999999'         || echo "  (kcoll capture rc=$?)"
capture empty GET /offices "" 'Fineract-Platform-TenantId;' || echo "  (empty capture rc=$?)"
echo ""

echo "--- CALIBRATION: untouched positive control must VERIFY ---"
rc=$(verify "$EV/src/post" post req)
if [ "$rc" != "0" ]; then
  echo "ABORT: positive control did not verify (rc=$rc); nothing may be scored."
  cat "$EV/src/post/post.verr" 2>/dev/null
  exit 4
fi
echo "  positive control VERIFIED rc=0"
echo ""

mk() { rm -rf "$EV/$1"; cp -R "$EV/src/$2" "$EV/$1"; }

echo "--- ATTACKS (expect rc=1 MISMATCH or rc=2 REFUSED; rc=0 is a GAP) ---"

# A1. duplicated header on the wire, one copy DELETED from the sidecar.
mk a1 dup
python3 - "$EV/a1/dup.http" <<'PY'
import sys
p=sys.argv[1]; ls=open(p).read().split("\n"); out=[]; seen=False
for l in ls:
    if l.startswith("Fineract-Platform-TenantId:") and not seen:
        seen=True; continue          # drop the FIRST of the two sent copies
    out.append(l)
open(p,"w").write("\n".join(out))
PY
score "A1 duplicated header: one copy removed from sidecar" 1 "$(verify "$EV/a1" dup)" "$EV/a1" dup

# A2. sidecar's `body-sha256:` line DELETED, body swapped for a DIFFERENT body of
#     the SAME byte length.  Content-Length still matches, so only the sha would
#     have caught it -- and the sha line is simply gone.
mk a2 post
python3 - "$EV/a2/post.http" "$EV/a2/post.req" <<'PY'
import sys
sc, rq = sys.argv[1], sys.argv[2]
n = len(open(rq,"rb").read())
open(rq,"wb").write(b"Z"*n)                      # different bytes, same length
ls=[l for l in open(sc).read().split("\n") if not l.startswith("body-sha256: ")]
open(sc,"w").write("\n".join(ls))
PY
score "A2 body swapped (same length) + body-sha256 line deleted" 1 "$(verify "$EV/a2" post req)" "$EV/a2" post

# A3. sidecar's `body-bytes:` AND `body-sha256:` deleted, body truncated.
mk a3 post
python3 - "$EV/a3/post.http" "$EV/a3/post.req" <<'PY'
import sys
sc, rq = sys.argv[1], sys.argv[2]
b=open(rq,"rb").read(); open(rq,"wb").write(b[:len(b)//2])
ls=[l for l in open(sc).read().split("\n")
    if not l.startswith("body-sha256: ") and not l.startswith("body-bytes: ")
    and not l.startswith("content-length-crosscheck: ")]
open(sc,"w").write("\n".join(ls))
PY
score "A3 body truncated + all three body assertions deleted" 1 "$(verify "$EV/a3" post req)" "$EV/a3" post

# A4. header line REORDERED in the sidecar (membership, not sequence).
mk a4 post
python3 - "$EV/a4/post.http" <<'PY'
import sys
p=sys.argv[1]; ls=open(p).read().split("\n")
i=[n for n,l in enumerate(ls) if l.startswith("Fineract-Platform-TenantId:")]
j=[n for n,l in enumerate(ls) if l.startswith("Host:")]
if i and j: ls[i[0]],ls[j[0]] = ls[j[0]],ls[i[0]]
open(p,"w").write("\n".join(ls))
PY
score "A4 sidecar header lines REORDERED vs the wire" 1 "$(verify "$EV/a4" post req)" "$EV/a4" post

# A5. header whose NAME collides with a known sidecar key: its value tampered.
mk a5 kcoll
python3 - "$EV/a5/kcoll.http" <<'PY'
import sys
p=sys.argv[1]
t=open(p).read().replace("body-bytes: 999999","body-bytes: 1")
open(p,"w").write(t)
PY
score "A5 wire header named 'body-bytes' tampered in sidecar" 1 "$(verify "$EV/a5" kcoll)" "$EV/a5" kcoll

# A6. sidecar line whose key collides with a known key, INVENTED (never sent).
mk a6 post
python3 - "$EV/a6/post.http" <<'PY'
import sys
p=sys.argv[1]; t=open(p).read()
open(p,"w").write(t.rstrip("\n")+"\ncontent-length-crosscheck: MATCH (99999 bytes)\n")
PY
score "A6 invented 'content-length-crosscheck' line appended" 1 "$(verify "$EV/a6" post req)" "$EV/a6" post

# A7. header value containing a colon, tampered after the colon.
mk a7 colon
python3 - "$EV/a7/colon.http" <<'PY'
import sys
p=sys.argv[1]
t=open(p).read().replace("alpha: beta; gamma","alpha: DELTA; gamma")
open(p,"w").write(t)
PY
score "A7 colon-bearing header value tampered in sidecar" 1 "$(verify "$EV/a7" colon)" "$EV/a7" colon

# A8. header differing only in CASE in the sidecar.
mk a8 post
python3 - "$EV/a8/post.http" <<'PY'
import sys
p=sys.argv[1]
t=open(p).read().replace("Fineract-Platform-TenantId: ","fineract-platform-tenantid: ")
open(p,"w").write(t)
PY
score "A8 sidecar header name case-folded" 1 "$(verify "$EV/a8" post req)" "$EV/a8" post

# A9. the header record of a DIFFERENT request, with its matching sidecar's digest
#     line transplanted -- i.e. an attacker who has two real captures.
mk a9 post
cp "$EV/src/dup/dup.reqhdr" "$EV/a9/post.reqhdr"
score "A9 record swapped for a DIFFERENT real request's record" 1 "$(verify "$EV/a9" post req)" "$EV/a9" post

# A10. RESPONSE swapped: the .json answer replaced by another real capture's.
mk a10 post
cp "$EV/src/dup/dup.json" "$EV/a10/post.json"
score "A10 RESPONSE body swapped for another capture's response" 1 "$(verify "$EV/a10" post req)" "$EV/a10" post

# A11. request-headers-sha256 line DELETED entirely (not altered).
mk a11 post
python3 - "$EV/a11/post.http" <<'PY'
import sys
p=sys.argv[1]
ls=[l for l in open(p).read().split("\n") if not l.startswith("request-headers-sha256: ")]
open(p,"w").write("\n".join(ls))
PY
score "A11 request-headers-sha256 line deleted from sidecar" 1 "$(verify "$EV/a11" post req)" "$EV/a11" post

echo ""
echo "empty-tenant capture -- what the sidecar says when the tenant header is REMOVED by curl:"
python3 - "$EV/src/empty/empty.http" <<'PY'
import re,sys
t=open(sys.argv[1]).read()
m=re.search(r"(?im)^Fineract-Platform-TenantId:.*$", t)
print("   tenant line in sidecar : %s" % (m.group(0) if m else "<ABSENT -- no line, no warning>"))
print("   status                 : %s" % open(sys.argv[1].replace(".http",".status")).read().strip())
PY

echo ""
echo "SCORE: $PASS detected / $MISS missed of $N attacks"
exit 0
