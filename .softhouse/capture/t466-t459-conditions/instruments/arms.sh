#!/bin/bash
# =============================================================================================
# T466 -- the arms.  Usage:  arms.sh <baseref> <armname> [<armname> ...]
#
#   CTL      unmutated clone of <baseref>. The control: nothing planted, nothing suppressed.
#   CTLUNREG the planted checker COMMITTED, honest harness. Must REFUSE, or the forgeries
#            below prove nothing -- they are only interesting because the honest tree says no.
#   SKIPWT   --skip-worktree suppresses git's working-tree comparison; forged harness on disk.
#   ASSUME   --assume-unchanged, the same route by the other bit.
#   SMUDGE   a `filter=` attribute in .git/info/attributes (NEVER committed) with an inverting
#            `clean` half, so `git hash-object` returns the HONEST id over FORGED bytes.
#   LONGNOP  one inserted line -- `return 0` atop the guard's own body -- carried in on a
#            U+017F checkout collision. C-T459-2's eighth route.
#   WDIRTY   an HONEST uncommitted edit. Must still be ACCEPTED and NAMED; a fix that refuses
#            this makes the bar unusable during development, which is the same as switching
#            it off.
# =============================================================================================
set -u
. "$( cd "$( dirname "$0" )" && pwd )/drive.sh"

BASE="${1:?usage: arms.sh <baseref> <arm> [...]}"; shift

run_ctl() {
  arm "CTL-$BASE" "$BASE"
  local d; d="$( stage "CTL-$BASE" "$BASE" )" || exit 3
  ( cd "$d/src" && git commit -q --allow-empty -m "T466 CTL" ) >/dev/null 2>&1 || exit 3
  git clone -q --no-hardlinks "$d/src" "$d/graded" >/dev/null 2>&1 || exit 3
  show_local_state "$d/graded"
  runbar "$d/graded" "$d/bar.log"
}

run_ctlunreg() {
  arm "CTLUNREG-$BASE" "$BASE"
  local d; d="$( stage "CTLUNREG-$BASE" "$BASE" )" || exit 3
  plant_unreg "$d/src"
  git clone -q --no-hardlinks "$d/src" "$d/graded" >/dev/null 2>&1 || exit 3
  show_local_state "$d/graded"
  runbar "$d/graded" "$d/bar.log"
}

# $1 = skip-worktree | assume-unchanged
run_bit() {
  local bit="$1"
  arm "BIT-$bit-$BASE" "$BASE"
  local d; d="$( stage "BIT-$bit-$BASE" "$BASE" )" || exit 3
  plant_unreg "$d/src"
  git clone -q --no-hardlinks "$d/src" "$d/graded" >/dev/null 2>&1 || exit 3
  local g="$d/graded"
  echo "    BEFORE the bit is set:"; show_local_state "$g"
  ( cd "$g" && git update-index "--$bit" -- "$CONF" ) || exit 3
  forge "$g" "$d/forged.txt" ROW
  cp "$d/forged.txt" "$g/$CONF" || exit 3
  echo "    AFTER  the bit is set and the forged text is on disk:"; show_local_state "$g"
  runbar "$g" "$d/bar.log"
}

run_smudge() {
  arm "SMUDGE-$BASE" "$BASE"
  local d; d="$( stage "SMUDGE-$BASE" "$BASE" )" || exit 3
  plant_unreg "$d/src"
  git clone -q --no-hardlinks "$d/src" "$d/graded" >/dev/null 2>&1 || exit 3
  local g="$d/graded"
  cp "$g/$CONF" "$d/honest.txt" || exit 3
  forge "$g" "$d/forged.txt" ROW
  # A PERFECTLY INVERTING PAIR, and both halves are needed. The CLEAN half is what defeats
  # `git hash-object`; the SMUDGE half is what lets the file be MATERIALISED BY CHECKOUT, so
  # git records stat data that MATCHES and `git status` stays empty. Copying the forged bytes
  # in by hand leaves the entry stat-dirty and status reports ` M` -- the weaker construction,
  # measured first and recorded in this instrument's evidence. stdin is consumed before either
  # half writes, so no filter dies of SIGPIPE and turns a forgery arm into a crash arm.
  printf '#!/bin/bash\ncat >/dev/null\ncat %s\n' "$d/honest.txt" > "$d/clean.sh" || exit 3
  printf '#!/bin/bash\ncat >/dev/null\ncat %s\n' "$d/forged.txt" > "$d/smudge.sh" || exit 3
  chmod +x "$d/clean.sh" "$d/smudge.sh"
  ( cd "$g" && git config "filter.t466.clean" "$d/clean.sh" ) || exit 3
  ( cd "$g" && git config "filter.t466.smudge" "$d/smudge.sh" ) || exit 3
  printf '%s filter=t466\n' "$CONF" > "$g/.git/info/attributes" || exit 3
  rm -f "$g/$CONF" || exit 3
  ( cd "$g" && git checkout -- "$CONF" ) || exit 3
  echo "    absolving row present in the bytes on disk: $( LC_ALL=C grep -c 'zz-t466-unreg.sh|CALLER' "$g/$CONF" )"
  echo "    .git/info/attributes (LOCAL, NEVER COMMITTED):"
  sed 's/^/      /' "$g/.git/info/attributes"
  echo "    is that file tracked?  [$( cd "$g" && git ls-files -- '.git/info/attributes' )] (empty = no)"
  show_local_state "$g"
  runbar "$g" "$d/bar.log"
}

run_longnop() {
  arm "LONGNOP-$BASE" "$BASE"
  local d; d="$( stage "LONGNOP-$BASE" "$BASE" )" || exit 3
  plant_unreg "$d/src"
  forge "$d/src" "$d/forged.txt" NOP
  echo "    diff size of the forgery against the honest text:"
  diff "$d/src/$CONF" "$d/forged.txt" | sed 's/^/      /'
  local blob
  blob="$( cd "$d/src" && git hash-object -w --stdin < "$d/forged.txt" )" || exit 3
  [ -n "$blob" ] || exit 3
  ( cd "$d/src" && git update-index --add --cacheinfo "100755,$blob,$CONFLONG" ) || exit 3
  ( cd "$d/src" && git commit -q -m "T466 LONGNOP: one colliding index entry" ) >/dev/null 2>&1 \
    || exit 3
  git clone -q --no-hardlinks "$d/src" "$d/graded" >/dev/null 2>&1 || exit 3
  echo "    forged blob planted at the U+017F spelling = $blob"
  show_local_state "$d/graded"
  runbar "$d/graded" "$d/bar.log"
}

run_wdirty() {
  arm "WDIRTY-$BASE" "$BASE"
  local d; d="$( stage "WDIRTY-$BASE" "$BASE" )" || exit 3
  ( cd "$d/src" && git commit -q --allow-empty -m "T466 WDIRTY" ) >/dev/null 2>&1 || exit 3
  git clone -q --no-hardlinks "$d/src" "$d/graded" >/dev/null 2>&1 || exit 3
  printf '\n# T466 WDIRTY: an ordinary uncommitted edit, made the way a worker makes one.\n' \
    >> "$d/graded/$CONF" || exit 3
  show_local_state "$d/graded"
  runbar "$d/graded" "$d/bar.log"
}

for a in "$@"; do
  case "$a" in
    CTL)      run_ctl ;;
    CTLUNREG) run_ctlunreg ;;
    SKIPWT)   run_bit skip-worktree ;;
    ASSUME)   run_bit assume-unchanged ;;
    SMUDGE)   run_smudge ;;
    LONGNOP)  run_longnop ;;
    WDIRTY)   run_wdirty ;;
    *) echo "unknown arm $a" >&2; exit 3 ;;
  esac
done
