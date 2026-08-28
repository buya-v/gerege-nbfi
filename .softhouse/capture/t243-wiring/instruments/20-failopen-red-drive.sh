#!/bin/bash
# T243 RED DRIVE 2 — T238's FAIL-OPEN LINTER, driven RED THROUGH
# `bash .softhouse/conformance.sh`, the route that now runs it.
#
# T238 shipped the linter UNWIRED and said so loudly: "Nobody may cite it as an
# enforced control until it is wired." Wiring it without driving it red through
# the wired route would have reproduced the P-45 shape one level in, so this
# script plants a genuinely fail-open instrument, watches a GRADED RUN go EXIT 2,
# removes it, and watches the run go green again.
#
# THE PLANTED INSTRUMENT IS THE REAL SHAPE, not a token. It is a tracked .sh that
# searches the repository, hard-`cd`s into a directory that does not exist, and
# catches the failure with a `|| echo` arm that prints reassurance — i.e. C1 AND
# C2, the TIER 1 combination T238 MEASURED as "exit 0, prints a negative,
# measured nothing". Before it is put in front of conformance.sh it is RUN, and
# its own fail-open behaviour is recorded, so the thing the harness refuses is
# demonstrably fail-open rather than merely lint-positive.
#
# ENGINE AND FLAGS (P-33 / P-53 / P-75): `/usr/bin/grep` by absolute path, BSD
# grep 2.6.0-FreeBSD, LC_ALL=C -a. No bare `grep`, no `rg`. The repo root comes
# from `git rev-parse --show-toplevel`, so this instrument cannot itself acquire
# the dead `cd` it is about to plant deliberately.
set -euo pipefail

R="$(git rev-parse --show-toplevel)"
cd "$R"
export GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go
export GOPATH=/Users/buv/gerege-nbfi/.softhouse/toolchain/gopath
export GOCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gocache
export GOMODCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache
export PATH="$GOROOT/bin:$PATH"

# T114: THE DEFAULT DESTINATION IS COMMITTED EVIDENCE. control0.txt, red1.txt,
# green1.txt and plant-behaviour.txt under that directory are in the record, so a
# re-run in place OVERWRITES evidence rather than superseding it. The destination
# is therefore overridable and the DEFAULT IS UNCHANGED, so the original
# invocation behaves byte-for-byte as before while a later worker driving this
# instrument red can send its transcript to scratch. T258 drove it both ways
# through this variable.
LOG="${T243_RED_DRIVE_LOG:-$R/.softhouse/capture/t243-wiring/evidence}"
mkdir -p "$LOG"
PLANT="$R/.softhouse/capture/t243-wiring/evidence/planted-failopen-sweep.sh"
PASS=0; FAIL=0
RC=0

cleanup() {
  git rm -q --cached --ignore-unmatch -- "$PLANT" >/dev/null 2>&1 || true
  rm -f "$PLANT"
  # T258: the pin block is scratch, never a file left behind in an evidence directory.
  rm -f "${PINBLOCK:-}"
}
trap cleanup EXIT          # P-54: the tree is restored on EVERY exit path, not just the happy one

ok()  { echo "  OK   $*"; PASS=$((PASS+1)); }
bad() { echo "  ***  $*"; FAIL=$((FAIL+1)); }

run() { # run <tag>
  local tag="$1"
  set +e
  bash .softhouse/conformance.sh > "$LOG/$tag.txt" 2>&1
  RC=$?
  set -e
}

want_line() {
  local tag="$1" label="$2" needle="$3" n
  n=$(LC_ALL=C /usr/bin/grep -c -aF -- "$needle" "$LOG/$tag.txt" || true)
  if [ "${n:-0}" -gt 0 ]; then ok "[$label] found ($n): $needle"
  else bad "[$label] NOT FOUND: $needle"; fi
}

# ---------------------------------------------------------------------------
# THE PINNED CARDINAL IS DERIVED FROM THE PIN, NEVER TYPED HERE.  [T258, P-80]
# ---------------------------------------------------------------------------
# WHAT WAS HERE BEFORE, AND WHY IT WAS A DEFECT RATHER THAN A STALE NUMBER.
# Two `want_line` checks asserted a LITERAL equality sentence naming NINE rows.
# The frontier was nine when T243 wrote this. T248 moved it to ten and T252 to
# eleven, and BOTH corrected the count WHERE IT IS NAMED (FAILOPEN_PIN_FILE_LIST
# in conformance.sh) and not WHERE IT IS RESTATED (here). MEASURED at T258's own
# commit before any edit, this instrument failed on its OWN CONTROL ARM with
# `NOT FOUND` on that sentence, 11 passed / 2 failed (transcript:
# .softhouse/capture/t255-frontier-rot/transcripts/10-BEFORE-red-drive.txt).
#
# WHY DERIVING AND NOT RETYPING. Replacing the nine with the current count buys
# exactly one cycle and leaves the mechanism — a cardinal maintained in two
# places — completely intact. P-80's rule is the one applied here: THE FIX IS
# NEVER THE NEW NUMBER, IT IS TO MAKE THE SECOND SITE READ THE FIRST. So the
# count below is COUNTED OUT OF FAILOPEN_PIN_FILE_LIST at run time. The next
# task to move the frontier edits one place, as it always should have.
#
# WHY NOT SIMPLY DROP THE CARDINAL AND ASSERT THE BARE INVARIANT. Asserting only
# the words "frontier == pinned" was the cheaper option and it is strictly
# weaker: the harness prints that sentence only when the two SETS are equal, so
# it can never disagree with itself — checking it tells you the harness ran, not
# that the pin is the pin this instrument was written about. Counting the pin
# here, out of the harness SOURCE, and requiring the harness OUTPUT to name that
# same number, is a genuine two-source agreement: it fires if the pin list and
# the printed cardinal ever diverge, which is the failure the derivation inside
# conformance.sh (T300) is itself there to prevent. Both are kept.
#
# FAIL-CLOSED. If the pin block cannot be read — renamed, reformatted, moved —
# the derivation yields no digits and this instrument DIES here with a distinct
# message. It must never fall back to 0 and then report a frontier mismatch,
# because a derivation failure and a real frontier movement are different events
# and reporting one as the other is the whole class this rig exists to refuse.
PINSRC="$R/.softhouse/conformance.sh"
PINBLOCK="$(mktemp "${TMPDIR:-/tmp}/t243-pinblock.XXXXXXXXXX")"
LC_ALL=C /usr/bin/sed -n '/^FAILOPEN_PIN_FILE_LIST="/,/"$/p' "$PINSRC" > "$PINBLOCK"
PINNED_ROWS="$(LC_ALL=C /usr/bin/grep -c -aE '^(FAILOPEN_PIN_FILE_LIST=")?TIER[0-9]' "$PINBLOCK")"
case "${PINNED_ROWS:-}" in ''|*[!0-9]*) PINNED_ROWS=0 ;; esac
if [ "$PINNED_ROWS" -lt 1 ]; then
  echo "  ***  [pin] COULD NOT DERIVE the pinned frontier cardinal from FAILOPEN_PIN_FILE_LIST"
  echo "  ***        source: $PINSRC"
  echo "  ***        block read: $PINBLOCK ($(LC_ALL=C /usr/bin/grep -ac '' "$PINBLOCK") line(s))"
  echo "  ***  This is a DERIVATION failure, not a frontier movement. No count is available,"
  echo "  ***  so no assertion about the frontier is made. RED DRIVE 2 ABORTED."
  exit 1
fi
FRONTIER_EQ="frontier == pinned (all $PINNED_ROWS rows, by path)."

# harness_pinned <tag> — the cardinal the HARNESS published, read out of its own
# transcript. Deliberately anchored on the DIGITS after "pinned at" and on
# nothing that follows them: T258 MEASURED that the two neighbouring
# restatements — .softhouse/capture/t252-tier3/instruments/50-conformance-red-
# drive.py:122 and .softhouse/reviews/t262-verdict-predicate/bar_check_t262.sh:55
# — assert that cardinal WITH A TRAILING PERIOD, and T300 reworded the harness
# line so the period is gone. Both are FALSE TODAY with the count still correct,
# which is a rot no search for the number can find. A cardinal check must bind to
# the digits, never to the sentence around them.
harness_pinned() {
  LC_ALL=C /usr/bin/sed -n 's/^.*; frontier [0-9][0-9]*, pinned at \([0-9][0-9]*\).*$/\1/p' "$LOG/$1.txt"
}

want_pin_agreement() { # want_pin_agreement <tag> <label>
  local tag="$1" label="$2" hp
  hp="$(harness_pinned "$tag")"
  if [ -z "$hp" ]; then
    bad "[$label] the harness published NO 'frontier N, pinned at P' cardinal at all"
  elif [ "$hp" = "$PINNED_ROWS" ]; then
    ok "[$label] pin agreement: harness published 'pinned at $hp'; FAILOPEN_PIN_FILE_LIST counts $PINNED_ROWS"
  else
    bad "[$label] PIN DISAGREEMENT: harness published 'pinned at $hp' but FAILOPEN_PIN_FILE_LIST counts $PINNED_ROWS"
  fi
}

echo "T243 RED DRIVE 2 — T238's fail-open linter, through conformance.sh"
echo "commit : $(git rev-parse HEAD)"
echo "pinned frontier rows, DERIVED from FAILOPEN_PIN_FILE_LIST (never typed here): $PINNED_ROWS"
echo "the equality line this run will require: $FRONTIER_EQ"
echo

echo "=================================================================="
echo "CONTROL 0 — the wired harness over the pristine tree. The linter"
echo "runs, censuses the WHOLE repository, and its frontier equals the pin."
echo "=================================================================="
run control0
echo "  exit=$RC"
want_line control0 control0 "CENSUS fail-open instruments"
want_line control0 control0 "$FRONTIER_EQ"
want_pin_agreement control0 control0
want_line control0 control0 "VERDICT: PASS (exit 0)"
if [ "$RC" -eq 0 ]; then ok "[control0] exit 0"; else bad "[control0] exit $RC, wanted 0"; fi
echo

echo "=================================================================="
echo "THE PLANT — a genuinely fail-open sweep, and its behaviour MEASURED"
echo "before it is put in front of the harness. If this stanza did not"
echo "show exit 0 over a negative it never measured, the refusal below"
echo "would be a lint opinion rather than a demonstrated defect."
echo "=================================================================="
# THE PLANT IS ASSEMBLED, NOT PASTED, AND THAT IS NOT STYLE. If the two lethal
# lines appeared LITERALLY in this instrument, the linter would classify THIS
# FILE as TIER 1 the moment it was committed — a dead absolute path and a
# printing failure arm are exactly what it detects, and it does not care that
# they are inside a heredoc. The frontier pin would then move because the red
# drive exists, and the red drive would be measuring itself. So the dead path
# and the `||` are composed from variables here and are literal only in the
# GENERATED file, which is the file under test and is never committed.
DEAD="$R/.claude/worktrees/agent-T243-DELETED-LONG-AGO"
OR='||'
{
  printf '%s\n' '#!/bin/sh'
  printf '%s\n' '# A DELIBERATELY FAIL-OPEN SWEEP planted by T243 RED DRIVE 2. Removed by the'
  printf '%s\n' '# script that plants it; it must never be committed.'
  printf 'WT=%s\n' "$DEAD"
  printf '%s\n' "for re in 'MinorUnits' 'DoubleEntryBalances'; do"
  printf '%s\n' '  echo "--- pattern: $re"'
  printf '  ( cd "$WT" && git grep -n -I -E "$re" -- . ) %s echo "   (no hits)"\n' "$OR"
  printf '%s\n' 'done'
} > "$PLANT"
echo "  the planted file, verbatim:"
LC_ALL=C /usr/bin/sed 's/^/    | /' "$PLANT"
chmod +x "$PLANT"
git add -f -- "$PLANT"
set +e
sh "$PLANT" > "$LOG/plant-behaviour.txt" 2>&1
PRC=$?
set -e
echo "  the planted sweep, run on its own: exit=$PRC"
LC_ALL=C /usr/bin/grep -c -aF '(no hits)' "$LOG/plant-behaviour.txt" > "$LOG/plant-nohits.txt" || true
echo "  '(no hits)' lines it printed: $(cat "$LOG/plant-nohits.txt")"
echo "  hit lines it printed        : $(LC_ALL=C /usr/bin/grep -c -aE '^[^-]' "$LOG/plant-behaviour.txt" || true)"
if [ "$PRC" -eq 0 ]; then
  ok "[plant] exit 0 while reaching NO corpus — this is the fail-OPEN shape, measured, not asserted"
else
  bad "[plant] exit $PRC — the plant is not fail-open, so the refusal below proves less than claimed"
fi
echo

echo "=================================================================="
echo "RED — the same graded run, with the planted instrument tracked."
echo "=================================================================="
run red1
echo "  exit=$RC"
want_line red1 RED "THE FAIL-OPEN FRONTIER IS NOT THE PINNED FRONTIER"
want_line red1 RED "planted-failopen-sweep.sh"
want_line red1 RED "a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass."
if [ "$RC" -eq 2 ]; then ok "[RED] exit 2"; else bad "[RED] exit $RC, wanted 2"; fi
echo "  --- the frontier diff the harness printed: ---"
LC_ALL=C /usr/bin/grep -aF 'TIER' "$LOG/red1.txt" | LC_ALL=C /usr/bin/grep -aF '+' || true
echo
echo "  AND IT REFUSED BEFORE GRADING: the guard tally runs ahead of the"
echo "  reference-oracle probe, so no verdict was computed over a tree whose"
echo "  instruments cannot be trusted."
if LC_ALL=C /usr/bin/grep -aqF 'VERDICT: PASS' "$LOG/red1.txt"; then
  bad "[RED] a PASS verdict was printed on the refused run"
else
  ok "[RED] no verdict line at all on the refused run"
fi
echo

echo "=================================================================="
echo "GREEN AGAIN — remove the plant; the same command goes back to PASS."
echo "=================================================================="
cleanup
run green1
echo "  exit=$RC"
want_line green1 GREEN "$FRONTIER_EQ"
want_pin_agreement green1 GREEN
want_line green1 GREEN "VERDICT: PASS (exit 0)"
if [ "$RC" -eq 0 ]; then ok "[GREEN] exit 0"; else bad "[GREEN] exit $RC, wanted 0"; fi
echo

echo "=================================================================="
echo "RED DRIVE 2: $PASS passed, $FAIL failed"
echo "=================================================================="
[ "$FAIL" -eq 0 ]
