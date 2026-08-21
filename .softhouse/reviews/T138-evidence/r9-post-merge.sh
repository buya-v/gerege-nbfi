#!/bin/sh
# T138 — P-24 step 2: re-run the ARTEFACTS on the merged tree, not just conformance.
# That is what caught T98's relocated time bomb, so it is a standing step.
set -u
D=/tmp/T138-merge
MAIN=bcf2c55b57a244e2eb773094c1aa7109ca1b58a1
cd "$D" || exit 2
echo "merged head $(git rev-parse HEAD)   over main $MAIN"
echo

echo "=== blob identity for the frozen surfaces (correct paths)"
for f in .softhouse/vectors/PIN.json .softhouse/vectors/capabilities.json \
         nexus/internal/apps/loanschedule/contract/contract.go \
         .softhouse/conformance.sh .softhouse/gates.md .softhouse/tasks.json; do
  a=$(git rev-parse "$MAIN:$f" 2>/dev/null || echo ABSENT)
  b=$(git rev-parse "HEAD:$f" 2>/dev/null || echo ABSENT)
  s='*** DIFFERS ***'; [ "$a" = "$b" ] && s=IDENTICAL
  printf '   %-60s %s  %s\n' "$f" "$(echo "$a" | cut -c1-12)" "$s"
done
echo

echo "=== ARTEFACT 1/5: prove-guards.sh on the MERGED tree"
sh .softhouse/capture/t91/prove-guards.sh > /tmp/T138-pm-guards.txt 2>&1
echo "   exit=$?"
LC_ALL=C grep -aE 'NOT AS EXPECTED|done —' /tmp/T138-pm-guards.txt | sed 's/^/   /'
LC_ALL=C grep -ac 'OK      \[' /tmp/T138-pm-guards.txt | sed 's/^/   legs OK: /'
echo

echo "=== ARTEFACT 2/5: t115-drive-mf1.sh on the MERGED tree"
sh .softhouse/capture/t91/t115-drive-mf1.sh > /tmp/T138-pm-mf1.txt 2>&1
echo "   exit=$?"
tail -4 /tmp/T138-pm-mf1.txt | sed 's/^/   /'
echo

echo "=== ARTEFACT 3/5: t115-drive-mf2.sh on the MERGED tree"
sh .softhouse/capture/t91/t115-drive-mf2.sh > /tmp/T138-pm-mf2.txt 2>&1
echo "   exit=$?"
tail -6 /tmp/T138-pm-mf2.txt | sed 's/^/   /'
LC_ALL=C grep -aiE 'N9|N10|STILL ADMIT' /tmp/T138-pm-mf2.txt | head -12 | sed 's/^/   /'
echo

echo "=== ARTEFACT 4/5: t115-drive-mf3-mf4.sh on the MERGED tree"
sh .softhouse/capture/t91/t115-drive-mf3-mf4.sh > /tmp/T138-pm-mf34.txt 2>&1
echo "   exit=$?"
LC_ALL=C grep -aE 'delta|DISTINCT FILES|TOTAL|20|23' /tmp/T138-pm-mf34.txt | tail -12 | sed 's/^/   /'
echo

echo "=== ARTEFACT 5/5: t115-rerun-attacks.sh on the MERGED tree"
sh .softhouse/capture/t91/t115-rerun-attacks.sh > /tmp/T138-pm-attacks.txt 2>&1
echo "   exit=$?"
tail -20 /tmp/T138-pm-attacks.txt | sed 's/^/   /'
