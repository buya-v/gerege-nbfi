#!/usr/bin/env bash
# T402 -- THE THREE CHECKS OF THE C-1 REPAIR, DRIVEN INDIVIDUALLY.
#
#   bash .softhouse/capture/t402-t386-conditions/instruments/t402-errf-helpers-drive.sh \
#        <repo-root> <ref>
#
# WHY THIS EXISTS. t402-errf-class-drive.sh proves the repair refuses under two whole-file
# sabotages. It does NOT reach all three of the repair's checks:
#
#   * ARM U (directory removed) is caught by the READ check -- `cat` fails.
#   * ARM R (file chmod 0444)  is caught by the PRIME check -- the file will not open for write.
#   * NEITHER ARM REACHES THE WITNESS CHECK -- the sentinel surviving the search, which is the
#     only one of the three that is a POSITIVE PROOF that the command never ran rather than an
#     inference from a reader's status.
#
# An undriven guard is a guard nobody has seen work, and this program has a name for shipping
# one. So the two helpers are extracted FROM GIT BY NAME -- never by line number, this program
# lost a day to a pin that moved 546 lines -- their sha256 is printed so the drive cannot grade
# an edited copy, and each check is put in front of the state it exists to catch.
#
# ENGINE DECLARED (P-33/P-53): `awk` for the by-name extraction, no repository search at all,
# no backslash-class in any pattern.
#
# EXIT: 0 every case behaved as specified; 1 at least one did not; 2 the rig could not be built.
set -uo pipefail

REPO=${1:?usage: <repo-root> <ref>}
REF=${2:?usage: <repo-root> <ref>}
SRC='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t402-helpers.XXXXXXXX") || exit 2
trap 'chmod -R u+w "$WORK"; rm -rf "$WORK"' EXIT

git -C "$REPO" show "$REF:$SRC" > "$WORK/f.sh" || exit 2

echo "T402 ERRF-HELPER UNIT DRIVE"
echo "  ref        : $REF"
echo "  file       : $SRC"
echo "  file sha256: $(shasum -a 256 < "$WORK/f.sh" | cut -d' ' -f1)"

# ---- EXTRACT BY NAME ----------------------------------------------------------------------
awk '/^_errf_prime\(\) \{/,/^\}/' "$WORK/f.sh" >  "$WORK/helpers.sh"
awk '/^_errf_read\(\) \{/,/^\}/'  "$WORK/f.sh" >> "$WORK/helpers.sh"
P_LINES=$(awk '/^_errf_prime\(\) \{/,/^\}/' "$WORK/f.sh" | grep -c '')
R_LINES=$(awk '/^_errf_read\(\) \{/,/^\}/'  "$WORK/f.sh" | grep -c '')
echo "  extracted  : _errf_prime $P_LINES line(s), _errf_read $R_LINES line(s)"
echo "  extract sha: $(shasum -a 256 < "$WORK/helpers.sh" | cut -d' ' -f1)"
if [ "$P_LINES" -lt 4 ] || [ "$R_LINES" -lt 6 ]; then
  echo "  REFUSED: extraction by name did not yield both helpers. Nothing was driven." >&2
  exit 2
fi
echo

# shellcheck source=/dev/null
. "$WORK/helpers.sh" || exit 2

FAILS=0
SWEEP_ERRF="$WORK/errf"
SWEEP_ERRF_SENTINEL="zzq-t402-drive-sentinel-$$-${RANDOM}-fixed"
SWEEP_ERRF_WHY=""
ERRF_TEXT=""

case_() { # case_ <label> <expected read rc> <expected ERRF_TEXT or __ANY__>
  printf '  %-52s ' "$1"
  local want_rc="$2" want_txt="$3" got_rc
  _errf_read; got_rc=$?
  if [ "$got_rc" != "$want_rc" ]; then
    printf 'FAIL read rc=%s wanted %s\n' "$got_rc" "$want_rc"; FAILS=$((FAILS+1)); return
  fi
  if [ "$want_txt" != "__ANY__" ] && [ "$ERRF_TEXT" != "$want_txt" ]; then
    printf 'FAIL text=[%s] wanted [%s]\n' "$ERRF_TEXT" "$want_txt"; FAILS=$((FAILS+1)); return
  fi
  printf 'OK  rc=%s  text=[%s]\n' "$got_rc" "$ERRF_TEXT"
  [ -n "$SWEEP_ERRF_WHY" ] && printf '        why: %s\n' "$SWEEP_ERRF_WHY"
  return 0
}

echo '=== THE PRIME CHECK ======================================================='
rm -f "$SWEEP_ERRF"
printf '  %-52s ' 'Z0 CONTROL: writable path, prime must SUCCEED'
if _errf_prime; then echo 'OK  rc=0'; else echo 'FAIL'; FAILS=$((FAILS+1)); fi

printf '  %-52s ' 'Z4 file chmod 0444, prime must REFUSE'
chmod 0444 "$SWEEP_ERRF"
if _errf_prime; then
  echo 'FAIL -- prime returned 0 on an unwritable file'; FAILS=$((FAILS+1))
else
  echo 'OK  rc=1'
  printf '        why: %s\n' "$SWEEP_ERRF_WHY"
fi
chmod 0644 "$SWEEP_ERRF"
echo

echo '=== THE READ CHECK AND THE WITNESS CHECK =================================='
echo '  (each case sets the scratch file to a state and calls _errf_read)'

# Z1 CONTROL -- the redirect opened and the engine wrote a warning. This is a REAL stderr
# reading and it MUST come back usable, or the repair has broken the R4 repair it sits on.
_errf_prime
printf '%s\n' 'warning: a real engine complaint' > "$SWEEP_ERRF"
case_ 'Z1 CONTROL: redirect opened, engine wrote stderr' 0 'warning: a real engine complaint'

# Z2 CONTROL -- the redirect opened and the engine wrote NOTHING. A genuinely silent, genuinely
# successful search. MUST come back usable with empty text; a refusal here would be T383's
# defect wearing the opposite sign.
_errf_prime
: > "$SWEEP_ERRF"
case_ 'Z2 CONTROL: redirect opened, engine silent' 0 ''

# Z3 THE WITNESS -- prime wrote the sentinel and it is STILL THERE after the "search". The
# shell never truncated the file, so the redirect was never opened and the command never ran.
# Neither cat's status nor bash's status can tell you this; the sentinel can.
_errf_prime
case_ 'Z3 WITNESS: sentinel survived -- command never ran' 1 ''

# Z5 THE READ -- the file is gone. cat fails.
_errf_prime
rm -f "$SWEEP_ERRF"
case_ 'Z5 READ: scratch file removed, cat fails' 1 ''

# Z6 -- a stderr line that merely CONTAINS the sentinel is not the sentinel. The witness must
# not be defeatable by an engine echoing its own environment, and must not misfire on one.
_errf_prime
printf '%s\n' "warning: something mentioning $SWEEP_ERRF_SENTINEL in passing" > "$SWEEP_ERRF"
case_ 'Z6 witness is exact-match, not substring' 0 "warning: something mentioning $SWEEP_ERRF_SENTINEL in passing"
echo

echo "DRIVE-RESULT: cases_failed=$FAILS"
if [ "$FAILS" -eq 0 ]; then
  echo '*** ALL SIX CASES BEHAVED AS SPECIFIED, INCLUDING THE THREE CONTROLS.'
  echo '*** The WITNESS check (Z3) is driven here and nowhere else: it is the only one of the'
  echo '*** three that proves the command never ran rather than inferring it from a reader.'
else
  echo "*** $FAILS CASE(S) DID NOT. This drive reports failure through its exit status."
fi
exit $(( FAILS > 0 ? 1 : 0 ))
