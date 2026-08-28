#!/bin/zsh
# T325 instrument 40 — GATE 3, the worker-worktree sweep, driven on THE SHIPPED BYTES.
#
# The sweep's whole theory of "there is nothing here to rescue" was
# `[[ -n "$WS" ]] || continue` over `git status --porcelain`. T325 replaces that
# line with a block that asks T324's independent hidden-work terms first. This
# instrument EXTRACTS both blocks from `fire-program.sh` by their markers and runs
# them — a copy pasted into a fixture would drift from the file that executes, and
# P-45's rule is "verify the path that actually executes ... calls it, not merely
# that a test does".
#
# It REFUSES if either marker pair is missing, rather than silently testing
# nothing: a selector that matches nothing while reporting PASS is the defect
# class this whole task is about.
#
# Arms include the COUNTERFACTUAL: the same fixtures through the pre-T325 line,
# so the added power is measured rather than asserted.

set -uo pipefail

HERE=${0:A:h}
REPO_ROOT=${HERE:h:h:h:h}
FIRE="$REPO_ROOT/.softhouse/bin/fire-program.sh"
[[ -r "$FIRE" ]] || { print -r -- "REFUSED: cannot read $FIRE"; exit 2 }

ROOT=$(mktemp -d /private/tmp/t325-sweep-XXXXXX) || exit 2
ROOT=$(cd -- "$ROOT" && pwd -P)
case "$ROOT" in ("$REPO_ROOT"*) print -r -- "REFUSED: scratch root inside the repo"; exit 2 ;; esac
print -r -- "scratch: $ROOT"
print -r -- "shipped file under test: $FIRE"
print -r -- "git: $(git --version)"
print

# ---- extraction, with a refusal when the marker finds nothing ---------------
extract() {
  local begin="$1" end="$2" out="$3"
  awk -v b="$begin" -v e="$end" '
    index($0,b) { inb=1; next }
    index($0,e) { inb=0 }
    inb { print }
  ' "$FIRE" > "$out"
  local n; n=$(grep -c '.' "$out")
  if (( n == 0 )); then
    print -r -- "REFUSED: marker pair [$begin .. $end] extracted ZERO lines from $FIRE. Testing a copy instead would be the very defect this drive exists to catch."
    exit 2
  fi
  print -r -- "extracted $n lines for [$begin]"
}

extract 'T324-PRUNE-BLINDSPOT-GUARD BEGIN' 'T324-PRUNE-BLINDSPOT-GUARD END' "$ROOT/t324-block.zsh"
extract 'T325-SWEEP-HIDDENWORK-GUARD BEGIN' 'T325-SWEEP-HIDDENWORK-GUARD END' "$ROOT/t325-block.zsh"
print

source "$ROOT/t324-block.zsh" || { print -r -- "REFUSED: could not source the extracted T324 block"; exit 2 }

# `log` writes to a FILE, not an array: the sweep is invoked inside a command
# substitution to capture its stdout, which is a SUBSHELL, and an array mutated
# there dies with it. The first run of this instrument scored three FAILs for
# exactly that reason [evidence/40-sweep-gate-FAILED-FIRST-RUN.txt] — the gate
# had fired and the harness could not see it.
LOGFILE="$ROOT/gate.log"
log() { print -r -- "$*" >> "$LOGFILE" }

# The sweep, with the SHIPPED T325 block spliced in where fire-program.sh has it.
{
  print -r -- 'sweep_t325() {'
  print -r -- '  local W="$1" WS WS_RC'
  print -r -- '  WS=$(git -C "$W" status --porcelain); WS_RC=$?'
  print -r -- '  (( WS_RC != 0 )) && { log "ERROR: could not read git status"; return 9 }'
  print -r -- '  for W in "$W"; do'
  cat "$ROOT/t325-block.zsh"
  print -r -- '    print -r -- "REACHED-RESCUE-PATH"'
  print -r -- '  done'
  print -r -- '}'
  # The pre-T325 counterfactual: the single line the block replaced.
  print -r -- 'sweep_legacy() {'
  print -r -- '  local W="$1" WS'
  print -r -- '  WS=$(git -C "$W" status --porcelain)'
  print -r -- '  for W in "$W"; do'
  print -r -- '    [[ -n "$WS" ]] || continue'
  print -r -- '    print -r -- "REACHED-RESCUE-PATH"'
  print -r -- '  done'
  print -r -- '}'
} > "$ROOT/harness.zsh"
source "$ROOT/harness.zsh" || { print -r -- "REFUSED: harness would not load"; exit 2 }

PASS=0; FAIL=0; FAILED=()

mkwt() {
  local name="$1"
  local d="$ROOT/$name"
  git init -q -b main "$d" >/dev/null 2>&1 || return 1
  (
    cd "$d" || exit 1
    git config user.name Buyan; git config user.email buya.vol@gmail.com
    printf '.DS_Store\ntoolchain/\n' > .gitignore
    printf 'irreplaceable worker output\n' > worker-output.txt
    git add -A; git commit -q -m init
  ) || return 1
  print -rn -- "$d"
}

# name, expect_gate_fires(0|1), expect_rescue_reached(0|1)
run() {
  local name="$1" want_fire="$2" want_rescue="$3" d="$4"
  : > "$LOGFILE"
  local out; out=$(sweep_t325 "$d")
  local -a LOGBUF; LOGBUF=(${(f)"$(cat "$LOGFILE")"})
  local reached=0; [[ "$out" == *REACHED-RESCUE-PATH* ]] && reached=1
  local fired=0
  local l; for l in ${LOGBUF+"${LOGBUF[@]}"}; do [[ "$l" == ERROR:* ]] && fired=1; done
  local lout; lout=$(sweep_legacy "$d")
  local legacy_reached=0; [[ "$lout" == *REACHED-RESCUE-PATH* ]] && legacy_reached=1

  if (( fired == want_fire && reached == want_rescue )); then
    print -r -- "ARM $name: PASS  T325-gate-fired=$fired rescue-path-reached=$reached   [pre-T325 line: rescue-reached=$legacy_reached, and it can say NOTHING else]"
    PASS=$((PASS+1))
  else
    print -r -- "ARM $name: FAIL  T325-gate-fired=$fired (want $want_fire) rescue-path-reached=$reached (want $want_rescue)"
    FAIL=$((FAIL+1)); FAILED+=("$name")
  fi
  for l in ${LOGBUF+"${LOGBUF[@]}"}; do print -r -- "      $l"; done
}

print -r -- "=== LEGITIMATE ARMS — the gate must stay QUIET ==="

# S1 — a spotless worktree. The sweep skips it, silently, exactly as before.
d=$(mkwt s1) || exit 2
run S1_clean_worktree 0 0 "$d"

# S2 — a worktree with IGNORED content only (.DS_Store, a toolchain tree). T324
# measured this population on the live repo: the ignored paths here are layout and
# reproducible toolchain, not work. The gate must not fire.
d=$(mkwt s2) || exit 2
printf 'junk' > "$d/.DS_Store"; mkdir -p "$d/toolchain"; printf 'go' > "$d/toolchain/go"
run S2_ignored_content_only 0 0 "$d"

# S3 — an ORDINARY dirty worktree: a killed worker's uncommitted deliverable. The
# rescue path must still be reached, and the new block must not intercept it.
d=$(mkwt s3) || exit 2
printf 'new deliverable\n' > "$d/handoff.md"
run S3_ordinary_dirty_worktree 0 1 "$d"

print
print -r -- "=== HIDDEN-WORK ARMS — the gate must FIRE, and the pre-T325 line could not ==="

# S4 — THE SHAPE THAT COST 61 BYTES IN T318's DRIVE. Content overwritten behind an
# `--assume-unchanged` bit: `git status --porcelain` is EMPTY, the sweep used to
# `continue` in silence, and (before T324) the prune loop then deleted the
# worktree.
d=$(mkwt s4) || exit 2
( cd "$d" && git update-index --assume-unchanged worker-output.txt && printf 'DESTROYED\n' > worker-output.txt )
run S4_skip_bit_hides_content 1 0 "$d"

# S5 — `--skip-worktree`, the other bit (tagged `S`, not lowercase).
d=$(mkwt s5) || exit 2
( cd "$d" && git update-index --skip-worktree worker-output.txt && printf 'DESTROYED\n' > worker-output.txt )
run S5_skip_worktree_bit 1 0 "$d"

# S6 — untracked worker output hidden from a bare `--porcelain` by
# `status.showUntrackedFiles=no`. T324's TERM 2; the sweep inherits it.
d=$(mkwt s6) || exit 2
( cd "$d" && git config status.showUntrackedFiles no )
printf 'a whole handoff nobody can see\n' > "$d/handoff.md"
run S6_untracked_hidden_by_config 1 0 "$d"

print
print -r -- "================================================================"
print -r -- "TOTAL: PASS=$PASS FAIL=$FAIL"
if (( FAIL != 0 )); then
  print -r -- "FAILED: ${FAILED[*]}"
  print -r -- "scratch kept: $ROOT"
  exit 1
fi
print -r -- "scratch kept: $ROOT"
exit 0
