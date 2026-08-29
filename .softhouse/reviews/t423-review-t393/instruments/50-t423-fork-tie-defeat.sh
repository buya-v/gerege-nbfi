#!/bin/bash
# T423 — THE ATTACK NEITHER T393 NOR THE FIRST T423 WORKER RAN: DEFEAT THE CROSS-CHECK.
#
# T393's F-4 repair has two independent halves:
#   (1) FORK_TIES  — the literal must also appear in prove-a2-7-additive.py and in
#                    verify-manifest-independently.py, in section 4's own spelling;
#   (2) FORK_OBS_PIN = 403 / FORK_NONOBS_PIN = 27 — ARM A's and ARM E's population sizes.
#
# T393's `f4b` drive moves the constant in ONE file, so BOTH halves fire and the AFTER
# transcript shows four refusals. That drive therefore does NOT establish that (2) works on
# its own. An attacker who has read the file moves the constant in ALL THREE tracked files:
# half (1) is then satisfied and only half (2) is left standing.
#
# THIS IS THE CASE THAT DECIDES WHETHER F-4 IS ACTUALLY CLOSED. If the coordinated move
# passes, T393's repair is a speed bump; if it REFUSES on the pins alone, the repair holds
# with one tripwire to spare.
#
#   f4c  — committed mutation of a fork-sha observation + FORK moved in ALL THREE files.
#          EXPECTED at AFTER: section 10 exit 2 (REFUSED on the two population pins),
#          run-all FAIL. EXPECTED at BEFORE: exit 0, PASS (there are no pins there at all).
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298). Every location is a required parameter.
#   T423_SRC=<repo>  T423_CLONE=<scratch OUTSIDE the repo>  T423_OUT=<dir>
#   T423_BEFORE=<pre-fix sha>  T423_AFTER=<post-fix sha>  bash 50-t423-fork-tie-defeat.sh
#
# EXIT 0 both refs produced the expected section-10 code.  EXIT 1 one did not.
# EXIT 3 the harness could not run. Never read as a result.
set -u
SRC="${T423_SRC:?T423_SRC must name the source repository}"
SCROOT="${T423_CLONE:?T423_CLONE must name a scratch directory OUTSIDE the repository}"
OUT="${T423_OUT:?T423_OUT must name the directory to write transcripts into}"
BEFORE="${T423_BEFORE:?}"
AFTER="${T423_AFTER:?}"

CAP=".softhouse/capture/tierA-a2"
INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
RUNALL=".softhouse/reviews/A2-11/run-all.sh"
TIE1="$CAP/prove-a2-7-additive.py"
TIE2=".softhouse/reviews/A2-11/verify-manifest-independently.py"
FORK="12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"
mkdir -p "$OUT" "$SCROOT" || exit 3

FORKOBS="$(git -C "$SRC" ls-tree -r --name-only "$FORK" -- "$CAP/out" "$CAP/req" \
           | sed "s|^$CAP/||" | LC_ALL=C sort | head -1)"
[ -n "$FORKOBS" ] || { echo "REFUSED: empty fork observation set" >&2; exit 3; }
echo "T423 f4c target: $FORKOBS"

FAILURES=0
for ref in BEFORE AFTER; do
  if [ "$ref" = "BEFORE" ]; then tag="$BEFORE"; expect=0; else tag="$AFTER"; expect=2; fi
  D="$SCROOT/f4c-$ref"
  rm -rf "$D" || exit 3
  git clone --quiet --shared "$SRC" "$D" || exit 3
  git -C "$D" config user.email t423@softhouse.local
  git -C "$D" config user.name T423
  git -C "$D" checkout --quiet --detach "$tag" || exit 3
  git -C "$D" reset --quiet --hard "$tag" || exit 3

  echo "--- f4c @ $ref ($tag)"
  printf '\nT423-MUTATION-MARKER\n' >> "$D/$CAP/$FORKOBS" || exit 3
  git -C "$D" add -- "$CAP/$FORKOBS" || exit 3
  git -C "$D" commit -q -m "T423 f4c: committed mutation of a FORK-SHA observation" || exit 3
  PROBE="$(git -C "$D" rev-parse HEAD)" || exit 3

  # Move the constant in ALL THREE tracked files. Each substitution is asserted, so a
  # spelling that did not match cannot be mistaken for an attack that was repelled.
  n1=$(grep -c -E "^FORK = \"$FORK\"\$" "$D/$INT")
  n2=$(grep -c -E "^BASELINE = \"$FORK\"\$" "$D/$TIE1")
  n3=$(grep -c -E "^FORK = \"$FORK\"\$" "$D/$TIE2")
  echo "      assignments found: section10=$n1 prove-a2-7-additive=$n2 verify-manifest-independently=$n3"
  if [ "$ref" = "AFTER" ] && { [ "$n1" != "1" ] || [ "$n2" != "1" ] || [ "$n3" != "1" ]; }; then
    echo "REFUSED: expected exactly one assignment in each of the three files at AFTER" >&2
    exit 3
  fi
  perl -pi -e "s/^FORK = \"$FORK\"\$/FORK = \"$PROBE\"/"     "$D/$INT"
  perl -pi -e "s/^BASELINE = \"$FORK\"\$/BASELINE = \"$PROBE\"/" "$D/$TIE1"
  perl -pi -e "s/^FORK = \"$FORK\"\$/FORK = \"$PROBE\"/"     "$D/$TIE2"
  m1=$(grep -c -E "^FORK = \"$PROBE\"\$" "$D/$INT")
  m2=$(grep -c -E "^BASELINE = \"$PROBE\"\$" "$D/$TIE1")
  m3=$(grep -c -E "^FORK = \"$PROBE\"\$" "$D/$TIE2")
  echo "      constant moved to $PROBE in: section10=$m1 tie1=$m2 tie2=$m3"

  ( cd "$D" && bash "$RUNALL" ) > "$OUT/T423-case-f4c-all-three-$ref.txt" 2>&1
  rc=$?
  sec10="$(awk '/^  10 /{print $3}' "$OUT/T423-case-f4c-all-three-$ref.txt" | tail -1)"; : "${sec10:=none}"
  verdict="$(sed -n 's/.*RUN-ALL VERDICT: \([A-Z]*\).*/\1/p' "$OUT/T423-case-f4c-all-three-$ref.txt" | tail -1)"; : "${verdict:=none}"
  named="$(grep -c -E -- "^ +DIFF ${FORKOBS}\$" "$OUT/T423-case-f4c-all-three-$ref.txt")"
  pop="$(sed -n 's/^ *at the fork sha *: \([0-9]*\) observations.*/\1/p' "$OUT/T423-case-f4c-all-three-$ref.txt" | tail -1)"; : "${pop:=none}"
  ties="$(grep -c 'REFUSED  .*does NOT carry' "$OUT/T423-case-f4c-all-three-$ref.txt")"
  pins="$(grep -c 'REFUSED  ARM . population is\|REFUSED  ARM .'"'"'s population is' "$OUT/T423-case-f4c-all-three-$ref.txt")"
  echo "      section10=$sec10 rc=$rc verdict=$verdict sec4-named=$named armA-pop=$pop tie-refusals=$ties pin-refusals=$pins expected=$expect"
  if [ "$sec10" != "$expect" ]; then echo "      *** UNEXPECTED ***"; FAILURES=$((FAILURES+1)); fi
done

echo
echo "unexpected results: $FAILURES"
[ "$FAILURES" -ne 0 ] && { echo "T423 f4c VERDICT: FAIL"; exit 1; }
echo "T423 f4c VERDICT: PASS"
exit 0
