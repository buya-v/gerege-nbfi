#!/bin/bash
# T382 — sharper drive of the SECTION 4 RESIDUAL.
#
# 30-saturation-audit.sh happened to pick CAPTURE-PLAN.md, one of the TWO files section 4
# already reports as DIFFER, so the delta was only the MANIFEST MISMATCH line. This drives a
# target that is CURRENTLY BYTE-IDENTICAL — .softhouse/capture/tierA-a2/manifest.py, the
# script that writes the manifest — so the before/after is unambiguous:
#     control:  428 byte-identical, 2 DIFFER   run-all EXIT 0
#     mutated:  427 byte-identical, 3 DIFFER   run-all EXIT ?
set -u
# HOST STATE IS A PARAMETER, NOT A LITERAL (guard_no_host_state_in_lint_corpus).
# A /tmp path assigned to a name in a tracked instrument is shared across worktrees,
# absent from every commit and deleted on reboot. Supply them:
#   T382_CLONE=<throwaway clone> T382_OUT=<scratch dir> bash <this script>
# The committed transcripts were produced with T382_OUT=/tmp/t382-out and the clone
# named in each transcript's first line.
SC="${T382_CLONE:?set T382_CLONE to a throwaway clone of this repo}"
O="${T382_OUT:?set T382_OUT to a scratch output directory}"
T=".softhouse/capture/tierA-a2/manifest.py"
mkdir -p "$O"

git -C "$SC" checkout -q pinmerge
git -C "$SC" reset --hard -q HEAD
git -C "$SC" clean -fdq
echo "at: $(git -C "$SC" log --oneline -1)"
echo "target (currently byte-identical to the fork sha): $T"

echo
echo "### CONTROL"
( cd "$SC" && python3 .softhouse/reviews/A2-11/verify-manifest-independently.py ) > "$O/sat31-00-sec4-control.txt" 2>&1
echo "  section 4 EXIT=$?"
grep -E 'byte-identical fork-vs-today|DIFFER  |manifest hash agrees' "$O/sat31-00-sec4-control.txt"
( cd "$SC" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$O/sat31-01-runall-control.txt" 2>&1
echo "  run-all   EXIT=$?"
grep -E '^  (4|10) |sections run' "$O/sat31-01-runall-control.txt"
git -C "$SC" checkout -q -- .

echo
echo "### MUTATED — one line appended to $T"
printf '\n# T382-SATURATION-PROBE\n' >> "$SC/$T"
( cd "$SC" && python3 .softhouse/reviews/A2-11/verify-manifest-independently.py ) > "$O/sat31-02-sec4-mutated.txt" 2>&1
echo "  section 4 EXIT=$?  (adjudicated 1 — SATURATED)"
grep -E 'byte-identical fork-vs-today|DIFFER  |manifest hash agrees|DIFF manifest.py|MANIFEST MISMATCH manifest.py' "$O/sat31-02-sec4-mutated.txt"
( cd "$SC" && python3 .softhouse/reviews/A2-11/verify-capture-integrity.py ) > "$O/sat31-03-sec10-mutated.txt" 2>&1
echo "  section 10 EXIT=$?  (the T374 guard — out/ and req/ ONLY, so blind here)"
( cd "$SC" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$O/sat31-04-runall-mutated.txt" 2>&1
echo "  run-all   EXIT=$?"
grep -E '^  (4|10) |sections run|RUN-ALL VERDICT' "$O/sat31-04-runall-mutated.txt"
git -C "$SC" checkout -q -- .

echo
echo "### CONTROL AGAIN"
( cd "$SC" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$O/sat31-05-runall-control-again.txt" 2>&1
echo "  run-all   EXIT=$?"
git -C "$SC" checkout -q -- .

echo
echo "### is run-all.sh (and therefore section 10) invoked by the graded bar at all?"
grep -c 'run-all.sh' /Users/buv/gerege-nbfi/.claude/worktrees/agent-a5c55c8ed65c59f4b/.softhouse/conformance.sh || echo "  0 occurrences of run-all.sh in conformance.sh"
