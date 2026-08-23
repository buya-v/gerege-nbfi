#!/usr/bin/env bash
# T300 — drive the CANNOT-CATCH size derivation, both directions.
#
# The guard now prints "the full $cc-line block" with $cc read from main.go instead of the
# literal 33 that had been typed there. Two arms, because a derivation only proved in the
# direction that works is half a proof (P-57 rule 3 — "a presence check must itself be driven
# red both ways"):
#   GREEN — against the real main.go, the expression must return the const's true size.
#   RED   — against a copy whose const is RENAMED, it must return < 2, which is what makes the
#           guard print the words "line count NOT DERIVABLE" instead of a guessed number.
# The RED arm runs on a COPY in scratch this script owns and removes, so nothing in the tree
# is touched and no literal shared-temp path is assigned to a name (the shape the host-state
# census refuses).
set -u

ROOT="$(git rev-parse --show-toplevel)"
SRC="$ROOT/.softhouse/guards/ledgerguard/main.go"
EXPR='/^const cannotCatch = `/,/`$/p'

green="$(LC_ALL=C sed -n "$EXPR" "$SRC" | LC_ALL=C grep -ac '')"
echo "GREEN arm — subject: .softhouse/guards/ledgerguard/main.go"
echo "  selector : sed -n '$EXPR' | grep -ac ''"
echo "  derived  : $green"

D="$(mktemp -d "${TMPDIR:-/tmp}/t300-cc.XXXXXXXXXX")"
trap 'rm -rf "$D"' EXIT INT TERM HUP
LC_ALL=C sed 's/^const cannotCatch = `/const somethingElseEntirely = `/' "$SRC" >"$D/main.go"
if LC_ALL=C grep -qF 'const cannotCatch = `' "$D/main.go"; then
  echo "REFUSED: the rename mutation did not apply; the RED arm would be vacuous." >&2
  exit 1
fi
red="$(LC_ALL=C sed -n "$EXPR" "$D/main.go" | LC_ALL=C grep -ac '')"
echo "RED arm — same selector, const renamed in a scratch copy"
echo "  derived  : $red   (< 2 => the guard prints 'line count NOT DERIVABLE' and warns on stderr)"

ok=1
[ "$green" -gt 2 ] || ok=0
[ "$red" -lt 2 ]   || ok=0
if [ "$ok" = 1 ]; then
  echo "RESULT: BOTH ARMS AS CLAIMED (green $green, red $red)."
  exit 0
fi
echo "RESULT: NOT AS CLAIMED (green $green, red $red)." >&2
exit 1
