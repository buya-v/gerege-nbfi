#!/bin/sh
set -u
cd /tmp/t135/missprobe || exit 9
echo "--- the probe's own behaviour on EMPTY input (every line printed is a vacuous pass):"
sh probe.sh
echo
echo "--- T99b sweep grep-3 pattern A (count-compared-to-0):"
LC_ALL=C grep -nE 'grep -[a-zA-Z]*c[a-zA-Z]*( |$)|wc -l' probe.sh || echo "  (no hits)"
echo
echo "--- T99b sweep pattern B (absence assertions):"
LC_ALL=C grep -nE '\[ "\$[a-z_]+" = "?0"? \]|\[ -z "\$[a-z_]+" \]' probe.sh || echo "  (no hits)"
