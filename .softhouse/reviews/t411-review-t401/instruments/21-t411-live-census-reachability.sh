#!/usr/bin/env bash
# T411 item 3, part 2: of the extension-shaped selectors found by instrument 20,
# WHICH ARE LIVE -- i.e. reachable from `bash .softhouse/conformance.sh`?
#
# A dormant selector in a closed task's grant is not a census gap; nothing grades
# it. The gap only matters where a PINNED bar figure depends on the corpus.
#
# Reachability is computed as: conformance.sh, plus everything conformance.sh
# names as an executable path, plus everything THOSE name, to fixpoint.
set -uo pipefail
GREP=/usr/bin/grep
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT" || exit 9

W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
echo ".softhouse/conformance.sh" > "$W/frontier"
: > "$W/seen"

round=0
while [ -s "$W/frontier" ]; do
  round=$((round+1)); [ "$round" -gt 12 ] && break
  : > "$W/next"
  while read -r f; do
    $GREP -qxF "$f" "$W/seen" && continue
    echo "$f" >> "$W/seen"
    [ -f "$f" ] || continue
    # any .softhouse-rooted .py/.sh literal mentioned in this file
    $GREP -ohE '\.softhouse/[A-Za-z0-9_./-]+\.(py|sh)' "$f" 2>/dev/null | sort -u >> "$W/next"
  done < "$W/frontier"
  sort -u "$W/next" | while read -r c; do [ -f "$c" ] && echo "$c"; done > "$W/frontier"
done

sort -u "$W/seen" | while read -r f; do [ -f "$f" ] && echo "$f"; done > "$W/reach"
echo "REACHABLE from conformance.sh (transitive path-literal closure): $(wc -l < "$W/reach" | tr -d ' ') files"
echo
cat "$W/reach" | sed 's/^/  /'
echo
echo "=================================================================="
echo "OF THOSE, WHICH BUILD A CORPUS FROM FILE EXTENSIONS?"
echo "=================================================================="
while read -r f; do
  hits="$($GREP -nE "endswith\(\(|ls-files[^|]*\*\.|ls-files[^|]*['\"]\.softhouse/\*|git grep .*-- *'\*\.|:\(glob\)|--include=?'?\*\." "$f" 2>/dev/null \
          | $GREP -E "\.(sh|py|go|zsh|bash|java|md|json|disposable)" || true)"
  [ -n "$hits" ] && { echo; echo "### $f"; printf '%s\n' "$hits" | sed 's/^/    /'; }
done < "$W/reach"
echo
echo "=================================================================="
echo "REACHES .zsh?  (a selector naming zsh anywhere in the reachable set)"
echo "=================================================================="
# The negative here is the WHOLE POINT of this section, so it may not be printed on
# the strength of a grep exit status -- that is the C2 fail-open this very repo lints
# for, and the T238 linter caught this line in its first draft. Materialise the result,
# assert the corpus was non-empty, and report the COUNT.
: > "$W/zsh.hits"
while read -r f; do
  $GREP -nE "zsh" "$f" 2>/dev/null | sed "s|^|$f:|" >> "$W/zsh.raw" || true
done < "$W/reach"
[ -s "$W/reach" ] || { echo "REFUSE: the reachable set is EMPTY -- that is a selector failure, not a clean result."; exit 2; }
$GREP -E "endswith|ls-files|git grep|--include|glob" "$W/zsh.raw" > "$W/zsh.hits" 2>/dev/null || true
NZ="$($GREP -c . "$W/zsh.hits" 2>/dev/null || echo 0)"
echo "  reachable files searched : $($GREP -c . "$W/reach")"
echo "  selector lines naming zsh: $NZ"
[ "$NZ" -gt 0 ] && sed 's/^/    /' "$W/zsh.hits"
echo "  => $( [ "$NZ" -eq 0 ] && echo 'NO reachable selector names .zsh' || echo 'at least one reachable selector names .zsh' )"
