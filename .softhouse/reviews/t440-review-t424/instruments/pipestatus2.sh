#!/usr/bin/env bash
# T440: what status does bash actually exit with when set -u kills it on PIPESTATUS[1]?
echo "bash: $BASH_VERSION"
cat > /tmp/t440/def.sh <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
sh -c "exit 7" | sh -c "exit 0"
x=${PIPESTATUS[0]}
y=${PIPESTATUS[1]}
echo "REACHED THE END x=$x y=$y"
exit 0
EOF
rc=0; bash /tmp/t440/def.sh >/dev/null 2>&1 || rc=$?
echo "  script file, invoked as \`bash def.sh\`      -> exit $rc"
rc=0; bash -c 'set -uo pipefail
sh -c "exit 7" | sh -c "exit 0"
x=${PIPESTATUS[0]}
y=${PIPESTATUS[1]}
echo end' >/dev/null 2>&1 || rc=$?
echo "  same body via \`bash -c\`                    -> exit $rc"

# a plain unbound variable, for comparison
cat > /tmp/t440/def2.sh <<'EOF'
#!/usr/bin/env bash
set -u
echo "$NOPE_NOT_SET"
exit 0
EOF
rc=0; bash /tmp/t440/def2.sh >/dev/null 2>&1 || rc=$?
echo "  plain unbound variable in a script file    -> exit $rc"

# and the healthy control: what a REAL caught-failing-arm looks like
cat > /tmp/t440/good.sh <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
exit 1
EOF
rc=0; bash /tmp/t440/good.sh >/dev/null 2>&1 || rc=$?
echo "  a genuine 'caught a failing arm'           -> exit $rc"
