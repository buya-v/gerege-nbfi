#!/bin/sh
set -u
S=/tmp/t135/charges/run/preconditions.sh
P=/tmp/t135/f5/main/.softhouse/capture/pathb/t36/preconditions.sh
MUT=/tmp/t135/f2/mutated.json

echo "=== ATTACK 2 (LIVE, tenant gerege) — T77's tautology: the mutated request is NOT a"
echo "    half-minor-unit tie, so it answers 20925.05 under HALF_UP *and* HALF_EVEN and"
echo "    certifies nothing.  The charges copy has no digest pin to stop it."
for pair in "charges:$S" "pathb-hardened:$P"; do
  lbl=${pair%%:*}; f=${pair#*:}
  CANARY_REQ=$MUT sh "$f" gerege > /tmp/t135/charges/b-$lbl.out 2> /tmp/t135/charges/b-$lbl.err
  echo "  --- $lbl  EXIT=$?"
  cat /tmp/t135/charges/b-$lbl.out /tmp/t135/charges/b-$lbl.err \
    | grep -E 'effective rounding mode canary|DIGEST|ALL PRECONDITIONS|BREACHED' | cut -c1-165 | sed 's/^/      /'
done

echo
echo "=== ATTACK 1 (stub curl, so this is a statement about the GUARD, not about the oracle)"
echo "    A curl that answers 20925.04 — what a HALF_EVEN process returns — plus"
echo "    CANARY_EXPECT=20925.04 supplied by the runner."
mkdir -p /tmp/t135/charges/stub
cat > /tmp/t135/charges/stub/curl <<'EOF'
#!/bin/sh
case "$*" in
  *actuator/health*) printf '{"status":"UP"}' ; exit 0 ;;
  *calculateLoanSchedule*) printf '{"periods":[{"interestOriginalDue":20925.04}]}\n200' ; exit 0 ;;
esac
exit 1
EOF
chmod +x /tmp/t135/charges/stub/curl
for pair in "charges:$S" "pathb-hardened:$P"; do
  lbl=${pair%%:*}; f=${pair#*:}
  PATH=/tmp/t135/charges/stub:$PATH CANARY_EXPECT=20925.04 \
    CANARY_REQ=/tmp/t135/f5/main/.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json \
    sh "$f" gerege > /tmp/t135/charges/c-$lbl.out 2> /tmp/t135/charges/c-$lbl.err
  echo "  --- $lbl  EXIT=$?"
  cat /tmp/t135/charges/c-$lbl.out /tmp/t135/charges/c-$lbl.err \
    | grep -E 'effective rounding mode canary|CANARY_EXPECT was set' | cut -c1-165 | sed 's/^/      /'
done
