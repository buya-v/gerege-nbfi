#!/usr/bin/env bash
# T108 — does this defect reach a MONEY guard?
#
# The rigs were read, not assumed.  Across recapture.sh, forbidden-sentence.sh,
# preconditions.sh, attest.py and conformance.sh the only content scanners in
# use are: grep (43), perl (16), tr (14), sed (8), python3 (3), shasum (2).
# No rg, no ag, no awk, no standalone ugrep.
#
# Two of those greps are HARD money guards in .softhouse/conformance.sh:
#
#   :184  guard_no_float_in_vectors
#         perl -0pe 's/"(\\.|[^"\\])*"//g' "$f" | grep -Eq '[-0-9][0-9]*\.[0-9]|...'
#   :201  guard_no_float_in_harness
#         perl -0pe '...' | grep -Eq '\bfloat(32|64)\b|...'
#
# Both are bare `grep -Eq` — no -a, no LC_ALL=C — and both are "fires when it
# finds something bad" guards, so a blind grep is a SILENT PASS on a float.
# This probe measures whether the defect reaches them.
#
# This script contains no arithmetic; no floating point (P-25).  The literal
# "2.0" below is a MALFORMED FIXTURE the guard is supposed to reject, not a
# computed value.
#
# Usage: bash probe-conformance-guards.sh
set -u

S="$(mktemp -d -t t108guard)"

python3 - "$S" <<'PY'
import os, sys
s = sys.argv[1]
# after perl strips string literals, the float-shaped token must remain visible
clean = b'{\n  "number_of_repayments": 2.0,\n  "note": "ok"\n}\n'
open(os.path.join(s, 'clean.json'), 'wb').write(clean)
# same file with a lone 0xE2 BEFORE the float-shaped token, on the same line
i = clean.find(b'2.0')
open(os.path.join(s, 'poisoned.json'), 'wb').write(clean[:i] + b'\xe2 ' + clean[i:])
# and with the bad byte on an EARLIER line, to show that shape is harmless
j = clean.find(b'\n') + 1
open(os.path.join(s, 'earlier-line.json'), 'wb').write(clean[:j] + b'  \xe2\n' + clean[j:])
print('built clean.json / poisoned.json / earlier-line.json')
PY

RE='[-0-9][0-9]*\.[0-9]|[0-9][eE][-+]?[0-9]'

echo
echo "The guard as it is written in conformance.sh:184 —"
echo "  perl -0pe 's/\"(\\\\.|[^\"\\\\])*\"//g' \$f | grep -Eq '<float regex>'"
echo "  exit 0 = 'FLOAT FOUND, reject'   exit 1 = 'clean, pass'"
echo
printf '%-18s %-10s %-24s %s\n' FILE LOCALE 'GUARD SAYS' VERDICT
for f in clean poisoned earlier-line; do
  for loc in utf8 posixC; do
    if [ "$loc" = utf8 ]; then
      env -u LC_ALL LANG=C.UTF-8 LC_CTYPE=C.UTF-8 bash -c \
        "perl -0pe 's/\"(\\\\.|[^\"\\\\])*\"//g' \"\$1\" | /usr/bin/grep -Eq \"\$2\"" _ "$S/$f.json" "$RE"
    else
      env LC_ALL=C LANG=C bash -c \
        "perl -0pe 's/\"(\\\\.|[^\"\\\\])*\"//g' \"\$1\" | /usr/bin/grep -Eq \"\$2\"" _ "$S/$f.json" "$RE"
    fi
    st=$?
    if [ "$st" -eq 0 ]; then says="FLOAT FOUND (rejects)"; else says="clean (PASSES)"; fi
    if [ "$st" -eq 0 ]; then v="correct"; else v="*** SILENT PASS ON A FLOAT ***"; fi
    printf '%-18s %-10s %-24s %s\n' "$f.json" "$loc" "$says" "$v"
  done
done

echo
echo "and with the two tokens added (this is the proposed fix, NOT applied here —"
echo ".softhouse/conformance.sh belongs to another worker this fire):"
printf '%-18s %-10s %-24s %s\n' FILE LOCALE 'GUARD SAYS' VERDICT
for f in clean poisoned earlier-line; do
  for loc in utf8 posixC; do
    if [ "$loc" = utf8 ]; then
      env -u LC_ALL LANG=C.UTF-8 LC_CTYPE=C.UTF-8 bash -c \
        "perl -0pe 's/\"(\\\\.|[^\"\\\\])*\"//g' \"\$1\" | LC_ALL=C /usr/bin/grep -aEq \"\$2\"" _ "$S/$f.json" "$RE"
    else
      env LC_ALL=C LANG=C bash -c \
        "perl -0pe 's/\"(\\\\.|[^\"\\\\])*\"//g' \"\$1\" | LC_ALL=C /usr/bin/grep -aEq \"\$2\"" _ "$S/$f.json" "$RE"
    fi
    st=$?
    if [ "$st" -eq 0 ]; then says="FLOAT FOUND (rejects)"; else says="clean (PASSES)"; fi
    if [ "$st" -eq 0 ]; then v="correct"; else v="*** SILENT PASS ON A FLOAT ***"; fi
    printf '%-18s %-10s %-24s %s\n' "$f.json" "$loc" "$says" "$v"
  done
done

echo
echo "hexdump of poisoned.json:"
xxd "$S/poisoned.json"
rm -rf "$S"
