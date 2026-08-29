#!/bin/bash
# =============================================================================================
# T466 -- DRIVE INSTRUMENT for C-T459-1 (SKIPWT, SMUDGE) and C-T459-2 (LONGNOP).
#
# ATTACKER MODEL, stated because it bounds every claim below: the worker runs the bar in its
# own checkout and publishes the transcript. SKIPWT and SMUDGE both live entirely in LOCAL,
# UNCOMMITTED state -- an index bit and a `.git/info/attributes` line -- so what they forge is
# THE TRANSCRIPT, never the commit. A reader who fetches the commit and hashes it themselves is
# not fooled by either. That bound is preserved verbatim in every finding this instrument
# supports; closing them here raises the cost of a fraudulent transcript and does not make the
# transcript trustworthy on its own.
#
# INVARIANTS THIS INSTRUMENT ENFORCES ON ITSELF:
#   * every real path it plants is ASSEMBLED FROM FRAGMENTS at run time, never spelled as a
#     literal, so a copy of this file adds no row to the dead-path frontier;
#   * an ABSENT or EMPTY bar log is an INSTRUMENT failure (exit 3), never "the bar refused";
#   * the probe line's PRESENCE is counted BEFORE its value is read;
#   * a forgery that is byte-identical to the honest text is an instrument failure, because it
#     would prove nothing and read as a pass;
#   * all scratch lives under $T466_WORK, which must be OUTSIDE the repository.
# =============================================================================================
set -u

SRCREPO="${SRCREPO:?set SRCREPO to the repository to clone}"
WORK="${T466_WORK:?set T466_WORK to a scratch dir OUTSIDE the repository}"
case "$WORK" in
  "$SRCREPO"|"$SRCREPO"/*)
    echo "INSTRUMENT FAILURE: scratch $WORK is INSIDE the repository under test" >&2; exit 3 ;;
esac
ROOT="$WORK/arms"; CWD="$WORK/cwd"
mkdir -p "$ROOT" "$CWD" || exit 3

# ---- path fragments, assembled at run time -------------------------------------------------
SH=".soft""house"
CONF="$SH/conformance"".sh"
CONFLONG="$SH/conformance."$'\xc5\xbf'"h"        # .softhouse/conformance.<U+017F>h
GUARDS="$SH/gua""rds"
UNREG="$GUARDS/zz-t466-unreg"".sh"
WITN="$GUARDS/zz-t466-wit"".txt"
GUARDNAME="guard_harness_text_is_""committed"

arm() { printf '\n================ ARM %s   (base %s)\n' "$1" "$2"; }

# stage <armname> <baseref>  -> echoes the arm dir; $d/src is a fresh clone at <baseref>
stage() {
  # DECLARED ONE PER LINE, not folded onto a single `local`. `local` is a builtin and its
  # arguments are expanded BEFORE any of them is assigned, so `local a="$1" d="$ROOT/$a"`
  # builds $d from whatever `a` meant in the CALLER -- here the arm-loop variable, which
  # happened to hold a usable name and hid the bug. Measured, then fixed.
  local a="$1"
  local base="$2"
  local d="$ROOT/$a"
  rm -rf "$d"; mkdir -p "$d" || exit 3
  git clone -q --no-hardlinks "$SRCREPO" "$d/src" >/dev/null 2>&1 || exit 3
  ( cd "$d/src" && git checkout -q --detach "$base" ) >/dev/null 2>&1 || exit 3
  ( cd "$d/src" && git config user.email t466@example.invalid && git config user.name T466 ) \
    >/dev/null 2>&1 || exit 3
  echo "$d"
}

# plant_unreg <srcdir> -- a checker in the guards dir that nothing invokes, plus a witness
# file that names it. On the honest harness this makes guard_guards_dir_registration REFUSE
# with invoked-by-nothing=1; the forgery below absolves it with a DECLARATION TABLE row.
plant_unreg() {
  local d="$1"
  printf '#!/usr/bin/env bash\n# T466 fixture: a checker nothing invokes.\nexit 0\n' \
    > "$d/$UNREG" || exit 3
  chmod +x "$d/$UNREG"
  printf 'T466 witness. It names zz-t466-unreg%s so a CALLER row can cite it.\n' ".sh" \
    > "$d/$WITN" || exit 3
  ( cd "$d" && git add -- "$UNREG" "$WITN" ) >/dev/null 2>&1 || exit 3
  ( cd "$d" && git commit -q -m "T466 fixture: an unregistered checker" ) >/dev/null 2>&1 || exit 3
}

# forge <dir> <out> <mode> -- build the forged harness text from <dir>'s honest copy.
#   ROW : honest text plus a third DECLARATION TABLE row absolving the planted checker
#   NOP : ROW, plus `return 0` as the first statement of the guard's own body (C-T459-2)
forge() {
  local d="$1" out="$2" mode="$3"
  local row3="zz-t466-unreg.sh|CALLER|$WITN|zz-t466-unreg.sh"
  LC_ALL=C awk -v row="$row3" '
    /^drive-red-ledger-invariants\.sh\|SUBJECT\|/ && /ledgerguard"$/ {
      sub(/ledgerguard"$/, "ledgerguard\n" row "\"")
    } { print }
  ' "$d/$CONF" > "$out" || exit 3
  case "$mode" in
    ROW) : ;;
    NOP)
      LC_ALL=C awk -v g="$GUARDNAME" '
        $0 == g "() {" { print; print "  return 0"; next } { print }' "$out" > "$out.x" \
        && mv "$out.x" "$out" || exit 3 ;;
    *) echo "INSTRUMENT FAILURE: unknown forge mode $mode" >&2; exit 3 ;;
  esac
  if cmp -s "$out" "$d/$CONF"; then
    echo "INSTRUMENT FAILURE: forged text is byte-identical to the honest text" >&2; exit 3
  fi
  if ! LC_ALL=C grep -qF 'zz-t466-unreg.sh|CALLER|' "$out"; then
    echo "INSTRUMENT FAILURE: the forged row is not in the forged text" >&2; exit 3
  fi
}

# runbar <gradeddir> <logfile>
runbar() {
  local g="$1" log="$2" rc=0 n v verdict census
  ( cd "$CWD" && bash "$g/$CONF" ) > "$log" 2>&1 || rc=$?
  if [ ! -s "$log" ]; then
    echo "INSTRUMENT FAILURE: empty bar log $log" >&2; exit 3
  fi
  n="$( LC_ALL=C grep -c 'probe = ' "$log" )"          # PRESENCE first, then value
  v="<no probe line>"
  if [ "$n" -gt 0 ]; then v="$( LC_ALL=C grep -m1 'probe = ' "$log" | sed 's/.*probe = //' )"; fi
  verdict="$( LC_ALL=C grep -m1 '^VERDICT' "$log" | cut -c1-100 )"
  census="$( LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population' "$log" \
             | sed 's/.*population/population/' )"
  printf '    EXIT       = %s\n' "$rc"
  printf '    probe cnt  = %s   (PRESENCE read before value)\n' "$n"
  printf '    probe val  = %s\n' "$v"
  printf '    VERDICT    = %s\n' "${verdict:-<none>}"
  printf '    reg census = %s\n' "${census:-<none>}"
  printf '    --- every HARNESS-TEXT / SUPPRESSION line the run printed:\n'
  LC_ALL=C grep -n 'HARNESS-TEXT\|this harness \|SUPPRESSION\|LOCAL-STATE\|substituted path\|'"$GUARDNAME" \
    "$log" | sed 's/^/      /'
  printf '    --- guard verdict refusals (the "<name> FAILED:" form) and any EXIT 2:\n'
  LC_ALL=C grep -m8 -E 'guard_[a-z_]+ FAILED:|EXIT 2' "$log" | sed 's/^/      ! /'
  return 0
}

# show_local_state <gradeddir> -- the three facts a reader needs to see are LOCAL and UNCOMMITTED
show_local_state() {
  local g="$1"
  echo "    git status --porcelain      : [$( cd "$g" && git status --porcelain | tr '\n' ';' )]"
  echo "    git diff-index --name-only  : [$( cd "$g" && git diff-index --name-only HEAD -- | tr '\n' ';' )]"
  echo "    ls-files -v, entries not H  : [$( cd "$g" && git ls-files -v | grep -v '^H ' | tr '\n' ';' )]"
  echo "    committed HEAD:harness      = $( cd "$g" && git rev-parse "HEAD:$CONF" )"
  echo "    hash-object (DEFAULT)       = $( cd "$g" && git hash-object -- "$CONF" )"
  echo "    hash-object --no-filters    = $( cd "$g" && git hash-object --no-filters -- "$CONF" )"
}
