#!/bin/zsh
# T346 F-1 probe. Isolates the two fail-opens my census found SURVIVING on T342's branch:
# `released_at` whose value is a JSON STRING that is not a timestamp. The parser accepts
# any non-empty string, arm 1 fires on it, and a LIVE lock reads FREE.
# usage: t346-stringy-null.zsh <path-to-fire-program.sh>
emulate -L zsh
set -uo pipefail
FP="$1"
S="$(mktemp -d)"; mkdir -p "$S/.softhouse"
H="$(hostname -s)"; N="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
sleep 300 & L=$!
trap "kill $L 2>/dev/null; rm -rf $S" EXIT
print -r -- "file=$FP  host=$H  LIVE pid=$L  started_at=$N (fresh)"
print -r -- "Correct answer for every row: HELD-* . FREE-released here = a LIVE lock declared free."
print -r -- ""
for v in 'null' '"2026-08-28T06:00:00Z"' '"null"' '"None"' '"NULL"' '" "' '"   "' '"false"' '"0"' '"no"' '"-"' '"pending"' '""'; do
  printf '{"host": "%s", "pid": %s, "started_at": "%s", "released_at": %s}' "$H" "$L" "$N" "$v" > "$S/.softhouse/LOCK"
  printf '  released_at=%-24s -> %s\n' "$v" "$(GEREGE_NBFI_REPO=$S zsh "$FP" --lock-signals 2>&1 | grep '^verdict')"
done
