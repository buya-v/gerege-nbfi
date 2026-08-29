#!/usr/bin/env bash
# T446: sweep the repo for conformance.sh:NNNN citations and resolve each of them
# against BOTH main's conformance.sh and the T445 tip's, so a citation that T445
# MOVED is distinguishable from one that was already rotted.
set -u
ROOT="$1"; MAIN="$2"; TIP="$3"
cd "$ROOT" || exit 1
git grep -n -o -E 'conformance\.sh:[0-9]+(-[0-9]+)?' -- . ':!.softhouse/capture' ':!.softhouse/reviews' \
  | sort -u | while IFS= read -r hit; do
  file="${hit%%:*}"
  cit="${hit##*:conformance.sh:}"
  start="${cit%%-*}"
  printf '%s\n' "$hit"
  printf '    main  :%s = %s\n' "$start" "$(sed -n "${start}p" "$MAIN" | cut -c1-100)"
  printf '    tip   :%s = %s\n' "$start" "$(sed -n "${start}p" "$TIP"  | cut -c1-100)"
done
echo
echo "== RESUME.md =="
printf 'grep -c conformance.sh:[0-9] .softhouse/RESUME.md = %s\n' \
  "$(LC_ALL=C grep -c 'conformance\.sh:[0-9]' .softhouse/RESUME.md || true)"
