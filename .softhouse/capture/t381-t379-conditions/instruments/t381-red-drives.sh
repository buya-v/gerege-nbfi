#!/usr/bin/env bash
# =============================================================================================
# T381 -- THE RED DRIVES FOR R1..R4 OF T379'S REVIEW OF T371.
#
#   bash .softhouse/capture/t381-t379-conditions/instruments/t381-red-drives.sh
#
# A REPAIR WITH NO RED DRIVE IS NOT A REPAIR, it is a claim. So every finding below is driven
# in the same shape: take the code under test, BREAK EXACTLY ONE THING, and show that the
# BEFORE version prints a PASS it did not earn while the AFTER version REFUSES.
#
# P-22 -- NEITHER VERSION IS READ FROM THE WORKING TREE. Both are extracted from git on every
# run and their sha256 is printed, so this cannot silently grade a since-edited copy. The refs
# are arguments so a reviewer can re-point them:
#
#   BEFORE_REF (default `main`)  the shipped T371 code that carries the defects
#   AFTER_REF  (default `HEAD`)  the T381 repair
#
# ENGINE, declared because it is the thing under test (P-33/P-53): `git grep`, git version
# printed below; POSIX sed/awk/diff/sha256sum-or-shasum; bash. Two of the drives substitute a
# `git` SHIM onto PATH -- that is the point of them, and the shim's source is printed.
#
# CORPUS REACHABILITY, asserted before anything is graded (P-35): this script refuses unless it
# is inside a git work tree whose tracked universe is non-empty, because a drive that ran over
# no corpus would print the same "no difference" a passing drive prints.
#
# CALIBRATION (P-72): before any BEFORE/AFTER comparison is believed, the drive proves that a
# KNOWN POSITIVE difference is visible to its own comparator -- see CALIBRATE below. A
# comparator that cannot see a difference it was handed would report every drive as "no
# difference found", which is this program's signature failure.
#
# It reaches no network and no database. It writes only inside a `mktemp -d` scratch directory
# and the caller-supplied output stream.
# =============================================================================================
set -uo pipefail

BEFORE_REF="${BEFORE_REF:-main}"
AFTER_REF="${AFTER_REF:-HEAD}"
TARGET='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'

TOP=$(git rev-parse --show-toplevel 2>/dev/null) || TOP=""
if [ -z "$TOP" ]; then
  echo "DRIVE ABORT (exit 2): not inside a git work tree. Nothing can be extracted or graded." >&2
  exit 2
fi
cd "$TOP" || { echo "DRIVE ABORT (exit 2): cannot enter $TOP" >&2; exit 2; }

TRACKED=$(git ls-files | grep -c .) || TRACKED=0
if [ "${TRACKED:-0}" -lt 1 ]; then
  echo "DRIVE ABORT (exit 2): the tracked universe is EMPTY. A drive over no corpus proves" >&2
  echo "  nothing and would print the same 'no difference' a passing drive prints (P-35)." >&2
  exit 2
fi

REAL_GIT=$(command -v git) || REAL_GIT=""
if [ -z "$REAL_GIT" ] || [ ! -x "$REAL_GIT" ]; then
  echo "DRIVE ABORT (exit 2): cannot locate an executable git to build the engine shims from." >&2
  exit 2
fi

D=$(mktemp -d "${TMPDIR:-/tmp}/t381-red-drives.XXXXXXXXXX") || {
  echo "DRIVE ABORT (exit 2): could not create a scratch directory." >&2; exit 2; }
trap 'rm -rf "$D"' EXIT HUP INT TERM

_sha() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}';
         else shasum -a 256 "$1" | awk '{print $1}'; fi; }

echo "============================================================================"
echo "T381 RED DRIVES -- R1..R4 of T379's review of T371"
echo "repo      : $(git rev-parse --short HEAD)   date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "engine    : $(git --version)"
echo "corpus    : $TRACKED tracked files (non-empty, asserted before grading)"
echo "target    : $TARGET"
echo "BEFORE_REF: $BEFORE_REF     AFTER_REF: $AFTER_REF"
echo "============================================================================"

# ---- extract both versions FROM GIT, never from the working tree (P-22) --------------------
if ! git show "$BEFORE_REF:$TARGET" > "$D/before.sh" 2>"$D/e"; then
  echo "DRIVE ABORT (exit 2): could not extract $BEFORE_REF:$TARGET" >&2; sed 's/^/  ! /' "$D/e" >&2; exit 2
fi
if ! git show "$AFTER_REF:$TARGET" > "$D/after.sh" 2>"$D/e"; then
  echo "DRIVE ABORT (exit 2): could not extract $AFTER_REF:$TARGET -- the repair is probably not" >&2
  echo "  COMMITTED yet. This drive refuses to grade an uncommitted working copy." >&2
  sed 's/^/  ! /' "$D/e" >&2; exit 2
fi
echo "BEFORE sha256: $(_sha "$D/before.sh")   ($(grep -c . "$D/before.sh") lines)"
echo "AFTER  sha256: $(_sha "$D/after.sh")    ($(grep -c . "$D/after.sh") lines)"
if [ "$(_sha "$D/before.sh")" = "$(_sha "$D/after.sh")" ]; then
  echo "DRIVE ABORT (exit 2): BEFORE and AFTER are the SAME FILE. There is nothing to drive," >&2
  echo "  and every drive below would report 'no difference' for the wrong reason." >&2
  exit 2
fi

# ---- CALIBRATION of the comparator itself (P-72) -------------------------------------------
# The comparator this script relies on is `cmp -s` over two captured transcripts. Prove it can
# SEE a difference it is handed, before any "IDENTICAL" verdict below is allowed to mean
# anything. A comparator that always says "same" would silently pass every drive.
printf 'alpha\n' > "$D/cal.a"; printf 'beta\n' > "$D/cal.b"; printf 'alpha\n' > "$D/cal.c"
if cmp -s "$D/cal.a" "$D/cal.b"; then
  echo "DRIVE ABORT (exit 3): the comparator called two DIFFERENT files identical. Nothing" >&2
  echo "  it reports below would be interpretable." >&2; exit 3
fi
if ! cmp -s "$D/cal.a" "$D/cal.c"; then
  echo "DRIVE ABORT (exit 3): the comparator called two IDENTICAL files different." >&2; exit 3
fi
echo "CALIBRATE comparator: PASS -- it sees a planted difference and sees a planted sameness."
echo

# ---- helpers --------------------------------------------------------------------------------
run() { # run <script> <outfile> [PATH-prefix]
  local s="$1" o="$2" p="${3:-}"
  if [ -n "$p" ]; then PATH="$p:$PATH" bash "$s" > "$o" 2>&1
  else bash "$s" > "$o" 2>&1; fi
  return $?
}
say_rc() { printf '    exit=%s\n' "$1"; }
show() { grep -E "$2" "$1" | sed 's/^/      | /' | head -"${3:-8}"; }

# =============================================================================================
# D-R2 -- THE ANTI-CALIBRATION PASSES ON A SEARCH THAT NEVER RAN.
# =============================================================================================
# BREAK EXACTLY ONE THING: the anti-calibration's PATHSPEC, so that ITS `git grep` -- and only
# its -- exits 128. Everything else in the file is untouched. In BEFORE, `2>/dev/null` eats the
# complaint and the pipe into awk eats the status, so n=0, which on this arm is the PASS
# condition. In AFTER, engine_count() reads the status and the run refuses.
echo "============================================================================"
echo "D-R2  the ANTI-CALIBRATION on a search that ERRORED  (T379 R2, the near-rejection)"
echo "============================================================================"
python3 - "$D/before.sh" "$D/r2-before.sh" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
out = []
hits = 0
for l in open(src, encoding='utf-8'):
    # the anti-calibration is the ONE non-comment line that both uses CALIB_NEG_STR and runs a search
    if 'CALIB_NEG_STR' in l and not l.lstrip().startswith('#') and '--' in l and 'git grep' in l:
        l = l.replace('-- .softhouse/', "-- ':(zzbogusmagic)x'").replace('-- .softhouse ', "-- ':(zzbogusmagic)x' ")
        hits += 1
    out.append(l)
if hits != 1:
    sys.exit("D-R2 patch: expected 1 anti-calibration search line in BEFORE, found %d" % hits)
open(dst, 'w', encoding='utf-8').writelines(out)
PY
[ $? -eq 0 ] || { echo "  D-R2: could not patch BEFORE. DRIVE FAILED."; exit 4; }
python3 - "$D/after.sh" "$D/r2-after.sh" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
out = []
hits = 0
for l in open(src, encoding='utf-8'):
    if 'CALIB_NEG_STR' in l and not l.lstrip().startswith('#') and 'engine_count' in l:
        l = l.replace('-- .softhouse;', "-- ':(zzbogusmagic)x';")
        hits += 1
    out.append(l)
if hits != 1:
    sys.exit("D-R2 patch: expected 1 anti-calibration search line in AFTER, found %d" % hits)
open(dst, 'w', encoding='utf-8').writelines(out)
PY
[ $? -eq 0 ] || { echo "  D-R2: could not patch AFTER. DRIVE FAILED."; exit 4; }

run "$D/before.sh"    "$D/r2-before-control.out"; rc_bc=$?
run "$D/r2-before.sh" "$D/r2-before-broken.out";  rc_bb=$?
run "$D/after.sh"     "$D/r2-after-control.out";  rc_ac=$?
run "$D/r2-after.sh"  "$D/r2-after-broken.out";   rc_ab=$?

echo "  BEFORE, unmodified (control):"; say_rc "$rc_bc"
show "$D/r2-before-control.out" 'CALIBRATE|SWEEP-RESULT' 4
echo "  BEFORE, anti-calibration search FORCED TO ERROR (git grep rc=128):"; say_rc "$rc_bb"
show "$D/r2-before-broken.out" 'CALIBRATE|SWEEP-RESULT' 4
echo
if cmp -s <(grep -E 'CALIBRATE' "$D/r2-before-control.out") \
          <(grep -E 'CALIBRATE' "$D/r2-before-broken.out"); then
  echo "  >>> RED CONFIRMED: BEFORE's calibration lines are BYTE-IDENTICAL whether the search ran"
  echo "  >>> or ERRORED, and both runs exit $rc_bc/$rc_bb. That is a PASS printed for a search"
  echo "  >>> that never happened -- a negative the instrument did not measure."
else
  echo "  >>> R2 DID NOT REPRODUCE in BEFORE. The finding must be re-derived before it is quoted."
fi
echo
echo "  AFTER, unmodified (control):"; say_rc "$rc_ac"
show "$D/r2-after-control.out" 'CALIBRATE|SWEEP-RESULT' 6
echo "  AFTER, anti-calibration search FORCED TO ERROR:"; say_rc "$rc_ab"
show "$D/r2-after-broken.out" 'SWEEP ABORT|DID NOT RUN|fatal|CALIBRATE' 8
if [ "$rc_ab" -eq 3 ] && grep -q 'DID NOT RUN' "$D/r2-after-broken.out"; then
  echo "  >>> GREEN CONFIRMED: AFTER REFUSES -- exit 3, and it names the engine's status."
else
  echo "  >>> AFTER DID NOT REFUSE (exit $rc_ab). THE REPAIR IS NOT PROVEN."
fi
echo

# =============================================================================================
# D-R1 -- A REAL HIT REPORTED AS `LIVE: 0` BECAUSE THE ARCHIVE PREDICATE DID NOT RUN.
# =============================================================================================
echo "============================================================================"
echo "D-R1  the ARCHIVE-predicate greps' discarded status  (T379 R1, inherited from main)"
echo "============================================================================"
for v in before after; do
  sed "s|^ARCHIVE='.*'$|ARCHIVE='([unclosed-group'|" "$D/$v.sh" > "$D/r1-$v.sh"
  if ! grep -q "ARCHIVE='(\[unclosed-group'" "$D/r1-$v.sh"; then
    echo "  D-R1: could not break \$ARCHIVE in $v. DRIVE FAILED."; exit 4
  fi
done
run "$D/r1-before.sh" "$D/r1-before.out"; rc_1b=$?
run "$D/r1-after.sh"  "$D/r1-after.out";  rc_1a=$?
echo "  BEFORE, \$ARCHIVE replaced by an INVALID ERE (nothing else touched):"; say_rc "$rc_1b"
show "$D/r1-before.out" 'hits total|SWEEP-RESULT' 4
echo "  AFTER, same break:"; say_rc "$rc_1a"
show "$D/r1-after.out" 'CLASSIFICATION DID NOT RUN|hits total|SWEEP-RESULT' 6
if grep -q 'LIVE: 0' "$D/r1-before.out" && [ "$rc_1b" -eq 0 ]; then
  echo "  >>> RED CONFIRMED: BEFORE prints 'LIVE: 0' for selectors that HIT, and exits 0."
else
  echo "  >>> R1 DID NOT REPRODUCE in BEFORE (exit $rc_1b)."
fi
if [ "$rc_1a" -eq 4 ] && grep -q 'CLASSIFICATION DID NOT RUN' "$D/r1-after.out"; then
  echo "  >>> GREEN CONFIRMED: AFTER refuses to print a LIVE figure it could not compute; exit 4."
else
  echo "  >>> AFTER DID NOT REFUSE (exit $rc_1a). THE REPAIR IS NOT PROVEN."
fi
echo

# =============================================================================================
# D-R3a -- A LITERAL-MINDED `-E`. THIRTEEN SELECTORS GO SILENT AND THE -F CALIBRATION CANNOT SEE IT.
# =============================================================================================
echo "============================================================================"
echo "D-R3a the calibration runs in -F; thirteen selectors run in -E  (T379 R3)"
echo "============================================================================"
mkdir -p "$D/shimE"
cat > "$D/shimE/git" <<SHIM
#!/usr/bin/env bash
# T381 D-R3a ENGINE SHIM: a git whose \`grep\` treats every pattern LITERALLY -- i.e. exactly the
# failure mode T238 measured and the failure mode a -F-only calibration is blind to. Every other
# git subcommand is passed straight through, so only the SEARCH semantics change.
if [ "\${1:-}" = "grep" ]; then
  shift
  args=()
  for a in "\$@"; do
    case "\$a" in
      -E) args+=( -F ) ;;
      *)  args+=( "\$a" ) ;;
    esac
  done
  exec "$REAL_GIT" grep "\${args[@]}"
fi
exec "$REAL_GIT" "\$@"
SHIM
chmod +x "$D/shimE/git"
echo "  shim: rewrites 'git grep -E' to 'git grep -F'; all other subcommands pass through."
run "$D/before.sh" "$D/r3-before.out" "$D/shimE"; rc_3b=$?
run "$D/after.sh"  "$D/r3-after.out"  "$D/shimE"; rc_3a=$?
echo "  BEFORE under the literal-minded engine:"; say_rc "$rc_3b"
show "$D/r3-before.out" 'CALIBRATE\+|CALIBRATE-|SWEEP-RESULT' 4
echo "  AFTER under the literal-minded engine:"; say_rc "$rc_3a"
show "$D/r3-after.out" 'CALIBRATE|SWEEP ABORT|NOBODY MEASURED|DISAGREE|SAME COUNT' 8
# THE DISCRIMINATOR IS *NOT* A COUNT OF `MEASURED ZERO`, AND THE FIRST VERSION OF THIS DRIVE WAS
# WRONG TO USE ONE. On this corpus a literal-minded engine does not fall silent: the ERE patterns
# of S1..S16 appear VERBATIM in `.softhouse/` -- in the sweep script itself, in handoffs and in
# transcripts that quote the selectors -- so searching for them literally returns SELF-REFERENTIAL
# HITS instead of zeros. Measured: 0 `MEASURED ZERO` lines under the shim. That is a worse failure
# than silence, not a milder one, and it is why the honest discriminator is DIVERGENCE: how many
# selectors reported a different `hits total` once the engine's semantics changed underneath them,
# while the instrument went on declaring `calibration=yes exit=0`.
grep 'hits total' "$D/r2-before-control.out" > "$D/r3-hits-clean.txt"
grep 'hits total' "$D/r3-before.out"         > "$D/r3-hits-shim.txt"
n_clean=$(grep -c . "$D/r3-hits-clean.txt"); n_shim=$(grep -c . "$D/r3-hits-shim.txt")
n_diff=$(diff "$D/r3-hits-clean.txt" "$D/r3-hits-shim.txt" | grep -c '^<')
printf '      | selectors reporting `hits total`: clean=%s shimmed=%s ; rows that CHANGED: %s\n' \
  "$n_clean" "$n_shim" "$n_diff"
printf '      | `MEASURED ZERO` lines under the shim: %s (see the note in the source -- a literal\n' \
  "$(grep -c 'MEASURED ZERO' "$D/r3-before.out")"
printf '      |   engine returns SELF-REFERENTIAL hits on this corpus, not zeros)\n'
if [ "$rc_3b" -eq 0 ] && grep -q 'calibration=yes' "$D/r3-before.out" && [ "${n_diff:-0}" -ge 1 ]; then
  echo "  >>> RED CONFIRMED: the engine's semantics changed under BEFORE's feet -- $n_diff selector"
  echo "  >>> row(s) report a different hit count -- and BEFORE still printed calibration=yes and"
  echo "  >>> exited 0, because both of its calibration arms are -F and cannot reach the hazard."
else
  echo "  >>> R3 DID NOT REPRODUCE in BEFORE (exit $rc_3b, changed rows $n_diff)."
fi
if [ "$rc_3a" -eq 3 ] && grep -qE 'NOBODY MEASURED|SAME COUNT' "$D/r3-after.out"; then
  echo "  >>> GREEN CONFIRMED: AFTER's -E/-F discrimination pair catches it; exit 3, no selector"
  echo "  >>> result printed at all."
else
  echo "  >>> AFTER DID NOT REFUSE (exit $rc_3a). THE REPAIR IS NOT PROVEN."
fi
echo

# =============================================================================================
# D-R3b -- A SELECTOR CARRYING A BACKSLASH-CLASS. The header CLAIMED none; now it is CHECKED.
# =============================================================================================
echo "============================================================================"
echo "D-R3b a selector pattern carrying a backslash-class  (T379 R3, the enforced claim)"
echo "============================================================================"
# THE INSERTION IS DONE BY A SCRIPT, NOT BY `awk -v`, AND THE FIRST RUN OF THIS DRIVE IS WHY.
# `awk -v` EXPANDS ESCAPE SEQUENCES in the assigned value, so the probe's `\b` arrived in the
# file as an actual BACKSPACE. The drive then measured a selector carrying a backspace instead of
# one carrying a backslash-class: the BEFORE arm printed MEASURED ZERO for the wrong reason and
# the AFTER arm did not refuse at all. An instrument that mangles its own test input is the same
# class of error as one that emits a negative it did not measure. The helper below refuses unless
# the backslash-class survives the round trip.
INS="$TOP/.softhouse/capture/t381-t379-conditions/instruments/t381-insert-probe-selector.py"
if [ ! -f "$INS" ]; then
  echo "  D-R3b: the probe inserter is ABSENT at $INS. DRIVE FAILED -- not skipped."; exit 4
fi
for v in before after; do
  if ! python3 "$INS" "$D/$v.sh" "$D/r3b-$v.sh" | sed 's/^/    /'; then
    echo "  D-R3b: the probe inserter REFUSED on $v. DRIVE FAILED."; exit 4
  fi
done
run "$D/r3b-before.sh" "$D/r3b-before.out"; rc_3bb=$?
run "$D/r3b-after.sh"  "$D/r3b-after.out";  rc_3ba=$?
echo "  BEFORE with the probe selector appended:"; say_rc "$rc_3bb"
grep -A12 'ZZ-DRIVE' "$D/r3b-before.out" | sed 's/^/      | /' | head -13
echo "  AFTER with the probe selector appended:"; say_rc "$rc_3ba"
grep -A12 'ZZ-DRIVE' "$D/r3b-after.out" | sed 's/^/      | /' | head -13
if grep -A12 'ZZ-DRIVE' "$D/r3b-before.out" | grep -q 'MEASURED ZERO'; then
  echo "  >>> RED CONFIRMED: BEFORE prints MEASURED ZERO for a pattern the engine compiled to"
  echo "  >>> the literal letters -- a negative it did not measure -- and counts it as a selector."
else
  echo "  >>> R3b DID NOT REPRODUCE in BEFORE."
fi
if grep -A12 'ZZ-DRIVE' "$D/r3b-after.out" | grep -q 'SELECTOR REFUSED' && [ "$rc_3ba" -ne 0 ]; then
  echo "  >>> GREEN CONFIRMED: AFTER REFUSES the selector and exits $rc_3ba, non-zero."
else
  echo "  >>> AFTER DID NOT REFUSE (exit $rc_3ba). THE REPAIR IS NOT PROVEN."
fi
echo

# =============================================================================================
# D-R4 -- ENGINE STDERR FOLDED INTO THE HIT SET ON A SEARCH THAT COMPLETED.
# =============================================================================================
echo "============================================================================"
echo "D-R4  a warning line counted as a hit  (T379 R4, cosmetic but a wrong cardinal)"
echo "============================================================================"
mkdir -p "$D/shimW"
cat > "$D/shimW/git" <<SHIM
#!/usr/bin/env bash
# T381 D-R4 ENGINE SHIM: a git whose \`grep\` prints ONE warning line to stderr and otherwise
# behaves exactly as usual, PRESERVING ITS EXIT STATUS. This is a search that COMPLETED.
if [ "\${1:-}" = "grep" ]; then
  shift
  "$REAL_GIT" grep "\$@"; _rc=\$?
  echo "warning: zz-t381-drive-synthetic-engine-warning" >&2
  exit \$_rc
fi
exec "$REAL_GIT" "\$@"
SHIM
chmod +x "$D/shimW/git"
run "$D/before.sh" "$D/r4-before.out" "$D/shimW"; rc_4b=$?
run "$D/after.sh"  "$D/r4-after.out"  "$D/shimW"; rc_4a=$?
w_before=$(grep -c 'zz-t381-drive-synthetic-engine-warning' "$D/r4-before.out")
w_after=$(grep -c 'zz-t381-drive-synthetic-engine-warning' "$D/r4-after.out")
echo "  BEFORE: exit $rc_4b; the warning appears $w_before time(s) in its output"
grep -B1 -m2 'zz-t381-drive-synthetic-engine-warning' "$D/r4-before.out" | sed 's/^/      | /' | head -4
echo "  AFTER : exit $rc_4a; the warning appears $w_after time(s) in its output"
grep -B1 -m2 'zz-t381-drive-synthetic-engine-warning' "$D/r4-after.out" | sed 's/^/      | /' | head -4
# The discriminator is not the warning's presence but WHERE it is counted. Compare the first
# selector's `hits total` between the shimmed and unshimmed runs of each version.
# The unshimmed baselines are the D-R2 CONTROL runs, reused rather than re-run: same script,
# same corpus, same commit, and re-running them would cost two more full sweeps for bytes that
# are already captured above.
cp "$D/r2-before-control.out" "$D/r4-before-clean.out"
cp "$D/r2-after-control.out"  "$D/r4-after-clean.out"
hb_dirty=$(grep -m1 'hits total' "$D/r4-before.out"       | sed 's/.*hits total: *\([0-9]*\).*/\1/')
hb_clean=$(grep -m1 'hits total' "$D/r4-before-clean.out" | sed 's/.*hits total: *\([0-9]*\).*/\1/')
ha_dirty=$(grep -m1 'hits total' "$D/r4-after.out"        | sed 's/.*hits total: *\([0-9]*\).*/\1/')
ha_clean=$(grep -m1 'hits total' "$D/r4-after-clean.out"  | sed 's/.*hits total: *\([0-9]*\).*/\1/')
printf '  first selector "hits total"     BEFORE: clean=%s  with-warning=%s\n' "$hb_clean" "$hb_dirty"
printf '                                AFTER : clean=%s  with-warning=%s\n' "$ha_clean" "$ha_dirty"
if [ "${hb_dirty:-0}" -gt "${hb_clean:-0}" ]; then
  echo "  >>> RED CONFIRMED: BEFORE's hit count GREW by $(( hb_dirty - hb_clean )) because a stderr line was"
  echo '  >>> folded into the hit set. The printed "hits total" is not a hit count in BEFORE.'
else
  echo "  >>> R4 DID NOT REPRODUCE in BEFORE."
fi
if [ "${ha_dirty:-0}" -eq "${ha_clean:-0}" ] && grep -q 'ENGINE STDERR' "$D/r4-after.out"; then
  echo "  >>> GREEN CONFIRMED: AFTER's hit count is UNCHANGED and the warning is reported on its"
  echo "  >>> own ENGINE STDERR line instead of being counted or dropped."
else
  echo "  >>> AFTER DID NOT SEPARATE STDERR (clean=$ha_clean dirty=$ha_dirty). THE REPAIR IS NOT PROVEN."
fi
echo

# =============================================================================================
# D-GREEN -- THE REPAIRED INSTRUMENT, UNMODIFIED, ON THE REAL ENGINE.
# =============================================================================================
echo "============================================================================"
echo "D-GREEN  the repair on an unbroken engine -- it must still be usable"
echo "============================================================================"
# Reuses the D-R2 AFTER control run, for the same reason.
cp "$D/r2-after-control.out" "$D/green.out"; rc_g=$rc_ac
say_rc "$rc_g"
show "$D/green.out" 'CALIBRATE|OBSERVE|SWEEP-RESULT' 10
if [ "$rc_g" -eq 0 ] && grep -q 'did_not_run=0' "$D/green.out" && grep -q 'calibration=yes' "$D/green.out"; then
  echo "  >>> GREEN: exit 0, all sixteen selectors ran, four calibration arms passed."
else
  echo "  >>> THE REPAIRED INSTRUMENT DOES NOT RUN CLEAN (exit $rc_g). That is a defect."
fi
echo

# =============================================================================================
# D-R5 -- THE BACKSLASH-CLASS CHECK'S OWN STATUS. [found by T381's own audit of T381's own fix]
# =============================================================================================
# The obvious way to write the R3 refusal is `if printf | grep -q PAT; then refuse; fi`, and
# that is the FIFTH instance of this file's own defect: `grep` exits 2 on ERROR, an `if` reads
# a 2 as FALSE, and a check that DID NOT RUN passes the selector through. There is no version
# on `main` to compare against because the check is new, so the RED specimen is CONSTRUCTED --
# exactly what T238 did when it preserved `sweep-ORIGINAL.sh`. Both variants then have the
# CHECK'S OWN PATTERN replaced by an invalid BRE so `grep` really does error, and the only
# difference left between them is whether that error is read.
echo "============================================================================"
echo "D-R5  the backslash-class check's OWN exit status  (T381's audit of T381's fix)"
echo "============================================================================"
MK="$TOP/.softhouse/capture/t381-t379-conditions/instruments/t381-make-r5-variants.py"
if [ ! -f "$MK" ]; then
  echo "  D-R5: the variant builder is ABSENT at $MK. DRIVE FAILED -- not skipped."; exit 4
fi
if ! python3 "$MK" "$D/after.sh" "$D/r5-red.sh" "$D/r5-green.sh" | sed 's/^/    /'; then
  echo "  D-R5: the variant builder REFUSED. DRIVE FAILED."; exit 4
fi
for v in red green; do
  if ! python3 "$INS" "$D/r5-$v.sh" "$D/r5-$v-probe.sh" | sed 's/^/    /'; then
    echo "  D-R5: the probe inserter REFUSED on the $v variant. DRIVE FAILED."; exit 4
  fi
done
run "$D/r5-red-probe.sh"   "$D/r5-red.out";   rc_5r=$?
run "$D/r5-green-probe.sh" "$D/r5-green.out"; rc_5g=$?
# WINDOW 12, NOT 3 -- see the note at D-R3b. The erroring check prints one `grep: invalid
# character range` PER ARGUMENT before the selector reaches its result, so a narrow window reads
# the noise and calls the defect absent.
echo "  RED specimen (check written as an \`if\` over the pipeline; check pattern invalid):"
say_rc "$rc_5r"
grep -A12 'ZZ-DRIVE' "$D/r5-red.out" | sed 's/^/      | /' | head -13
echo "  SHIPPED form (status read explicitly; same invalid check pattern):"
say_rc "$rc_5g"
grep -A12 'ZZ-DRIVE' "$D/r5-green.out" | sed 's/^/      | /' | head -13
if grep -A12 'ZZ-DRIVE' "$D/r5-red.out" | grep -qE 'MEASURED ZERO|hits total'; then
  echo "  >>> RED CONFIRMED: with the check itself erroring, the naive form lets the selector"
  echo "  >>> through and prints a RESULT for it, at exit $rc_5r. The guard did not run and"
  echo "  >>> nothing in the output says so -- only the engine's own complaint, which is not a"
  echo "  >>> statement about the selector."
else
  echo "  >>> D-R5 DID NOT REPRODUCE in the RED specimen."
fi
if grep -A12 'ZZ-DRIVE' "$D/r5-green.out" | grep -q 'CHECK ITSELF did not run' && [ "$rc_5g" -ne 0 ]; then
  echo "  >>> GREEN CONFIRMED: the shipped form REFUSES and exits $rc_5g."
else
  echo "  >>> THE SHIPPED FORM DID NOT REFUSE (exit $rc_5g). THE HARDENING IS NOT PROVEN."
fi
echo
echo "END OF DRIVES."
