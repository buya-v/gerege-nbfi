#!/bin/bash
# =============================================================================================
# T459 -- INDEPENDENT DRIVE INSTRUMENT for the review of T454.
#
# Every path this script plants is ASSEMBLED AT RUN TIME from fragments, never spelled as a
# literal, so that a copy of this file committed under the reviews tree adds NO row to the
# dead-path frontier.  (The reflex that has refused seven first bars this fire.)
#
# INVARIANTS THIS INSTRUMENT ENFORCES ON ITSELF:
#   * an ABSENT or EMPTY bar log is an INSTRUMENT failure (exit 3), never "the bar refused";
#   * the probe line's PRESENCE is counted BEFORE its value is read (P-84);
#   * every arm re-clones after planting, so the collision materialises the way a fresh
#     checkout would, and no `git add -A` is ever run after a --cacheinfo plant.
# =============================================================================================
set -u

SRCREPO="${SRCREPO:?set SRCREPO to the repository to clone}"
WORK="${T459_WORK:-/tmp/t459}"
ROOT="$WORK/arms"
CWD="$WORK/cwd"
mkdir -p "$ROOT" "$CWD"

# ---- path fragments, assembled at run time -------------------------------------------------
SH=".soft""house"                       # .softhouse
CONF="$SH/conformance"".sh"             # .softhouse/conformance.sh
CONFLONG="$SH/conformance."$'\xc5\xbf'"h"   # .softhouse/conformance.<U+017F>h
GUARDS="$SH/gua""rds"                   # .softhouse/guards
UNREG="$GUARDS/zz-t459-unreg"".sh"
WIT="$GUARDS/zz-t459-wit"".txt"

arm() { printf '\n=== ARM %s  (base %s)\n' "$1" "$2"; }

# plant_unreg <srcdir>  -- an unregistered checker plus a witness that names it
plant_unreg() {
  local d="$1"
  printf '#!/usr/bin/env bash\n# T459 fixture: a checker nothing invokes.\nexit 0\n' > "$d/$UNREG"
  chmod +x "$d/$UNREG"
  printf 'T459 witness. It names zz-t459-unreg%s so a CALLER row can cite it.\n' ".sh" > "$d/$WIT"
  ( cd "$d" && git add -- "$UNREG" "$WIT" ) >/dev/null 2>&1
}

# forge <srcdir> <outfile> <mode>  -- build the forged harness text
#   mode ROW      : honest text + a third DECLARATION TABLE row absolving the planted checker
#   mode STRIP    : ROW, minus the timed_guard wiring AND the GUARD_COST_BUDGETS row
#   mode STRIP1   : ROW, minus the timed_guard wiring only
#   mode NOP      : ROW, plus `return 0` as the first statement of the guard's own body
forge() {
  local d="$1"; local out="$2"; local mode="$3"
  local G="guard_harness_text_is_""committed"
  local ROW3="zz-t459-unreg.sh|CALLER|$WIT|zz-t459-unreg.sh"
  # the third row goes inside the DECLARED here-string, before its closing quote
  LC_ALL=C awk -v row="$ROW3" '
    /^drive-red-ledger-invariants\.sh\|SUBJECT\|/ && /ledgerguard"$/ {
      sub(/ledgerguard"$/, "ledgerguard\n" row "\"")
    } { print }
  ' "$d/$CONF" > "$out"
  case "$mode" in
    ROW) : ;;
    STRIP)
      LC_ALL=C grep -v -e "timed_guard $G" -e "^$G|60" "$out" > "$out.x" && mv "$out.x" "$out" ;;
    STRIP1)
      LC_ALL=C grep -v -e "timed_guard $G" "$out" > "$out.x" && mv "$out.x" "$out" ;;
    NOP)
      LC_ALL=C awk -v g="$G" '
        $0 == g "() {" { print; print "  return 0"; next } { print }' "$out" > "$out.x" && mv "$out.x" "$out" ;;
    *) echo "forge: unknown mode $mode" >&2; exit 3 ;;
  esac
  # the forgery must actually differ from the honest text, or the arm proves nothing
  if cmp -s "$out" "$d/$CONF"; then echo "forge: forged text is identical to honest text" >&2; exit 3; fi
}

# collide <srcdir> <forgedfile> -- add ONE extra index entry at the U+017F spelling
collide() {
  local d="$1"; local f="$2"; local blob
  blob="$( cd "$d" && git hash-object -w --stdin < "$f" )" || exit 3
  [ -n "$blob" ] || exit 3
  ( cd "$d" && git update-index --add --cacheinfo "100755,$blob,$CONFLONG" ) || exit 3
  echo "    planted colliding entry, forged blob $blob"
}

# runbar <gradeddir> <logfile>
runbar() {
  local g="$1"; local log="$2"; local rc=0
  ( cd "$CWD" && bash "$g/$CONF" ) > "$log" 2>&1 || rc=$?
  if [ ! -s "$log" ]; then echo "INSTRUMENT FAILURE: empty bar log $log" >&2; exit 3; fi
  local n v verdict census harness
  n="$( LC_ALL=C grep -c 'probe = ' "$log" )"          # PRESENCE first (P-84)
  v="-"; [ "$n" -gt 0 ] && v="$( LC_ALL=C grep -m1 'probe = ' "$log" | sed 's/.*probe = //' )"
  verdict="$( LC_ALL=C grep -m1 '^VERDICT' "$log" | cut -c1-96 )"
  census="$( LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population' "$log" | sed 's/.*population/population/' )"
  harness="$( LC_ALL=C grep -m1 'HARNESS-TEXT: \|substituted path' "$log" | sed 's/^conformance: *//' )"
  printf '    EXIT      = %s\n' "$rc"
  printf '    probe cnt = %s   (PRESENCE read before value)\n' "$n"
  printf '    probe val = %s\n' "$v"
  printf '    VERDICT   = %s\n' "${verdict:-<none>}"
  printf '    census    = %s\n' "${census:-<none>}"
  printf '    harness   = %s\n' "${harness:-<none>}"
  LC_ALL=C grep -m3 'FAILED:\|REFUSED' "$log" | sed 's/^/    ! /'
  return 0
}

# stage <arm> <baseref>  -> echoes the graded dir
stage() {
  local a="$1"; local base="$2"; local d="$ROOT/$a-$base"
  rm -rf "$d"; mkdir -p "$d"
  git clone -q --no-hardlinks "$SRCREPO" "$d/src" >/dev/null 2>&1 || exit 3
  ( cd "$d/src" && git checkout -q "$base" ) >/dev/null 2>&1 || exit 3
  ( cd "$d/src" && git config user.email t459@example.invalid && git config user.name T459 ) >/dev/null 2>&1
  echo "$d"
}

reclone() {
  local d="$1"
  ( cd "$d/src" && git commit -q --allow-empty -m "T459 fixture" ) >/dev/null 2>&1 || exit 3
  rm -rf "$d/graded"
  git clone -q --no-hardlinks "$d/src" "$d/graded" 2>"$d/clone.err" || exit 3
  if [ -s "$d/clone.err" ]; then sed 's/^/    clone-stderr: /' "$d/clone.err"; fi
  echo "    committed HEAD:$CONF = $( cd "$d/graded" && git rev-parse "HEAD:$CONF" )"
  echo "    materialised at path = $( cd "$d/graded" && git hash-object -- "$CONF" )"
  echo "    git status --porcelain of the graded clone:"
  ( cd "$d/graded" && git status --porcelain ) | head -5 | sed 's/^/      /'
}
