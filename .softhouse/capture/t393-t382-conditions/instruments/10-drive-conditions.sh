#!/bin/bash
# T393 — RED BEFORE GREEN for every condition T382 filed, driven on real repositories.
#
# Each case is run TWICE: once against the bytes BEFORE T393's fix and once against the bytes
# AFTER it, in scratch clones, with the whole run-all.sh runner. The RED half is not a claim
# about what used to happen — it is the same mutation, on the same file, against the earlier
# commit, producing the earlier answer. A fix whose RED half was never observed is a fix whose
# author guessed (P-22).
#
# NO HOST PATH IS WRITTEN IN THIS FILE. The source repo, the scratch root, the output
# directory and BOTH commit-ishes are required parameters; a missing one aborts the run
# rather than defaulting to somebody's disk (T256/T298 — no graded path may depend on where
# it runs; this is an instrument, held to the same rule).
#
#   T393_SRC=<repo>  T393_CLONE=<scratch>  T393_OUT=<dir> \
#   T393_BEFORE=<sha> T393_AFTER=<sha>  bash 10-drive-conditions.sh
#
# EXIT 0 every case produced the expected RED and the expected GREEN.
# EXIT 1 at least one did not — printed by name, never counted only.
# EXIT 3 the harness could not run (bad parameter, clone failure). Never read as a result.
set -u

SRC="${T393_SRC:?T393_SRC must name the source repository}"
SCROOT="${T393_CLONE:?T393_CLONE must name a scratch directory OUTSIDE the repository}"
OUT="${T393_OUT:?T393_OUT must name the directory to write transcripts into}"
BEFORE="${T393_BEFORE:?T393_BEFORE must name the commit-ish carrying the PRE-fix bytes}"
AFTER="${T393_AFTER:?T393_AFTER must name the commit-ish carrying the POST-fix bytes}"

CAP=".softhouse/capture/tierA-a2"
A211=".softhouse/reviews/A2-11"
INT="$A211/verify-capture-integrity.py"
RUNALL="$A211/run-all.sh"
MAN="$CAP/MANIFEST.sha256"
PICK=".softhouse/capture/t393-t382-conditions/instruments/11-pick-targets.py"
FAB="T393-FABRICATED-OBSERVATION.http"

mkdir -p "$OUT" || exit 3
mkdir -p "$SCROOT" || exit 3
MATRIX="$OUT/MATRIX.tsv"
: > "$MATRIX" || exit 3
printf 'case\tref\tsec10\trunall_rc\tverdict\tsec4_named_the_mutation\texpected\tresult\n' \
  >> "$MATRIX"

# ---------------------------------------------------------------------------------------
# The mutation targets are MEASURED, not typed. See 11-pick-targets.py; it REFUSES on an
# empty set, so a case can never silently become a no-op.
# ---------------------------------------------------------------------------------------
if ! TARGETS="$(python3 "$SRC/$PICK")"; then
  echo "REFUSED: could not pick mutation targets from $SRC. Nothing below can run." >&2
  exit 3
fi
FORKOBS="$(printf '%s\n' "$TARGETS" | awk -F'\t' '$1=="FORKOBS"{print $2}')"
POSTFORK="$(printf '%s\n' "$TARGETS" | awk -F'\t' '$1=="POSTFORK"{print $2}')"
NONOBS="$(printf '%s\n' "$TARGETS" | awk -F'\t' '$1=="NONOBS"{print $2}')"
if [ -z "$FORKOBS" ] || [ -z "$POSTFORK" ] || [ -z "$NONOBS" ]; then
  echo "REFUSED: a mutation target came back empty: [$FORKOBS] [$POSTFORK] [$NONOBS]" >&2
  exit 3
fi
echo "targets: FORKOBS=$FORKOBS  POSTFORK=$POSTFORK  NONOBS=$NONOBS"

FAILURES=0

prepare() {   # prepare <clonedir> <ref>
  local d="$1" ref="$2"
  if [ ! -d "$d/.git" ]; then
    rm -rf "$d" || return 1
    git clone --quiet --shared "$SRC" "$d" || return 1
    git -C "$d" config user.email "t393@softhouse.local" || return 1
    git -C "$d" config user.name "T393" || return 1
  fi
  # Order matters: a previous case may have left the clone dirty AND on a probe commit, and
  # `checkout --detach` refuses over a dirty tree. Reset to whatever HEAD is, clean, THEN
  # move. Every arm is fatal — a clone that did not reach the requested ref would grade the
  # wrong bytes and report a colour about a commit it was never on.
  git -C "$d" reset --quiet --hard || return 1
  git -C "$d" clean -qfdx || return 1
  git -C "$d" checkout --quiet --detach "$ref" || return 1
  git -C "$d" reset --quiet --hard "$ref" || return 1
  return 0
}

# --- the mutations. Each takes the clone directory and returns non-zero if it could not
# --- apply, because a mutation that silently did nothing turns a RED case into a control.
mut_control()      { return 0; }

mut_commit_mutate_postfork() {
  printf '\nT393-MUTATION-MARKER\n' >> "$1/$CAP/$POSTFORK" || return 1
  git -C "$1" add -- "$CAP/$POSTFORK" || return 1
  git -C "$1" commit -q -m "T393 probe: committed mutation of a POST-FORK observation" || return 1
}

mut_commit_mutate_postfork_laundered() {
  printf '\nT393-MUTATION-MARKER\n' >> "$1/$CAP/$POSTFORK" || return 1
  python3 "$SRC/.softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py" \
    "$1" "$POSTFORK" || return 1
  git -C "$1" add -- "$CAP/$POSTFORK" "$MAN" || return 1
  git -C "$1" commit -q -m "T393 probe: committed mutation of a POST-FORK observation, manifest row rewritten to match" || return 1
}

mut_commit_delete_postfork() {
  git -C "$1" rm -q -- "$CAP/$POSTFORK" || return 1
  git -C "$1" commit -q -m "T393 probe: committed DELETION of a post-fork observation" || return 1
}

mut_commit_add_fabricated() {
  printf 'HTTP/1.1 200 OK\r\n\r\n{"fabricated":true}\n' > "$1/$CAP/out/$FAB" || return 1
  git -C "$1" add -- "$CAP/out/$FAB" || return 1
  git -C "$1" commit -q -m "T393 probe: committed ADDITION of a fabricated observation" || return 1
}

mut_untracked_fabricated() {
  printf 'HTTP/1.1 200 OK\r\n\r\n{"fabricated":true}\n' > "$1/$CAP/out/$FAB" || return 1
  return 0
}

mut_symlink_identical_bytes() {
  local keep="$SCROOT/t393-symlink-target"
  cp "$1/$CAP/$POSTFORK" "$keep" || return 1
  rm -f "$1/$CAP/$POSTFORK" || return 1
  ln -s "$keep" "$1/$CAP/$POSTFORK" || return 1
  return 0
}

mut_commit_mutate_forkobs() {
  printf '\nT393-MUTATION-MARKER\n' >> "$1/$CAP/$FORKOBS" || return 1
  git -C "$1" add -- "$CAP/$FORKOBS" || return 1
  git -C "$1" commit -q -m "T393 probe: committed mutation of a FORK-SHA observation" || return 1
}

# T382 FINDING 4, verbatim: commit a mutation of a fork-sha observation ARM A catches, then
# move section 10's OWN baseline constant forward ONE LINE to the commit that contains it.
mut_move_fork_constant() {
  mut_commit_mutate_forkobs "$1" || return 1
  local probe old
  probe="$(git -C "$1" rev-parse HEAD)" || return 1
  old="$(python3 "$SRC/.softhouse/capture/t393-t382-conditions/instruments/13-move-fork-constant.py" \
        "$1/$INT" "$probe")" || return 1
  echo "      FORK moved: $old -> $probe"
  return 0
}

mut_commit_mutate_nonobs() {
  printf '\n# T393-MUTATION-MARKER\n' >> "$1/$CAP/$NONOBS" || return 1
  git -C "$1" add -- "$CAP/$NONOBS" || return 1
  git -C "$1" commit -q -m "T393 probe: committed mutation of a fork-sha NON-observation entry" || return 1
}

mut_commit_mutate_nonobs_laundered() {
  printf '\n# T393-MUTATION-MARKER\n' >> "$1/$CAP/$NONOBS" || return 1
  python3 "$SRC/.softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py" \
    "$1" "$NONOBS" || return 1
  git -C "$1" add -- "$CAP/$NONOBS" "$MAN" || return 1
  git -C "$1" commit -q -m "T393 probe: committed mutation of a fork-sha NON-observation entry, manifest row rewritten to match" || return 1
}

# ---------------------------------------------------------------------------------------
run_case() {   # run_case <name> <mutfn> <expect_before> <expect_after>
  local name="$1" mutfn="$2" exp_before="$3" exp_after="$4" ref tag d rc sec10 verdict named
  for ref in BEFORE AFTER; do
    if [ "$ref" = "BEFORE" ]; then
      tag="$BEFORE"; d="$SCROOT/before"
    else
      tag="$AFTER"; d="$SCROOT/after"
    fi
    if ! prepare "$d" "$tag"; then
      echo "REFUSED: could not prepare $d at $tag" >&2
      exit 3
    fi
    echo "--- $name @ $ref ($tag)"
    if ! "$mutfn" "$d"; then
      echo "REFUSED: mutation $mutfn failed to apply in $d. A mutation that did not apply" >&2
      echo "         would turn this case into a control and report a false GREEN." >&2
      exit 3
    fi
    ( cd "$d" && bash "$RUNALL" ) > "$OUT/case-$name-$ref.txt" 2>&1
    rc=$?
    sec10="$(awk '/^  10 /{print $3}' "$OUT/case-$name-$ref.txt" | tail -1)"
    if [ -z "$sec10" ]; then sec10="none"; fi
    verdict="$(sed -n 's/.*RUN-ALL VERDICT: \([A-Z]*\).*/\1/p' "$OUT/case-$name-$ref.txt" | tail -1)"
    if [ -z "$verdict" ]; then verdict="none"; fi
    # SECTION 4's OUTPUT LINE, not any sentence that quotes it. The first spelling of this
    # column was `grep -c -- "DIFF $FORKOBS"`, and the control row at the POST-fix ref came
    # back 1 on an UNMUTATED tree: the hit was section 10's own new BANNER, which quotes
    # T382's finding verbatim ("...section 4 printed DIFF out/A2-000-... BY NAME"). A column
    # that counts the harness describing the defect instead of the harness detecting it is a
    # false positive of exactly the shape this whole review is about, so it is anchored to
    # the printed form -- `        DIFF <name>` at line start, nothing after it. Found by
    # reading a control row that should have been 0 and was 1; the first drive was killed and
    # re-run from the corrected bytes rather than post-processed, so the committed matrix and
    # the committed instrument are the same bytes (T356/P-22 spelling).
    named="$(grep -c -E -- "^ +DIFF ${FORKOBS}\$" "$OUT/case-$name-$ref.txt")"
    local expect result
    if [ "$ref" = "BEFORE" ]; then expect="$exp_before"; else expect="$exp_after"; fi
    if [ "$sec10" = "$expect" ]; then result="as expected"; else
      result="*** UNEXPECTED ***"; FAILURES=$((FAILURES + 1)); fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$name" "$ref" "$sec10" "$rc" "$verdict" "$named" "$expect" "$result" >> "$MATRIX"
    echo "      section10=$sec10  run-all rc=$rc  verdict=$verdict  sec4-named-mutation=$named  expected=$expect  $result"
  done
}

echo "############ T393 RED-BEFORE-GREEN DRIVE"
echo "BEFORE = $BEFORE   (T374's section 10, two arms, untied constant)"
echo "AFTER  = $AFTER   (T393's section 10, five arms, cross-checked constant)"
echo

# name                                   mutation                              BEFORE AFTER
run_case control                         mut_control                           0 0
run_case f1-13-commit-mutate-postfork    mut_commit_mutate_postfork            0 1
run_case f1-14-commit-delete-postfork    mut_commit_delete_postfork            0 1
run_case f1-15-commit-add-fabricated     mut_commit_add_fabricated             0 1
run_case f1-16-untracked-fabricated      mut_untracked_fabricated              0 1
run_case f1-09-symlink-identical-bytes   mut_symlink_identical_bytes           0 1
run_case f4a-control-commit-mutate-forkobs mut_commit_mutate_forkobs           1 1
run_case f4b-move-fork-constant          mut_move_fork_constant                0 2
run_case f3-commit-mutate-nonobs         mut_commit_mutate_nonobs              0 1
run_case f3b-commit-mutate-nonobs-laundered mut_commit_mutate_nonobs_laundered 0 1
# DISCLOSED RESIDUAL, driven so the boundary statement is a measurement and not a hope.
# Expected UNDETECTED at BOTH refs: a committed mutation of a post-fork observation whose
# manifest row is rewritten in the same commit has no baseline older than HEAD anywhere in
# this repository. The docstring says so; this row is the evidence that it says so truly.
run_case f1-13b-postfork-laundered-RESIDUAL mut_commit_mutate_postfork_laundered 0 0

echo
echo "############ MATRIX"
cat "$MATRIX"
echo
echo "unexpected results: $FAILURES"
if [ "$FAILURES" -ne 0 ]; then
  echo "DRIVE VERDICT: FAIL — a case did not produce the expected exit code. Read the rows"
  echo "marked *** UNEXPECTED *** above and the transcript named for each."
  exit 1
fi
echo "DRIVE VERDICT: PASS — every case was RED at $BEFORE and GREEN at $AFTER, except the"
echo "two rows that are deliberately expected to be unchanged: the f4a control (ARM A caught"
echo "it at both refs) and the f1-13b disclosed residual (undetected at both, which is what"
echo "the boundary statement in verify-capture-integrity.py says)."
exit 0
