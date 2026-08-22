#!/bin/bash
# T243 RED DRIVE 1 — the six DELIBERATELY WRONG ledger implementations, driven RED
# THROUGH `bash .softhouse/conformance.sh`, which is the route P-45 says must run
# them. Not through the Go binary and not through `go test`: A2-34 already proved
# both of those work, and that was exactly the finding.
#
# ENGINE AND FLAGS (P-33 / P-53 / P-75). Every search below is `/usr/bin/grep` by
# ABSOLUTE PATH — BSD grep 2.6.0-FreeBSD — with LC_ALL=C and -a. A bare `grep` in
# an agent shell is a FUNCTION that execs ugrep with `--ignore-files` silently
# prepended, and `rg` does not exist in a script at all (P-75); neither appears
# here. The repository root comes from `git rev-parse --show-toplevel`, never from
# a hard-coded worktree path, so this instrument cannot acquire a dead `cd` the
# day this worktree is deleted (T238's fail-open class). Calibration is not a
# separate stanza: every arm names a fixed string that must be FOUND and the
# CONTROL arms name strings that must be ABSENT, so a broken matcher fails the
# run rather than quietly agreeing with it.
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
IMPL=nexus/internal/apps/ledger/conformance/impl.go
PASS=0; FAIL=0
RC=0

# RESTORE FROM A BYTE COPY TAKEN BEFORE ANY MUTATION, NOT FROM `git checkout --`.
# Measured the hard way in this task's own first run: `git checkout -- <file>`
# restores the file to HEAD, which silently DELETES any uncommitted work in it,
# and the next arm then ran against a tree that did not compile. A red drive
# whose restore depends on what has been committed is a red drive that behaves
# differently depending on when you run it.
BACKUP="$(mktemp -d -t t243-rd1)"
cp "$IMPL" "$BACKUP/impl.go"
restore() { cp "$BACKUP/impl.go" "$IMPL"; }
trap 'restore; rm -rf "$BACKUP"' EXIT   # P-54: guarded on EVERY exit path

ok()  { echo "  OK   $*"; PASS=$((PASS+1)); }
bad() { echo "  ***  $*"; FAIL=$((FAIL+1)); }

run() { # run <tag>   -> exit code in $RC, output in $LOG/<tag>.txt
  local tag="$1"
  set +e
  bash .softhouse/conformance.sh > "$LOG/$tag.txt" 2>&1
  RC=$?
  set -e
}

want_line() { # want_line <tag> <label> <fixed string>
  local tag="$1" label="$2" needle="$3" n
  n=$(LC_ALL=C /usr/bin/grep -c -aF -- "$needle" "$LOG/$tag.txt" || true)
  if [ "${n:-0}" -gt 0 ]; then ok "[$label] found ($n): $needle"
  else bad "[$label] NOT FOUND: $needle"; fi
}

want_absent() {
  local tag="$1" label="$2" needle="$3" n
  n=$(LC_ALL=C /usr/bin/grep -c -aF -- "$needle" "$LOG/$tag.txt" || true)
  if [ "${n:-0}" -eq 0 ]; then ok "[$label] absent as required: $needle"
  else bad "[$label] PRESENT but must be absent ($n): $needle"; fi
}

proven_applied() { # proven_applied <file> <fixed string now expected>
  local f="$1" s="$2" n
  n=$(LC_ALL=C /usr/bin/grep -c -aF -- "$s" "$f" || true)
  if [ "${n:-0}" -gt 0 ]; then echo "  perturbation PROVEN APPLIED in $f"
  else bad "PERTURBATION DID NOT APPLY to $f — the case below would prove nothing"; fi
}

echo "T243 RED DRIVE 1 — six wrong ledger implementations, through conformance.sh"
echo "commit : $(git rev-parse HEAD)"
echo "vectors: $(git rev-parse HEAD:.softhouse/vectors)"
echo

echo "=================================================================="
echo "BASELINE — A2-34's F-7, re-derived. conformance.sh has no"
echo "--ledger-impl option, and it never runs go test."
echo "=================================================================="
set +e
bash .softhouse/conformance.sh --ledger-impl ledger-wrong-truncating > "$LOG/00-baseline.txt" 2>&1
echo "  exit=$? for: bash .softhouse/conformance.sh --ledger-impl ledger-wrong-truncating"
set -e
LC_ALL=C /usr/bin/grep -aF 'unknown option' "$LOG/00-baseline.txt" || true
echo -n "  occurrences of the string 'go test' in .softhouse/conformance.sh : "
LC_ALL=C /usr/bin/grep -c -aF 'go test' .softhouse/conformance.sh || true
echo "  (the flag is still not an option of this SCRIPT, and it should not be:"
echo "   the six are now run BY the script on every graded run, which is the fix.)"
echo

echo "=================================================================="
echo "CONTROL 0 — the wired harness over the pristine tree must be GREEN,"
echo "and must SAY it executed all six. Anti-no-op for every arm below."
echo "=================================================================="
run control0
echo "  exit=$RC"
want_line control0 control0 "VERDICT: PASS (exit 0)"
want_line control0 control0 "all 6 wrong ledger implementations DIED through this harness, not by hand."
want_line control0 control0 "KILLED  ledger-wrong-truncating"
want_line control0 control0 "KILLED  ledger-wrong-netting-totals"
want_line control0 control0 "KILLED  ledger-wrong-split-drift"
want_line control0 control0 "KILLED  ledger-wrong-code-ignored"
want_line control0 control0 "KILLED  ledger-wrong-header-refusing"
want_line control0 control0 "KILLED  ledger-wrong-manual-permission-ignored"
want_absent control0 control0 "SURVIVED"
if [ "$RC" -eq 0 ]; then ok "[control0] exit 0"; else bad "[control0] exit $RC, wanted 0"; fi
echo

echo "=================================================================="
echo "RED 1 — A WRONG IMPLEMENTATION THAT STOPS BEING WRONG. truncating is"
echo "        made to return the CORRECT port's answer verbatim. Its"
echo "        registration, its name, its declared defect and every vector"
echo "        are untouched, so the only thing that changed is whether the"
echo "        corpus can still tell it apart. This is the shape a green"
echo "        conformance.sh run could not see before today."
echo "=================================================================="
python3 - "$IMPL" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = ("func (truncatingPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {\n"
       "\tbase, ref, err := GoPoster{}.PostEntry(req)")
new = ("func (truncatingPoster) PostEntry(req Request) (PostedEntry, *Refusal, error) {\n"
       "\tif true {\n"
       "\t\treturn GoPoster{}.PostEntry(req) // T243 RED DRIVE - deliberately no longer wrong\n"
       "\t}\n"
       "\tbase, ref, err := GoPoster{}.PostEntry(req)")
assert s.count(old) == 1, s.count(old)
open(p, 'w', encoding='utf-8').write(s.replace(old, new))
PY
proven_applied "$IMPL" "T243 RED DRIVE - deliberately no longer wrong"
run red1
echo "  exit=$RC"
want_line red1 RED-1 "SURVIVED ledger-wrong-truncating"
want_line red1 RED-1 "A DELIBERATELY WRONG LEDGER IMPLEMENTATION SURVIVED THE CORPUS."
want_line red1 RED-1 "EXIT 2 — no verdict is available. This is NOT a pass."
# NOT `want_absent "VERDICT: PASS (exit 0)"`. MEASURED, and reported rather than
# smoothed: that line IS still printed on a red run, because it is the BINARY's
# verdict over the vector corpus and this gate runs after the report, exactly as
# gate_exemption_census does. What must be true is that the RUN does not end in a
# pass and that the stale line is explicitly WITHDRAWN in the output a reader
# sees. Both are asserted here instead.
want_line red1 RED-1 "IT IS"
want_line red1 RED-1 "WITHDRAWN BY THIS GATE."
if [ "$RC" -eq 2 ]; then ok "[RED-1] exit 2"; else bad "[RED-1] exit $RC, wanted 2"; fi
restore
echo

echo "=================================================================="
echo "RED 2 — INFLATION. Register a SEVENTH wrong implementation. It dies"
echo "        like the other six, so EVERY per-implementation arm stays"
echo "        green and only the POPULATION PIN can notice. This is the"
echo "        direction a count-free loop misses completely: a registered"
echo "        wrong implementation that nobody ever decided to execute."
echo "=================================================================="
python3 - "$IMPL" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
anchor = '\tRegisterWrong("ledger-wrong-truncating",'
add = ('\tRegisterWrong("ledger-wrong-t243-reddrive",\n'
       '\t\t"T243 RED DRIVE - a seventh registration nothing decided to execute",\n'
       '\t\ttruncatingPoster{})\n')
assert s.count(anchor) == 1
open(p, 'w', encoding='utf-8').write(s.replace(anchor, add + anchor))
PY
proven_applied "$IMPL" "ledger-wrong-t243-reddrive"
run red2
echo "  exit=$RC"
want_line red2 RED-2 "WRONG-IMPLEMENTATION POPULATION 7, PINNED 6."
want_line red2 RED-2 "An added one must be executed here in the same commit that registers it"
want_line red2 RED-2 "WITHDRAWN BY THIS GATE."
if [ "$RC" -eq 2 ]; then ok "[RED-2] exit 2"; else bad "[RED-2] exit $RC, wanted 2"; fi
restore
echo

echo "=================================================================="
echo "RED 3 — DEFLATION, and it is caught by a DIFFERENT mechanism, which"
echo "        is worth recording rather than assuming. Withdraw one wrong"
echo "        implementation from the registry entirely. The population"
echo "        pin is NOT what fires first: admit.go refuses every vector"
echo "        whose graded_against names an implementation nobody can run,"
echo "        so the run dies further upstream. Both are exit 2 and the"
echo "        diagnostic is asserted, never the code alone (P-62)."
echo "=================================================================="
python3 - "$IMPL" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = ('\tRegisterWrong("ledger-wrong-split-drift",\n'
       '\t\t"keeps the entry internally balanced (I-1 holds) while the splits sum to ONE MINOR UNIT less "+\n'
       '\t\t\t"than the transaction amount the caller requested (I-2 fails). It is the implementation "+\n'
       '\t\t\t"that proves I-2 is not a restatement of I-1",\n'
       '\t\tsplitDriftPoster{})\n')
new = '\t_ = splitDriftPoster{} // T243 RED DRIVE - withdrawn from the registry\n'
assert s.count(old) == 1, s.count(old)
open(p, 'w', encoding='utf-8').write(s.replace(old, new))
PY
proven_applied "$IMPL" "T243 RED DRIVE - withdrawn from the registry"
run red3
echo "  exit=$RC"
want_line red3 RED-3 "ledger-wrong-split-drift"
want_absent red3 RED-3 "VERDICT: PASS (exit 0)"
if [ "$RC" -eq 2 ]; then ok "[RED-3] exit 2"; else bad "[RED-3] exit $RC, wanted 2"; fi
echo "  --- what actually refused, verbatim: ---"
LC_ALL=C /usr/bin/grep -aF -m 3 'ledger-wrong-split-drift' "$LOG/red3.txt" || true
restore
echo

echo "=================================================================="
echo "GREEN AGAIN — the anti-no-op close. If this arm ever fails, the gate"
echo "        has stopped being a gate and become an unconditional refusal."
echo "=================================================================="
run green1
echo "  exit=$RC"
want_line green1 GREEN "VERDICT: PASS (exit 0)"
want_line green1 GREEN "all 6 wrong ledger implementations DIED through this harness, not by hand."
if [ "$RC" -eq 0 ]; then ok "[GREEN] exit 0"; else bad "[GREEN] exit $RC, wanted 0"; fi
echo
echo -n "  impl.go differs from its pre-mutation copy (0 = byte-identical): "
if cmp -s "$BACKUP/impl.go" "$IMPL"; then echo 0; else echo 1; fi
echo

echo "=================================================================="
echo "RED DRIVE 1: $PASS passed, $FAIL failed"
echo "=================================================================="
[ "$FAIL" -eq 0 ]
