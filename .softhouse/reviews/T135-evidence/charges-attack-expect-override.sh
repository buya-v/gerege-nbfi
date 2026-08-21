#!/bin/sh
set -u
S=/tmp/t135/charges/run/preconditions.sh
P=/tmp/t135/f5/main/.softhouse/capture/pathb/t36/preconditions.sh
cat > /tmp/t135/charges/stub/curl <<'EOF'
#!/bin/sh
case "$*" in
  *actuator/health*) printf '{"status":"UP"}' ; exit 0 ;;
  *calculateLoanSchedule*) printf '{"a":1,"interestOriginalDue":20925.04,"b":2}\n200\n' ; exit 0 ;;
esac
exit 1
EOF
chmod +x /tmp/t135/charges/stub/curl
echo "A HALF_EVEN answer (20925.04) + CANARY_EXPECT=20925.04 supplied by the runner:"
for pair in "charges:$S" "pathb-hardened:$P"; do
  lbl=${pair%%:*}; f=${pair#*:}
  PATH=/tmp/t135/charges/stub:$PATH CANARY_EXPECT=20925.04 \
    CANARY_REQ=/tmp/t135/f5/main/.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json \
    sh "$f" gerege > /tmp/t135/charges/d-$lbl.out 2> /tmp/t135/charges/d-$lbl.err
  echo "  --- $lbl  EXIT=$?"
  cat /tmp/t135/charges/d-$lbl.out /tmp/t135/charges/d-$lbl.err \
    | grep -E 'rounding mode canary|rounding-mode canary|CANARY_EXPECT was set' | cut -c1-165 | sed 's/^/      /'
done
