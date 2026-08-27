#!/bin/sh
# T135 — does T99b's widened sweep pattern catch the three F-5 sites, and what else does it miss?
# Run from a SCRIPT, so `grep` is /usr/bin/grep (BSD grep) — P-33.
set -u
cd "$1" || exit 9
echo "grep in force: $(type -a grep 2>&1 | head -1)"
echo "binary: $(command -v grep)  version: $(grep --version 2>&1 | head -1)"
echo
echo "=== A. T99b widened pattern, greps-3 line 66, over MAIN's t36/preconditions.sh"
LC_ALL=C grep -nE 'grep -[a-zA-Z]*c[a-zA-Z]*( |$)|wc -l' t36/preconditions.sh
echo
echo "=== B. T99b absence-assertion pattern, line 70"
LC_ALL=C grep -nE '\[ "\$[a-z_]+" = "?0"? \]|\[ -z "\$[a-z_]+" \]' t36/preconditions.sh
echo
echo "=== C. T99's ORIGINAL pattern (grep -c | grep -ac | wc -l) for comparison"
LC_ALL=C grep -nE 'grep -c|grep -ac|wc -l' t36/preconditions.sh
