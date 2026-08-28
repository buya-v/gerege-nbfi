#!/usr/bin/env bash
# T386 -- an INDEPENDENT re-derivation of the counts T381's AUDIT.md asserts, at the SHIPPED
# head rather than at the head the audit was written against.
#
#   bash .softhouse/reviews/t386-review-t381/instruments/t386-status-census.sh <repo> <ref>
#
# T381 claims, for `casualty-sweep.sh`:
#     `set -o pipefail`                      PRESENT at :118, and present on `main` too
#     `2>/dev/null` on an executable line    1 remaining (:127), fail-CLOSED
#     pipelines a fact depends on            4, all read
#     pipelines whose status is discarded    10, each classified
#
# THIS SCRIPT DOES NOT ASSERT THOSE NUMBERS. It enumerates the sites and prints them with line
# numbers, so the reviewer counts them from the printed list rather than from prose. The audit's
# own line numbers were derived at 93e82869 and the file has since grown by 36 lines -- so every
# site after the calibration block moved, and a reader who follows AUDIT.md's numbers into the
# shipped file lands in the wrong place. That is measured here too.
set -uo pipefail
REPO=${1:?usage: <repo-root> <ref>}
REF=${2:?usage: <repo-root> <ref>}
SRC='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'
W=$(mktemp -d "${TMPDIR:-/tmp}/t386-census.XXXXXXXX"); trap 'rm -rf "$W"' EXIT

git -C "$REPO" show "$REF:$SRC" > "$W/head.sh" || exit 2
git -C "$REPO" show "main:$SRC" > "$W/main.sh" || exit 2
git -C "$REPO" show "93e82869:$SRC" > "$W/audit.sh" || exit 2

echo "SHIPPED  $REF  $(wc -l < "$W/head.sh"  | tr -d ' ') lines  sha $(shasum -a 256 < "$W/head.sh"  | cut -c1-16)"
echo "AUDITED  93e82869    $(wc -l < "$W/audit.sh" | tr -d ' ') lines  sha $(shasum -a 256 < "$W/audit.sh" | cut -c1-16)"
echo "MAIN                 $(wc -l < "$W/main.sh"  | tr -d ' ') lines  sha $(shasum -a 256 < "$W/main.sh"  | cut -c1-16)"
echo

# strip comment-only lines and blank lines; keep original numbering
strip() { grep -n '' "$1" | grep -v ':[[:space:]]*#' | grep -v ':[[:space:]]*$'; }

echo '=== 1. `set -o pipefail` ==========================================================='
echo "  SHIPPED : $(grep -n 'set -.*pipefail' "$W/head.sh")"
echo "  MAIN    : $(grep -n 'set -.*pipefail' "$W/main.sh")"
echo "  >>> if MAIN already carries it, then 'pipefail is on' was TRUE while all six fail-opens"
echo "  >>> were live, and greping for pipefail is not a way to learn anything about this file."
echo

echo '=== 2. `2>/dev/null` on an EXECUTABLE line ========================================='
strip "$W/head.sh" | grep '2>/dev/null' || echo "  (none)"
echo

echo '=== 3. every executable line carrying a SHELL PIPE ================================='
echo '    (regex alternation inside single quotes is excluded by hand below; each line is shown'
echo '     so the reader classifies it rather than trusting a count)'
strip "$W/head.sh" | grep -E '\|' | grep -vE "^[0-9]+:(ARCHIVE=|_ere_|CALIB_|sel \")" || true
echo

echo '=== 4. every executable line whose NEXT token reads a status (`; *rc=\$?` or `||`) =='
strip "$W/head.sh" | grep -E '=\$\?|\|\|' || true
echo

echo '=== 5. every COMMAND SUBSTITUTION whose status is NOT read ========================='
echo '    (this is the class AUDIT.md does not have a row for: not a `2>/dev/null`, not a pipe)'
strip "$W/head.sh" | grep -E '\$\(' | grep -vE '=\$\?|\|\|' || true
echo

echo '=== 6. AUDIT.md line numbers vs the SHIPPED file ==================================='
for n in 118 127 193 206 309 339 344 348 356 357 362 368 369 374 375 376; do
  a=$(sed -n "${n}p" "$W/audit.sh" | cut -c1-72)
  h=$(sed -n "${n}p" "$W/head.sh"  | cut -c1-72)
  if [ "$a" = "$h" ]; then m="SAME "; else m="MOVED"; fi
  printf '  :%-4s %s  audit=[%s]\n' "$n" "$m" "$a"
  [ "$m" = "MOVED" ] && printf '            shipped :%-4s =[%s]\n' "$n" "$h"
done
echo
echo '  offset between the two heads, measured:'
echo "    audit  :309 = $(sed -n '309p' "$W/audit.sh" | sed 's/^ *//' | cut -c1-56)"
for n in 343 344 345 346; do
  echo "    shipped:$n = $(sed -n "${n}p" "$W/head.sh" | sed 's/^ *//' | cut -c1-56)"
done
