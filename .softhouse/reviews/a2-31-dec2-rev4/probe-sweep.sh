#!/bin/bash
# A2-31 PROBE — the WHOLE-REPO sweep for every claim DEC-2 rev 4 says it retracted or
# corrected. NOT scoped to the ADR: every previous sweep was, and that is precisely why
# the retracted guard-existence claim survived one FILE over (T224), and why it survived a
# SECOND file over into .softhouse/guards/ledgerguard/main.go:1, which nobody has raised.
#
# It sweeps for the CLAIM in several spellings, never for one sentence.
#
# `git grep` over TRACKED CONTENT, deliberately: a plain recursive grep over this checkout
# takes many minutes (1.3M lines of capture dumps) and the untracked residue is /tmp scratch
# and toolchain. Every artefact a ratifier could read is tracked.
#
# READ-ONLY: git grep only. Nothing is written.
set -u
cd /Users/buv/gerege-nbfi/.claude/worktrees/agent-a3fcb4c7f1ea451ee || exit 1
echo "worktree HEAD: $(git rev-parse --short HEAD)"

sweep() {
  local label="$1"; shift
  echo
  echo "############################################################"
  echo "## $label"
  echo "############################################################"
  for pat in "$@"; do
    echo "--- pattern: $pat"
    # exclude this script's own pattern list from its own results
    git grep -n -i -E "$pat" -- . 2>/dev/null | grep -v 'a2-31-dec2-rev4/probe-sweep.sh' | cut -c1-260
  done
}

sweep "R1 — 'no ledger vector CAN exist' (ADMISSION-impossibility; retracted in rev 3)" \
  'no .?ledger.? vector (can|could) exist' \
  'zero .?ledger.? vectors (can|could) exist' \
  'can be admitted at all' \
  'ledger.{0,20}vector.{0,20}cannot be admitted'

sweep "R2 — 'no guard for I-3/I-4 exists' / '4.4.1 records it as not existing' (T208 built it)" \
  'no guard for either' \
  'no such guard exists' \
  'records as not existing' \
  'record[s]? .{0,25}as not existing' \
  '4\.4\.1 (records|record)'

sweep "R3 — 'three of its FOUR detection classes' (P-67; the guard declares SEVEN)" \
  'of (its |the )?four detection' \
  '3 of 4 detection' \
  'three of four detection' \
  'four detection class'

sweep "R4 — 'three of SEVEN inspected an empty population' (A2-31 MEASURES it as FOUR)" \
  'three of (its |the )?seven' \
  'three of the guard' \
  'SEVEN DETECTION CLASSES'

sweep "R5 — FU-T208-1: 'the head DROPS CANNOT-CATCH on the pass path' (T209 closed it)" \
  'DROPS on the pass path' \
  'head (swallows|drops) CANNOT-CATCH'

sweep "R6 — A2-8 F-1: 'the hard guards are scoped to loanschedule' (T166 widened them)" \
  'scoped to .?loanschedule' \
  'guards? (are|were) scoped to'
