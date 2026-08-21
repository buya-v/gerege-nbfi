#!/bin/bash
# T155 probe (xiii) — THE DRIVER'S QUESTION, measured rather than reasoned.
#
# Does T154's leg-3 census close the DEFLATED direction (a vector REMOVED from
# the store) or only the INFLATED one (a file present-but-unloaded)?
#
# Arms, all on the SCRATCH MERGE of T154 into current main, so "post-fix" means
# post-fix and the count baseline is measured, never assumed.
set -u
POST=/tmp/t155/post
PRE=/tmp/t155/pre
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh

run() { # $1 tree $2 label
  ( cd "$1" && bash "$1/.softhouse/conformance.sh" ) > "/tmp/t155/out/xiii-$2.txt" 2>&1
  local rc=$?
  local p c
  p="$(LC_ALL=C grep -aE '^ +parity vectors +PASS' "/tmp/t155/out/xiii-$2.txt" | head -1 | awk '{print $4}')"
  c="$(LC_ALL=C grep -aE '^ +cells compared' "/tmp/t155/out/xiii-$2.txt" | head -1 | awk '{print $3}')"
  printf '  exit=%-3s parity=%-4s cells=%-6s %s\n' "$rc" "${p:-NA}" "${c:-NA}" \
    "$(LC_ALL=C grep -a '^VERDICT' "/tmp/t155/out/xiii-$2.txt" | head -1 | cut -c1-60)"
  local w
  w="$(LC_ALL=C grep -aiE 'STORE FILE CENSUS|CASE_ID INTEGRITY|missing|absent|removed|fewer|expected' "/tmp/t155/out/xiii-$2.txt" | head -1 | sed 's/^ *//' | cut -c1-110)"
  [ -n "$w" ] && printf '        %s\n' "$w"
}

echo "=== CONTROL: the merged tree, store intact ==="
run "$POST" control
echo

echo "=== DEFLATION: remove exactly ONE parity vector file ==="
V="$POST/.softhouse/vectors/loanschedule"
VICTIM="$V/P-01-18x18pt5pct-principal-87654321.json"
[ -f "$VICTIM" ] || { echo "APPARATUS: victim vector not found"; exit 9; }
mv "$VICTIM" /tmp/t155/victim.json
run "$POST" deflated
mv /tmp/t155/victim.json "$VICTIM"
echo

echo "=== DEFLATION, larger: remove FIVE parity vectors ==="
mkdir -p /tmp/t155/victims
n=0
for f in $(find "$V" -name 'P-*.json' -type f | sort | head -5); do mv "$f" /tmp/t155/victims/; n=$((n+1)); done
echo "  moved $n files out"
run "$POST" deflated5
mv /tmp/t155/victims/*.json "$V"/
echo

echo "=== DEFLATION, total: remove the WHOLE loanschedule context ==="
mv "$V" /tmp/t155/ctx-out
run "$POST" deflated-all
mv /tmp/t155/ctx-out "$V"
echo

echo "=== INFLATION, for contrast: one extra unloaded .json (what T154 DID close) ==="
printf '{ "note": "planted", "amount": "1250000" }\n' > "$POST/.softhouse/vectors/T155-INFLATE.json"
run "$POST" inflated
rm -f "$POST/.softhouse/vectors/T155-INFLATE.json"
echo

echo "=== does ANY committed artefact name an expected corpus size? ==="
echo "  PIN.json keys:"
LC_ALL=C grep -aoE '"[a-z_]+":' "$POST/.softhouse/vectors/PIN.json" | sort -u | tr '\n' ' ' | sed 's/^/    /'
echo
echo "  any 'expected'/'manifest'/'corpus size' notion in conformance.sh:"
LC_ALL=C grep -anE 'expected_vector|manifest|corpus_size|EXPECTED_(PARITY|VECTORS)|minimum.*vector' "$POST/.softhouse/conformance.sh" | sed 's/^/    /'
echo "    (end)"
echo
echo "  the refusal T156 cites, vector.go:988 region:"
sed -n '980,1000p' "$POST/nexus/internal/apps/loanschedule/conformance/vector.go" | sed 's/^/    /'
echo
echo "  restored store still clean?"
run "$POST" restored
