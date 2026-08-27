#!/usr/bin/env bash
# Regenerate out/leg1-RED-before-fix.txt from the PINNED pre-fix bytes.
#
# It runs drive-leg1.sh with the file UNDER TEST pointed at the pre-fix
# extraction, so PRE and POST are the same bytes and every POST row reports the
# state T154 leg 1 exists to end. Re-runnable forever; it reads a literal
# immutable sha and nothing that can follow `main` (P-24).
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SHA=187e9726dfad5076f4b68877f411d7d218280889
TMP="$(mktemp -d -t t154-regen)"; trap 'rm -rf "$TMP"' EXIT
( cd "$REPO_ROOT" && git show "$SHA:.softhouse/conformance.sh" ) > "$TMP/prefix-conformance.sh"
T154_CONF_UNDER_TEST="$TMP/prefix-conformance.sh" \
  bash "$SCRIPT_DIR/drive-leg1.sh" > "$SCRIPT_DIR/out/leg1-RED-before-fix.txt" 2>&1
echo "drive-leg1.sh against the PRE-FIX bytes exited $? (nonzero is the point)"
echo "wrote $SCRIPT_DIR/out/leg1-RED-before-fix.txt"
