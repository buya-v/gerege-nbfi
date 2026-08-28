#!/bin/zsh
# T377 — DRIVE THE NEW WIRED CONTROLS RED.
#
# T368's F-T368-2 is that the fatal pre-fire control passed while grading nothing. The fix is
# in `fire-program.sh`'s WIRING (the path that executes), not here. THIS FILE IS EVIDENCE, NOT
# THE CONTROL — and it says so, because a floor that lives only in a capture directory is the
# exact defect being closed. What it does is prove each new refusal can FIRE, by mutating a
# COPY of the shipped wrapper and driving `--probe` at it.
#
# Every mutation is an exact string replacement whose anchor must occur EXACTLY ONCE; anything
# else is reported VOID and the case is not scored as a pass. That is T368's discipline and the
# reason a mutation table cannot pass vacuously.
#
# Usage:  zsh red-drive.zsh [path-to-fire-program.sh]
# zsh, never bash: the subject is `#!/bin/zsh` and uses zsh glob syntax bash cannot parse.
set -uo pipefail

HERE="${0:A:h}"
SUBJECT="${1:-$HERE/../../../bin/fire-program.sh}"
SUBJECT="${SUBJECT:A}"
BINDIR="${SUBJECT:h}"
REPO="${BINDIR:h:h}"                      # .../.softhouse/bin -> repo root
WORK="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/t377-red.XXXXXX")" || exit 2
trap '[[ -n "${WORK:-}" && "${WORK:-}" != "/" ]] && rm -rf "$WORK"' EXIT

print -r -- "subject : $SUBJECT"
print -r -- "sha256  : $(/usr/bin/shasum -a 256 "$SUBJECT" | cut -d' ' -f1)"
print -r -- "repo    : $REPO"
print -r -- "scratch : $WORK"
print -r -- ""
print -r -- "ENV NOTE, measured and material: this worker runs INSIDE a live fire, which exports"
print -r -- "FIRE_SNAPSHOT_OF / FIRE_SCRIPT_DIR / FIRE_REPO_SCRIPT. Inherited, they suppress the"
print -r -- "T301 snapshot re-exec and point SCRIPT_DIR at the parent fire's bin. Every case below"
print -r -- "sets all three EXPLICITLY so FIRE_SELF is the mutated copy and the guards resolve to"
print -r -- "the subject's own repo -- otherwise the census would grade a file that is not running."
print -r -- ""

typeset -i CHECKS=0 WRONG=0 VOID=0

# apply <src> <dst> <anchor> <replacement>   -- returns 1 and prints VOID unless anchor occurs once
apply() {
  local src="$1" dst="$2" anchor="$3" repl="$4"
  /usr/bin/python3 - "$src" "$dst" "$anchor" "$repl" <<'PY'
import sys, io
src, dst, anchor, repl = sys.argv[1:5]
s = io.open(src, encoding="utf-8").read()
n = s.count(anchor)
if n != 1:
    sys.stderr.write("VOID anchor occurs %d times\n" % n)
    sys.exit(3)
io.open(dst, "w", encoding="utf-8").write(s.replace(anchor, repl))
PY
}

# drop_rows <src> <dst>  -- delete every _row/_arow INVOCATION line (the definitions survive)
drop_rows() {
  /usr/bin/python3 - "$1" "$2" <<'PY'
import sys, io, re
src, dst = sys.argv[1:3]
lines = io.open(src, encoding="utf-8").read().split("\n")
pat = re.compile(r'^[ \t]*_(row|arow)[ \t]')
kept = [l for l in lines if not pat.match(l)]
removed = len(lines) - len(kept)
if removed == 0:
    sys.stderr.write("VOID no row invocations matched\n"); sys.exit(3)
sys.stderr.write("rows removed: %d\n" % removed)
io.open(dst, "w", encoding="utf-8").write("\n".join(kept))
PY
}

# run <file> <label> [VAR=VAL ...]   -> prints rc, leaves output in $WORK/<label>.out
run_probe() {
  local file="$1" label="$2"; shift 2
  local -a envs; envs=("$@")
  env "${envs[@]}" \
      GEREGE_NBFI_REPO="$REPO" \
      LOG_DIR="$WORK/logs" \
      FIRE_SCRIPT_DIR="$BINDIR" \
      FIRE_REPO_SCRIPT="$SUBJECT" \
      FIRE_SNAPSHOT_OF="$SUBJECT" \
      /bin/zsh "$file" --probe > "$WORK/$label.out" 2>&1
  return $?
}

score() {   # $1 label  $2 want_rc  $3 got_rc  $4 required pattern  $5 forbidden pattern ('' = none)  $6 why
  local label="$1"; local -i want="$2" got="$3"; local need="$4" forbid="$5" why="$6"
  local -i ok=1
  CHECKS+=1
  local detail=""
  if (( got != want )); then ok=0; detail="rc=$got want=$want"; fi
  if [[ -n "$need" ]] && ! LC_ALL=C grep -qE "$need" "$WORK/$label.out"; then
    ok=0; detail="$detail; MISSING /$need/"
  fi
  if [[ -n "$forbid" ]] && LC_ALL=C grep -qE "$forbid" "$WORK/$label.out"; then
    ok=0; detail="$detail; PRESENT-BUT-FORBIDDEN /$forbid/"
  fi
  if (( ok )); then
    printf '%-6s ok            rc=%-3d %s\n' "$label" "$got" "$why"
  else
    WRONG+=1
    printf '%-6s *** WRONG     rc=%-3d %s  [%s]\n' "$label" "$got" "$why" "$detail"
    print -r -- "         --- last 6 lines of $label.out ---"
    tail -6 "$WORK/$label.out" | sed 's/^/         /'
  fi
}

void() { VOID+=1; CHECKS+=1; printf '%-6s *** VOID      %s\n' "$1" "$2"; }

# ------------------------------------------------------------------ r00 CONTROL
cp "$SUBJECT" "$WORK/r00.sh"
run_probe "$WORK/r00.sh" r00; rc=$?
score r00 0 $rc 'lockselftest: tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' \
      'FATAL' 'UNMUTATED control: probe passes and the wiring PRINTS the reconciliation it performed'

# ------------------------------------------------------ r01 summary line deleted (P-84)
if apply "$SUBJECT" "$WORK/r01.sh" \
     '  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"' \
     '  : # T377 red drive r01: summary suppressed'; then
  run_probe "$WORK/r01.sh" r01; rc=$?
  score r01 2 $rc 'FATAL: the lock-reader self-test printed NO TALLY LINE' '' \
        'the tally line is DELETED: presence is tested before value, so the fire REFUSES (was: rc 0, fire starts)'
else void r01 'anchor for the summary print did not occur exactly once'; fi

# ------------------------------------------- r02 EVERY row invocation deleted (the headline)
if drop_rows "$SUBJECT" "$WORK/r02.sh" 2>"$WORK/r02.drop"; then
  print -r -- "       (r02 $(cat "$WORK/r02.drop"))"
  run_probe "$WORK/r02.sh" r02; rc=$?
  score r02 2 $rc 'FATAL: the lock-reader self-test.s row POPULATION IS EMPTY' '' \
        'THE F-T368-2 CASE: all 45 rows gone. Before T377 this printed ROWS=0 and the fire STARTED.'
else void r02 'no row invocation lines matched the selector'; fi

# ---------------------------------------------------- r03 rows execute but are not counted
if apply "$SUBJECT" "$WORK/r03a.sh" \
     '    _n+=1; mark="ok"
    if [[ "$want" == HELD ]]; then' \
     '    mark="ok"   # T377 red drive r03: _row ROWS counter frozen
    if [[ "$want" == HELD ]]; then'; then
  if apply "$WORK/r03a.sh" "$WORK/r03.sh" \
       '    _n+=1; mark="ok"
    if [[ "$got" != "$want" ]]; then' \
       '    mark="ok"   # T377 red drive r03: _arow ROWS counter frozen
    if [[ "$got" != "$want" ]]; then'; then
    run_probe "$WORK/r03.sh" r03; rc=$?
    score r03 2 $rc 'FATAL: the lock-reader self-test executed ZERO ROWS' '' \
          'all 45 rows RUN but ROWS stays 0: a control reporting a zero population must never pass'
  else void r03 'anchor for the _arow counter did not occur exactly once'; fi
else void r03 'anchor for the _row counter did not occur exactly once'; fi

# ------------------------------- r04 a whole group DECLARED but neither executed nor skipped
if apply "$SUBJECT" "$WORK/r04a.sh" \
     '  _row z01 HELD' '  if false; then
  _row z01 HELD'; then
  if apply "$WORK/r04a.sh" "$WORK/r04.sh" \
       '"CONTROL for z06: INSIDE the skew bound must still FREE, so C1 is a bound and not a ban"' \
       '"CONTROL for z06: INSIDE the skew bound must still FREE, so C1 is a bound and not a ban"
  fi'; then
    run_probe "$WORK/r04.sh" r04; rc=$?
    score r04 2 $rc 'FATAL: the lock-reader self-test does not reconcile' '' \
          'group Z guarded off: 45 declared, 38 executed, 0 announced skipped -- the census catches the 7 that vanished'
  else void r04 'anchor for the z07 row did not occur exactly once'; fi
else void r04 'anchor for the z01 row did not occur exactly once'; fi

# ------------- r05 the self-test's OWN exit-1 removed AND a reader broken: rc lies, tally does not
if apply "$SUBJECT" "$WORK/r05a.sh" \
     '  (( _open == 0 && _shut == 0 )) || exit 1' \
     '  (( _open == 0 && _shut == 0 )) || true   # T377 red drive r05: rc made to lie'; then
  if apply "$WORK/r05a.sh" "$WORK/r05.sh" \
       '  (( _e > 0 )) || return 0' \
       '  # T377 red drive r05: the plausibility floor removed, so group Z fails OPEN'; then
    run_probe "$WORK/r05.sh" r05; rc=$?
    score r05 2 $rc 'FATAL: the lock-reader self-test FAILED \(rc=0, FAIL_OPEN=[1-9]' '' \
          'THE INDEPENDENCE CASE: the self-test exits 0 while reporting FAIL_OPEN rows. The wiring reads the TALLY, not only rc.'
  else void r05 'anchor for the C1 plausibility floor did not occur exactly once'; fi
else void r05 'anchor for the self-test exit did not occur exactly once'; fi

# -------------------- r06 the subprocess sees a knob this process did not (F-T368-3 in the wiring)
if apply "$SUBJECT" "$WORK/r06.sh" \
     '_ST_OUT="$(/bin/zsh "$FIRE_SELF" --self-test-lock-readers 2>&1)"; _ST_RC=$?' \
     '_ST_OUT="$(LOCK_RELEASE_SKEW_SECS=abc /bin/zsh "$FIRE_SELF" --self-test-lock-readers 2>&1)"; _ST_RC=$?'; then
  run_probe "$WORK/r06.sh" r06; rc=$?
  score r06 78 $rc 'FATAL: the lock-reader self-test refused with EX_CONFIG' \
        'FAIL-OPEN row means|FAILED \(rc=' \
        'subprocess-only misconfiguration: reported as CONFIGURATION, never as a reader regression'
else void r06 'anchor for the self-test invocation did not occur exactly once'; fi

# ============================== KNOB CASES: no mutation, environment only ==============
# These refuse at the top of the file, before the log exists, so the message is on stderr.
print -r -- ""
print -r -- "--- knob validator (F-T368-3). Subject UNMUTATED; environment hostile. ---"
knob() {   # $1 label  $2 want_rc  $3 required  $4 forbidden  $5 why  $6.. env
  local label="$1"; local -i want="$2"; local need="$3" forbid="$4" why="$5"; shift 5
  run_probe "$WORK/r00.sh" "$label" "$@"; local -i rc=$?
  score "$label" $want $rc "$need" "$forbid" "$why"
}
knob k01 78 'CONFIGURATION ERROR — LOCK_RELEASE_SKEW_SECS is not a non-negative decimal integer' \
     'FAIL-SHUT|lock-reader self-test FAILED' 'non-numeric skew: named as CONFIGURATION, and the reader message never appears' \
     LOCK_RELEASE_SKEW_SECS=abc
knob k02 78 'CONFIGURATION ERROR — LOCK_RELEASE_SKEW_SECS=.99999999999999999999. does not fit' \
     'FAIL-SHUT|lock-reader self-test FAILED' 'int64-overflowing skew: the ROUND-TRIP catches the wrap, no digit-limit is typed' \
     LOCK_RELEASE_SKEW_SECS=99999999999999999999
knob k03 78 'CONFIGURATION ERROR — LOCK_RELEASE_SKEW_SECS is not a non-negative' \
     'FAIL-OPEN' 'negative skew: refused outright (T368 measured this one producing a FAIL-OPEN ROW before)' \
     LOCK_RELEASE_SKEW_SECS=-100000
knob k04 78 'CONFIGURATION ERROR — LOCK_CEILING_SECS is not a non-negative' \
     'lock-reader self-test FAILED' 'the same class on the OTHER knob, which T368 noted behaved identically' \
     LOCK_CEILING_SECS=abc
knob k05 78 'CONFIGURATION ERROR — LOCK_CEILING_SECS=.0. is below its structural minimum' \
     'lock-reader self-test FAILED' 'a ZERO ceiling is an OPEN setting, not a strict one: arm 3 would fire on every readable started_at' \
     LOCK_CEILING_SECS=0
# k06's forbidden pattern is ANCHORED, and the first run of this driver is why. Written as a
# bare `INJECTED` it scored *** WRONG on a subject that behaves CORRECTLY: the refusal message
# QUOTES the offending value back to the operator (`Got: '0)) || { print INJECTED; }; ((1'`),
# so the token appears as DATA in the diagnostic. The thing that must never happen is the
# payload EXECUTING, which would put `INJECTED` on a line of its own. That is what `^INJECTED$`
# tests. The failing transcript is kept at `out/02-red-drive.txt` rather than overwritten --
# a driver that catches its own author is the evidence the driver works.
knob k06 78 'CONFIGURATION ERROR — LOCK_RELEASE_SKEW_SECS is not a non-negative' \
     '^INJECTED$' 'arithmetic-injection payload: refused by the glob before any arithmetic context sees it; the token appears only as QUOTED DATA in the diagnostic' \
     'LOCK_RELEASE_SKEW_SECS=0)) || { print INJECTED; }; ((1'

print -r -- ""
print -r -- "--- knob validator is a BOUND, not a BAN: legitimate values still start the fire. ---"
knob k07 0 'tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' 'FATAL' \
     'skew 0 is legitimate ("believe no future instant") and T368 measured the corpus green there' \
     LOCK_RELEASE_SKEW_SECS=0
knob k08 0 'tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' 'FATAL' \
     'ceiling 604800 -- T365 C3 derived the C and G fixtures from it, so raising it must NOT turn rows red' \
     LOCK_CEILING_SECS=604800

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG VOID=$VOID"
if (( WRONG || VOID )); then
  print -r -- "RESULT: FAIL — a control did not fire where it must, or a mutation anchor was VOID."
  exit 1
fi
print -r -- "RESULT: PASS — every new refusal fired for the exact defect it names, and no legitimate configuration was refused."
exit 0
