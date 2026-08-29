#!/bin/bash
# A2-11 — re-run every check in this review and record the transcript.
#   bash run-all.sh   -> writes TRANSCRIPT-A2-11.txt, and EXITS NON-ZERO if any section's
#                        verdict has moved off the value adjudicated for it below.
# Checks that need the live reference oracle (Fineract) are marked; the rest are offline.
DIR="$(cd "$(dirname "$0")" && pwd)"
STATUS="$(mktemp -t a2-11-status)"
trap 'rm -f "$STATUS"' EXIT

# sec N EXPECTED_RC CMD...   run a section, print its exit, and record it for the verdict.
# EXPECTED_RC is the value this section has been ADJUDICATED to produce. It is not a wish:
# sections 1, 2 and 4 are expected NON-ZERO for reasons stated at each site, and a section
# that moves OFF its expected value — in EITHER direction — fails the aggregate verdict.
# T357 added this. Before it, the whole body was `{ ... } | tee`, so `bash run-all.sh` exited
# with TEE's status: 0, always, even with five sections aborting on a traceback. A runner
# that always reports success is the same trap as a guard that always reports PASS.
sec() {
  local n="$1" expect="$2"; shift 2
  "$@"; local rc=$?
  echo "exit=$rc"
  printf '%s\t%s\t%s\n' "$n" "$expect" "$rc" >> "$STATUS"
}

{
  echo "############ A2-11 independent review of A2-7 — full transcript"
  date -u +"generated %Y-%m-%dT%H:%M:%SZ"
  echo
  echo "READ THE EXIT CODES THIS WAY: sections 1 and 2 assert A2-7'S CLAIMS, so a non-zero"
  echo "exit there is a FINDING AGAINST A2-7, not a broken script. Sections 3-9 assert things"
  echo "that should hold. Every failing assertion is printed by name, and the VERDICT block at"
  echo "the end compares every section against the exit code adjudicated for it."
  echo
  echo "############ HISTORY OF THIS FILE — three corrections, each by measurement"
  echo
  echo "T270. Section 8 used to run a SUPERSEDED prover that could not fail. Bytes preserved,"
  echo "execution stopped; the successor is READ from the register. See section 8."
  echo
  echo "T270 also recorded that sections 2, 4, 5, 6 and 7 ABORTED with a traceback, because"
  echo "enumerate-corpus.py:22, verify-manifest-independently.py:21, audit-float.py:18,"
  echo "prove-resolve7-float-red.py:33 and prove-a2-7-guards-are-falsifiable.py:19 each"
  echo "hard-coded ROOT/RIG to the RETIRED worktree path .../agent-a3ac3d56d665ff7da. T270"
  echo "left them alone, calling the repair a separate decision."
  echo
  echo "T357 MADE THAT DECISION AND REPAIRED THEM. Each of the five now derives its root from"
  echo "__file__ (parents[3] IS the checkout root), with an A2_11_ROOT env override. The"
  echo "substitution was chosen because it is OUTPUT-NEUTRAL in the worktree that produced the"
  echo "committed evidence — in agent-a3ac3d56d665ff7da, parents[3] resolved to exactly that"
  echo "path — so it RESTORES re-derivability rather than altering the record. That is a"
  echo "MEASUREMENT, not a hope: T357 diffed the regenerated transcript against the committed"
  echo "one section by section, and sections 1, 2, 3, 6 and 7 came back IDENTICAL, including"
  echo "section 2's three findings against A2-7. Sections 4 and 5 differ, for a stated reason"
  echo "given at each site: both enumerate the CURRENT capture rig, which has grown since A2-7."
  echo "Section 8 differs because T270 changed it. Evidence:"
  echo ".softhouse/capture/t357-a2-11-section1-red/out/40-section-diff-committed-vs-rootfix.txt"
  echo
  echo "T357 also corrected the SECTION 1 LABEL, which read '[ORACLE] live re-observation' and"
  echo "was wrong twice: check-shape.py imports only json, sys, decimal and pathlib and replays"
  echo "committed bytes under obs/. It never contacts the oracle. In a program that grades"
  echo "provenance, a section advertising an offline replay as a live observation is a false"
  echo "provenance claim. The corrected label is now itself PROVED, in section 9, from the"
  echo "AST — not swapped for a second unchecked adjective."
  echo
  echo "############ 1. contract shape, replayed OFFLINE from A2-11's committed obs/ bytes"
  echo "############    [NO ORACLE CONTACTED — proved from the AST in section 9]"
  echo
  echo "EXPECTED RC 1. This section is PERMANENTLY AND CORRECTLY RED, with three named"
  echo "failures, and has been since it was committed on 2026-08-21. They are the executable"
  echo "form of A2-11's finding F-1 / patterns.md P-46: A2-7 printed three FABRICATED lines"
  echo "claiming the collection-valued mapping fields come back 'present with the value null',"
  echo "reasoned a contract rule from them, and fed that rule to the coder A2-8. The lines are"
  echo "not in any capture. The oracle omits a null field on the read path. Section 9"
  echo "ADJUDICATES this RED and goes red itself if a FOURTH failure ever appears, or if any"
  echo "of the three ever disappears."
  echo
  sec 1 1 python3 "$DIR/check-shape.py"
  echo
  echo "############ 2. corpus enumeration at A2-7's fork point (offline, counts its skips)"
  echo "############    EXPECTED RC 1 — asserts A2-7's claims; three of them are refuted."
  echo "############    Reproduces the committed transcript IDENTICALLY after T357's root fix."
  sec 2 1 python3 "$DIR/enumerate-corpus.py"
  echo
  echo "############ 3. double-entry in INTEGER MINOR UNITS (offline)   EXPECTED RC 0"
  sec 3 0 python3 "$DIR/verify-double-entry-minor-units.py"
  echo
  echo "############ 4. manifest, hashes RECOMPUTED not trusted (offline)"
  echo "############    EXPECTED RC 1 — and the reason is DRIFT, not a defect."
  echo
  echo "This section pins counts taken AT A2-7'S MOMENT (a 571-entry manifest, 141 added over"
  echo "the 430 at the fork sha). The rig has been added to by many tasks since, so it now"
  echo "holds 1139, and the count assertions necessarily fail. That is the section measuring"
  echo "the passage of time, not finding a defect. READ THE THIRD ARM INSTEAD, which is the"
  echo "one that matters: of the 430 files that existed at the fork sha, 428 are still"
  echo "BYTE-IDENTICAL, 0 are missing, the current manifest agrees with disk on all 430 (no"
  echo "laundering), and the 2 that differ are NAMED — CAPTURE-PLAN.md and cap.sh, which are"
  echo "rig tooling and a plan document. NO CAPTURED ORACLE OBSERVATION under out/ or req/ has"
  echo "been mutated. If that ever stops being true, this section will say so by name."
  echo
  echo "T374 / T362 F-1 -- READ THIS BEFORE TRUSTING THE SENTENCE ABOVE. It says so BY NAME,"
  echo "in printed text, and until T374 that was ALL it did. This section is adjudicated RED"
  echo "for drift, so the integrity arm is SATURATED: it cannot make the section any redder,"
  echo "and the VERDICT block below therefore could not see it. T362 PROVED that by appending"
  echo "one line to out/A2-000-glaccounts-preexisting.http -- section 4 printed DIFF for it BY"
  echo "NAME and run-all.sh still exited 0 printing RUN-ALL VERDICT: PASS. T374 reproduced it"
  echo "in a scratch clone before repairing it. THE REPAIR IS SECTION 10, which asks the"
  echo "integrity question where GREEN is the adjudicated value. Section 4 keeps the drift arm."
  echo
  echo "T393 / T382 F-3 -- AND THIS SECTION STAYED SATURATED FOR 27 MORE FILES UNTIL NOW."
  echo "T374 lifted the saturation for out/ and req/ ONLY. The fork-sha manifest holds 430"
  echo "entries; 403 are observations under out/ or req/, and the other 27 -- cap.sh,"
  echo "manifest.py, the mkreq*.py, the run-*.sh, the sql, and the red/green evidence that"
  echo "grades them: the scripts that PRODUCED the observations -- were still graded ONLY by"
  echo "this saturated arm. T382 drove it: mutate manifest.py, this section prints"
  echo "DIFF manifest.py BY NAME, byte-identical 428 -> 427, and run-all.sh still exits 0"
  echo "printing RUN-ALL VERDICT: PASS. T362's F-1 verbatim, one directory over."
  echo "THE REPAIR IS SECTION 10's ARM E, which adjudicates those same 27 where GREEN is the"
  echo "expected value, with the two known differences (CAPTURE-PLAN.md, cap.sh) adjudicated"
  echo "BY DIGEST rather than only by name. SO: NOTHING IN THE FORK-SHA MANIFEST IS COVERED"
  echo "BY THIS SATURATED SECTION ALONE ANY MORE. What this section still uniquely carries is"
  echo "the DRIFT measurement (the pinned 571-vs-1139 counts) and the branch-shape arm, and"
  echo "those are the only reasons it is adjudicated RED."
  sec 4 1 python3 "$DIR/verify-manifest-independently.py"
  echo
  echo "############ 5. P-25 float audit of A2-7's scripts (offline)   EXPECTED RC 0"
  echo "############    Enumerates the CURRENT rig, so its file list grows over time; the"
  echo "############    VERDICT is the flag count, and A2-7's two flagged files are stable."
  sec 5 0 python3 "$DIR/audit-float.py"
  echo
  echo "############ 6. resolve7.py P-25 defect, driven RED (offline)   EXPECTED RC 0"
  sec 6 0 python3 "$DIR/prove-resolve7-float-red.py"
  echo
  echo "############ 7. are A2-7's 16 assertions falsifiable? (offline, sabotage)   EXPECTED RC 0"
  sec 7 0 python3 "$DIR/prove-a2-7-guards-are-falsifiable.py"
  echo
  echo "############ 8. the float property A2-7's guard prover claimed — RUN FROM ITS"
  echo "############    REPLACEMENT, because the original could not fail (offline)  EXPECTED RC 0"
  echo
  echo "T270. Until this change, this section ran prove-mkreq7-guard-red.py unmodified and"
  echo "printed 'ok  it parses JSON numbers as Decimal' / '16 assertions, 0 failed' / exit=0."
  echo "That arm is a WHOLE-FILE SOURCE GREP (\`\"parse_float=decimal.Decimal\" in src\`), and"
  echo "the token occurs twice in its target analyze7.py — at :39 in the code and at :6 in"
  echo "the file's OWN DOCSTRING. Delete the keyword from the CALL SITE and the assertion is"
  echo "still satisfied, by the prose. T164 reproduced that end to end and replaced the arm."
  echo
  echo "T114 requires the BYTES of prove-mkreq7-guard-red.py be preserved, so that"
  echo "RED-GREEN-A2-7-guards.txt stays re-derivable from the script that made it. It does"
  echo "NOT require the file keep being EXECUTED as though it still graded something. Those"
  echo "are two different obligations. A superseded guard that still prints PASS is not"
  echo "preserved evidence, it is a trap — P-45 inverted: not a guard that never runs, but a"
  echo "NON-guard that always runs and always says PASS. Bytes unchanged; execution stopped."
  echo
  echo "The successor is not named here. It is READ from the register, so this site cannot"
  echo "drift out of step with it, and a DELETED register line makes this section REFUSE"
  echo "rather than quietly fall back to the trap."
  echo
  RIG="$DIR/../../capture/tierA-a2"
  if REPL="$(python3 "$DIR/resolve-supersession.py" "$RIG/SUPERSEDED.txt" prove-mkreq7-guard-red.py)"; then
    echo "SUPERSEDED.txt resolves: prove-mkreq7-guard-red.py -> $REPL"
    echo
    sec 8 0 python3 "$RIG/$REPL"
  else
    echo "exit=2  (REFUSED — see the message above; no fallback to the superseded file)"
    printf '%s\t%s\t%s\n' 8 0 2 >> "$STATUS"
  fi
  echo
  echo "NOT COVERED BY THE REPLACEMENT, STATED SO THIS IS NOT READ AS EQUIVALENT (P-40):"
  echo "prove-mkreq7-guard-red.py carried 16 assertions. guard-parse-float-ast.py replaces"
  echo "only the 3 in its analyze7.py float arm. The other 13 — mkreq7.py's D-1 refusal"
  echo "behaviour and resolve7.py's four refusals — are re-run by NOTHING today. They are"
  echo "recorded as an open follow-up in the T270 handoff, not silently absorbed."
  echo
  echo "############ 9. ADJUDICATE section 1's permanent RED (offline)   EXPECTED RC 0"
  echo "############    T357. Section 1 has been RED with three named failures since the day"
  echo "############    it was written and NOBODY READ THEM. This section pins those three,"
  echo "############    proves section 1 is offline and deterministic from the AST, and"
  echo "############    MEASURES whether any of them touches a vector graded by"
  echo "############    conformance.sh. It goes RED on a fourth failure or a vanished one."
  sec 9 0 python3 "$DIR/adjudicate-section1.py"
  echo
  echo "############ 10. EVIDENCE INTEGRITY — captured oracle observations (offline)"
  echo "############    EXPECTED RC 0. T374, closing T362's F-1."
  echo
  echo "The corpus this whole program grades against is the captured oracle observations"
  echo "under capture/tierA-a2/out/ and req/. Section 4 already compares them byte for byte —"
  echo "but section 4 is adjudicated RED for manifest drift, and a status that cannot get"
  echo "worse cannot carry new information. So the integrity question is asked HERE, in a"
  echo "section adjudicated GREEN, where a mutated or deleted observation MOVES the section"
  echo "and fails the aggregate verdict."
  echo
  echo "T393 / T382 F-1, F-3, F-4 -- FIVE ARMS, NOT TWO, AND A CALIBRATION THAT IS CHECKED."
  echo "T374 shipped two arms: the literal fork sha (403 observations) and HEAD (all 1035,"
  echo "including the 632 captured since). T382 measured what they could not see and drove"
  echo "every case with a control. Both arms are handed a population by a git listing, so:"
  echo "  a COMMITTED DELETION took HEAD's population 1035 -> 1034 and printed VERDICT: PASS;"
  echo "  a COMMITTED ADDITION of a fabricated observation took it to 1036, PASS;"
  echo "  an UNTRACKED fabricated observation in out/ was never handed to any arm at all;"
  echo "  a SYMLINK with identical bytes passed, because open() follows symlinks."
  echo "And section 10's OWN baseline constant was tied to nothing: T382 moved it ONE LINE"
  echo "forward to a commit containing a mutation, ARM A's population collapsed 403 -> 1035"
  echo "onto ARM B's, the mutation went invisible, and run-all.sh exited 0 printing PASS while"
  echo "section 4 printed DIFF out/A2-000-glaccounts-preexisting.http BY NAME."
  echo "T393 closes all of it: ARM C reads the tracked MANIFEST.sha256 as a PATH-SET and as"
  echo "RECOMPUTED digests (deletion, addition); ARM D walks the DISK with lstat (untracked,"
  echo "symlink); ARM E covers the 27 fork-sha manifest entries outside out/ and req/ that"
  echo "section 4's saturated arm was the only thing looking at; the fork sha is CROSS-CHECKED"
  echo "against the two tracked files that also carry it; and ARM A's population is PINNED at"
  echo "403 -- a property of an immutable commit, so it cannot drift. An empty population, a"
  echo "population off its pin, or an untied constant is REFUSED with exit 2, not passed."
  echo
  echo "T433 / C-T423-1 -- ARM F, AND A CORRECTION. This banner used to end with the text"
  echo "quoted on the next three lines. It is kept rather than deleted, and TAGGED, so that a"
  echo "guard can tell a quotation from an assertion by grep alone:"
  echo "  [QUOTED-FALSE-CLAIM] \"What is still NOT closed ... a committed change to a POST-FORK"
  echo "  [QUOTED-FALSE-CLAIM]  observation that ALSO rewrites its manifest row in the same"
  echo "  [QUOTED-FALSE-CLAIM]  commit. There is no committed baseline older than HEAD for those 632.\""
  echo "THE LAST SENTENCE WAS FALSE, and it was load-bearing rather than a"
  echo "wording slip: T393's handoff reasoned FROM the impossibility to send the next task to"
  echo "build a substitute artefact the repository already contained. THE BASELINE IS THE"
  echo "BLOB AT THE COMMIT THAT FIRST ADDED EACH OBSERVATION -- \`git log --diff-filter=A\` --"
  echo "an object inside an ALREADY-COMMITTED commit, which rewriting the manifest inside the"
  echo "mutating commit cannot reach. T433 swept the WHOLE 632, not a sample, with two"
  echo "independent derivations of the birth commit that agree 632/632: all 632 born strictly"
  echo "older than the tip, 0 born at the tip, 631 still byte-identical to their birth blob,"
  echo "and exactly one legitimate re-capture -- out/A2-370-db-ledger-state.txt -- adjudicated"
  echo "by digest. Section 8 of verify-capture-integrity.py is that arm. On T393's own"
  echo "'unclosable' laundered residual it exits 1 NAMING the file, where ARMs A-E exit 0."
  echo "What ARM F still does NOT reach is named at boundary (iv) of that file's docstring:"
  echo "an observation born AT THE TIP has no baseline older than HEAD and is reported"
  echo "UNGRADED, never equal; and a rename-and-mutate in ONE commit resets its own baseline."
  sec 10 0 python3 "$DIR/verify-capture-integrity.py"
  echo
  echo "############ VERDICT — every section against its adjudicated exit code"
  echo
  printf '  %-9s %-14s %-9s %s\n' SECTION EXPECTED ACTUAL RESULT
  DEVIATIONS=0
  while IFS=$'\t' read -r n expect rc; do
    if [ "$expect" = "$rc" ]; then
      printf '  %-9s %-14s %-9s %s\n' "$n" "$expect" "$rc" "as adjudicated"
    else
      printf '  %-9s %-14s %-9s %s\n' "$n" "$expect" "$rc" "*** MOVED ***"
      DEVIATIONS=$((DEVIATIONS + 1))
    fi
  done < "$STATUS"
  SECTIONS=$(wc -l < "$STATUS" | tr -d ' ')
  echo
  echo "  sections run: $SECTIONS    deviations: $DEVIATIONS"
  # T374: 9 -> 10. Section 10 (evidence integrity) is new. If you are adding a section,
  # this number moves WITH it — a stale bound here would read a missing section as a pass.
  if [ "$SECTIONS" -ne 10 ]; then
    echo "  RUN-ALL VERDICT: FAIL — $SECTIONS sections recorded, expected 10. A section that"
    echo "  did not record a verdict is a section that did not run, and it is never read as"
    echo "  a pass."
    echo "$((DEVIATIONS + 1))" > "$STATUS.rc"
  elif [ "$DEVIATIONS" -eq 0 ]; then
    echo "  RUN-ALL VERDICT: PASS — every section produced exactly the exit code adjudicated"
    echo "  for it. Note that this INCLUDES sections 1, 2 and 4, which are adjudicated RED."
    echo "  PASS here means 'the review reproduces', NOT 'A2-7 was right'."
    echo "0" > "$STATUS.rc"
  else
    echo "  RUN-ALL VERDICT: FAIL — $DEVIATIONS section(s) moved off the adjudicated verdict."
    echo "  Read the moved sections above. A section that moved is either a new defect or a"
    echo "  repair that nobody recorded; both need a human, neither is absorbed here."
    echo "$DEVIATIONS" > "$STATUS.rc"
  fi
} 2>&1 | tee "$DIR/TRANSCRIPT-A2-11.txt"

# ----------------------------------------------------------------------------------------
# T374, closing T362's F-5. THIS SCRIPT JUST OVERWROTE A TRACKED FILE.
# TRANSCRIPT-A2-11.txt is committed evidence, and the `tee` above rewrites it on every run —
# at minimum its "generated <timestamp>" line on line 2. That means `bash run-all.sh` leaves
# a dirty working tree, silently, and a reader who then runs `git status` sees a modified
# review artefact with no idea who modified it. It is also the item MISSING from T357's own
# T356 disclosure: T357 disclosed six edited files with an exact revert for each; this
# transcript is the seventh modified tracked path and had no revert entry. T362 graded the
# disclosure and named the gap. This block closes it, at the site, so it cannot go missing
# from a handoff again.
#
# The transcript is deliberately still WRITTEN — it is the re-derivable record, and making it
# opt-in would decide something T356 owns. What changes is that the effect is now DISCLOSED
# with its exact revert, every run, in the terminal rather than only in a handoff.
if command -v git >/dev/null 2>&1 &&
   ! git -C "$DIR" diff --quiet -- "$DIR/TRANSCRIPT-A2-11.txt" 2>/dev/null; then
  echo
  echo "NOTE (T374 / T362 F-5): this run REWROTE the tracked file"
  echo "  .softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt"
  echo "so your working tree is now dirty. That is expected — the transcript carries a"
  echo "generation timestamp — and it is NOT a finding. To restore it:"
  echo "  git checkout -- .softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt"
fi

RC=$(cat "$STATUS.rc" 2>/dev/null || echo 1)
rm -f "$STATUS.rc"

# T374 / T362 F-1, stated where the exit code is produced, because this is the sentence that
# gets quoted: DO NOT READ EXIT 0 AS "THE A2-11 EVIDENCE IS INTACT" on any version of this
# file that predates section 10. Before T374 a mutated capture under out/ or req/ was absorbed
# by section 4's adjudicated RED and this script exited 0 printing PASS. From T374 the
# integrity question is section 10's, adjudicated GREEN, and a mutation moves it.
exit "$RC"
