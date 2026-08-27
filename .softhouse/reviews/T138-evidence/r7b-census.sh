#!/bin/sh
# T138 — MF-4 census, third independent measurement, with a WIDER net than my
# first pass (which anchored on the literal path 'charges/bin/preconditions.sh'
# and so missed the callers that build the path from a variable such as $CH).
set -u
B=/tmp/T138-mf2-post
CAP=$B/.softhouse/capture

echo "NET 1 — every .sh/.py line under .softhouse/capture/ mentioning 'preconditions.sh',"
echo "        excluding the t91 harness (a red/green rig, not a pipeline caller):"
LC_ALL=C grep -rn --include='*.sh' --include='*.py' -a 'preconditions\.sh' "$CAP" \
  | LC_ALL=C grep -av '/t91/' | LC_ALL=C sed "s|$CAP/||" | sort > /tmp/T138-census-raw.txt
echo "   raw mention lines: $(wc -l < /tmp/T138-census-raw.txt | tr -d ' ')"
echo
echo "NET 2 — restrict to lines that are EXECUTABLE invocations of the charges shim"
echo "        or of the T40 wrapper.  Comments (^#), grep -v exclusions and"
echo "        provenance strings are excluded and listed separately."
echo
echo "--- (a) DIRECT invocations of charges/bin/preconditions.sh:"
LC_ALL=C grep -a -E '(sh|bash) +"?[^"]*(\$CH/bin|charges/bin)/preconditions\.sh|preconditions\.sh(["'"'"']?,)' /tmp/T138-census-raw.txt \
  | LC_ALL=C grep -av ':[0-9]*:[[:space:]]*#' \
  | LC_ALL=C grep -av 'pathb/t36/preconditions\.sh' \
  | LC_ALL=C grep -av '^audit-t44/' \
  | LC_ALL=C grep -av 'grep -v' | sed 's/^/    /'
echo
echo "--- python callers (they build the argv list, not a shell line):"
LC_ALL=C grep -rn --include='*.py' -a "preconditions" "$CAP/charges/bin" | LC_ALL=C grep -a "'sh'\|\"sh\"\|preconditions.sh" | LC_ALL=C sed "s|$CAP/||" | sed 's/^/    /'
echo
echo "--- the 5 sites T115 names, quoted verbatim from the tree:"
for s in "charges/bin/run-preconditions.sh:9" "charges/bin/attest.py:90" "charges/bin/attest-t40.py:91" "charges/bin/t51-negative.sh:21" "leapboundary/bin/t55-negative-tests.sh:52"; do
  f=${s%:*}; n=${s##*:}
  printf '    %-46s %s\n' "$s" "$(LC_ALL=C sed -n "${n}p" "$CAP/$f" | sed 's/^[[:space:]]*//')"
done
echo
echo "--- the exclusions T115 names, quoted verbatim:"
for s in "charges/bin/selfcheck.sh:15" "charges/bin/attest-t40.py:305"; do
  f=${s%:*}; n=${s##*:}
  printf '    %-46s %s\n' "$s" "$(LC_ALL=C sed -n "${n}p" "$CAP/$f" | sed 's/^[[:space:]]*//')"
done
echo
echo "--- (b) WRAPPER invocations (run-preconditions.sh), executable lines only:"
LC_ALL=C grep -rn --include='*.sh' --include='*.py' -a 'run-preconditions\.sh' "$CAP" \
  | LC_ALL=C grep -av '/t91/' \
  | LC_ALL=C grep -av ':[0-9]*:[[:space:]]*#' \
  | LC_ALL=C sed "s|$CAP/||" | sort > /tmp/T138-census-wrap.txt
cat /tmp/T138-census-wrap.txt | sed 's/^/    /'
echo "    ---- wrapper call SITES: $(wc -l < /tmp/T138-census-wrap.txt | tr -d ' ')"
echo "    ---- wrapper call FILES: $(cut -d: -f1 /tmp/T138-census-wrap.txt | sort -u | wc -l | tr -d ' ')"
echo
echo "=== TOTALS (T138's own count)"
DF=$( { echo charges/bin/run-preconditions.sh; echo charges/bin/attest.py; echo charges/bin/attest-t40.py; echo charges/bin/t51-negative.sh; echo leapboundary/bin/t55-negative-tests.sh; } | sort -u | wc -l | tr -d ' ')
WS=$(wc -l < /tmp/T138-census-wrap.txt | tr -d ' ')
WF=$(cut -d: -f1 /tmp/T138-census-wrap.txt | sort -u | wc -l | tr -d ' ')
echo "    direct sites: 5   direct files: $DF"
echo "    wrapper sites: $WS   wrapper files: $WF"
echo "    union of files:"
{ echo charges/bin/run-preconditions.sh; echo charges/bin/attest.py; echo charges/bin/attest-t40.py; echo charges/bin/t51-negative.sh; echo leapboundary/bin/t55-negative-tests.sh; cut -d: -f1 /tmp/T138-census-wrap.txt; } | sort -u > /tmp/T138-census-files.txt
cat /tmp/T138-census-files.txt | sed 's/^/       /'
echo "    ---- DISTINCT FILES: $(wc -l < /tmp/T138-census-files.txt | tr -d ' ')"
echo "    ---- TOTAL SITES:    $((5 + WS))"
