#!/usr/bin/env bash
# T254 — EXECUTING THE BSD ARM THAT T253 COULD NOT EXECUTE.
#
# T253 fixed ten `mktemp -t NAME` sites in .softhouse/conformance.sh. It stated
# plainly that it could not run the BSD half: no BSD host, no BSD mktemp binary,
# man pages not installed, POSIX fetch returned 196 bytes. In place of execution it
# re-enacted the GETOPT PARSE from two transcribed optstrings.
#
# THIS INSTRUMENT REPLACES THAT RE-ENACTMENT WITH THE REAL PROGRAM. Apple's
# shell_cmds mktemp.c -- the exact source of /usr/bin/mktemp on Buyan's Mac -- is
# committed next to this file and COMPILED HERE. glibc supplies getopt_long,
# mkstemp and mkdtemp; the __APPLE__ blocks are not compiled. That matters less
# than it sounds and the reason is precise:
#
#   THE __APPLE__ BLOCKS LIVE ENTIRELY ON THE `-t` CODE PATH (case 'p', and the
#   `if (tflag)` block). The NEW form passes no `-t` and no `-p`, so tflag stays 0
#   and neither block is reachable. The new form's whole route through main() is
#   getopt (no options, or `-d`) -> strdup(argv[0]) -> mkstemp/mkdtemp.
#
# WHAT IS STILL NOT EXECUTED, STATED SO NOBODY INFERS OTHERWISE: Darwin libc's own
# mkstemp/mkdtemp, and Darwin's getopt_long. Neither is a residual risk worth
# carrying, for one measured reason: BSD mktemp's OWN `-t` path builds the template
# `<prefix>.XXXXXXXXXX` (mktemp.c:166,168) and hands it to the SAME mkstemp. A
# ten-X template through Darwin mkstemp is what `mktemp -t` has always done on that
# Mac. If ten X's failed there, the OLD form would never have worked either.
#
# Usage:  bash bsd-mktemp-proof.sh
set -uo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit 1

OK=0; FAIL=0
ok()  { OK=$((OK+1));   printf 'OK    %s\n' "$1"; }
bad() { FAIL=$((FAIL+1)); printf 'FAIL  %s\n' "$1"; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t254-bsdproof.XXXXXXXXXX") || exit 1
trap 'rm -rf "$WORK"' EXIT

command -v cc >/dev/null 2>&1 || { echo "no C compiler; cannot execute the BSD arm"; exit 2; }
cc -O0 -o "$WORK/bsd-mktemp" apple-shell_cmds-mktemp.c 2>"$WORK/cc.err" \
  || { echo "COMPILE FAILED:"; cat "$WORK/cc.err"; exit 2; }
B="$WORK/bsd-mktemp"

echo "=============================================================================="
echo "T254 BSD ARM — Apple shell_cmds mktemp.c, compiled and EXECUTED"
echo "  GNU on this host: $(mktemp --version 2>&1 | head -1)"
echo "=============================================================================="

# --- 1. The optstrings, read from source rather than from a synopsis -------------
# BSD/Apple: getopt_long(argc, argv, "dp:qt:u", ...)   -- t: takes an argument
# GNU     : getopt_long(argc, argv, "dp:qtuV", ...)    -- t  takes none
if LC_ALL=C /usr/bin/grep -q 'getopt_long(argc, argv, "dp:qt:u"' apple-shell_cmds-mktemp.c
then ok '1a BSD optstring is "dp:qt:u" (t CARRIES a colon) — read from Apple source'
else bad '1a BSD optstring not found in Apple source'; fi

# --- 2. THE DEFECT: the OLD form parses differently on the two implementations ---
o=$("$B" -t conformance-failopen 2>&1); r=$?
if [ $r -eq 0 ] && [ -e "$o" ]
then ok "2a BSD  ACCEPTS the old form  -> $o"; rm -f "$o"
else bad "2a BSD rejected the old form (rc=$r): $o"; fi

o=$(mktemp -t conformance-failopen 2>&1); r=$?
case "$o" in
  *"too few X's"*) ok "2b GNU  REFUSES the old form -> $o" ;;
  *) bad "2b GNU did not refuse the old form (rc=$r): $o"; [ $r -eq 0 ] && rm -f "$o" ;;
esac

# --- 3. THE FIX: the NEW form is accepted by BOTH, file and directory ------------
for form in file dir; do
  if [ "$form" = dir ]; then dflag=-d; label="-d directory"; else dflag=""; label="file"; fi
  # shellcheck disable=SC2086
  ob=$("$B" $dflag "$WORK/conf.XXXXXXXXXX" 2>&1); rb=$?
  # shellcheck disable=SC2086
  og=$(mktemp  $dflag "$WORK/conf.XXXXXXXXXX" 2>&1); rg=$?
  if [ $rb -eq 0 ] && [ $rg -eq 0 ] && [ -e "$ob" ] && [ -e "$og" ]
  then ok "3 NEW form ($label) accepted by BOTH — BSD:$ob  GNU:$og"
  else bad "3 NEW form ($label) disagreed — BSD rc=$rb [$ob] / GNU rc=$rg [$og]"; fi
done

# --- 4. NEGATIVE CONTROL. Without this, check 3 proves nothing: a form that ------
#        ALWAYS succeeds would pass it. Both must still FAIL on an unwritable dir,
#        because every call site in conformance.sh has a `|| return 1` arm that
#        must keep firing.
ob=$("$B" "$WORK/no-such-dir/conf.XXXXXXXXXX" 2>&1); rb=$?
og=$(mktemp  "$WORK/no-such-dir/conf.XXXXXXXXXX" 2>&1); rg=$?
if [ $rb -ne 0 ] && [ $rg -ne 0 ]
then ok "4 NEGATIVE CONTROL: both still FAIL on a missing directory (BSD rc=$rb, GNU rc=$rg)"
else bad "4 NEGATIVE CONTROL DID NOT FAIL — BSD rc=$rb, GNU rc=$rg; check 3 is vacuous"; fi

# --- 5. The cheap patch T253 refused, refuted by EXECUTION rather than by parse --
#        "just sprinkle X's after -t" still makes the two disagree.
ob=$("$B" -t conf.XXXXXXXXXX 2>&1); og=$(mktemp -t conf.XXXXXXXXXX 2>&1)
bn=$(basename -- "$ob"); gn=$(basename -- "$og")
if [ "$bn" != "$gn" ] && case "$bn" in *XXXXXXXXXX.*) true ;; *) false ;; esac
then ok "5 '-t NAME.XXXXXXXXXX' still DISAGREES: BSD keeps the literal X's ($bn), GNU consumes them ($gn)"
else bad "5 discrimination lost: BSD [$bn] GNU [$gn]"; fi
rm -f "$ob" "$og"

# --- 6. TMPDIR TYPE DRIVE — the input whose TYPE decides the answer. macOS always
#        sets TMPDIR WITH a trailing slash. conf_tmpdir() strips it; '/' is restored.
conf_tmpdir() { local d="${TMPDIR:-/tmp}"; d="${d%/}"; [ -n "$d" ] || d=/; printf '%s' "$d"; }
for t in "UNSET" "$WORK" "$WORK/" "" "/"; do
  if [ "$t" = UNSET ]; then ( unset TMPDIR; d=$(conf_tmpdir); [ "$d" = /tmp ] ) && res=ok || res=bad
    [ $res = ok ] && ok "6 TMPDIR unset      -> /tmp" || bad "6 TMPDIR unset wrong"
  else
    d=$(TMPDIR="$t" ; export TMPDIR; conf_tmpdir)
    case "$t" in
      "$WORK/") [ "$d" = "$WORK" ] && ok "6 TMPDIR trailing / -> stripped ($d)" || bad "6 trailing slash not stripped: $d" ;;
      "")       [ "$d" = /tmp ]    && ok "6 TMPDIR empty      -> /tmp"          || bad "6 empty TMPDIR wrong: $d" ;;
      "/")      [ "$d" = / ]       && ok "6 TMPDIR=/          -> / (restored, not blank)" || bad "6 TMPDIR=/ wrong: $d" ;;
      *)        [ "$d" = "$WORK" ] && ok "6 TMPDIR plain      -> unchanged"     || bad "6 plain TMPDIR wrong: $d" ;;
    esac
  fi
done

echo "=============================================================================="
echo "T254 BSD ARM: $OK OK, $FAIL FAIL"
echo "=============================================================================="
[ "$FAIL" -eq 0 ]
