#!/usr/bin/env bash
# T261 RED-DRIVE C -- is the `--trace-ascii` 64-byte WRAP bug GENUINELY fixed?
#
# T250 reports (handoff s.2, defect 2) that `--trace-ascii` wraps payload lines at
# 64 bytes, that a 300-byte header value was therefore attested as 51 bytes, and
# that the record was "corrupt for any header longer than ~64 bytes" until it
# reassembled on the trace's own offsets.  This is the most dangerous thing in the
# diff -- a corrupt record that still LOOKS like evidence -- so it is checked here
# against a spread of lengths INCLUDING the wrap boundary, not just at 300.
#
# GROUND TRUTH: the exact bytes handed to curl's `-H`.  The sidecar must reproduce
# them character for character.  Nothing is taken from T250's transcript.
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../../.." && pwd)
EV="$ROOT/.softhouse/reviews/t261-tenant-attestation/evidence/redC"
# --- T304 FAIL-CLOSED GUARD (FU-T284-3) ---------------------------------------------
# This instrument rebuilds its evidence directory from scratch on every run, and that
# directory holds 110 TRACKED files. T114 binds: committed evidence is named and
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

rm -rf "$EV"; mkdir -p "$EV"

send_and_check() {   # send_and_check NAME HEADERVALUE
  sname=$1; sval=$2
  mkdir -p "$EV/$sname"
  OS_BASE="$BASE"; OS_OUTDIR="$EV/$sname"; OS_LIB_DIR="$LIB"
  OS_HEADERS="$A
Fineract-Platform-TenantId: default
X-T261-Long: $sval"
  export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
  # shellcheck disable=SC1091
  . "$LIB/oracle_send.sh"
  if ! oracle_send "$sname" GET /offices >/dev/null 2>"$EV/$sname/send.err"; then
    printf '  %-14s len=%-5s DERIVE/SEND REFUSED  <-- ' "$sname" "${#sval}"
    head -1 "$EV/$sname/send.err"
    return 1
  fi
  python3 - "$EV/$sname/$sname.http" "$sval" "$sname" <<'PY'
import re, sys
sidecar, expect, name = open(sys.argv[1]).read(), sys.argv[2], sys.argv[3]
m = re.search(r"(?m)^X-T261-Long: (.*)$", sidecar)
got = m.group(1) if m else "<ABSENT>"
ok = (got == expect)
print("  %-14s len=%-5d attested=%-5s %s"
      % (name, len(expect), len(got) if m else "-", "EXACT" if ok else "*** CORRUPT ***"))
if not ok:
    print("      expected[:80] %r" % expect[:80])
    print("      attested[:80] %r" % got[:80])
    sys.exit(1)
PY
  rcv=$?
  python3 "$WA" verify --sidecar "$EV/$sname/$sname.http" --headers "$EV/$sname/$sname.reqhdr" >/dev/null 2>&1 \
      || { echo "      verify FAILED for $sname"; return 1; }
  return $rcv
}

mkval() { python3 -c "import sys;print('A'*int(sys.argv[1]))" "$1"; }

echo "T261 RED-DRIVE C -- trace-ascii wrap reassembly"
echo "curl: $(curl --version | head -1)"
echo ""
echo "Header value lengths swept across the 64-byte wrap boundary and well beyond."
echo "'attested' is the length of the value recovered from the derived sidecar."
echo ""

fail=0
for n in 1 10 60 61 62 63 64 65 66 127 128 129 200 300 1000 4000; do
  v=$(mkval "$n")
  send_and_check "L$n" "$v" || fail=1
done

echo ""
echo "--- mixed shape: a long value CONTAINING colons and spaces ---"
v=$(python3 -c "print('x: y; '*60)")
send_and_check "Lmix" "$v" || fail=1

echo ""
echo "--- duplicated IDENTICAL header, one copy deleted from the sidecar ---"
mkdir -p "$EV/dupid"
OS_BASE="$BASE"; OS_OUTDIR="$EV/dupid"; OS_LIB_DIR="$LIB"
OS_HEADERS="$A
Fineract-Platform-TenantId: default
Fineract-Platform-TenantId: default"
export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
# shellcheck disable=SC1091
. "$LIB/oracle_send.sh"
oracle_send dupid GET /offices >/dev/null
python3 - "$EV/dupid/dupid.http" "$EV/dupid/dupid.reqhdr" <<'PY'
import sys
sc, rec = sys.argv[1], sys.argv[2]
nrec = open(rec).read().count("Fineract-Platform-TenantId: default")
nsc  = open(sc).read().count("Fineract-Platform-TenantId: default")
print("  wire record carries the header %d time(s); sidecar carries it %d time(s)" % (nrec, nsc))
ls = open(sc).read().split("\n"); out=[]; dropped=False
for l in ls:
    if l == "Fineract-Platform-TenantId: default" and not dropped:
        dropped = True; continue
    out.append(l)
open(sc, "w").write("\n".join(out))
print("  dropped ONE of the %d identical copies from the sidecar" % nsc)
PY
python3 "$WA" verify --sidecar "$EV/dupid/dupid.http" --headers "$EV/dupid/dupid.reqhdr" >/dev/null 2>"$EV/dupid/verr"
rc=$?
if [ "$rc" -eq 0 ]; then
  echo "  verify rc=0  <-- GAP: multiplicity is NOT checked (set membership only)"
  fail=$((fail))
else
  echo "  verify rc=$rc DETECTED"; sed 's/^/      /' "$EV/dupid/verr"
fi

echo ""
echo "--- CRLF injected into a header value ---"
mkdir -p "$EV/crlf"
OS_BASE="$BASE"; OS_OUTDIR="$EV/crlf"; OS_LIB_DIR="$LIB"
OS_HEADERS="$A
Fineract-Platform-TenantId: default
X-T261-Inj: safe$(printf '\r\n')X-T261-Evil: injected"
export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
# shellcheck disable=SC1091
. "$LIB/oracle_send.sh"
if oracle_send crlf GET /offices >/dev/null 2>"$EV/crlf/send.err"; then
  python3 - "$EV/crlf/crlf.reqhdr" <<'PY'
import sys
t=open(sys.argv[1]).read()
print("  record lines mentioning X-T261:")
for l in t.split("\n"):
    if l.startswith("X-T261"):
        print("      %r" % l)
PY
else
  echo "  capture REFUSED:"; sed 's/^/      /' "$EV/crlf/send.err" | head -3
fi

echo ""
echo "--- multibyte body: is the Content-Length crosscheck byte-exact? ---"
mkdir -p "$EV/mb"
python3 -c "
import io,sys
s='{\"name\":\"Улаанбаатар ᠮᠣᠩᠭᠣᠯ\",\"x\":1}'
open('$EV/mb/body.json','wb').write(s.encode('utf-8'))
print('  body bytes on disk: %d (chars %d)' % (len(s.encode('utf-8')), len(s)))
"
OS_BASE="$BASE"; OS_OUTDIR="$EV/mb"; OS_LIB_DIR="$LIB"
OS_HEADERS="$A
Fineract-Platform-TenantId: default
Content-Type: application/json"
export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
# shellcheck disable=SC1091
. "$LIB/oracle_send.sh"
oracle_send mb POST /offices "$EV/mb/body.json" >/dev/null 2>&1 || echo "  (send rc=$?)"
python3 - "$EV/mb/mb.http" "$EV/mb/mb.req" <<'PY'
import os,re,sys
sc=open(sys.argv[1]).read()
print("  Content-Length on the wire : %s" % (re.search(r"(?m)^Content-Length: (\d+)$", sc) or ["","<none>"])[1])
print("  crosscheck line            : %s" % (re.search(r"(?m)^content-length-crosscheck: .*$", sc).group(0) if re.search(r"(?m)^content-length-crosscheck: .*$", sc) else "<none>"))
print("  committed .req size        : %d" % os.path.getsize(sys.argv[2]))
PY
# truncate mid-multibyte, keep every sidecar assertion
cp -R "$EV/mb" "$EV/mbtrunc"
python3 - "$EV/mbtrunc/mb.req" <<'PY'
import sys
b=open(sys.argv[1],"rb").read()
# cut one byte off a multibyte character in the middle
open(sys.argv[1],"wb").write(b[:len(b)-1])
PY
python3 "$WA" verify --sidecar "$EV/mbtrunc/mb.http" --headers "$EV/mbtrunc/mb.reqhdr" --req "$EV/mbtrunc/mb.req" >/dev/null 2>"$EV/mbtrunc/verr"
echo "  truncated-mid-multibyte body, all assertions intact -> verify rc=$?"
sed 's/^/      /' "$EV/mbtrunc/verr" 2>/dev/null | head -4

echo ""
if [ "$fail" -ne 0 ]; then echo "RESULT: at least one length was CORRUPT or refused"; else echo "RESULT: every swept length attested EXACTLY"; fi
exit 0
