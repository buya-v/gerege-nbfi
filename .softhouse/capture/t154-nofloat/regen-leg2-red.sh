#!/usr/bin/env bash
# Regenerate out/leg2-RED-before-fix.txt from the PINNED pre-fix bytes, by making
# the POST arm the pre-fix tree. Every POST row then reports the state T154 leg 2
# exists to end: a float literal that builds, passes the guard, and takes
# conformance to exit 0. Reads a literal immutable sha, never a ref (P-24).
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
T154_POST_REV=187e9726dfad5076f4b68877f411d7d218280889 \
  bash "$SCRIPT_DIR/drive-leg2.sh" > "$SCRIPT_DIR/out/leg2-RED-before-fix.txt" 2>&1
echo "drive-leg2.sh with the POST arm pinned to the PRE-FIX bytes exited $? (nonzero is the point)"
echo "wrote $SCRIPT_DIR/out/leg2-RED-before-fix.txt"
