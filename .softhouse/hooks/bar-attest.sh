#!/usr/bin/env bash
# =============================================================================================
# BAR ATTESTATION.  [T412]   `bash .softhouse/hooks/bar-attest.sh [<commit-ish>]`
#
# Runs `bash .softhouse/conformance.sh` against a NAMED COMMIT'S TREE, materialised in scratch,
# and records the result in the attestation ledger keyed BY THAT TREE'S SHA.
#
# THIS IS THE ONLY WAY TO SATISFY THE DRIVER PUSH GATE'S C3, AND THAT IS DELIBERATE.
# The alternative -- letting the driver hand the gate an existing bar transcript -- was rejected:
# a transcript is bytes, and nothing in it binds it to the tree it claims to have graded. That is
# T314's witness-path forgery in a new costume. Here the tool checks the tree out ITSELF, so the
# tree it records is unforgeably the tree it graded.
#
# IT ALSO CLOSES INSTANCE 2 MECHANICALLY. On 2026-08-28 the driver ran the bar in a scratch merge
# directory, then pushed a merge commit whose tree had moved underneath it, and noticed only
# because it happened to compare two tree hashes by hand. This tool cannot make that mistake: it
# is given a commit, it resolves that commit's tree, it grades THAT, and the ledger row is the
# tree -- there is no path through it that grades one thing and records another.
#
# ACCEPTANCE, and every clause is checked in this order for a reason:
#   1. `grep -c 'probe = '` >= 1                  -- PRESENCE BEFORE VALUE. Four exit-2 paths in
#      conformance.sh run BEFORE the probe prints, including a failed HARD guard, so an ABSENT
#      probe line is not `down` -- it is "no verdict is available" (P-84).
#   2. every probe line reads `up`                -- an oracle outage is not a pass.
#   3. a `VERDICT: PASS` line is present.
#   4. the bar's exit status is 0.
# All four, or no attestation is written. A partial pass is not an attestation of anything.
#
# ENGINE (P-33/P-53): bash, git, POSIX grep/sed. Declared, not assumed.
# =============================================================================================
set -u

say() { printf 'bar-attest: %s\n' "$*"; }
die() { printf 'bar-attest: %s\n' "$*"; exit 3; }

REF="${1:-HEAD}"

TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || die "ABORT(3) -- \`git rev-parse --show-toplevel\` failed. Not inside a work tree."
[ -n "$TOPLEVEL" ] || die "ABORT(3) -- empty repository root."
COMMON="$(git rev-parse --git-common-dir 2>/dev/null)" \
  || die "ABORT(3) -- \`git rev-parse --git-common-dir\` failed."
case "$COMMON" in /*) : ;; *) COMMON="$TOPLEVEL/$COMMON" ;; esac

COMMIT="$(git rev-parse --verify --quiet "$REF^{commit}")" \
  || die "ABORT(3) -- '$REF' does not resolve to a commit."
TREE="$(git rev-parse --verify --quiet "$COMMIT^{tree}")" \
  || die "ABORT(3) -- could not resolve the tree of $COMMIT."

GATE_DIR="$COMMON/softhouse-driver-gate"
ATTEST="$GATE_DIR/attest.tsv"
mkdir -p "$GATE_DIR" || die "ABORT(3) -- could not create $GATE_DIR"

D="$(mktemp -d "${TMPDIR:-/tmp}/t412-attest.XXXXXXXXXX")" \
  || die "ABORT(3) -- could not create a scratch directory."
WT="$D/wt"

cleanup() {
  # The worktree registry entry is removed before the directory, and both are best-effort at
  # EXIT because a failed prune must not overwrite the exit status of the grading run itself.
  if [ -d "$WT" ]; then
    git worktree remove --force "$WT" >/dev/null 2>&1
  fi
  git worktree prune >/dev/null 2>&1
  if [ -n "${D:-}" ] && [ -d "$D" ]; then
    rm -rf "$D"
  fi
}
trap cleanup EXIT

say "commit $COMMIT"
say "tree   $TREE"
say "scratch worktree $WT"

# The FULL bar needs a real work tree with a real .git link -- guard_graded_root_is_this_tree and
# several guards call `git rev-parse --show-toplevel` and `git ls-files` from $REPO_ROOT. A bare
# checkout-index directory would not satisfy them, so this one uses `git worktree add --detach`,
# which is the shape every other task in this program already uses for merge-result grading, and
# it is pruned on exit.
git worktree add --detach "$WT" "$COMMIT" >"$D/wt-add.log" 2>&1 \
  || { LC_ALL=C sed -n '1,20p' "$D/wt-add.log"; die "ABORT(3) -- \`git worktree add\` failed for $COMMIT."; }

WTTREE="$(git -C "$WT" rev-parse --verify --quiet 'HEAD^{tree}')" \
  || die "ABORT(3) -- could not read the scratch worktree's HEAD tree."
if [ "$WTTREE" != "$TREE" ]; then
  die "ABORT(3) -- the scratch worktree checked out tree $WTTREE, not $TREE. REFUSING: grading one tree and recording another is the defect this tool exists to close."
fi

BAR="$WT/.softhouse/conformance.sh"
[ -f "$BAR" ] || die "ABORT(3) -- .softhouse/conformance.sh is absent from tree $TREE. It is the bar; its absence is a refusal and never a pass."

LOG="$D/bar.log"
say "running the bar (this takes minutes) ..."
( cd "$WT" || exit 9; bash .softhouse/conformance.sh ) >"$LOG" 2>&1
BARRC=$?
say "bar exit: $BARRC"

if [ "$BARRC" -eq 9 ]; then
  die "ABORT(3) -- could not enter the scratch worktree. 9 is this tool's own code for that, and it is never a bar verdict."
fi

# 1. PRESENCE BEFORE VALUE.
PROBE_N="$(LC_ALL=C grep -ac 'probe = ' "$LOG")"
case "${PROBE_N:-}" in ''|*[!0-9]*) PROBE_N=0 ;; esac
say "probe lines PRINTED: $PROBE_N"
if [ "$PROBE_N" -lt 1 ]; then
  say "REFUSED -- the probe line was NEVER PRINTED. Four exit-2 paths run before it, including a"
  say "  failed HARD guard. ABSENCE IS NOT \`down\`; it is 'no verdict is available' (P-84)."
  LC_ALL=C grep -aE '^conformance: (EXIT|.*REFUSED|.*FAILED)' "$LOG" | LC_ALL=C sed -n '1,20p'
  LC_ALL=C sed -n '$p' "$LOG"
  cp "$LOG" "$GATE_DIR/last-refused-bar.log" 2>/dev/null
  say "  transcript kept at ${GATE_DIR}/last-refused-bar.log"
  exit 1
fi

# 2. VALUE.
NOT_UP="$(LC_ALL=C grep -a 'probe = ' "$LOG" | LC_ALL=C grep -av 'probe = up')"
if [ -n "$NOT_UP" ]; then
  say "REFUSED -- a probe line does not read \`up\`:"
  printf '%s\n' "$NOT_UP" | LC_ALL=C sed -n '1,5p'
  cp "$LOG" "$GATE_DIR/last-refused-bar.log" 2>/dev/null
  exit 1
fi

# 3. VERDICT.
if ! LC_ALL=C grep -aq 'VERDICT: PASS' "$LOG"; then
  say "REFUSED -- no \`VERDICT: PASS\` line in the transcript."
  LC_ALL=C grep -a 'VERDICT' "$LOG" | LC_ALL=C sed -n '1,10p'
  cp "$LOG" "$GATE_DIR/last-refused-bar.log" 2>/dev/null
  exit 1
fi

# 4. EXIT STATUS.
if [ "$BARRC" -ne 0 ]; then
  say "REFUSED -- the bar exited $BARRC. A probe line and a verdict do not outrank a non-zero exit."
  cp "$LOG" "$GATE_DIR/last-refused-bar.log" 2>/dev/null
  exit 1
fi

VERDICT="$(LC_ALL=C grep -a 'VERDICT: PASS' "$LOG" | LC_ALL=C sed -n '1p' | LC_ALL=C tr '\t' ' ')"
printf 'FULL\t%s\t%s\t%s\t%s\n' "$TREE" "$COMMIT" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  "exit0 probe=${PROBE_N}xup ${VERDICT}" >>"$ATTEST" \
  || die "ABORT(3) -- could not append the attestation. An attestation that was not recorded is not an attestation."

cp "$LOG" "$GATE_DIR/attested-${TREE}.log" 2>/dev/null

say ""
say "ATTESTED FULL -- tree $TREE"
say "  exit 0, probe PRESENT x$PROBE_N all reading \`up\`, $VERDICT"
say "  ledger:     $ATTEST"
say "  transcript: ${GATE_DIR}/attested-${TREE}.log"
exit 0
