#!/bin/bash
# T433 / C-T423-1 — ARM F driven RED then GREEN *IN SITU*, inside the shipped section-10
# grader, plus every miss-by-one T433 could construct.
#
# T423 drove ARM F as a standalone 25-line instrument. That proves the COMPARISON works; it
# does not prove the SHIPPED grader carries it, and a guard that exists beside the grader
# instead of inside it is P-45. This script grades
# `.softhouse/reviews/A2-11/verify-capture-integrity.py` itself, at two refs, on real
# repositories in scratch clones.
#
# A GUARD YOU HAVE NOT SEEN FAIL IS NOT A GUARD (P-22). Every case below states the exit code
# it expects at BOTH refs, and a case that produces the expected code for the wrong reason is
# caught by also requiring the NAMED line to be present or absent.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298 — an instrument is held to the same rule as
# a graded path). Every location is a required parameter:
#
#   T433_SRC=<repo>  T433_CLONE=<scratch dir OUTSIDE the repo>  T433_OUT=<dir> \
#   T433_BEFORE=<sha carrying the PRE-ARM-F bytes>  T433_AFTER=<sha carrying ARM F> \
#   bash 20-t433-armf-in-situ-drive.sh
#
# EXIT 0  every case produced the expected code at both refs, for the stated reason.
# EXIT 1  at least one did not — named, never counted only.
# EXIT 3  the harness could not run. Never read as a result.
set -u

SRC="${T433_SRC:?T433_SRC must name the source repository}"
SCROOT="${T433_CLONE:?T433_CLONE must name a scratch directory OUTSIDE the repository}"
OUT="${T433_OUT:?T433_OUT must name the directory to write transcripts into}"
BEFORE="${T433_BEFORE:?T433_BEFORE must name the commit-ish carrying the PRE-ARM-F bytes}"
AFTER="${T433_AFTER:?T433_AFTER must name the commit-ish carrying ARM F}"

CAP=".softhouse/capture/tierA-a2"
INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
MAN="$CAP/MANIFEST.sha256"
PICK=".softhouse/capture/t393-t382-conditions/instruments/11-pick-targets.py"
LAUNDER=".softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py"
ADJ="out/A2-370-db-ledger-state.txt"      # ARM F's ONE adjudicated post-fork difference
FAB="T433-FABRICATED-OBSERVATION.http"

mkdir -p "$OUT" "$SCROOT" || exit 3
MATRIX="$OUT/MATRIX-armf.tsv"
: > "$MATRIX" || exit 3
printf 'case\tref\tsec10_rc\tverdict\tarmf_named\tarmf_at_tip\tarmf_moved\texpected_rc\tresult\n' >> "$MATRIX"

if ! TARGETS="$(python3 "$SRC/$PICK")"; then
  echo "REFUSED: could not pick mutation targets from $SRC." >&2; exit 3
fi
POSTFORK="$(printf '%s\n' "$TARGETS" | awk -F'\t' '$1=="POSTFORK"{print $2}')"
[ -n "$POSTFORK" ] || { echo "REFUSED: POSTFORK target came back empty" >&2; exit 3; }
echo "T433 ARM-F IN-SITU DRIVE"
echo "  BEFORE = $BEFORE   (section 10 WITHOUT ARM F)"
echo "  AFTER  = $AFTER   (section 10 WITH ARM F)"
echo "  post-fork mutation target = $POSTFORK   (MEASURED by 11-pick-targets.py, never typed)"
echo "  adjudicated target        = $ADJ"
echo

FAILURES=0
D="$SCROOT/t433-armf"

prepare() {   # prepare <ref>
  local ref="$1"
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
    git -C "$D" config user.email "t433@softhouse.local" || return 1
    git -C "$D" config user.name "T433" || return 1
  fi
  git -C "$D" reset --quiet --hard || return 1
  git -C "$D" clean -qfdx || return 1
  git -C "$D" checkout --quiet --detach "$ref" || return 1
  git -C "$D" reset --quiet --hard "$ref" || return 1
  return 0
}

# ---- mutations. Each returns non-zero if it could not do what it says, so a case can never
# ---- silently become a no-op and report the colour of an unmutated tree.
mut_none() { return 0; }

mut_residual() {            # T393's "unclosable" case: mutate post-fork obs + launder row
  printf '\nT433-RESIDUAL-MARKER\n' >> "$D/$CAP/$POSTFORK" || return 1
  python3 "$D/$LAUNDER" "$D" "$POSTFORK" >/dev/null || return 1
  git -C "$D" add -- "$CAP/$POSTFORK" "$MAN" || return 1
  git -C "$D" commit -q -m "T433 residual: post-fork observation mutated, manifest row rewritten in the SAME commit" || return 1
}

mut_born_at_tip() {         # boundary (iv-a): fabricate an observation AND its manifest row
  printf 'T433 fabricated observation, born at the tip.\n' > "$D/$CAP/out/$FAB" || return 1
  local d; d="$(shasum -a 256 "$D/$CAP/out/$FAB" | awk '{print $1}')" || return 1
  printf '%s  out/%s\n' "$d" "$FAB" >> "$D/$MAN" || return 1
  git -C "$D" add -- "$CAP/out/$FAB" "$MAN" || return 1
  git -C "$D" commit -q -m "T433 (iv-a): a fabricated observation added AT THE TIP with a matching manifest row" || return 1
}

mut_rename_and_mutate() {   # boundary (iv-b): rename + mutate + relabel the manifest row, one commit
  local new="RENAMED-$(basename "$POSTFORK")"
  git -C "$D" mv "$CAP/$POSTFORK" "$CAP/out/$new" || return 1
  printf '\nT433-RENAME-MUTATE-MARKER\n' >> "$D/$CAP/out/$new" || return 1
  local d; d="$(shasum -a 256 "$D/$CAP/out/$new" | awk '{print $1}')" || return 1
  perl -pi -e "s|^[0-9a-f]{64}(\s+\*?)\Q$POSTFORK\E\$|$d\$1out/$new|" "$D/$MAN" || return 1
  grep -q -E "^$d  out/$new\$" "$D/$MAN" || { echo "    (manifest row not relabelled)"; return 1; }
  git -C "$D" add -A -- "$CAP" || return 1
  git -C "$D" commit -q -m "T433 (iv-b): a post-fork observation RENAMED and mutated with its manifest row relabelled, all in ONE commit" || return 1
}

mut_adjudicated_further() { # the adjudicated entry mutated FURTHER + laundered
  printf '\nT433-ADJ-FURTHER-MARKER\n' >> "$D/$CAP/$ADJ" || return 1
  python3 "$D/$LAUNDER" "$D" "$ADJ" >/dev/null || return 1
  git -C "$D" add -- "$CAP/$ADJ" "$MAN" || return 1
  git -C "$D" commit -q -m "T433: ARM F's adjudicated entry mutated FURTHER, manifest laundered" || return 1
}

mut_adjudicated_reverted() {   # the adjudicated entry REVERTED to its birth bytes + laundered
  local birth
  birth="$(git -C "$D" log --diff-filter=A --format=%H -- "$CAP/$ADJ" | tail -1)" || return 1
  [ -n "$birth" ] || { echo "    (no birth commit for $ADJ)"; return 1; }
  git -C "$D" show "$birth:$CAP/$ADJ" > "$D/$CAP/$ADJ" || return 1
  python3 "$D/$LAUNDER" "$D" "$ADJ" >/dev/null || return 1
  git -C "$D" add -- "$CAP/$ADJ" "$MAN" || return 1
  git -C "$D" commit -q -m "T433: ARM F's adjudicated entry REVERTED to its birth bytes, manifest laundered" || return 1
}

mut_rename_and_rewrite() {  # boundary (iv-b2): rename + REPLACE the bytes, so git sees D+A
  # (iv-b) turned out to REFUSE, because git reports a high-similarity rename as R and ARM F
  # then has no ADD record at all. That answer depends on SIMILARITY. This case removes the
  # similarity: the file is renamed and its content wholly replaced, so git records a genuine
  # ADD at the new path, dated at the tip — which lands in (iv-a) and is UNGRADED, not
  # refused. Driving both is the only way to know which of the two answers is the real one.
  local new="REWRITTEN-$(basename "$POSTFORK")"
  git -C "$D" mv "$CAP/$POSTFORK" "$CAP/out/$new" || return 1
  printf 'T433 (iv-b2): every byte of this observation replaced, so no rename similarity remains.\n' \
    > "$D/$CAP/out/$new" || return 1
  local d; d="$(shasum -a 256 "$D/$CAP/out/$new" | awk '{print $1}')" || return 1
  perl -pi -e "s|^[0-9a-f]{64}(\s+\*?)\Q$POSTFORK\E\$|$d\$1out/$new|" "$D/$MAN" || return 1
  grep -q -E "^$d  out/$new\$" "$D/$MAN" || { echo "    (manifest row not relabelled)"; return 1; }
  git -C "$D" add -A -- "$CAP" || return 1
  git -C "$D" commit -q -m "T433 (iv-b2): a post-fork observation renamed AND wholly rewritten, manifest row relabelled, ONE commit" || return 1
}

mut_vacuity() {   # every post-fork observation born AT THE TIP: ARM F grades NOTHING
  # An orphan commit re-adds every tracked path in ONE commit, so every birth commit IS the
  # tip. Nothing on disk changes, so ARMs A-E are untouched: the ONLY thing that can move is
  # ARM F's own vacuity control. This is the RED half of "an arm that graded nothing reads
  # exactly like an arm that found no differences".
  # `--orphan` refuses over an existing branch name, and this function runs twice (BEFORE and
  # AFTER) in the SAME clone. Delete first, or the second call is a HARNESS FAILURE that looks
  # like a finding. Detach before deleting so the branch is never the checked-out one.
  git -C "$D" checkout -q --detach 2>/dev/null
  git -C "$D" branch -q -D t433-vacuity 2>/dev/null
  git -C "$D" checkout -q --orphan t433-vacuity || return 1
  git -C "$D" add -A || return 1
  git -C "$D" commit -q -m "T433 vacuity: every tracked path re-added in ONE commit, so every birth commit IS the tip" || return 1
}

run_case() {   # run_case <name> <mutfn> <expect_before> <expect_after>
  local name="$1" mutfn="$2" eb="$3" ea="$4" ref rc want tag
  # T433_CASES, when set, is a space-separated allowlist. It exists so a single case can be
  # re-driven after a harness fix without re-running the whole matrix; a run that used it says
  # so in the transcript, and the RECORDED matrix in out/ is always from an unfiltered run.
  if [ -n "${T433_CASES:-}" ] && ! printf ' %s ' "${T433_CASES}" | grep -q " $name "; then
    echo "  $name  SKIPPED (T433_CASES filter)"
    return 0
  fi
  for tag in BEFORE AFTER; do
    if [ "$tag" = BEFORE ]; then ref="$BEFORE"; want="$eb"; else ref="$AFTER"; want="$ea"; fi
    if ! prepare "$ref"; then
      echo "  $name/$tag: HARNESS FAILURE preparing the clone at $ref"; exit 3
    fi
    if ! "$mutfn"; then
      echo "  $name/$tag: HARNESS FAILURE applying the mutation — a case that did not mutate"
      echo "             would report the colour of a CLEAN tree, which is a null control."
      exit 3
    fi
    local t="$OUT/armf-case-$name-$tag.txt"
    ( cd "$D" && python3 "$INT" ) > "$t" 2>&1
    rc=$?
    local verdict named at_tip moved
    verdict="$(sed -n 's/^VERDICT: \([A-Z]*\).*/\1/p' "$t" | tail -1)"
    named="$(grep -c 'LAUNDERED-OR-MUTATED' "$t")"
    at_tip="$(grep -c 'UNGRADED-BORN-AT-TIP' "$t")"
    moved="$(grep -c 'ADJUDICATION MOVED' "$t")"
    local result="as expected"
    if [ "$rc" != "$want" ]; then result="*** UNEXPECTED ***"; FAILURES=$((FAILURES + 1)); fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$name" "$tag" "$rc" "${verdict:-none}" "$named" "$at_tip" "$moved" "$want" "$result" >> "$MATRIX"
    printf '  %-24s %-6s rc=%s %-8s named=%s born-at-tip=%s adj-moved=%s  expected %s  %s\n' \
      "$name" "$tag" "$rc" "${verdict:-none}" "$named" "$at_tip" "$moved" "$want" "$result"
  done
}

# name                       mutation                   BEFORE AFTER
run_case control              mut_none                   0 0
# THE CONDITION. T393 shipped this as an unclosable residual on a false impossibility.
# BEFORE: section 10 exits 0 / PASS on a mutated, laundered post-fork observation.
# AFTER : ARM F exits 1 and NAMES it. This single row is C-T423-1's whole close.
run_case residual-laundered   mut_residual               0 1
# ARM F's adjudication is not a hole: a FURTHER mutation moves it, and so does a REVERT.
run_case adjudicated-further  mut_adjudicated_further    0 1
run_case adjudicated-revert   mut_adjudicated_reverted   0 1
# BOUNDARY (iv-a) — DISCLOSED, NOT CLOSED. A fabricated observation added at the tip with a
# matching manifest row is reached by NO arm in the file. Expected 0 at BOTH refs; what
# changes at AFTER is that ARM F PRINTS it as UNGRADED-BORN-AT-TIP instead of being silent.
run_case born-at-tip-iv-a     mut_born_at_tip            0 0
# BOUNDARY (iv-b) — MEASURED, AND THE ANSWER WAS NOT THE ONE PREDICTED. T433 expected a
# rename+mutate to reset ARM F's baseline silently (0 at both refs). It does not: git reports
# a HIGH-SIMILARITY rename as R, not A, so ARM F has NO ADD record for the new path and
# REFUSES with exit 2. A refusal moves adjudicated section 10 and fails run-all.sh's verdict,
# so this case is CAUGHT — as a refusal, which this file's own rules say is never a pass.
run_case rename-mutate-iv-b   mut_rename_and_mutate      0 2
# BOUNDARY (iv-b2) — THE SAME ATTACK WITH THE SIMILARITY REMOVED, which is the version that
# actually lands in (iv-a). Renamed AND wholly rewritten, git records a real ADD at the tip,
# ARM F reports it UNGRADED-BORN-AT-TIP and the file exits 0. DISCLOSED, NOT CLOSED.
run_case rename-rewrite-iv-b2 mut_rename_and_rewrite     0 0
# THE VACUITY CONTROL, DRIVEN. If every post-fork observation were born at the tip, ARM F
# would grade nothing and report zero differences — which reads exactly like a pass. Section 9
# asserts f_graded > 0, and this case is the proof that assertion can FAIL.
run_case vacuity-armf-grades-0 mut_vacuity               0 1

echo
echo "############ MATRIX"
column -t -s "$(printf '\t')" "$MATRIX" 2>/dev/null || cat "$MATRIX"
echo
echo "unexpected results: $FAILURES"

# Exit code agreement is necessary and not sufficient: a case can be the right colour for the
# wrong reason. These assert the REASON, by the named line, at the AFTER ref.
say() { echo "  $1"; }
REASONS=0
chk() {  # chk <label> <file> <pattern> <expected count>
  local got; got="$(grep -c "$3" "$OUT/$2")"
  if [ "$got" = "$4" ]; then say "OK   $1  ($3 x$got)"
  else say "BAD  $1  expected $3 x$4, got x$got"; REASONS=$((REASONS + 1)); fi
}
echo "############ REASONS, not just colours"
chk "residual: ARM F NAMES the laundered file at AFTER" \
    "armf-case-residual-laundered-AFTER.txt" "LAUNDERED-OR-MUTATED $POSTFORK" 1
chk "residual: nothing named it at BEFORE (there was no ARM F)" \
    "armf-case-residual-laundered-BEFORE.txt" "LAUNDERED-OR-MUTATED" 0
chk "adjudicated-further: ARM F reports the adjudication MOVED" \
    "armf-case-adjudicated-further-AFTER.txt" "ADJUDICATION MOVED $ADJ" 1
chk "adjudicated-revert: a VANISHED difference moves it too" \
    "armf-case-adjudicated-revert-AFTER.txt" "ADJUDICATION MOVED $ADJ" 1
chk "iv-a: the fabricated tip-born observation is PRINTED as ungraded, not silently equal" \
    "armf-case-born-at-tip-iv-a-AFTER.txt" "UNGRADED-BORN-AT-TIP out/$FAB" 1
# x2, not x1: verify-capture-integrity.py prints a refusal where it happens AND re-prints its
# first line in the REFUSALS summary block at the end. Measured, not guessed — the first run of
# this drive expected x1 and was told x2, and that is the only reason this comment exists.
chk "iv-b: the renamed+mutated observation has NO ADD record and is REFUSED, not passed" \
    "armf-case-rename-mutate-iv-b-AFTER.txt" "have NO recorded ADD commit" 2
chk "iv-b2: with the similarity removed it IS a real ADD at the tip, and is PRINTED ungraded" \
    "armf-case-rename-rewrite-iv-b2-AFTER.txt" "UNGRADED-BORN-AT-TIP out/REWRITTEN-" 1
chk "vacuity: the control FAILS when ARM F graded nothing" \
    "armf-case-vacuity-armf-grades-0-AFTER.txt" "FAIL  ARM F actually GRADED" 1
chk "vacuity: ARM F did in fact grade zero there" \
    "armf-case-vacuity-armf-grades-0-AFTER.txt" "GRADED against a birth blob older than HEAD     : 0" 1
chk "control: a clean tree at AFTER names nothing and grades everything" \
    "armf-case-control-AFTER.txt" "DIFFER and are NOT adjudicated               : 0" 1

echo
if [ "$FAILURES" -ne 0 ] || [ "$REASONS" -ne 0 ]; then
  echo "T433 ARM-F IN-SITU DRIVE VERDICT: FAIL — $FAILURES wrong exit code(s), $REASONS wrong reason(s)."
  exit 1
fi
echo "T433 ARM-F IN-SITU DRIVE VERDICT: PASS."
echo "  RED  : at $BEFORE the laundered post-fork mutation exits 0 / PASS — T393's residual, real."
echo "  GREEN: at $AFTER ARM F exits 1 and NAMES it. The 'impossible' baseline was the birth blob."
echo "  ARM F's own boundary is DRIVEN, not asserted:"
echo "    (iv-a)  an observation born AT THE TIP is reported UNGRADED and remains UNCLOSED —"
echo "            a fabricated observation added at the tip WITH a matching manifest row is"
echo "            reached by no arm in the file, and only the oracle could distinguish it;"
echo "    (iv-b)  a HIGH-SIMILARITY rename+mutate is REFUSED (exit 2), not silently passed —"
echo "            the prediction was wrong and the measurement corrected it;"
echo "    (iv-b2) the SAME attack with the similarity removed lands in (iv-a), exit 0;"
echo "    the vacuity control is shown to FAIL when ARM F grades nothing, so 'no differences'"
echo "    can never be printed by an arm that read nothing."
exit 0
