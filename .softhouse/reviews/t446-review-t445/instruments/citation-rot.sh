#!/usr/bin/env bash
# T446: re-measure T445's C-3 claim in the direction T445 swept —
# do the patterns.md:NNNN citations INSIDE conformance.sh still resolve on `main`?
set -u
PAT="$1"     # path to patterns.md as it stands on main
CONF="$2"    # path to conformance.sh as it stands on main
echo "patterns.md line count: $(wc -l < "$PAT")"
echo
echo "cited-line -> what that line actually says, and what the citation CLAIMS:"
echo
LC_ALL=C grep -o 'patterns\.md:[0-9]*' "$CONF" | sort -u | while IFS= read -r c; do
  n="${c##*:}"
  printf '=== %s ===\n' "$c"
  printf '  cited line   : %s\n' "$(sed -n "${n}p" "$PAT" | cut -c1-120)"
  # what does conformance.sh say the citation backs? take the P-number nearest the citation
  printf '  cited FOR    : %s\n' \
    "$(LC_ALL=C grep -o "P-[0-9a-z]*[^\"]\{0,0\}.\{0,60\}patterns\.md:$n" "$CONF" | head -1 | cut -c1-120)"
  # where does that P-number's heading actually live now?
  printf '  +31 line     : %s\n' "$(sed -n "$((n+31))p" "$PAT" | cut -c1-120)"
  echo
done
echo "== headings for the three T445 names them rotted =="
for p in P-45 P-84 P-95 P-80 P-57 P-22 P-35; do
  printf '%-6s heading at line: %s\n' "$p" "$(LC_ALL=C grep -n "^#\{1,6\}.*\b$p\b" "$PAT" | head -2 | tr '\n' ' ')"
done
