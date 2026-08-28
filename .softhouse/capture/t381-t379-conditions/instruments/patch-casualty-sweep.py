#!/usr/bin/env python3
"""
T381 -- the source edit that closes T379's R1..R4 on `casualty-sweep.sh`.

This is kept as an instrument rather than thrown away because every substitution below is
ANCHORED: it asserts that its `old` text occurs EXACTLY ONCE and dies otherwise. Re-running it
on an already-patched file therefore FAILS LOUDLY instead of silently doing nothing, which is
the property a reader needs in order to tell "this patch was applied" from "this patch was a
no-op".  It is idempotent in the honest direction only.

    python3 .softhouse/capture/t381-t379-conditions/instruments/patch-casualty-sweep.py

ENGINE: python3 str.replace, count-checked. No regex, no `git grep`, no network, no database.
"""
import sys

P = ".softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh"
s = open(P, encoding="utf-8").read()
orig = s


def sub1(old, new, tag):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("PATCH %s: expected exactly 1 occurrence, found %d -- REFUSING" % (tag, n))
    s = s.replace(old, new, 1)


# ------------------------------------------------------------------ 1. header + scratch file
old_hdr = """# POPULATION: `git ls-files .softhouse` -- TRACKED files only. Untracked files are not part of
# the record and were separately confirmed to be zero in number at the time of writing.
#
# It writes nothing and reaches no network and no database. It is a grep.
set -uo pipefail
"""
new_hdr = """# ------------------------------------------------------------------------------------------
# T381 REPAIR -- R1..R4 FROM T379'S REVIEW OF THE T371 REPAIR ABOVE.
#
# T379 approved T371 and filed four residual defects. THREE OF THEM ARE THE SAME SHAPE AS THE
# ONE T371 CAME HERE TO FIX, and one of those three was INSIDE T371's fix. Writing the rule
# does not immunise you against it; only a guard that RUNS does (P-81; and P-45, whose rule is
# that a control nobody is obliged to run enforces nothing).
#
#   R2 (the near-rejection). The ANTI-calibration was itself fail-open:
#
#       n=$(git grep -c -F "$CALIB_NEG_STR" -- <corpus> 2>/dev/null | awk ...)
#       if [ "${n:-0}" -gt 0 ]; then ... exit 3; fi
#
#     `2>/dev/null` threw the engine's complaint away and the PIPE threw its exit status away,
#     so a search that ERRORED yielded n=0 -- which on THIS arm is the PASS condition. It
#     printed `CALIBRATE-: PASS -- known negative matched 0 times across the tracked corpus`
#     and `calibration=yes exit=0`, BYTE-IDENTICALLY to a run in which the search really ran.
#     `set -o pipefail` is ON in this file and did NOT help, because the status of the
#     assignment was never read either: pipefail is not a substitute for CHECKING.
#     FIXED: every calibration search now runs through engine_count(), which reads git grep's
#     status AND awk's status and refuses a non-numeric tally. RED-DRIVEN: T381 drive D-R2.
#
#   R3. Both calibrations were `-F`; THIRTEEN OF THE SIXTEEN SELECTORS ARE `-E`, and the
#     anti-calibration's own stated justification is an `-E` hazard. The calibration therefore
#     never exercised the mode the selectors run in. FIXED three ways: an `-E` POSITIVE arm
#     whose pattern matches only if ERE metacharacters are really interpreted; an `-E` ANTI arm
#     on a run-time sentinel; and sel() now REFUSES any selector pattern carrying a
#     backslash-class, which turns this header's `NO \\b anywhere` CLAIM into a CHECK.
#     RED-DRIVEN: T381 drive D-R3, a shim that rewrites `-E` to `-F` -- a literal-minded engine.
#
#   R1. sel() read `git grep`'s status and then handed the hits to two ARCHIVE-predicate greps
#     whose status it did not read, so a malformed predicate turned a real hit into `LIVE: 0`
#     at exit 0 -- F2's shape moved one step downstream of the repair. FIXED: both statuses are
#     read, and a classification that did not run refuses instead of printing a zero. D-R1.
#
#   R4. `2>&1` folded stderr into the hit set on EVERY path: at rc=0 a warning line was counted
#     as a hit and listed as LIVE, and at rc=1 it was discarded unprinted. FIXED: stderr goes
#     to a private scratch file outside the repository and is reported on its own line on every
#     path. RED-DRIVEN: T381 drive D-R4.
#
# THE T238 HAZARD IS STILL LIVE ON THIS HOST, and calibrate() now MEASURES it on every run
# instead of asserting it in prose -- see the `SWEEP OBSERVE` line. Re-measured by T381: the
# escaped and the literal spelling of the same term return byte-identical output, because git
# compiles the backslash-class down to those literal letters.
#
# POPULATION: `git ls-files .softhouse` -- TRACKED files only. Untracked files are not part of
# the record and were separately confirmed to be zero in number at the time of writing.
#
# It reaches no network and no database, and it writes NOTHING INTO THE REPOSITORY. Since T381
# it creates exactly one scratch file, via `mktemp`, outside the repository, to keep the
# engine's stderr out of the hit set; it is removed on exit. It is still a grep.
set -uo pipefail

# THE ENGINE'S STDERR NEEDS SOMEWHERE TO GO THAT IS NOT THE HIT SET. [T381, R4]
SWEEP_ERRF=$(mktemp "${TMPDIR:-/tmp}/casualty-sweep-stderr.XXXXXXXXXX") || {
  echo "SWEEP ABORT (exit 2): could not create a scratch file for the engine's stderr. Without" >&2
  echo "  it a warning line cannot be told apart from a hit, and no count below is trustworthy." >&2
  exit 2
}
trap 'rm -f "$SWEEP_ERRF"' EXIT HUP INT TERM
"""
sub1(old_hdr, new_hdr, "header")

# ------------------------------------------------------------------ 2. engine + calibration
old_cal = """CALIB_NEG_STR="zzq-t371-anticalibration-sentinel-$$-${RANDOM}-$(date -u +%s)"

calibrate() {
  local n
  n=$(git grep -c -F "$CALIB_POS_STR" -- "$CALIB_POS_PATH" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  if [ "${n:-0}" -lt 1 ]; then
    echo "SWEEP ABORT (exit 3): CALIBRATION MISSED. '$CALIB_POS_STR' found 0 in $CALIB_POS_PATH," >&2
    echo "  where it is KNOWN present. The engine, the pattern language or the corpus is broken;" >&2
    echo "  no negative printed below would be interpretable, so nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE+: PASS -- known positive matched %s time(s) in %s\\n' "$n" "$CALIB_POS_PATH"
  n=$(git grep -c -F "$CALIB_NEG_STR" -- .softhouse/ 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  if [ "${n:-0}" -gt 0 ]; then
    echo "SWEEP ABORT (exit 3): ANTI-CALIBRATION FAILED. The known-absent sentinel matched $n time(s)." >&2
    echo "  The engine is FABRICATING matches; every POSITIVE below would be suspect, not only the" >&2
    echo "  zeros. Nothing is printed." >&2
    exit 3
  fi
  # NB: no bare '.softhouse/' immediately before the \\n. T316's dead-path census reads
  # `.softhouse/\\n` as a repo-path token, it does not resolve, and the frontier guard REFUSES.
  # Measured on this exact line: frontier 109 -> 110, guard_dead_path_frontier FAILED.
  printf 'SWEEP CALIBRATE-: PASS -- known negative matched 0 times across the tracked corpus\\n'
  SWEEP_CALIBRATED=yes
}
"""
new_cal = """CALIB_NEG_STR="zzq-t371-anticalibration-sentinel-$$-${RANDOM}-$(date -u +%s)"

# T381 (R3). THE SELECTORS RUN IN `-E`, SO THE CALIBRATION MUST TOO. Thirteen of S1..S16 are
# `-E` and both of T371's calibration arms were `-F`, which has no metacharacters and so cannot
# reach the hazard the anti-calibration's own comment cites as its reason for existing.
#
# CALIB_POS_ERE matches ONLY if the engine really interprets a bracket expression, a group, an
# alternation and a bounded quantifier. A literal-minded `-E` -- exactly the failure T238 named
# -- returns 0 for it, and the run now ABORTS instead of printing thirteen unmeasured zeros. It
# is written so that its OWN definition line cannot match it: the text here reads `C[A]SUALTY`
# while the pattern demands a literal `CASUALTY`.
CALIB_POS_ERE='C[A]SUALTY SW(EEP|OOP) for the T3[0-9]{2}'
CALIB_NEG_ERE="(zzq|qzz)-t381-ere-anticalib-[0-9]+-$$-${RANDOM}-$(date -u +%s)"

# --------------------------------------------------------------------------- engine plumbing
# T381 (R2). ONE PLACE RUNS `git grep` FOR A COUNT, AND IT READS BOTH STATUSES.
#   ENGINE_RC   0 matched | 1 a MEASURED zero | >=2 the search DID NOT RUN
#   return      0 usable  | 2 did-not-run     | 3 the TALLY itself failed
# An errored search is not an empty one, and a missing count is not a count of zero.
ENGINE_N=""; ENGINE_RC=0; ENGINE_ERR=""
engine_count() {
  local out rc n arc
  ENGINE_N=""; ENGINE_ERR=""
  out=$(git grep "$@" 2>"$SWEEP_ERRF"); rc=$?
  ENGINE_RC=$rc
  ENGINE_ERR=$(cat "$SWEEP_ERRF")
  if [ "$rc" -ge 2 ]; then return 2; fi
  n=$(printf '%s\\n' "$out" | awk -F: '{s+=$NF} END{print s+0}'); arc=$?
  if [ "$arc" -ne 0 ]; then return 3; fi
  case "$n" in ''|*[!0-9]*) return 3 ;; esac
  ENGINE_N=$n
  return 0
}

_calib_refuse() { # _calib_refuse <arm label> <engine_count return>
  local arm="$1" ec="$2"
  if [ "$ec" -eq 2 ]; then
    echo "SWEEP ABORT (exit 3): the $arm calibration search DID NOT RUN -- git grep rc=$ENGINE_RC." >&2
    echo "  An ERRORED search is not a search that found nothing. Until T381 this arm discarded" >&2
    echo "  that status and printed PASS for exactly this state (T379 R2). Engine output follows:" >&2
    printf '%s' "$ENGINE_ERR" | grep . | cut -c1-200 | sed 's/^/    ! /' >&2
  else
    echo "SWEEP ABORT (exit 3): the $arm calibration ran, but its TALLY produced no number." >&2
    echo "  A missing count is not a count of zero, so nothing below would be interpretable." >&2
  fi
  exit 3
}

calibrate() {
  local ec
  # ---- arm 1 of 4: -F POSITIVE. A known-present string must be findable (P-72).
  engine_count -c -F "$CALIB_POS_STR" -- "$CALIB_POS_PATH"; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-F POSITIVE" "$ec"
  if [ "$ENGINE_N" -lt 1 ]; then
    echo "SWEEP ABORT (exit 3): CALIBRATION MISSED. '$CALIB_POS_STR' found 0 in $CALIB_POS_PATH," >&2
    echo "  where it is KNOWN present. The engine, the pattern language or the corpus is broken;" >&2
    echo "  no negative printed below would be interpretable, so nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE+F: PASS -- known positive matched %s time(s) in %s\\n' "$ENGINE_N" "$CALIB_POS_PATH"

  # ---- arm 2 of 4: -F ANTI. A known-absent sentinel must return zero -- AND THE SEARCH MUST
  # HAVE RUN, or that zero means nothing. This is the arm T379 R2 caught printing PASS.
  engine_count -c -F "$CALIB_NEG_STR" -- .softhouse; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-F ANTI" "$ec"
  if [ "$ENGINE_N" -gt 0 ]; then
    echo "SWEEP ABORT (exit 3): ANTI-CALIBRATION FAILED. The known-absent sentinel matched $ENGINE_N time(s)." >&2
    echo "  The engine is FABRICATING matches; every POSITIVE below would be suspect, not only the" >&2
    echo "  zeros. Nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE-F: PASS -- known negative matched 0 times, and the search RAN (rc=%s)\\n' "$ENGINE_RC"

  # ---- arm 3 of 4: -E POSITIVE. [T381 R3] The mode thirteen of the sixteen selectors use.
  engine_count -c -E "$CALIB_POS_ERE" -- "$CALIB_POS_PATH"; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-E POSITIVE" "$ec"
  if [ "$ENGINE_N" -lt 1 ]; then
    echo "SWEEP ABORT (exit 3): -E CALIBRATION MISSED. The pattern '$CALIB_POS_ERE' matched 0 times" >&2
    echo "  in $CALIB_POS_PATH, where an ERE-interpreting engine finds it. This engine is NOT" >&2
    echo "  interpreting ERE metacharacters, so the thirteen '-E' selectors below would each print" >&2
    echo "  a zero NOBODY MEASURED. Nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE+E: PASS -- ERE metacharacters ARE interpreted; pattern matched %s time(s)\\n' "$ENGINE_N"

  # ---- arm 4 of 4: -E ANTI. [T381 R3] No fabrication in the mode those thirteen use.
  engine_count -c -E "$CALIB_NEG_ERE" -- .softhouse; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-E ANTI" "$ec"
  if [ "$ENGINE_N" -gt 0 ]; then
    echo "SWEEP ABORT (exit 3): -E ANTI-CALIBRATION FAILED. A run-time sentinel that cannot exist" >&2
    echo "  in the corpus matched $ENGINE_N time(s) under '-E'. The engine FABRICATES in the mode" >&2
    echo "  thirteen selectors use. Nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE-E: PASS -- known negative matched 0 times under -E, and the search RAN (rc=%s)\\n' "$ENGINE_RC"

  # ---- the T238 hazard, MEASURED rather than asserted. [T381 R3] Deliberately NOT a gate, and
  # it says so: on this host the two spellings are EXPECTED to agree, because git compiles the
  # backslash-class down to the literal letters, so gating on disagreement would brick the sweep
  # for the wrong reason. The GATE built on this fact is the refusal in sel() below. This line
  # is the standing measurement that keeps that gate honest -- a host where the hazard has gone
  # away shows up in the transcript instead of being assumed either way.
  local bs hz_esc hz_lit n_esc n_lit
  bs='\\'
  hz_esc="${bs}bmain${bs}b"
  hz_lit="bmainb"
  engine_count -c -E "$hz_esc" -- .softhouse; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-E T238-HAZARD (escaped)" "$ec"
  n_esc="$ENGINE_N"
  engine_count -c -E "$hz_lit" -- .softhouse; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-E T238-HAZARD (literal)" "$ec"
  n_lit="$ENGINE_N"
  if [ "$n_esc" -eq "$n_lit" ]; then
    printf 'SWEEP OBSERVE: T238 hazard LIVE -- escaped=%s literal=%s AGREE, so -E compiles the\\n' "$n_esc" "$n_lit"
    printf '               backslash-class to the literal letters. sel() REFUSES such patterns.\\n'
  else
    printf 'SWEEP OBSERVE: T238 hazard NOT reproducing here -- escaped=%s literal=%s DISAGREE. The\\n' "$n_esc" "$n_lit"
    printf '               refusal in sel() is conservative rather than necessary; it stays.\\n'
  fi
  SWEEP_CALIBRATED=yes
}
"""
sub1(old_cal, new_cal, "calibrate")

# ------------------------------------------------------------------ 3. sel()
old_sel = """  SWEEP_SELECTORS=$((SWEEP_SELECTORS+1))
  local all live arch rc
  # THE REPAIR. stderr is FOLDED IN rather than discarded, and the status is READ.
  #   rc 0  -> matched
  #   rc 1  -> a MEASURED zero: the engine ran over the corpus and matched nothing
  #   rc >1 -> the search DID NOT RUN. That is not "zero hits" and must never print as one.
  all=$(git grep "$@" -- .softhouse/ 2>&1); rc=$?
  if [ "$rc" -ge 2 ]; then
    SWEEP_DIDNOTRUN=$((SWEEP_DIDNOTRUN+1)); SWEEP_RC=4
    printf '    *** SELECTOR DID NOT RUN (git grep rc=%s). THIS IS NOT "ZERO HITS" -- no absence\\n' "$rc"
    printf '    *** may be read from this selector. Engine output follows:\\n'
    printf '%s' "$all" | grep . | cut -c1-200 | sed 's/^/      ! /'
    return
  fi
  if [ "$rc" -eq 1 ]; then
    printf '    MEASURED ZERO -- engine ran over %s tracked files under .softhouse/ and matched nothing\\n' \\
      "$(git ls-files .softhouse | grep -c .)"
    printf '    hits total: 0   archived (snapshots, correctly stale): 0   LIVE: 0\\n'
    return
  fi
  live=$(printf '%s' "$all" | grep -v -E "$ARCHIVE")
  arch=$(printf '%s' "$all" | grep -c -E "$ARCHIVE")
  printf '    hits total: %s   archived (snapshots, correctly stale): %s   LIVE: %s\\n' \\
    "$(printf '%s' "$all" | grep -c .)" "$arch" "$(printf '%s' "$live" | grep -c .)"
  printf '%s' "$live" | grep . | cut -c1-200 | sed 's/^/      /'
}
"""
new_sel = """  # T381 (R3). THE HEADER'S `NO \\b ANYWHERE` WAS A CLAIM. THIS MAKES IT A CHECK.
  # This engine compiles a backslash-class down to the literal letter and returns zero
  # SILENTLY -- calibrate() re-measures that on every run and prints the result. A selector
  # carrying one would emit a negative nobody measured, which is the invariant this whole file
  # is named after, so it is REFUSED before the engine is asked anything at all.
  local a
  for a in "$@"; do
    if printf '%s' "$a" | LC_ALL=C grep -q '\\\\[bBdDsSwW<>]'; then
      printf '    *** SELECTOR REFUSED: its pattern carries a backslash-class, which this engine\\n'
      printf '    *** reads as a LITERAL letter (see the SWEEP OBSERVE line above). Nothing was\\n'
      printf '    *** searched, because the zero it would return would not be a measurement.\\n'
      [ "$SWEEP_RC" -ge 3 ] || SWEEP_RC=3
      return
    fi
  done
  SWEEP_SELECTORS=$((SWEEP_SELECTORS+1))
  local all live arch rc err live_rc arch_rc
  # THE REPAIR. The status is READ.
  #   rc 0  -> matched
  #   rc 1  -> a MEASURED zero: the engine ran over the corpus and matched nothing
  #   rc >1 -> the search DID NOT RUN. That is not "zero hits" and must never print as one.
  # T381 (R4): stderr now goes to a scratch file OUTSIDE the hit set. T371 folded it in with
  # `2>&1`, so at rc=0 a warning line was counted by `grep -c .` as a hit and listed as LIVE,
  # and at rc=1 it was thrown away unprinted. It is now neither counted nor lost.
  all=$(git grep "$@" -- .softhouse 2>"$SWEEP_ERRF"); rc=$?
  err=$(cat "$SWEEP_ERRF")
  if [ "$rc" -ge 2 ]; then
    SWEEP_DIDNOTRUN=$((SWEEP_DIDNOTRUN+1)); SWEEP_RC=4
    printf '    *** SELECTOR DID NOT RUN (git grep rc=%s). THIS IS NOT "ZERO HITS" -- no absence\\n' "$rc"
    printf '    *** may be read from this selector. Engine output follows:\\n'
    printf '%s' "$err" | grep . | cut -c1-200 | sed 's/^/      ! /'
    return
  fi
  if [ -n "$err" ]; then
    printf '    ENGINE STDERR on a search that DID complete (rc=%s). NOT counted as a hit:\\n' "$rc"
    printf '%s' "$err" | grep . | cut -c1-200 | sed 's/^/      ~ /'
  fi
  if [ "$rc" -eq 1 ]; then
    printf '    MEASURED ZERO -- engine ran over %s tracked files in the sweep corpus and matched nothing\\n' \\
      "$(git ls-files .softhouse | grep -c .)"
    printf '    hits total: 0   archived (snapshots, correctly stale): 0   LIVE: 0\\n'
    return
  fi
  # T381 (R1). THE THIRD AND FOURTH STATUSES. T371 read the engine's and then handed the hits
  # to these two greps without reading theirs, so a malformed $ARCHIVE turned a REAL HIT into
  # `LIVE: 0` at exit 0 -- F2's exact shape, one step downstream of where it was repaired.
  # grep: 0 matched, 1 matched nothing (both legitimate here), >=2 CLASSIFICATION DID NOT RUN.
  live=$(printf '%s' "$all" | grep -v -E "$ARCHIVE"); live_rc=$?
  arch=$(printf '%s' "$all" | grep -c -E "$ARCHIVE"); arch_rc=$?
  if [ "$live_rc" -ge 2 ] || [ "$arch_rc" -ge 2 ]; then
    SWEEP_DIDNOTRUN=$((SWEEP_DIDNOTRUN+1)); SWEEP_RC=4
    printf '    *** SELECTOR HIT, BUT ITS CLASSIFICATION DID NOT RUN (archive-predicate grep\\n'
    printf '    *** rc=%s/%s). The engine FOUND %s line(s) and they could not be split into\\n' \\
      "$live_rc" "$arch_rc" "$(printf '%s' "$all" | grep -c .)"
    printf '    *** archived and LIVE, so NO live figure may be printed here -- a "LIVE: 0" would\\n'
    printf '    *** be a negative nobody measured. Check ARCHIVE is a valid ERE.\\n'
    return
  fi
  printf '    hits total: %s   archived (snapshots, correctly stale): %s   LIVE: %s\\n' \\
    "$(printf '%s' "$all" | grep -c .)" "$arch" "$(printf '%s' "$live" | grep -c .)"
  printf '%s' "$live" | grep . | cut -c1-200 | sed 's/^/      /'
}
"""
sub1(old_sel, new_sel, "sel")

# ------------------------------------------------------------------ 4. FU-T379-2: date it
sub1(
    """# `156 PROCESSED / 194 ERROR` -- live 162 / 197, T371 re-derived it against the live database
# in `.softhouse/capture/t371-t367-conditions/sql/q2-status-split.sql`.""",
    """# `156 PROCESSED / 194 ERROR` -- live 162 / 197 AS AT 2026-08-27, T371's re-derivation against
# the live database in `.softhouse/capture/t371-t367-conditions/sql/q2-status-split.sql`.
# [T381, closing FU-T379-2: a cardinal about a live table, typed into a live instrument, MUST
# carry the date it was true -- `.softhouse/capture/t363-oracle-baseline/CASUALTIES.md` already
# dates its own copy. It is a moving counter; undated it reads as current forever, and S12
# reports this very line LIVE on every run.]""",
    "fu-t379-2")

open(P, "w", encoding="utf-8").write(s)
print("PATCHED %s: %d -> %d bytes, 4 anchored substitutions" % (P, len(orig), len(s)))
