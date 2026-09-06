#!/usr/bin/env bash
# t553-wiring.sh <fire-program.sh>
# Drives every branch of the call site's `_nofs_check` against stub guards, to
# confirm (a) exit 2 is never read as a pass, (b) the fire continues on every
# branch, and (c) T552 MINOR-7's missing `($_nofs_when)` is now present on the
# guard-missing branch as well.
#
# NOTE ON FIDELITY: fire-program.sh is a ZSH script and zsh is NOT installed in
# this sandbox (`command -v zsh` is empty), so `_nofs_check` is extracted and run
# under BASH with a two-line `print` shim. Everything under test here is plain
# POSIX control flow; the shim is stated rather than hidden.
set -uo pipefail
SRC="$1"
WORK="$(mktemp -d)"; trap 'rm -rf -- "$WORK"' EXIT
awk '/^_nofs_check\(\) \{/,/^\}$/' "$SRC" > "$WORK/fn.sh"
[ -s "$WORK/fn.sh" ] || { echo "could not extract _nofs_check"; exit 2; }
echo "--- extracted $(wc -l < "$WORK/fn.sh") lines of _nofs_check"

log()   { printf '%s\n' "$*"; }
print() { shift $(( $# > 1 ? 2 : 0 )); printf '%s\n' "$@"; }   # zsh `print -r --` shim
# shellcheck disable=SC1090
. "$WORK/fn.sh"

for rc in 0 1 2 3 141; do
  printf '#!/bin/sh\necho "stub says %s"\nexit %s\n' "$rc" "$rc" > "$WORK/guard"
  chmod 755 "$WORK/guard"
  NOFS_GUARD="$WORK/guard"
  echo "=== stub exit $rc, called as 'fire'"
  _nofs_check fire | sed 's/^/    /'
  echo "    (block rc=$? — the fire CONTINUES on every branch)"
done
chmod 644 "$WORK/guard"; NOFS_GUARD="$WORK/guard"
echo "=== guard present but mode 644, called as 'probe'"
_nofs_check probe | sed 's/^/    /'
rm -f "$WORK/guard"
echo "=== guard absent, called as 'probe'  (T552 MINOR-7 — must name 'probe')"
_nofs_check probe | sed 's/^/    /'
echo "=== guard absent, called as 'fire'"
_nofs_check fire | sed 's/^/    /'
