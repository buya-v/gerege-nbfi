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

LOG="$R/.softhouse/capture/t243-wiring/evidence"
mkdir -p "$LOG"
PLANT="$R/.softhouse/capture/t243-wiring/evidence/planted-failopen-sweep.sh"
PASS=0; FAIL=0
RC=0

cleanup() {
  git rm -q --cached --ignore-unmatch -- "$PLANT" >/dev/null 2>&1 || true
  rm -f "$PLANT"
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

echo "T243 RED DRIVE 2 — T238's fail-open linter, through conformance.sh"
echo "commit : $(git rev-parse HEAD)"
echo

echo "=================================================================="
echo "CONTROL 0 — the wired harness over the pristine tree. The linter"
echo "runs, censuses the WHOLE repository, and its frontier equals the pin."
echo "=================================================================="
run control0
echo "  exit=$RC"
want_line control0 control0 "CENSUS fail-open instruments"
want_line control0 control0 "frontier == pinned (all 9 rows, by path)."
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
want_line green1 GREEN "frontier == pinned (all 9 rows, by path)."
want_line green1 GREEN "VERDICT: PASS (exit 0)"
if [ "$RC" -eq 0 ]; then ok "[GREEN] exit 0"; else bad "[GREEN] exit $RC, wanted 0"; fi
echo

echo "=================================================================="
echo "RED DRIVE 2: $PASS passed, $FAIL failed"
echo "=================================================================="
[ "$FAIL" -eq 0 ]
