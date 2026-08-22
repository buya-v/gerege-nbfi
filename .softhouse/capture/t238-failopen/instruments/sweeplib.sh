# sweeplib.sh — the fail-CLOSED preamble for sweep instruments.       T238, 2026-08-22
#
# SOURCE THIS, do not execute it:   . "$(git rev-parse --show-toplevel)/.softhouse/capture/t238-failopen/instruments/sweeplib.sh"
#
# ------------------------------------------------------------------------------------
# THE INVARIANT IT ENFORCES
#
#   AN INSTRUMENT MUST NOT BE ABLE TO EMIT A NEGATIVE IT DID NOT MEASURE.
#
#   "zero hits", "zero corpus" and "no working engine" are three DIFFERENT facts and
#   they must have three DIFFERENT exit codes. Every fail-open instrument in this
#   repository collapses all three onto "print a reassurance, exit 0".
#
# WHY A LIBRARY IS NOT ENOUGH, STATED HERE SO IT IS NOT FORGOTTEN
#
#   A2-33 is the best-calibrated sweep in this chain — two engines, published recall
#   transcripts, MISSES=0, its own patterns audited for \b \d \s \w — and it still
#   shipped a fail-open. A mechanism that must be REMEMBERED will be omitted by exactly
#   the authors careful enough not to need it. So this file is only half the fix. The
#   other half is instruments/40-failopen-lint.sh, which finds instruments that did NOT
#   adopt it. Adoption is optional; DETECTION is not.
#
# EXIT CODES — chosen so a caller can tell the failures apart
#   0   ran, and the result (hits or no hits) is a MEASUREMENT
#   1   reserved for the caller's own findings
#   90  corpus root unreachable
#   91  corpus reachable but EMPTY (denominator zero — P-35: inspecting nothing is an ERROR)
#   92  calibration MISSED a known positive — the engine or the pattern language is broken
#   93  no usable search engine
# ------------------------------------------------------------------------------------

set -u

SWEEPLIB_VERSION="T238.1"
SWEEP_PATTERNS=0
SWEEP_HITLINES=0
SWEEP_CALIBRATED=no

_sw_die() { printf 'SWEEP ABORT (exit %s): %s\n' "$1" "$2" >&2; exit "$1"; }

# --------------------------------------------------------------------- corpus
# sweep_root [override]
# Resolves the corpus root RELATIVELY. Never hard-code an absolute worktree path: the
# worktree that produced the evidence is deleted within days and the path outlives it.
sweep_root() {
  local r="${1:-}"
  if [ -z "$r" ]; then r=$(git rev-parse --show-toplevel 2>/dev/null) || r=""; fi
  [ -n "$r" ] || _sw_die 90 "no corpus root: not inside a git work tree and no root argument given"
  [ -d "$r" ] || _sw_die 90 "corpus root does not exist: $r"
  cd "$r" || _sw_die 90 "cannot cd into corpus root: $r"
  SWEEP_ROOT="$r"
  SWEEP_CORPUS_FILES=$(git ls-files | wc -l | tr -d ' ')
  [ "$SWEEP_CORPUS_FILES" -gt 0 ] 2>/dev/null \
    || _sw_die 91 "corpus root $r is reachable but tracks ZERO files. A sweep over nothing proves nothing (P-35)."
  printf 'SWEEP ROOT      : %s\n' "$SWEEP_ROOT"
  printf 'SWEEP COMMIT    : %s\n' "$(git rev-parse HEAD)"
  printf 'SWEEP CORPUS    : %s tracked files\n' "$SWEEP_CORPUS_FILES"
}

# --------------------------------------------------------------------- engine
# sweep_engine — declares the engine AND ITS FLAGS, and proves the pattern language works.
# git grep -E reads \b as a literal b and returns zero SILENTLY (P-53, P-12, re-measured
# by T238 at 477dc2d). ugrep is ABSENT on this host. ripgrep exists only as a Claude Code
# shell function that a `bash script.sh` child cannot see. BSD grep has no -P.
sweep_engine() {
  SWEEP_ENGINE="git grep -n -I -i -E"
  command -v git >/dev/null 2>&1 || _sw_die 93 "git not on PATH; no usable search engine"
  printf 'SWEEP ENGINE    : %s   [git %s]\n' "$SWEEP_ENGINE" "$(git --version | awk '{print $3}')"
  printf 'SWEEP ENGINE NB : this engine does NOT implement \\b \\d \\s \\w. Patterns must not use them.\n'
}

# --------------------------------------------------------------------- calibration
# sweep_calibrate <regex> <path>  — P-72: prove the instrument can find something BEFORE
# it is allowed to report that it found nothing. A calibration that misses is an ABORT,
# not a warning, because every subsequent "(no hits)" would be uninterpretable.
sweep_calibrate() {
  local re="$1" path="$2" n
  n=$(git grep -c -I -i -E "$re" -- "$path" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  if [ "${n:-0}" -lt 1 ]; then
    _sw_die 92 "CALIBRATION MISSED. Pattern '$re' found 0 in '$path', where it is KNOWN to be present. The engine, the pattern language or the corpus is broken; no negative from this run is interpretable."
  fi
  SWEEP_CALIBRATED=yes
  printf 'SWEEP CALIBRATE : PASS — known positive %s matched %s time(s) in %s\n' "$re" "$n" "$path"
}

# --------------------------------------------------------------------- the sweep
# sweep_run <label> <regex> [pathspec...]
# Distinguishes the three facts:
#   grep exit 0 -> matches, printed
#   grep exit 1 -> a MEASURED zero
#   grep exit >1 -> an ERROR; aborts, never prints "(no hits)"
sweep_run() {
  local label="$1" re="$2"; shift 2
  [ "$SWEEP_CALIBRATED" = yes ] \
    || _sw_die 92 "sweep_run called before sweep_calibrate. P-72: calibrate on a known positive before reporting any negative."
  SWEEP_PATTERNS=$((SWEEP_PATTERNS+1))
  printf '########## PATTERN %s :: %s\n' "$label" "$re"
  local out rc
  out=$(git grep -n -I -i -E "$re" -- "${@:-.}" 2>&1); rc=$?
  case "$rc" in
    0) printf '%s\n' "$out"
       SWEEP_HITLINES=$((SWEEP_HITLINES + $(printf '%s\n' "$out" | wc -l | tr -d ' '))) ;;
    1) printf '   MEASURED ZERO (engine ran over %s tracked files and matched nothing)\n' "$SWEEP_CORPUS_FILES" ;;
    *) _sw_die 93 "engine ERROR (exit $rc) on pattern $label :: $re
$out" ;;
  esac
  echo
}

# --------------------------------------------------------------------- trailer
# sweep_report — a machine-readable trailer. A reader (or a grader) can tell a real
# negative from a broken run WITHOUT reading the body.
sweep_report() {
  echo "=================================================================="
  printf 'SWEEP-RESULT: root=%s commit=%s corpus_files=%s patterns=%s hit_lines=%s calibration=%s lib=%s\n' \
    "$SWEEP_ROOT" "$(git rev-parse --short HEAD)" "$SWEEP_CORPUS_FILES" \
    "$SWEEP_PATTERNS" "$SWEEP_HITLINES" "$SWEEP_CALIBRATED" "$SWEEPLIB_VERSION"
  [ "$SWEEP_PATTERNS" -gt 0 ] || _sw_die 91 "zero patterns were run; there is nothing to report"
}
