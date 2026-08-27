#!/usr/bin/env bash
# T298 — narrow cross-reference: do the LIVE EXECUTABLE SURFACES name any of the 60?
# Surfaces searched (WIDER than T256's four: adds .claude/skills, .claude/*.md, docs/, CLAUDE.md,
# .github, Makefile, package.json, .softhouse/state, .softhouse/tasks.json):
set -u -o pipefail
cd "$1"
LIST="$2"
SURFACES=".softhouse/conformance.sh .softhouse/bin .softhouse/guards .softhouse/launchd .softhouse/tasks.json .softhouse/state .claude docs CLAUDE.md .github Makefile"
EXIST=""
for s in $SURFACES; do
  if [ -e "$s" ]; then EXIST="$EXIST $s"; else echo "SURFACE ABSENT (measured with -e): $s"; fi
done
echo "SURFACES SEARCHED:$EXIST"
echo "---"
n=0
while IFS= read -r p; do
  b="$(basename "$p")"
  hits="$(grep -rn -F -- "$b" $EXIST 2>/dev/null || true)"
  if [ -n "$hits" ]; then
    n=$((n+1))
    echo "HIT $p"
    printf '%s\n' "$hits" | sed 's/^/    /'
  fi
done < "$LIST"
echo "--- ARCHIVED FILES CITED BY A LIVE SURFACE: $n / 60"
