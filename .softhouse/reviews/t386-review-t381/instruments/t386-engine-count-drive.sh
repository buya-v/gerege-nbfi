#!/usr/bin/env bash
# T386 -- adversarial drive of engine_count(), the chokepoint T381 routed every calibration
# search through. If engine_count() has the discarded-status shape, every calibration arm
# inherits it and T381's repair is worse than the disease.
#
#   bash .softhouse/reviews/t386-review-t381/instruments/t386-engine-count-drive.sh
#
# THE FUNCTION UNDER TEST IS EXTRACTED FROM GIT, NEVER FROM A WORKING COPY (P-22). Its sha256
# is printed, so this drive cannot grade a since-edited file.
#
# Each case installs a hostile `git` (or `awk`) on PATH ahead of the real one and asks the
# single question that matters: DID engine_count RETURN 0 (usable) WITH A NUMBER IN ENGINE_N?
# A return of 0 for a search that did not run, or for a tally that did not produce a number,
# is the defect. A return of 2 or 3 is the guard working.
set -uo pipefail

REPO=${1:?usage: t386-engine-count-drive.sh <repo-root> <ref>}
REF=${2:?usage: t386-engine-count-drive.sh <repo-root> <ref>}
SRC='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t386-ecdrive.XXXXXXXX") || exit 2
trap 'rm -rf "$WORK"' EXIT

git -C "$REPO" show "$REF:$SRC" > "$WORK/sweep.sh" || exit 2
echo "UNDER TEST : $REF:$SRC"
echo "  sha256   : $(shasum -a 256 < "$WORK/sweep.sh" | cut -d' ' -f1)"
echo "  lines    : $(wc -l < "$WORK/sweep.sh" | tr -d ' ')"

# Extract the function BY NAME, never by a pinned line number -- this program has already been
# bitten by a line pin that moved (commit f3bf5563).
awk '/^ENGINE_N=""; ENGINE_RC=0; ENGINE_ERR=""$/,/^}$/' "$WORK/sweep.sh" > "$WORK/engine_count.sh"
echo "  extract  : $(wc -l < "$WORK/engine_count.sh" | tr -d ' ') lines, sha256 $(shasum -a 256 < "$WORK/engine_count.sh" | cut -d' ' -f1)"
grep -q '^engine_count() {' "$WORK/engine_count.sh" || { echo "DRIVE ABORT: extraction did not capture engine_count()"; exit 2; }
echo
echo '--- the function as extracted ------------------------------------------------------'
cat -n "$WORK/engine_count.sh"
echo '------------------------------------------------------------------------------------'
echo

PASS=0; FAIL=0

run_case() { # run_case <label> <expect: 0|2|3> <shimdir or -> <args...>
  local label="$1" expect="$2" shim="$3"; shift 3
  local rc n out
  out=$(
    cd "$REPO" || exit 9
    set -uo pipefail
    SWEEP_ERRF=$(mktemp "${TMPDIR:-/tmp}/t386-errf.XXXXXX") || exit 9
    trap 'rm -f "$SWEEP_ERRF"' EXIT
    # shellcheck disable=SC1090
    . "$WORK/engine_count.sh"
    [ "$shim" != "-" ] && PATH="$shim:$PATH"
    engine_count "$@"; rc=$?
    printf 'RETURN=%s ENGINE_RC=%s ENGINE_N=[%s]\n' "$rc" "$ENGINE_RC" "$ENGINE_N"
  )
  rc=$(printf '%s' "$out" | sed -n 's/.*RETURN=\([0-9]*\) .*/\1/p')
  n=$(printf '%s' "$out" | sed -n 's/.*ENGINE_N=\[\(.*\)\]$/\1/p')
  printf '%-58s expect=%s  got: %s\n' "$label" "$expect" "$out"
  if [ "$rc" = "$expect" ]; then
    printf '    -> GUARD OK\n\n'; PASS=$((PASS+1))
  else
    printf '    -> *** DEFECT: returned %s, wanted %s (ENGINE_N=[%s])\n\n' "$rc" "$expect" "$n"; FAIL=$((FAIL+1))
  fi
}

mkshim() { # mkshim <name> <body...>
  local d; d=$(mktemp -d "$WORK/shim.XXXXXX")
  printf '#!/usr/bin/env bash\n%s\n' "$2" > "$d/$1"
  chmod +x "$d/$1"
  printf '%s' "$d"
}

echo '=== C0 CONTROL: a healthy search that MATCHES ======================================='
run_case "C0  real git, known-present string" 0 - -c -F 'CASUALTY SWEEP for the T352' -- '.softhouse/capture/t363-oracle-baseline/instruments/'

echo '=== C1 CONTROL: a healthy search that MEASURES ZERO (rc 1) =========================='
run_case "C1  real git, sentinel absent from the corpus" 0 - -c -F "zzq-t386-sentinel-$$-$RANDOM" -- .softhouse

echo '=== C2 git grep exits 128 (the T367 malformed-selector case) ========================'
SH=$(mkshim git 'echo "fatal: bad revision" >&2; exit 128')
run_case "C2  git grep -> exit 128, nothing on stdout" 2 "$SH" -c -F anything -- .softhouse

echo '=== C3 git grep exits 2 =============================================================='
SH=$(mkshim git 'echo "grep: invalid option" >&2; exit 2')
run_case "C3  git grep -> exit 2" 2 "$SH" -c -F anything -- .softhouse

echo '=== C4 git grep exits 128 BUT ALSO PRINTS A PLAUSIBLE COUNT ON STDOUT ================'
# The nastiest engine: it errors AND emits something the tally will happily sum.
SH=$(mkshim git 'echo "some/file:7"; echo "fatal: partial failure" >&2; exit 128')
run_case "C4  git grep -> stdout 'file:7' AND exit 128" 2 "$SH" -c -F anything -- .softhouse

echo '=== C5 awk DIES (killed) ============================================================'
SH=$(mkshim awk 'kill -TERM $$; exit 143')
run_case "C5  awk killed by SIGTERM, prints nothing" 3 "$SH" -c -F 'CASUALTY SWEEP for the T352' -- '.softhouse/capture/t363-oracle-baseline/instruments/'

echo '=== C6 awk exits non-zero AFTER printing a number ==================================='
SH=$(mkshim awk 'echo 9999; exit 1')
run_case "C6  awk prints 9999 then exits 1" 3 "$SH" -c -F 'CASUALTY SWEEP for the T352' -- '.softhouse/capture/t363-oracle-baseline/instruments/'

echo '=== C7 awk exits 0 with NON-NUMERIC output =========================================='
SH=$(mkshim awk 'echo "not-a-number"; exit 0')
run_case "C7  awk prints 'not-a-number', exit 0" 3 "$SH" -c -F 'CASUALTY SWEEP for the T352' -- '.softhouse/capture/t363-oracle-baseline/instruments/'

echo '=== C8 awk exits 0 with EMPTY output ================================================'
SH=$(mkshim awk 'exit 0')
run_case "C8  awk prints nothing, exit 0" 3 "$SH" -c -F 'CASUALTY SWEEP for the T352' -- '.softhouse/capture/t363-oracle-baseline/instruments/'

echo '=== C9 awk exits 0 with LEADING WHITESPACE around a number =========================='
SH=$(mkshim awk 'printf "   12  \n"; exit 0')
run_case "C9  awk prints '   12  ', exit 0" 3 "$SH" -c -F 'CASUALTY SWEEP for the T352' -- '.softhouse/capture/t363-oracle-baseline/instruments/'

echo '=== C10 awk exits 0 with a NEGATIVE number =========================================='
SH=$(mkshim awk 'echo "-5"; exit 0')
run_case "C10 awk prints '-5', exit 0" 3 "$SH" -c -F 'CASUALTY SWEEP for the T352' -- '.softhouse/capture/t363-oracle-baseline/instruments/'

echo '=== C11 awk exits 0 with SCIENTIFIC NOTATION (real awk does this past ~1e16) ========'
SH=$(mkshim awk 'echo "1e+17"; exit 0')
run_case "C11 awk prints '1e+17', exit 0" 3 "$SH" -c -F 'CASUALTY SWEEP for the T352' -- '.softhouse/capture/t363-oracle-baseline/instruments/'

echo '=== C12 SIGPIPE: git grep emits an unbounded stream, awk exits early ================'
SH=$(mkshim awk 'exit 0')   # awk that reads nothing -> printf gets EPIPE
run_case "C12 awk closes its input immediately (SIGPIPE on printf)" 3 "$SH" -c -F 'CASUALTY SWEEP for the T352' -- '.softhouse/capture/t363-oracle-baseline/instruments/'

echo '=== C13 git grep writes a huge stderr but SUCCEEDS (R4 shape) ======================='
SH=$(mkshim git 'echo "some/file:3"; echo "warning: noise" >&2; exit 0')
run_case "C13 git grep -> 'file:3' + stderr warning, exit 0" 0 "$SH" -c -F anything -- .softhouse

echo '=== C14 THE SCRATCH FILE IS UNREADABLE (cat fails; its status is NOT read) =========='
# engine_count does  ENGINE_ERR=$(cat "$SWEEP_ERRF")  with the status discarded.
(
  cd "$REPO" || exit 9
  set -uo pipefail
  SWEEP_ERRF=$(mktemp "${TMPDIR:-/tmp}/t386-errf.XXXXXX")
  # shellcheck disable=SC1090
  . "$WORK/engine_count.sh"
  PATH="$(mkshim git 'echo "some/file:3"; echo "warning: THE ENGINE COMPLAINED" >&2; exit 0')":$PATH
  rm -f "$SWEEP_ERRF"            # the scratch file vanishes under it
  engine_count -c -F anything -- .softhouse 2>/dev/null; rc=$?
  printf 'C14 scratch file removed: RETURN=%s ENGINE_N=[%s] ENGINE_ERR=[%s]\n' "$rc" "$ENGINE_N" "$ENGINE_ERR"
  if [ "$rc" -eq 0 ] && [ -z "$ENGINE_ERR" ]; then
    printf '    -> the engine DID complain and ENGINE_ERR is EMPTY. cat failed and nobody read it.\n'
  fi
)
echo

echo "DRIVE-RESULT: cases_guarded=$PASS cases_defective=$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
exit 0
