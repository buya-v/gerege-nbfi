#!/usr/bin/env python3
"""T374 (T362 F-1) — EVIDENCE INTEGRITY for the tierA-a2 captured oracle observations,
with its OWN exit code, adjudicated GREEN, so run-all.sh's aggregate verdict can see it.
T393 (T382 F-1/F-3/F-4) — widened: the calibration is now CROSS-CHECKED, the population is
PINNED, the manifest is a third arm, the disk is walked, and section 4's remaining 27
saturated entries are adjudicated here.

WHY THIS FILE EXISTS — the measurement, not the theory.

run-all.sh section 4 (verify-manifest-independently.py) does check the byte-identity of the
pre-existing capture corpus, and its third arm prints any mutated file BY NAME. But section 4
is adjudicated RC 1, because its first two arms pin manifest COUNTS taken at A2-7's moment
and the rig has grown since. A section that is already failing is SATURATED: the integrity
arm cannot make it any redder, so the aggregate verdict cannot distinguish "section 4 is red
for drift, as adjudicated" from "section 4 is red for drift AND a captured oracle observation
was mutated". T362 proved this by appending a marker to a real captured observation,
.../out/A2-000-glaccounts-preexisting.http:

    verify-manifest-independently.py  rc=1   DIFF out/A2-000-glaccounts-preexisting.http
    run-all.sh                        rc=0   4  EXPECTED 1  ACTUAL 1  "as adjudicated"
                                             deviations: 0   RUN-ALL VERDICT: PASS

T374 reproduced that exactly, in a scratch clone, before writing this file (P-22 — every fix
driven RED first). Evidence: .softhouse/capture/t374-t362-conditions/out/.

THAT IS AN EVIDENCE-INTEGRITY DEFECT, NOT A COSMETIC ONE. The captured observations under
out/ and req/ ARE the record this program grades against. An exit status that stays 0 while
one of them is mutated means the corpus can rot with the harness saying PASS. It is the same
defect class T357 removed one level up: a status that cannot get worse carries no information.

>>> DO NOT READ run-all.sh's EXIT 0 AS "THE EVIDENCE IS INTACT" ON ANY VERSION THAT PREDATES
>>> THIS FILE. Before T374 it was not sensitive to a mutated capture. From T374 it is, because
>>> the integrity question is asked HERE, where GREEN is the adjudicated value and any
>>> deviation therefore moves the section and fails the aggregate.

============================================================================================
T393 — WHAT T382 MEASURED ABOUT THE T374 VERSION OF THIS FILE, AND WHAT EACH ARM NOW CLOSES.
============================================================================================
T382 reviewed T374 and returned APPROVED WITH CONDITIONS on four findings, all driven. Two of
them are about THIS FILE and they are the reason for every arm added below.

  T382 FINDING 4 — the tripwire had a switch on it. Section 4 ties its copy of the fork sha
  to another tracked file (`prove-a2-7-additive.py hard-codes the literal sha`). The T374
  version of this file carried the SAME literal tied to NOTHING, and asserted nothing about
  ARM A's population size. Moving that one constant forward to a commit that already contains
  a mutation collapsed ARM A's population 403 -> 1035, the two arms stopped being independent,
  and the mutation ARM A had caught a moment earlier became invisible — while section 4 went
  on printing `DIFF out/A2-000-glaccounts-preexisting.http` BY NAME and run-all.sh exited 0
  printing `RUN-ALL VERDICT: PASS`. That is T362's F-1 verbatim, on the branch that fixes it.
  CLOSED BY: section 1's cross-check (the literal must appear, in the same spelling section 4
  uses, in TWO tracked files) and section 2's ARM A cardinality pin (403 — a property of an
  IMMUTABLE commit, so it cannot drift; if it is not 403 the selector or the constant moved).

  T382 FINDING 1 — the uncovered set was larger than T374 disclosed. T374 disclosed committed
  MUTATION of a post-fork observation. T382 measured four more shapes outside both arms and
  outside the disclosure, all reported `VERDICT: PASS`, exit 0:
      committed DELETION of a post-fork observation  (HEAD population 1035 -> 1034, PASS)
      committed ADDITION of a fabricated observation (HEAD population 1035 -> 1036, PASS)
      an UNTRACKED fabricated observation left in out/
      a regular file replaced by a SYMLINK whose target has IDENTICAL bytes
  Root cause, stated by T382 and reproduced here: T374's own F-2 repair is the rule "an empty
  population is a SELECTOR failure, not a clean tree". Sections 2 applies that rule AT ZERO
  and stops. It never pins the population's CARDINALITY, so a shrink of up to 632 (every
  post-fork observation, with both out/ and req/ still non-empty so the refusal never fires)
  or any growth passes.
  CLOSED BY: ARM C (the manifest) and ARM D (the disk walk), below.

  T382 FINDING 2 — the artefact needed to close it ALREADY EXISTS. T374's follow-up asked for
  a new tracked `OBSERVATIONS.sha256`. `.softhouse/capture/tierA-a2/MANIFEST.sha256` already
  IS one. T393 re-verified T382's counts independently before relying on them
  (.softhouse/capture/t393-t382-conditions/out/00-t382-counts.txt, exit 0): 1139 rows, of
  which 1035 under out/ or req/ — EXACTLY the tracked observation path-set — 0 tracked
  observations without a row, 0 rows naming no tracked observation, 1035 digests agreeing
  with disk and 0 disagreeing, and all 632 post-fork observations covered. It also holds 104
  rows outside out/ and req/, all 104 agreeing with disk, covering every tracked file under
  the capture directory except MANIFEST.sha256 itself (1139 = 1140 - 1). NO NEW ARTEFACT WAS
  BUILT. A second one would have been a second thing to keep in step.

  T382 FINDING 3 — the saturation class was closed at exactly ONE site. T382 audited every
  section's return-code arithmetic: 3/5/6/7/8/9/10 cannot saturate, 1 is adjudicated by 9, 2
  has the shape but is inert (it reads only frozen git blobs). Section 4 is LIVE and still
  absorbed the 27 fork-sha manifest entries OUTSIDE out/ and req/ — cap.sh, manifest.py,
  mkreq*.py, the run-*.sh, the sql, and the red/green evidence that grades them: the scripts
  that PRODUCED the observations. Driven by T382 on manifest.py: 428 -> 427 byte-identical,
  `DIFF manifest.py` printed BY NAME, and run-all.sh still EXIT 0, `RUN-ALL VERDICT: PASS`.
  CLOSED BY: ARM E, which adjudicates those 27 here, where GREEN is the expected value.

WHAT THIS FILE DOES AND DOES NOT COVER (P-40 — the boundary is stated, not implied):
  * COVERS   every file under .softhouse/capture/tierA-a2/{out,req}/ — the captured oracle
             observations and the request bodies that produced them — in FIVE independent
             directions:
               ARM A  against the LITERAL fork sha (the historical baseline section 4 uses),
               ARM B  against HEAD (which also covers observations captured since),
               ARM C  against the tracked MANIFEST.sha256, BOTH as a path-set equality and as
                      a recomputed digest, which is what makes a committed DELETION or a
                      committed ADDITION visible at all,
               ARM D  against the DISK, which is what makes an UNTRACKED file and a SYMLINK
                      substitution visible at all,
               ARM F  against THE BLOB AT THE COMMIT THAT FIRST ADDED each POST-FORK
                      observation — the baseline this file used to say did not exist. It is
                      what makes a committed mutation with a LAUNDERED manifest row visible
                      at all (T423/T433, C-T423-1; section 8 below).
  * COVERS   ARM E: the 27 entries in the fork-sha manifest that are NOT under out/ or req/ —
             the capture scripts and the red/green evidence — against their fork-sha blobs,
             with the two known differences adjudicated BY NAME AND BY DIGEST. This is the
             population section 4's saturated third arm was the only thing looking at.
  * DOES NOT COVER  other capture directories, .softhouse/vectors/, or obs/ under this
             review. obs/ byte-identity is graded at the git-object level by the reviewer,
             and the graded vector store is graded by conformance.sh. Named so that silence
             here is distinguishable from not looking.
  * DOES NOT CLOSE — stated exactly, because T382's whole finding was that the previous
             disclosure was smaller than the measured gap, and an understated boundary is the
             defect this file exists to punish:
               (i)  [CLOSED BY ARM F — AND THE SENTENCE THAT USED TO STAND HERE WAS FALSE.
                    T423 found it, the driver re-measured it, T433 corrected it: C-T423-1.]
                    THE CASE: a committed mutation of a POST-FORK observation that ALSO
                    rewrites the matching MANIFEST.sha256 row in the same commit. ARM A
                    cannot see it (no fork blob), ARM B cannot see it (HEAD *is* the mutated
                    commit), ARM C cannot see it (the manifest was laundered to agree), ARM D
                    cannot see it (the file is tracked and regular).
                    WHAT THIS BLOCK USED TO SAY, VERBATIM — kept rather than deleted, and
                    TAGGED so a guard can tell a quotation from an assertion by grep alone:
                    [QUOTED-FALSE-CLAIM] "Closing this needs a committed baseline OLDER than
                    [QUOTED-FALSE-CLAIM]  HEAD for the post-fork observations, which does not
                    [QUOTED-FALSE-CLAIM]  exist and cannot be manufactured here."
                    THAT IS FALSE, and it was
                    load-bearing rather than a wording slip: T393's handoff reasoned FROM the
                    impossibility to send the next task to build a substitute artefact, so a
                    false negation spent a worker's budget and foreclosed the cheap fix.
                    WHAT THE BASELINE ACTUALLY IS — do not read a bare negation removed:
                    THE BLOB AT THE COMMIT THAT FIRST ADDED EACH OBSERVATION, reachable with
                    `git log --diff-filter=A -- <path>`. It is an object inside an
                    ALREADY-COMMITTED commit, so rewriting MANIFEST.sha256 inside the
                    mutating commit does not reach it, and nothing short of rewriting main's
                    history can move it.
                    MEASURED OVER THE WHOLE POPULATION, NOT A SAMPLE (T433, tip b102875c,
                    clean tree; `.softhouse/capture/t433-t423-c1/out/00-whole-632-sweep.txt`,
                    two independent derivations of the birth commit that agree on 632/632):
                    632 of 632 post-fork observations were born at a commit STRICTLY OLDER
                    than the tip and an ancestor of it; 0 were born at the tip; 631 still
                    equal their birth blob by git OID *and* by sha256; exactly ONE differs —
                    out/A2-370-db-ledger-state.txt, born aae501b5 and legitimately
                    re-captured at 32ba0fcd the same day with six further ledger rows. It is
                    adjudicated by digest in ARM_F_ADJUDICATED below.
                    ARM F is that comparison, and it is the arm that exits 1 NAMING the file
                    on the very laundered repository section 10 used to exit 0 / PASS on.
               (ii) A mutation committed to the fork sha itself. Not reachable without
                    rewriting main's history; section 1 checks the constant, not the object.
               (iii) The 403 fork-sha observations are FULLY covered against laundering, by
                    ARM A: it recomputes from the git blob and never reads a recorded digest,
                    so rewriting the manifest does not help (T382 matrix case 17).
               (iv) WHAT ARM F ITSELF MISSES BY ONE — stated because an arm's own boundary is
                    the next thing to be found (T433 drove each of these; see
                    `.softhouse/capture/t433-t423-c1/out/`):
                    (iv-a) BORN AT THE TIP — THE FAIL-OPEN IS NOW CLOSED; THE DETECTION HALF
                    IS NOT, AND THE TWO ARE DIFFERENT PROBLEMS (T448 C-T448-1, landed by
                    T455). An observation whose birth commit IS HEAD has no baseline older
                    than HEAD, so ARM F CANNOT grade it. T433 drove that and disclosed it,
                    and then wrote — kept verbatim and TAGGED, because deleting a false
                    sentence destroys the evidence that it was shipped:
                    [QUOTED-FALSE-CLAIM] "Not closable by internal consistency — a fabricated
                    [QUOTED-FALSE-CLAIM]  observation is a claim about the oracle, and only
                    [QUOTED-FALSE-CLAIM]  the oracle can refute it."
                    THAT RUNS TWO PROBLEMS TOGETHER, and only one of them is external.
                      * DETECTING that a capture is fabricated IS external. The clause is
                        true of that half. The anchor is named at (iv-a-anchor) below.
                      * REFUSING TO EXIT 0 OVER A POPULATION THIS ARM DID NOT MEASURE is
                        INTERNAL, and this file ALREADY STATED THE RULE nine lines above the
                        born-at-tip branch, for the sibling f_noborn case: "An arm that could
                        not measure part of its own population has not passed on it. REFUSED,
                        never a pass." The two cases are the same case. Only one of them was
                        asserted.
                    SO IT IS ASSERTED NOW, in section 9: a post-fork observation that ARM F
                    could not grade because it was born at the tip FAILS this file unless it
                    is adjudicated by name AND by digest in ARM_F_BORN_AT_TIP_ADJUDICATED.
                    A fabricated observation added at the tip with a laundered manifest row
                    is STILL not DETECTED here — nothing internal can do that — but it can no
                    longer be reported as a PASS, which is what the fail-open was.
                    MEASURED COST, ON A CLEAN TREE: zero. Every observation is born in the
                    commit that adds it, so f_at_tip is 0 on every tree except that commit
                    itself — the exact moment a human is present to adjudicate it, in the
                    same shape as ADJUDICATED_DIFFERENT (ARM E) and ARM_F_ADJUDICATED.
                    (iv-a-anchor) THE EXTERNAL ANCHOR for the detection half, named rather
                    than left blank: RE-OBSERVATION AGAINST THE PINNED REFERENCE ORACLE
                    (Fineract), digest-recorded — the procedure T357 already ran for the four
                    obs/ files on fire 20260828-140005 (sha256 match, 4 of 4). It is out of
                    THIS file's reach by construction: this file is offline.
                    (iv-b) MOVED/RENAMED — AND THE PREDICTION WAS WRONG, WHICH IS WHY IT WAS
                    DRIVEN. T433 expected `--diff-filter=A` to record a rename as an ADD at
                    the new path, resetting the baseline silently. It does not: git reports a
                    HIGH-SIMILARITY rename as R, so ARM F finds NO ADD record for the new path
                    and REFUSES with exit 2 — which run-all.sh adjudicates as a MOVE of section
                    10, never a pass. So rename+mutate+relabel in one commit is CAUGHT.
                    (iv-b2) …BUT ONLY WHILE THE SIMILARITY HOLDS. Rename the file AND replace
                    its bytes wholly and git records a genuine ADD at the tip, which lands in
                    (iv-a). It is the same edge as (iv-a) rather than a second one, and its
                    CONSEQUENCE MOVED WHEN (iv-a) CLOSED. Driven by T433, then by T455 as its
                    case 5, then re-driven at this ref by T467's
                    `30-t467-ivb2-consequence.sh` (transcript `30-IVB2-CONSEQUENCE.txt`):
                    the observation is reported UNGRADED and section 9 now REFUSES it, so the
                    outcome is EXIT 1 on the named assertion, not exit 0. T467 / F-T464-3 —
                    this sentence still said "exit 0" three commits after the file it
                    describes stopped doing that, in the file whose whole subject is
                    sentences that outlived their measurement.
                    (iv-c) DELETED AND RE-ADDED — DRIVEN FOUR WAYS BY T448, AND IT IS NOT A
                    HOLE. T433 disclosed this as open and undriven (its F-3). T448 built all
                    four shapes: re-add BYTE-IDENTICAL -> exit 0 and 632 graded, because
                    NOTHING HAPPENED (the bytes still equal the captured observation, which
                    is the only thing this arm asserts); re-add MUTATED with the manifest row
                    laundered in the same commit -> exit 1, NAMED; re-add identical then
                    mutate+launder in a third commit -> exit 1, NAMED; re-add with WHOLLY NEW
                    bytes -> exit 1, NAMED. The earliest ADD wins in every construction,
                    including the one where git's history simplification has the best chance
                    of hiding the gap. F-3 CLOSES. Evidence (T448, not re-driven by T455):
                    `.softhouse/reviews/t448-review-t433/out/20-ARMF-DRIVES.txt`.
                    (iv-d) LEGITIMATE AMENDMENT. A real re-capture moves ARM F and must be
                    re-adjudicated by digest in ARM_F_ADJUDICATED, exactly as ARM E's two
                    are. That is a cost, not a defect: it makes an amendment a visible,
                    signed act instead of an invisible one. DRIVEN by T433.

P-25: no floating point. The only numbers are counts from len() and sha256 hex digests.
P-24: the historical baseline is a LITERAL immutable sha, never `git merge-base`.
P-22: the comparator is driven RED against mutated bytes in memory before it is trusted, and
      end-to-end against real mutated repositories in scratch clones by
      .softhouse/capture/t374-t362-conditions/prove-t374-fixes-can-fail.sh (T374's seven
      cases) and .softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh
      (T393's seven, each run at the PRE-fix bytes and at the POST-fix bytes).
      ARM F specifically: driven RED then GREEN by T423
      (.softhouse/reviews/t423-review-t393/instruments/61-t423-armf-red-drive.sh) and
      re-driven, in situ inside THIS file, by T433
      (.softhouse/capture/t433-t423-c1/instruments/20-t433-armf-in-situ-drive.sh), whose
      laundered-residual case requires this file to exit 1 naming the file where it
      previously exited 0 / PASS. If ARM F cannot be made to fail it is not a guard (P-22).

EXIT CODES
  0  every captured observation is byte-identical in every direction, the manifest agrees
     with the tracked set and with disk, the disk holds nothing else, and the 27 adjudicated
     non-observation entries are exactly as adjudicated.
  1  at least one captured observation DIFFERS, is MISSING, is EXTRA, or is not a regular
     file; or an adjudicated non-observation entry moved. Named, never counted only.
  2  REFUSED — the instrument could not measure, or its own calibration failed (empty
     population, unusable git, missing baseline, a fork sha not carried by the two tracked
     files that also carry it, a population whose size is not the pinned one). A refusal is
     never reported as a pass.
"""
import ast
import hashlib
import os
import pathlib
import subprocess
import sys

# Root derivation matches the other A2-11 scripts: this file sits three levels below the
# checkout root, under reviews/A2-11, so parents[3] IS that root. A2_11_ROOT overrides.
ROOT = os.environ.get("A2_11_ROOT") or str(pathlib.Path(__file__).resolve().parents[3])
CAPREL = ".softhouse/capture/tierA-a2"
A2_11_REL = ".softhouse/reviews/A2-11"
OBS_DIRS = ("out", "req")
MANIFEST_NAME = "MANIFEST.sha256"
MANREL = CAPREL + "/" + MANIFEST_NAME
# LITERAL, immutable (P-24). A2-7's fork point; the same baseline section 4 uses.
FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"

# T393 / T382 FINDING 4 — THE CALIBRATION IS TIED TO TRACKED FILES, NOT LEFT BARE.
# Each entry is (repo-relative file, the EXACT assignment text that file must contain). The
# spelling is section 4's: `check("prove-a2-7-additive.py hard-codes the literal sha", ...)`.
# Moving FORK in this file alone now REFUSES, because neither tie is satisfied by the new
# value. Moving it in all three is a three-file diff that says what it is doing.
FORK_TIES = (
    (CAPREL + "/prove-a2-7-additive.py", 'BASELINE = "%s"' % FORK),
    (A2_11_REL + "/verify-manifest-independently.py", 'FORK = "%s"' % FORK),
)

# T393 / T382 FINDING 4 — ARM A's POPULATION SIZE, PINNED.
# 403 is a property of the tree at an IMMUTABLE commit, so unlike section 4's manifest counts
# it CANNOT drift with the rig: no future task can change how many observation files existed
# at 12a7f8d9. If this number is not 403, either FORK has been moved or the selector below
# stopped selecting, and both are instrument failures, not clean corpora.
FORK_OBS_PIN = 403
# Same argument for the fork-sha MANIFEST's non-observation rows — ARM E's population.
FORK_NONOBS_PIN = 27

# T393 / T382 FINDING 3 — THE TWO ADJUDICATED DIFFERENCES IN ARM E's POPULATION.
# Section 4's banner has always NAMED these two as "rig tooling and a plan document" that have
# changed since the fork sha. Naming is where section 4 stops, and naming alone leaves them as
# the one place in the capture directory where a further mutation is expected. So they are
# adjudicated here by NAME AND BY DIGEST, in both directions: the fork blob must still hash to
# what it hashed to, and disk must still hash to what it hashes to today. A FURTHER mutation
# of either file moves this section; so does a REVERT to the fork bytes, because a vanished
# adjudicated difference is a move in the other direction and section 9 already sets that
# precedent for section 1's three permanent failures.
#
# TO RE-ADJUDICATE after a deliberate edit: run
#   python3 .softhouse/capture/t393-t382-conditions/instruments/00-verify-t382-counts.py
# which prints both digests for every entry in this population that differs, and record the
# new value HERE with the reason. Do not delete the entry — an unadjudicated difference in
# this population is exactly what T382 measured as still-open.
ADJUDICATED_DIFFERENT = {
    "CAPTURE-PLAN.md": (
        "7c2e2795863fa035424aa1cf23e7d1735dad502c535b16f31a0938a3fc0050bd",
        "da0760bacc8af5f5fdbe8c0b6d9a56f1904158b4c4b2ada3f3a5547d2e4e99dd"),
    "cap.sh": (
        "67640ea31eb16c0ba0f929cfd93459f4ced687be3dda0f10db00c1b2d31f542a",
        "6a1c5e91bc93df436faa3a965f31402b10bfb0ff28f86c2227bd752a11f31e62"),
}

# T433 / C-T423-1 — ARM F's ADJUDICATED POST-FORK DIFFERENCE, by name and by digest.
# ARM F compares each post-fork observation to the blob at the commit that FIRST ADDED it.
# Over the whole 632 exactly one differs, and it differs LEGITIMATELY:
#   out/A2-370-db-ledger-state.txt  born at aae501b5 ("A2-26: raw-only ledger capture
#   readiness"), re-captured the same day at 32ba0fcd ("A2-26: close the last two mandatory
#   cash slots") with six further ledger rows, 48 -> 54, and the double-entry table still
#   balancing in INTEGER MINOR UNITS.
# Adjudicated in BOTH directions, in ARM E's spelling: a further mutation moves this entry,
# and so does a revert to the birth bytes. A vanished adjudicated difference is a move too.
# TO RE-ADJUDICATE after a deliberate re-capture: run
#   T433_TARGET=<repo> python3 \
#     .softhouse/capture/t433-t423-c1/instruments/00-t433-whole-632-birth-sweep.py
# which prints both digests for every post-fork observation that differs, and record the new
# value HERE with the reason. Do not delete the entry.
#                                   [birth blob sha256,  disk sha256]
ARM_F_ADJUDICATED = {
    "out/A2-370-db-ledger-state.txt": (
        "1ea4927a59068d0a5ec45773dbc50a4c80d9eaa0457f0cecdc820e4b8ed5f857",
        "1c23375b0f010cf5bb65b6fead9c9ec063fcafe9e4f16d713b34f367f41716e2"),
}

# T455 / C-T448-1 — THE (iv-a) BORN-AT-THE-TIP ADJUDICATION LIST. name -> sha256 of the bytes.
#
# ARM F cannot grade an observation whose birth commit IS HEAD: there is no earlier blob to
# compare against. Until T455 that was PRINTED and nothing asserted it, so an observation ARM
# F never measured was absorbed into an exit 0. Section 9 now REFUSES to pass over it unless
# it is adjudicated HERE, which is the rule this file already applied nine lines above the
# born-at-tip branch to the sibling f_noborn case.
#
# THIS TABLE IS EMPTY, AND ON A CLEAN TREE IT COSTS NOTHING. Every observation is born in the
# commit that adds it, so the count is 0 on every tree except that one commit — measured at
# 0 of 632 by T433's whole-population sweep and again by T448 under an independent primitive.
# The check therefore fires exactly once per capture-adding commit, when a human is present.
#
# TO ADJUDICATE A LEGITIMATELY NEW CAPTURE: run this file, read the UNGRADED-BORN-AT-TIP
# lines and the sha256 printed beside each, and record name -> digest here WITH THE REASON.
# The digest is load-bearing: a name-only entry would let the bytes be swapped afterwards
# without moving anything. Once the capture is one commit old the entry is DEAD and section 9
# fails on it (an adjudication that no longer describes the tree is a MOVE, exactly as in
# ADJUDICATED_DIFFERENT and ARM_F_ADJUDICATED) — so REMOVE it in the following commit.
#
# WHAT THIS DOES NOT DO, STATED SO THE NEXT READER DOES NOT INHERIT A WRONG MODEL: it does not
# DETECT a fabricated capture. Nothing internal can. It stops a population this arm did not
# measure from being reported as one it passed. See boundary (iv-a) and (iv-a-anchor) above.
ARM_F_BORN_AT_TIP_ADJUDICATED = {}

fails = []
refusals = []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        fails.append(label)


def refuse(*lines):
    for i, line in enumerate(lines):
        print(("  REFUSED  " if i == 0 else "           ") + line)
    refusals.append(lines[0])


def git(*args, check_rc=True):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True,
                          check=check_rc).stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


def parse_manifest(blob):
    """name -> hex digest. Same spelling as verify-manifest-independently.py's parser."""
    out = {}
    for line in blob.decode("utf-8").split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        out[parts[1].lstrip("*").strip()] = parts[0]
    return out


print("=== 0. THE INSTRUMENT ITSELF — driven RED before it is trusted (P-22) ===")
_a = b"HTTP/1.1 200 OK\r\n\r\n{\"id\":2}\n"
_b = _a + b"\nT374-SELFTEST-MARKER\n"
check("the comparator reports IDENTICAL on identical bytes", sha(_a) == sha(_a), sha(_a)[:16])
check("the comparator reports DIFFERENT on bytes with ONE line appended — the exact "
      "mutation shape T362 used to prove F-1", sha(_a) != sha(_b),
      "%s vs %s" % (sha(_a)[:16], sha(_b)[:16]))
_m = parse_manifest(b"# comment\n%s  out/x.http\n\n%s *req/y.json\n" % (b"a" * 64, b"b" * 64))
check("the manifest parser reads a two-column list, strips the binary-mode star, and skips "
      "comments and blank lines", _m == {"out/x.http": "a" * 64, "req/y.json": "b" * 64},
      repr(_m))

print()
print("=== 1. THE BASELINE EXISTS, AND ITS CALIBRATION IS CROSS-CHECKED (T382 FINDING 4) ===")
print("    T382: 'a tripwire whose calibration is a bare unchecked constant is a tripwire")
print("    with a switch on it.' Moving FORK forward to a commit that CONTAINS a mutation")
print("    collapsed ARM A onto ARM B (403 -> 1035) and the mutation went invisible while")
print("    section 4 printed it BY NAME and run-all.sh printed PASS. So the constant is now")
print("    tied to tracked files, in the same spelling section 4 already uses for its copy.")
have_fork = subprocess.run(["git", "-C", ROOT, "cat-file", "-e", FORK + "^{commit}"],
                           capture_output=True).returncode == 0
if not have_fork:
    refuse("the literal fork sha %s is not present in this repository." % FORK[:12],
           "That is an INSTRUMENT failure, not a clean corpus. With no baseline there is",
           "nothing to compare the captured observations against, and a comparison that",
           "cannot run is not a comparison that passed.")
else:
    print("  PASS  literal baseline sha %s is present" % FORK[:12])

for rel, needle in FORK_TIES:
    try:
        with open(os.path.join(ROOT, rel), "r", encoding="utf-8") as fh:
            src = fh.read()
    except OSError as exc:
        refuse("%s could not be read, so this file's fork sha is tied to nothing: %r"
               % (rel, exc),
               "The tie is the calibration. An untied constant is the T382 FINDING 4 defect,",
               "and reporting PASS on an unverifiable calibration is how it stayed invisible.")
        continue
    if needle in src:
        print("  PASS  %s carries `%s`" % (os.path.basename(rel), needle))
    else:
        refuse("%s does NOT carry `%s`." % (rel, needle),
               "Either this file's FORK constant was moved, or that file's was. Section 10",
               "cannot tell which, and it will not guess: a baseline that no longer agrees",
               "with the two tracked files that also carry it is a CALIBRATION failure and",
               "is REFUSED, never reported as a clean corpus.")

print()
print("=== 2. POPULATION — enumerated from the fork tree AND from HEAD, and PINNED ===")
print("    An EMPTY population is a SELECTOR failure, not a clean tree: this repository")
print("    tracks captured oracle observations under %s/{out,req}/ and always" % CAPREL)
print("    has. An empty census passes everything. REFUSED. (Same spelling as")
print("    guard_guards_dir_registration in conformance.sh — one idea, one spelling.)")
print("    T382 FINDING 1: applying that rule AT ZERO and stopping is not enough. A")
print("    population that silently shrank by up to 632, or grew by any number of")
print("    fabricated files, is the same class of selector failure one step short of empty.")
print("    ARM A's size is pinned below; ARM B's is pinned by the manifest in ARM C.")

fork_paths = []
if have_fork:
    for line in git("ls-tree", "-r", "--name-only", FORK, "--", CAPREL).decode().split("\n"):
        line = line.strip()
        if not line:
            continue
        rest = line[len(CAPREL) + 1:] if line.startswith(CAPREL + "/") else ""
        if rest.split("/")[0] in OBS_DIRS:
            fork_paths.append(line)
fork_paths.sort()

head_paths = sorted(
    line.strip()
    for line in git("ls-tree", "-r", "--name-only", "HEAD", "--", CAPREL).decode().split("\n")
    if line.strip()
    and line.strip().startswith(CAPREL + "/")
    and line.strip()[len(CAPREL) + 1:].split("/")[0] in OBS_DIRS)

per_dir_fork = {d: len([p for p in fork_paths if p.startswith(CAPREL + "/" + d + "/")])
                for d in OBS_DIRS}
per_dir_head = {d: len([p for p in head_paths if p.startswith(CAPREL + "/" + d + "/")])
                for d in OBS_DIRS}
print("      at the fork sha : %d observations  %s" % (len(fork_paths), per_dir_fork))
print("      at HEAD         : %d observations  %s" % (len(head_paths), per_dir_head))

if have_fork and (not fork_paths or any(v == 0 for v in per_dir_fork.values())):
    refuse("the fork-sha observation population is EMPTY or missing a whole directory: %s"
           % per_dir_fork,
           "SELECTOR failure. A zero-difference table over an empty population is a",
           "vacuous pass. REFUSED.")
if not head_paths or any(v == 0 for v in per_dir_head.values()):
    refuse("the HEAD observation population is EMPTY or missing a whole directory: %s"
           % per_dir_head,
           "SELECTOR failure. REFUSED.")
if have_fork and len(fork_paths) != FORK_OBS_PIN:
    refuse("ARM A's population is %d observations, and it is PINNED at %d."
           % (len(fork_paths), FORK_OBS_PIN),
           "This number is a property of an IMMUTABLE commit. It cannot drift with the rig,",
           "so a disagreement means the FORK constant moved or the selector stopped",
           "selecting. T382 drove exactly this: moving FORK forward to a later commit takes",
           "ARM A's population to ARM B's, the two arms stop being independent, and a",
           "mutation ARM A would have caught becomes invisible. REFUSED.")
elif have_fork:
    print("  PASS  ARM A's population is the pinned %d (a property of an immutable commit)"
          % FORK_OBS_PIN)

print()
print("=== 3. ARM A — every observation that existed at the fork sha, RECOMPUTED ===")
print("    git blob at %s  vs  the bytes on disk today." % FORK[:12])
a_identical = 0
a_diff = []
a_missing = []
a_unreadable = []
for rel in fork_paths:
    try:
        at_fork = git("show", FORK + ":" + rel)
    except subprocess.CalledProcessError as exc:      # NAMED, never swallowed (P-40)
        a_unreadable.append((rel, repr(exc)))
        continue
    try:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            today = fh.read()
    except OSError as exc:
        a_missing.append((rel, repr(exc)))
        continue
    if sha(at_fork) == sha(today):
        a_identical += 1
    else:
        a_diff.append((rel, sha(at_fork), sha(today)))

print("      enumerated                : %d" % len(fork_paths))
print("      byte-identical            : %d" % a_identical)
print("      DIFFER                    : %d" % len(a_diff))
print("      MISSING on disk           : %d" % len(a_missing))
print("      unreadable at the fork sha: %d" % len(a_unreadable))
for rel, h0, h1 in a_diff:
    print("        MUTATED %s\n                fork  %s\n                today %s" % (rel, h0, h1))
for rel, exc in a_missing:
    print("        MISSING %s  %s" % (rel, exc))
for rel, exc in a_unreadable:
    print("        UNREADABLE %s  %s" % (rel, exc))

check("NO captured oracle observation that existed at the fork sha has been MUTATED",
      not a_diff, "differ=%d" % len(a_diff))
check("NO captured oracle observation that existed at the fork sha has been DELETED",
      not a_missing and not a_unreadable,
      "missing=%d unreadable=%d" % (len(a_missing), len(a_unreadable)))

print()
print("=== 4. ARM B — every observation tracked at HEAD, including ones captured SINCE ===")
print("    git blob at HEAD  vs  the bytes on disk. Arm A cannot see an observation that")
print("    did not exist at the fork sha; %d of the %d tracked today are in that class."
      % (len(head_paths) - len(fork_paths), len(head_paths)))
b_identical = 0
b_diff = []
b_missing = []
for rel in head_paths:
    at_head = git("show", "HEAD:" + rel)
    try:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            today = fh.read()
    except OSError as exc:
        b_missing.append((rel, repr(exc)))
        continue
    if sha(at_head) == sha(today):
        b_identical += 1
    else:
        b_diff.append((rel, sha(at_head), sha(today)))

print("      enumerated     : %d" % len(head_paths))
print("      byte-identical : %d" % b_identical)
print("      DIFFER         : %d" % len(b_diff))
print("      MISSING on disk: %d" % len(b_missing))
for rel, h0, h1 in b_diff:
    print("        MUTATED %s\n                HEAD  %s\n                disk  %s" % (rel, h0, h1))
for rel, exc in b_missing:
    print("        MISSING %s  %s" % (rel, exc))

check("NO captured oracle observation tracked at HEAD differs from its committed bytes",
      not b_diff, "differ=%d" % len(b_diff))
check("NO captured oracle observation tracked at HEAD is missing from the working tree",
      not b_missing, "missing=%d" % len(b_missing))

print()
print("=== 5. ARM C — the tracked MANIFEST, as a PATH-SET and as RECOMPUTED DIGESTS ===")
print("    T382 FINDING 1/2. ARMs A and B compare files they were HANDED; neither can see a")
print("    file that was never handed to them, which is why a committed DELETION took the")
print("    HEAD population 1035 -> 1034 and a committed ADDITION took it to 1036, both")
print("    reporting VERDICT: PASS. %s is a TRACKED, per-file digest list" % MANIFEST_NAME)
print("    whose out/ + req/ row-set is EXACTLY the tracked observation path-set. Comparing")
print("    the two SETS is what makes a deletion and an addition visible at all.")
try:
    with open(os.path.join(ROOT, MANREL), "rb") as fh:
        manifest = parse_manifest(fh.read())
except OSError as exc:
    manifest = {}
    refuse("%s could not be read: %r" % (MANREL, exc),
           "It is the third arm's whole population. Without it ARM C is not a passing arm,",
           "it is an absent one. REFUSED.")

man_obs = {k: v for k, v in manifest.items() if k.split("/")[0] in OBS_DIRS}
tracked_rel = set(p[len(CAPREL) + 1:] for p in head_paths)
print("      manifest rows total                  : %d" % len(manifest))
print("      manifest rows under out/ or req/     : %d" % len(man_obs))
print("      observations tracked at HEAD         : %d" % len(tracked_rel))

if manifest and not man_obs:
    refuse("the manifest holds %d rows and NONE of them is under out/ or req/."
           % len(manifest),
           "SELECTOR failure — an empty ARM C population passes every observation.",
           "REFUSED.")

no_row = sorted(tracked_rel - set(man_obs))
no_file = sorted(set(man_obs) - tracked_rel)
for name in no_row[:20]:
    print("        ADDED-WITHOUT-A-ROW  %s" % name)
for name in no_file[:20]:
    print("        ROW-WITHOUT-A-FILE   %s" % name)
check("every observation tracked at HEAD has a MANIFEST row — a file ADDED to the corpus "
      "without one is a fabrication, not a capture",
      not no_row, "tracked observations with no manifest row: %d %s" % (len(no_row), no_row[:5]))
check("every MANIFEST row under out/ or req/ names an observation tracked at HEAD — a row "
      "whose file is gone is a DELETION, and the population moving is not a clean tree",
      not no_file, "manifest rows naming no tracked observation: %d %s"
      % (len(no_file), no_file[:5]))

c_agree = 0
c_disagree = []
c_unreadable = []
for name in sorted(man_obs):
    try:
        with open(os.path.join(ROOT, CAPREL, name), "rb") as fh:
            body = fh.read()
    except OSError as exc:
        c_unreadable.append((name, repr(exc)))
        continue
    if sha(body) == man_obs[name]:
        c_agree += 1
    else:
        c_disagree.append((name, man_obs[name], sha(body)))
print("      manifest digest agrees with disk     : %d" % c_agree)
print("      DISAGREES                            : %d" % len(c_disagree))
print("      unreadable                           : %d" % len(c_unreadable))
for name, want, got in c_disagree[:20]:
    print("        MANIFEST MISMATCH %s\n             manifest %s\n             disk     %s"
          % (name, want, got))
for name, exc in c_unreadable[:20]:
    print("        UNREADABLE %s  %s" % (name, exc))
check("every MANIFEST digest is the RECOMPUTED sha256 of the bytes on disk",
      not c_disagree and not c_unreadable,
      "agree=%d disagree=%d unreadable=%d" % (c_agree, len(c_disagree), len(c_unreadable)))

print()
print("=== 6. ARM D — THE DISK, walked. Nothing tracked ARMs A-C were never handed. ===")
print("    T382 FINDING 1, cases 16 and 09. ARMs A, B and C all start from a git or manifest")
print("    listing, so an UNTRACKED fabricated observation sitting in out/ is invisible to")
print("    all three — nobody hands it to them. And open(path,'rb') FOLLOWS SYMLINKS, so a")
print("    regular file replaced by a symlink to identical bytes reports PASS: the bytes are")
print("    right at that instant, but the file is no longer the tracked object and its")
print("    content is thereafter controlled from outside the repository. This arm starts")
print("    from the DISK instead, and uses lstat, which does not follow.")
disk_rel = []
disk_links = []
disk_odd = []
walk_missing = []
for d in OBS_DIRS:
    base = os.path.join(ROOT, CAPREL, d)
    if not os.path.isdir(base):
        walk_missing.append(d)
        continue
    for dirpath, _dirnames, filenames in os.walk(base):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, os.path.join(ROOT, CAPREL))
            disk_rel.append(rel)
            if os.path.islink(full):
                disk_links.append(rel)
            elif not os.path.isfile(full):
                disk_odd.append(rel)
print("      files on disk under out/ + req/      : %d" % len(disk_rel))
print("      of those that are SYMLINKS           : %d" % len(disk_links))
print("      of those that are neither file nor link: %d" % len(disk_odd))
if walk_missing:
    refuse("observation directories absent from disk: %s" % walk_missing,
           "SELECTOR failure — a walk over a directory that is not there finds nothing and",
           "reports nothing wrong. REFUSED.")
if not walk_missing and not disk_rel:
    refuse("the disk walk under out/ and req/ found NOTHING.",
           "SELECTOR failure. A zero-difference table over an empty walk is a vacuous",
           "pass. REFUSED.")

extra_on_disk = sorted(set(disk_rel) - tracked_rel)
absent_on_disk = sorted(tracked_rel - set(disk_rel))
for name in extra_on_disk[:20]:
    print("        UNTRACKED %s" % name)
for name in absent_on_disk[:20]:
    print("        ABSENT FROM DISK %s" % name)
for name in disk_links[:20]:
    print("        SYMLINK %s -> %s" % (name, os.readlink(os.path.join(ROOT, CAPREL, name))))
check("the disk holds NOTHING under out/ or req/ that is not tracked at HEAD — an untracked "
      "observation is a fabrication no arm reading a git listing can see",
      not extra_on_disk, "untracked: %d %s" % (len(extra_on_disk), extra_on_disk[:5]))
check("every observation tracked at HEAD is present on disk as a real directory entry",
      not absent_on_disk, "absent: %d %s" % (len(absent_on_disk), absent_on_disk[:5]))
check("every observation on disk is a REGULAR FILE — a symlink is not the tracked object "
      "even when its target's bytes are identical today",
      not disk_links and not disk_odd,
      "symlinks=%d other=%d" % (len(disk_links), len(disk_odd)))

print()
print("=== 7. ARM E — the 27 fork-sha manifest entries OUTSIDE out/ and req/ (T382 F-3) ===")
print("    These are the scripts that PRODUCED the observations and the red/green evidence")
print("    that grades them: cap.sh, manifest.py, the mkreq*.py, the run-*.sh, the sql. Until")
print("    T393 the ONLY thing comparing them to the fork sha was section 4's third arm, and")
print("    section 4 is adjudicated RED for drift, so that arm was SATURATED — T382 mutated")
print("    manifest.py, section 4 printed `DIFF manifest.py` BY NAME, and run-all.sh still")
print("    exited 0 printing RUN-ALL VERDICT: PASS. That is T362's F-1 verbatim, one")
print("    directory over. The question is asked HERE too, where GREEN is adjudicated.")
fork_nonobs = []
if have_fork:
    try:
        fork_manifest = parse_manifest(git("show", FORK + ":" + MANREL))
    except subprocess.CalledProcessError as exc:
        fork_manifest = {}
        refuse("the fork-sha manifest %s could not be read: %r" % (MANREL, exc),
               "ARM E has no population without it. REFUSED.")
    fork_nonobs = sorted(k for k in fork_manifest if k.split("/")[0] not in OBS_DIRS)
    print("      entries in the fork-sha manifest     : %d" % len(fork_manifest))
    print("      of those under out/ or req/          : %d" % (len(fork_manifest) - len(fork_nonobs)))
    print("      NOT under out/ or req/ (ARM E)       : %d" % len(fork_nonobs))
    if fork_manifest and len(fork_nonobs) != FORK_NONOBS_PIN:
        refuse("ARM E's population is %d entries, and it is PINNED at %d."
               % (len(fork_nonobs), FORK_NONOBS_PIN),
               "Like ARM A's pin this is a property of an IMMUTABLE commit and cannot drift.",
               "A disagreement means FORK moved or the selector broke. REFUSED.")

e_identical = 0
e_adjudicated = 0
e_diff = []
e_moved = []
e_missing = []
for name in fork_nonobs:
    rel = CAPREL + "/" + name
    try:
        at_fork = git("show", FORK + ":" + rel)
    except subprocess.CalledProcessError as exc:
        e_missing.append((name, "not in the fork-point tree: %r" % exc))
        continue
    try:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            today = fh.read()
    except OSError as exc:
        e_missing.append((name, repr(exc)))
        continue
    h_fork, h_today = sha(at_fork), sha(today)
    if name in ADJUDICATED_DIFFERENT:
        want_fork, want_today = ADJUDICATED_DIFFERENT[name]
        if h_fork == want_fork and h_today == want_today:
            e_adjudicated += 1
        else:
            e_moved.append((name, want_fork, h_fork, want_today, h_today))
    elif h_fork == h_today:
        e_identical += 1
    else:
        e_diff.append((name, h_fork, h_today))

print("      byte-identical to the fork sha       : %d" % e_identical)
print("      adjudicated-different, UNMOVED       : %d" % e_adjudicated)
print("      DIFFER and are NOT adjudicated       : %d" % len(e_diff))
print("      adjudicated but MOVED                : %d" % len(e_moved))
print("      missing / unreadable                 : %d" % len(e_missing))
for name, h0, h1 in e_diff:
    print("        DIFF %s\n             fork  %s\n             today %s" % (name, h0, h1))
for name, wf, gf, wt, gtd in e_moved:
    print("        ADJUDICATION MOVED %s\n             fork  adjudicated %s got %s"
          "\n             today adjudicated %s got %s" % (name, wf, gf, wt, gtd))
for name, exc in e_missing:
    print("        MISSING %s  %s" % (name, exc))
check("NO capture script or evidence file from the fork-sha manifest has been MUTATED, "
      "outside the two differences adjudicated by digest at the top of this file",
      not e_diff, "unadjudicated differences: %d" % len(e_diff))
check("the two ADJUDICATED differences are still exactly the differences adjudicated — a "
      "further mutation moves this, and so does a revert to the fork bytes",
      not e_moved and e_adjudicated == len(ADJUDICATED_DIFFERENT),
      "unmoved=%d of %d, moved=%d" % (e_adjudicated, len(ADJUDICATED_DIFFERENT), len(e_moved)))
check("NO entry from the fork-sha manifest is missing from disk or from the fork tree",
      not e_missing, "missing=%d" % len(e_missing))

print()
print("=== 8. ARM F — every POST-FORK observation vs the blob at the commit that FIRST ADDED it ===")
print("    T423 / T433, C-T423-1. Until T433 this file asserted, in its own docstring and in")
print("    run-all.sh's section-10 banner, that NO committed baseline older than HEAD existed")
print("    for the post-fork observations, and concluded from that impossibility that a")
print("    committed mutation which ALSO launders the manifest row could not be caught here.")
print("    THE ASSERTION WAS FALSE. `git log --diff-filter=A -- <path>` yields, for every one")
print("    of them, the commit that FIRST ADDED it; the blob there sits inside an ALREADY-")
print("    COMMITTED commit, so rewriting MANIFEST.sha256 in the mutating commit does not")
print("    reach it. That is the baseline. This is the arm. On T393's own 'unclosable'")
print("    laundered residual, ARMs A-E exit 0 / PASS and ARM F exits 1 naming the file.")
f_post = sorted(set(head_paths) - set(fork_paths)) if have_fork else []
try:
    head_sha = git("rev-parse", "HEAD").decode().strip()
except subprocess.CalledProcessError as exc:
    head_sha = ""
    refuse("HEAD could not be resolved: %r. ARM F has no tip to compare against. REFUSED."
           % exc)

print("      post-fork population (HEAD minus the fork sha) : %d" % len(f_post))
if have_fork and not f_post:
    refuse("ARM F's population is EMPTY.",
           "Every observation tracked at HEAD also existed at the fork sha, which means",
           "either the selector broke or FORK moved forward onto HEAD — the exact collapse",
           "T382 drove against ARM A. A zero-difference table over an empty population is a",
           "vacuous pass, and that is the defect this whole section exists to remove.",
           "REFUSED.")

# Birth commit per path, from ONE walk: newest-first, so the LAST assignment is the EARLIEST
# add. Cross-checked per-path against an independent derivation by T433's standalone sweep,
# .softhouse/capture/t433-t423-c1/instruments/00-t433-whole-632-birth-sweep.py, which REFUSES
# on any disagreement; it agreed on 632/632 at tip b102875c.
f_birth, _cur = {}, None
for _line in git("log", "HEAD", "--diff-filter=A", "--name-only", "--format=%H",
                 "--", CAPREL).decode().split("\n"):
    _line = _line.rstrip()
    if not _line:
        continue
    if len(_line) == 40 and all(c in "0123456789abcdef" for c in _line):
        _cur = _line
        continue
    f_birth[_line] = _cur

f_noborn = [p for p in f_post if p not in f_birth]
if f_noborn:
    refuse("%d post-fork observations have NO recorded ADD commit: %s"
           % (len(f_noborn), [p[len(CAPREL) + 1:] for p in f_noborn[:5]]),
           "ARM F's baseline is not derivable for them, so ARM F did not grade them.",
           "An arm that could not measure part of its own population has not passed on it.",
           "REFUSED, never a pass.")

f_same, f_adjudicated, f_diff, f_moved = 0, 0, [], []
f_at_tip, f_unreadable = [], []
f_tip_adjudicated, f_tip_moved = [], []
for rel in f_post:
    b = f_birth.get(rel)
    if b is None:
        continue
    name = rel[len(CAPREL) + 1:]
    if b == head_sha:
        # (iv-a) NO baseline older than HEAD exists for this one. Counted as UNGRADED, never
        # as equal: folding it into f_same is exactly the vacuous pass this file punishes.
        # T455 / C-T448-1: it is also ASSERTED now — section 9 fails on any entry left here
        # that is not adjudicated by name AND digest in ARM_F_BORN_AT_TIP_ADJUDICATED.
        try:
            with open(os.path.join(ROOT, rel), "rb") as fh:
                h_tip = sha(fh.read())
        except OSError as exc:
            f_unreadable.append((name, b, repr(exc)))
            continue
        if name in ARM_F_BORN_AT_TIP_ADJUDICATED:
            if ARM_F_BORN_AT_TIP_ADJUDICATED[name] == h_tip:
                f_tip_adjudicated.append(name)
            else:
                f_tip_moved.append((name, ARM_F_BORN_AT_TIP_ADJUDICATED[name], h_tip))
        else:
            f_at_tip.append((name, h_tip))
        continue
    try:
        at_birth = git("show", b + ":" + rel)
    except subprocess.CalledProcessError as exc:
        f_unreadable.append((name, b, repr(exc)))
        continue
    try:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            today = fh.read()
    except OSError as exc:
        f_unreadable.append((name, b, repr(exc)))
        continue
    h_birth, h_today = sha(at_birth), sha(today)
    if name in ARM_F_ADJUDICATED:
        if (h_birth, h_today) == ARM_F_ADJUDICATED[name]:
            f_adjudicated += 1
        else:
            f_moved.append((name, ARM_F_ADJUDICATED[name], (h_birth, h_today)))
    elif h_birth == h_today:
        f_same += 1
    else:
        f_diff.append((name, b, h_birth, h_today))

f_graded = f_same + f_adjudicated + len(f_diff) + len(f_moved)
print("      GRADED against a birth blob older than HEAD     : %d" % f_graded)
print("        equal to their birth blob                    : %d" % f_same)
print("        adjudicated-different, UNMOVED               : %d" % f_adjudicated)
print("        DIFFER and are NOT adjudicated               : %d" % len(f_diff))
print("        adjudicated but MOVED                        : %d" % len(f_moved))
print("      UNGRADED, born AT THE TIP (boundary iv-a)       : %d" % len(f_at_tip))
print("        of those, ADJUDICATED born-at-tip, UNMOVED   : %d" % len(f_tip_adjudicated))
print("        of those, adjudicated but MOVED              : %d" % len(f_tip_moved))
print("      unreadable at their own birth commit            : %d" % len(f_unreadable))
for name, h_tip in f_at_tip[:10]:
    print("        UNGRADED-BORN-AT-TIP %s" % name)
    print("                             disk sha256 %s" % h_tip)
    print("                             ADJUDICATE IT in ARM_F_BORN_AT_TIP_ADJUDICATED, or")
    print("                             this file FAILS: ARM F did not measure it.")
if len(f_at_tip) > 10:
    print("        ... and %d more born at the tip" % (len(f_at_tip) - 10))
for name in f_tip_adjudicated:
    print("        ADJUDICATED-BORN-AT-TIP %s (ungraded by ARM F, accepted by name+digest)"
          % name)
for name, want, got in f_tip_moved:
    print("        BORN-AT-TIP ADJUDICATION MOVED %s\n                                       "
          "adjudicated %s got %s" % (name, want, got))
for name, b, h0, h1 in f_diff:
    print("        LAUNDERED-OR-MUTATED %s" % name)
    print("                             born at %s" % b)
    print("                             birth   %s" % h0)
    print("                             disk    %s" % h1)
for name, want, got in f_moved:
    print("        ADJUDICATION MOVED %s\n                           birth adjudicated %s got %s"
          "\n                           disk  adjudicated %s got %s"
          % (name, want[0], got[0], want[1], got[1]))
for name, b, exc in f_unreadable:
    print("        UNREADABLE %s  born at %s  %s" % (name, b, exc))

check("NO post-fork captured oracle observation differs from the blob at the commit that "
      "FIRST ADDED it — the baseline a laundered MANIFEST.sha256 row cannot reach",
      not f_diff, "unadjudicated differences: %d" % len(f_diff))
check("ARM F's ONE adjudicated difference is still exactly the difference adjudicated — a "
      "further mutation moves it, and so does a revert to the birth bytes",
      not f_moved and f_adjudicated == len(ARM_F_ADJUDICATED),
      "unmoved=%d of %d, moved=%d" % (f_adjudicated, len(ARM_F_ADJUDICATED), len(f_moved)))
check("EVERY post-fork observation ARM F was handed was readable at its own birth commit",
      not f_unreadable, "unreadable=%d" % len(f_unreadable))

print()
print("=== 9. POSITIVE CONTROLS — every arm actually READ a non-empty population ===")
print("    T374's F-2 rule, applied to all six arms and not only at zero: an arm that")
print("    compared nothing reports no differences, and that is the vacuous pass this")
print("    review exists to make impossible.")
check("ARM A compared a non-empty population", have_fork and len(fork_paths) > 0,
      "%d observations at the fork sha" % len(fork_paths))
check("ARM B compared a non-empty population", len(head_paths) > 0,
      "%d observations at HEAD" % len(head_paths))
check("ARM C compared a non-empty manifest population", len(man_obs) > 0,
      "%d manifest rows under out/ or req/" % len(man_obs))
check("ARM D walked a non-empty disk population", len(disk_rel) > 0,
      "%d files on disk under out/ + req/" % len(disk_rel))
check("ARM E compared a non-empty population", len(fork_nonobs) > 0,
      "%d non-observation entries in the fork-sha manifest" % len(fork_nonobs))
# T433: ARM F's population CANNOT be pinned the way ARM A's 403 is — it grows with every
# legitimate capture. What CAN be asserted is that it is non-empty and that ARM F actually
# GRADED it. Those are different claims, and only the second one is falsified by the way ARM
# F fails open: if history were rewritten so that every post-fork observation were born at
# the tip, ARM F would report 632 ungraded, 0 differences, and read exactly like a pass.
check("ARM F compared a non-empty post-fork population", len(f_post) > 0,
      "%d observations tracked at HEAD that did not exist at the fork sha" % len(f_post))
check("ARM F actually GRADED a non-empty population against a baseline OLDER than HEAD — "
      "an arm whose whole population was born at the tip grades nothing and reads as a pass",
      f_graded > 0,
      "graded=%d of %d post-fork; ungraded because born at the tip=%d"
      % (f_graded, len(f_post), len(f_at_tip)))
# T455 / C-T448-1 — THE (iv-a) FAIL-OPEN, CLOSED. The check above asserts ARM F graded
# SOMETHING. That is not the same claim as "ARM F graded EVERYTHING it was handed", and the
# gap between them was the fail-open: 631 rows graded fine while one fabricated row sat
# UNGRADED and the file exited 0. The rule below is not new to this file — it is the rule
# stated verbatim at the f_noborn refusal in section 8, nine lines above the born-at-tip
# branch, applied to the other half of the same category.
check("ARM F GRADED ITS WHOLE POPULATION — every post-fork observation was measured against "
      "a baseline older than HEAD, or is adjudicated by name AND digest as born at the tip. "
      "AN ARM THAT COULD NOT MEASURE PART OF ITS OWN POPULATION HAS NOT PASSED ON IT — the "
      "sentence section 8 already applies to a path with no recorded ADD commit",
      not f_at_tip,
      "UNGRADED and UNADJUDICATED, born at the tip: %d of %d post-fork  %s"
      % (len(f_at_tip), len(f_post), [n for n, _ in f_at_tip][:5]))
check("ARM F's born-at-tip adjudications are EXACTLY the ones adjudicated — a further "
      "mutation of an adjudicated capture moves it, and so does an entry that no longer "
      "names anything born at the tip (a dead entry is a silent widening of the exception)",
      not f_tip_moved
      and len(f_tip_adjudicated) == len(ARM_F_BORN_AT_TIP_ADJUDICATED),
      "unmoved=%d of %d, moved=%d"
      % (len(f_tip_adjudicated), len(ARM_F_BORN_AT_TIP_ADJUDICATED), len(f_tip_moved)))
check("ARM B's population is a SUPERSET of ARM A's — every historical observation is still "
      "tracked, so neither arm is silently narrower than it reads",
      set(fork_paths) <= set(head_paths),
      "in fork but not at HEAD: %s" % sorted(set(fork_paths) - set(head_paths))[:10])
check("ARM C's row-set and ARM D's disk-set are the SAME set as ARM B's tracked set, so the "
      "three populations agree and none of them is silently the empty intersection",
      set(man_obs) == tracked_rel == set(disk_rel),
      "manifest=%d tracked=%d disk=%d" % (len(man_obs), len(tracked_rel), len(disk_rel)))

print()
print("=== 10. THE CORRECTION ITSELF — is the false claim QUOTED, or RE-ASSERTED? ===")
print("    T455 / C-T448-2. C-T423-1's repair keeps every false sentence VERBATIM and TAGS")
print("    it, so a guard can tell a quotation from an assertion by grep. T433's guard")
print("    asserted the TAG: no UNTAGGED line states the claim, and at least three tagged")
print("    lines survive. T448 defeated BOTH halves with a one-line edit, at guard exit 0 —")
print("    (B) re-assert the claim as a LIVE echo with the tag in a TRAILING COMMENT, so the")
print("    transcript prints it untagged; (C) DELETE the quotation and keep three bare tags.")
print("    The tag was graded; its BINDING to the text was not. Both predicates are here,")
print("    INSIDE the grader run-all.sh adjudicates (P-45), not beside it.")
print("    RE-DERIVED, NOT INHERITED: T448's supplied one-predicate repair closes (C) and")
print("    does NOT close (B) — the smuggled line carries the tag in its trailing comment,")
print("    so `both` == `all` == 2 and the binding predicate passes it. Measured, in")
print("    `.softhouse/capture/t455-t448-conditions/out/30-TAG-BINDING-DRIVE.txt`. (B) is")
print("    closed only by the SECOND predicate, which reads what a line PRINTS.")

# The claim patterns are ASSEMBLED FROM WORDS rather than written out as literals, for one
# reason: THIS FILE IS ONE OF THE FILES SCANNED BELOW, and a line here carrying a false claim
# in one piece would be an untagged assertion of it — the check would fail on its own matcher,
# or would have to exempt itself, which is a hole. Do not "tidy" these back into literals.
FALSE_CLAIMS = tuple(" ".join(w) for w in (
    ("there", "is", "no", "committed", "baseline", "older", "than", "head"),
    ("no", "baseline", "older", "than", "head", "anywhere"),
    ("does", "not", "exist", "and", "cannot", "be", "manufactured", "here"),
    ("committed", "baseline", "older", "than", "head", "for", "those", "632"),
    ("not", "closable", "by", "internal", "consistency"),
))
TAG = "QUOTED-" + "FALSE-CLAIM"
# file -> the POSITIVE half: the replacement text that must still be present. P-35: every
# vacuous guard in this repo is a negative one, so each negative is paired with a positive. A
# file that was simply DELETED, or emptied, fails the positive half.
CORRECTED = (
    (A2_11_REL + "/verify-capture-integrity.py",
     "THE BLOB AT THE COMMIT THAT FIRST ADDED EACH OBSERVATION"),
    (A2_11_REL + "/run-all.sh",
     "BLOB AT THE COMMIT THAT FIRST ADDED EACH OBSERVATION"),
    (".softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh",
     "THE BLOB AT THE COMMIT THAT"),
    (".softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py",
     "THE BASELINE EXISTS AND ALWAYS DID"),
)


def states_a_false_claim(line):
    low = line.lower()
    return any(c in low for c in FALSE_CLAIMS)


def strip_trailing_comment(line):
    """Remove a `#` comment that is OUTSIDE quotes — i.e. the part a reader never sees.

    This is the whole of abuse (B): the tag sits in a trailing shell comment, so the SOURCE
    line carries it and the PRINTED line does not. Reading the source is reading the wrong
    artefact. Only `"` and `'` are tracked, with backslash escapes; that is enough for the
    `echo "..."` and `print("...")` forms these four files use, and anything it cannot parse
    is left INTACT, which fails closed rather than open.
    """
    out, quote, i = [], None, 0
    while i < len(line):
        ch = line[i]
        if quote:
            if ch == "\\" and i + 1 < len(line):
                out.append(ch)
                out.append(line[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def quoted_segments(line):
    """Every string-literal BODY on one line, after any out-of-quote comment is cut.

    The lexical half of the payload extractor, used for shell files and for a python file
    that will not parse. An UNTERMINATED quote yields the rest of the line as a segment:
    fail CLOSED, because a payload this cannot lex is a payload it has not cleared.
    """
    code = strip_trailing_comment(line)
    segs, quote, buf, i = [], None, [], 0
    while i < len(code):
        ch = code[i]
        if quote:
            if ch == "\\" and i + 1 < len(code):
                buf.append(code[i + 1])
                i += 2
                continue
            if ch == quote:
                segs.append("".join(buf))
                buf = []
                quote = None
            else:
                buf.append(ch)
        elif ch in "\"'":
            quote = ch
        i += 1
    if quote is not None:
        segs.append("".join(buf))
    return segs


def python_payloads(text):
    """Every string CONSTANT in a python file that is not inert, as (lineno, value).

    INERT means "cannot reach a reader": a module/class/function DOCSTRING, and any bare
    string EXPRESSION STATEMENT. Comments are not in the AST at all, so they are excluded by
    construction. EVERYTHING ELSE IS A PAYLOAD — this never asks whether the constant is
    passed to `print`, to `sys.stdout.write`, to a logger, to `printf` through subprocess, or
    stored in a variable that is printed forty lines later. That is the whole point (T467 /
    F-T464-1): the question is what a line CARRIES to a reader, not which builtin carries it.
    Over-approximating in the payload direction is the FAIL-CLOSED direction.
    """
    tree = ast.parse(text)
    inert = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                and body and isinstance(body[0], ast.Expr) \
                and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            inert.add(id(body[0].value))
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            inert.add(id(node.value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in inert:
            out.append((getattr(node, "lineno", 0), node.value))
    return out


def printed_payloads(text, rel):
    """Every reader-visible payload in one file, as (lineno, payload).

    T467 / F-T464-1 — THE EMITTER CLASS, CLOSED. T455 shipped an `emitted_payload` that
    recognised exactly two spellings: a line whose first token is `echo` and a line whose
    first token is `print(`. THREE OTHER SPELLINGS WENT STRAIGHT THROUGH, measured at T455's
    own merge commit, each smuggling the tagged-away sentence back as a live untagged
    assertion with section 10 at EXIT 0:

        printf '%s\\n' "<the claim>"     # <tag>
        >&2 echo "<the claim>"           # <tag>
        sys.stdout.write("<the claim>")  # <tag>

    and this is not a hypothetical reach: `printf` is already used 12 times in
    10-drive-conditions.sh and 5 times in run-all.sh, two of the four files this section
    guards. An enumeration of emitter names is a list that the next author extends without
    reading, so the repair is NOT to add three names. It is to stop asking which builtin
    prints and start asking what the line CARRIES:

      * python  -> every string CONSTANT that is not a docstring or a bare string statement
                   (ast; comments are absent from the tree, so they cost nothing to exclude);
      * shell   -> every quoted SEGMENT left after the out-of-quote `#` comment is cut;
      * a .py that will not PARSE -> the shell rule, so a syntax error cannot buy silence.

    FAIL-CLOSED BY CONSTRUCTION: a non-emitting line that merely CARRIES a quoted claim (a
    grep pattern, a comparison string) is judged as if it printed. The cost of that is
    measured, not assumed — on the four guarded files at this ref it is ZERO false positives.
    WHAT IS DELIBERATELY NOT COVERED, and stays open: a claim assembled at RUNTIME and printed
    through a VARIABLE (`printf '%s' "$SENTENCE"`) carries no literal, so no static reader of
    the source can see it; and a claim WRAPPED across two payloads is caught by predicate 1
    (which de-wraps) but not by this one, which is per-payload.
    """
    if rel.endswith(".py"):
        try:
            return python_payloads(text)
        except SyntaxError:
            pass
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        for seg in quoted_segments(line):
            out.append((i, seg))
    return out


def tagged_blocks(text):
    """Every CONTIGUOUS run of tagged lines, DE-WRAPPED into one string each.

    A quotation of any length is wrapped across source lines, so a LINE-oriented matcher
    cannot bind a tag to the text it tags: measured on
    `10-drive-conditions.sh`, whose four tagged lines split the sentence at
    "... has no / baseline older than HEAD anywhere ...", so NO line carries the claim and a
    line-wise search scores it 0 stated, 0 tagged — indistinguishable from abuse (C), where
    the quotation is gone entirely. De-wrapping is what makes the two distinguishable.
    Blocks are CONTIGUOUS runs, not the whole file, so two unrelated quotations cannot be
    concatenated into a claim neither of them makes.
    """
    blocks, cur = [], []
    for line in text.split("\n"):
        if TAG in line:
            s = line.replace("[" + TAG + "]", " ").replace(TAG, " ")
            cur.append(s.lstrip().lstrip("#").strip())
        elif cur:
            blocks.append(" ".join(" ".join(cur).split()))
            cur = []
    if cur:
        blocks.append(" ".join(" ".join(cur).split()))
    return blocks


def grade_binding(text, rel):
    """(stated_untagged, quoted_claims, printed_untagged) for one file's text.

    PREDICATE 1 — BINDING, two halves that must BOTH hold:
      NEGATIVE  no UNTAGGED line states a false claim (T433's half, kept);
      POSITIVE  at least one DE-WRAPPED TAGGED BLOCK still contains a false claim VERBATIM.
                This is the half T433's guard did not have: it counted TAGS. Three bare tags
                satisfy a tag count and contain no quotation, which is abuse (C).
    PREDICATE 2 — PRINTED. Every reader-visible PAYLOAD that states a false claim must carry
    the tag INSIDE THE PAYLOAD. Closes (B): a tag in a trailing comment is never printed, so
    the source carries it and the reader's transcript does not. The source is not the artefact
    the reader sees, and the tag exists for the reader. `printed_payloads` decides what a
    payload IS without naming a single emitter — see its docstring (T467 / F-T464-1).
    """
    lines = text.split("\n")
    stated_untagged, printed_untagged = [], []
    for line in lines:
        if states_a_false_claim(line) and TAG not in line:
            stated_untagged.append(line.strip()[:90])
    for lineno, payload in printed_payloads(text, rel):
        if states_a_false_claim(payload) and TAG not in payload:
            src_line = lines[lineno - 1].strip()[:90] if 0 < lineno <= len(lines) else ""
            printed_untagged.append("%s:%d %s" % (os.path.basename(rel), lineno, src_line))
    quoted_claims = sum(1 for c in FALSE_CLAIMS
                        if any(c in b.lower() for b in tagged_blocks(text)))
    return stated_untagged, quoted_claims, printed_untagged


# P-22, IN SITU, BEFORE ANY VERDICT — the classifier is driven on a known GOOD text and on
# BOTH of T448's abuses, in memory. A binding check that has never rejected anything is not a
# check. The scratch-clone end-to-end drive is
# `.softhouse/capture/t455-t448-conditions/instruments/30-t455-tag-binding-drive.sh`.
# The fixture sentence is ASSEMBLED from the pattern table, never typed: a literal here would
# be an untagged assertion of the claim in this very file, and PREDICATE 1 would fail on its
# own test data. (It did, on the first run — states=3 tagged=1. The guard caught its author.)
_SENTENCE = "There is no " + FALSE_CLAIMS[3] + "."
_GOOD = ('  echo "  [%s] %s"\n'
         '  echo "THE BASELINE IS THE BLOB AT THE COMMIT THAT FIRST ADDED EACH OBSERVATION."\n'
         % (TAG, _SENTENCE))
_ABUSE_B = _GOOD + ('  echo "%s"  # %s\n' % (_SENTENCE, TAG))
_ABUSE_C = ('  # %s (tidied: the quotation was removed, the tag was not)\n' % TAG) * 3
_WRAPPED = ('  # [%s] "Expected UNDETECTED at BOTH refs ... has no\n'
            '  # [%s]  baseline older than HEAD anywhere in this repository."\n' % (TAG, TAG))
# T467 / F-T464-1 — THE THREE SPELLINGS THAT WENT THROUGH T455's `echo`/`print(` matcher,
# each built the same way as _ABUSE_B: a LIVE emitter with the tag in a trailing comment. They
# are fixtures for the CLASS, not a list to be extended — the predicate they drive names no
# emitter at all. `_ABUSE_OSWRITE` is deliberately a spelling nobody has used in this
# repository, so the class claim is tested against something that is not on any list.
_ABUSE_PRINTF = _GOOD + ("  printf '%%s\\n' \"%s\"  # %s\n" % (_SENTENCE, TAG))
_ABUSE_STDERR = _GOOD + ('  >&2 echo "%s"  # %s\n' % (_SENTENCE, TAG))
_ABUSE_SYSWRITE = ('print("  [%s] %s")\n' % (TAG, _SENTENCE)
                   + 'sys.stdout.write("%s\\n")  # %s\n' % (_SENTENCE, TAG))
_ABUSE_OSWRITE = ('print("  [%s] %s")\n' % (TAG, _SENTENCE)
                  + '_msg = "%s"  # %s\n' % (_SENTENCE, TAG)
                  + 'os.write(1, _msg.encode())\n')
# And the discrimination fixtures: text that quotes the claim but PRINTS NOTHING. A predicate
# that flagged these would be predicate 1 wearing a second name, and it would make every
# tagged comment in the corrected files a failure — which is how a guard gets deleted (P-29).
_INERT_COMMENT = '# [%s] "%s"\n' % (TAG, _SENTENCE)
_INERT_DOCSTRING = '"""a docstring\n[%s] "%s"\n"""\n' % (TAG, _SENTENCE)

_g_bad, _g_q, _g_printed = grade_binding(_GOOD, "fixture.sh")
_b_bad, _b_q, _b_printed = grade_binding(_ABUSE_B, "fixture.sh")
_c_bad, _c_q, _c_printed = grade_binding(_ABUSE_C, "fixture.sh")
_w_bad, _w_q, _w_printed = grade_binding(_WRAPPED, "fixture.sh")
_pf_bad, _pf_q, _pf_printed = grade_binding(_ABUSE_PRINTF, "fixture.sh")
_se_bad, _se_q, _se_printed = grade_binding(_ABUSE_STDERR, "fixture.sh")
_sw_bad, _sw_q, _sw_printed = grade_binding(_ABUSE_SYSWRITE, "fixture.py")
_ow_bad, _ow_q, _ow_printed = grade_binding(_ABUSE_OSWRITE, "fixture.py")
_ic_bad, _ic_q, _ic_printed = grade_binding(_INERT_COMMENT, "fixture.py")
_id_bad, _id_q, _id_printed = grade_binding(_INERT_DOCSTRING, "fixture.py")
check("SELF-DRIVE — the binding classifier ACCEPTS a correctly tagged quotation (a check "
      "that rejected everything would be a freeze, not a guard)",
      _g_q >= 1 and not _g_bad and not _g_printed,
      "untagged-statements=%d quoted-claims=%d printed-untagged=%d"
      % (len(_g_bad), _g_q, len(_g_printed)))
check("SELF-DRIVE — the classifier ACCEPTS a quotation WRAPPED across two lines, where no "
      "single line carries the claim. Rejecting it would make the guard unusable on the "
      "real files, which is how a guard gets deleted rather than fixed (P-29)",
      _w_q >= 1 and not _w_bad, "quoted-claims=%d untagged-statements=%d" % (_w_q, len(_w_bad)))
check("SELF-DRIVE — the classifier REJECTS abuse (B): the claim re-asserted as a LIVE echo "
      "with the tag in a TRAILING COMMENT. NOTE WHICH PREDICATE CATCHES IT — the binding "
      "half does NOT (the source line carries the tag); only the PRINTED half does. That is "
      "why there are two, and it is where T448's one-predicate repair stops short",
      bool(_b_printed) and not _b_bad and _b_q >= 1,
      "untagged-statements=%d quoted-claims=%d printed-untagged=%d %s"
      % (len(_b_bad), _b_q, len(_b_printed), _b_printed[:1]))
check("SELF-DRIVE — the classifier REJECTS abuse (C): the quotation deleted, bare tags kept "
      "(the outcome T433's third red drive claims to prevent, but never separates from the "
      "text because it deletes tag and text together)",
      _c_q == 0,
      "quoted-claims=%d tags=%d — bare tags satisfy a TAG COUNT and fail a BINDING"
      % (_c_q, _ABUSE_C.count(TAG)))

# T467 / F-T464-1 — THE SAME ABUSE, THREE OTHER SPELLINGS, AND ONE NOBODY HAS WRITTEN YET.
# T455 closed `echo`. Measured at T455's merge commit, `printf`, `>&2 echo` and
# `sys.stdout.write` each took section 10 to EXIT 0 with the sentence smuggled back as a live
# untagged assertion, and `printf` is ALREADY in two of the four guarded files (12 uses in
# 10-drive-conditions.sh, 5 in run-all.sh). These four assertions are the class, driven.
check("SELF-DRIVE — the classifier REJECTS abuse (B) spelled with `printf` — the emitter "
      "T455's matcher did not know and the guarded files already use 17 times between them",
      bool(_pf_printed) and not _pf_bad and _pf_q >= 1,
      "printed-untagged=%d %s" % (len(_pf_printed), _pf_printed[:1]))
check("SELF-DRIVE — the classifier REJECTS abuse (B) spelled `>&2 echo`, where the emitter "
      "T455 DID know about is not the first token on the line",
      bool(_se_printed) and not _se_bad and _se_q >= 1,
      "printed-untagged=%d %s" % (len(_se_printed), _se_printed[:1]))
check("SELF-DRIVE — the classifier REJECTS abuse (B) spelled `sys.stdout.write(...)` in a "
      "python file, which is neither `print(` nor `echo `",
      bool(_sw_printed) and not _sw_bad and _sw_q >= 1,
      "printed-untagged=%d %s" % (len(_sw_printed), _sw_printed[:1]))
check("SELF-DRIVE — and it REJECTS a spelling NOBODY IN THIS REPOSITORY HAS USED: the claim "
      "bound to a variable and written to fd 1 by `os.write`. This is the class claim under "
      "test — the predicate names no emitter, so an emitter it has never seen is not a hole",
      bool(_ow_printed) and not _ow_bad and _ow_q >= 1,
      "printed-untagged=%d %s" % (len(_ow_printed), _ow_printed[:1]))
check("SELF-DRIVE — the PRINTED predicate does NOT fire on a COMMENT that quotes the claim "
      "with the tag outside the quotes, and does NOT fire on a DOCSTRING that does the same. "
      "Those print nothing, predicate 1 already grades them, and a predicate that flagged "
      "them would redden every corrected file for carrying its own correction",
      not _ic_printed and not _id_printed,
      "comment-printed=%d docstring-printed=%d" % (len(_ic_printed), len(_id_printed)))

_bind_bad, _print_bad, _pos_bad, _missing = [], [], [], []
_emitted_tagged = 0
for _rel, _positive in CORRECTED:
    _abs = os.path.join(ROOT, _rel)
    try:
        with open(_abs, "r", encoding="utf-8") as fh:
            _text = fh.read()
    except OSError as exc:
        _missing.append((_rel, repr(exc)))
        continue
    _untagged, _quoted, _printed = grade_binding(_text, _rel)
    print("      %-42s untagged-statements=%d quoted-claims=%d printed-untagged=%d"
          % (os.path.basename(_rel), len(_untagged), _quoted, len(_printed)))
    for _u in _untagged:
        print("        UNTAGGED-ASSERTION %s" % _u)
    if _untagged or _quoted < 1:
        _bind_bad.append((_rel, len(_untagged), _quoted))
    for _p in _printed:
        _print_bad.append((_rel, _p))
    if _positive not in _text:
        _pos_bad.append((_rel, _positive))
    for _lineno, _pl in printed_payloads(_text, _rel):
        if states_a_false_claim(_pl) and TAG in _pl:
            _emitted_tagged += 1
for _rel, _exc in _missing:
    print("        MISSING %s  %s" % (_rel, _exc))
if _missing:
    refuse("%d of the %d corrected files could not be read: %s"
           % (len(_missing), len(CORRECTED), [r for r, _ in _missing]),
           "A file this section cannot read is a file this section did not grade.",
           "REFUSED, never a pass.")

check("PREDICATE 1, BINDING — in every corrected file, NO untagged line states a false claim, "
      "AND at least one DE-WRAPPED TAGGED BLOCK still contains one VERBATIM. A tag with no "
      "quotation under it grades nothing; a quotation with no tag is an assertion",
      not _bind_bad,
      "(file, untagged-statements, quoted-claims): %s" % _bind_bad)
check("PREDICATE 2, PRINTED — no line that the tooling actually EMITS states a false claim "
      "without the tag INSIDE what it prints. The source is not the artefact a reader sees, "
      "and a tag in a trailing comment is not printed at all",
      not _print_bad,
      "emitted untagged: %s" % _print_bad[:3])
check("POSITIVE HALF — every corrected file still states what the baseline IS. A negative "
      "assertion alone passes on an empty file (P-35)",
      not _pos_bad, "missing replacement text: %s" % [r for r, _ in _pos_bad])
check("VACUITY CONTROL — at least one TAGGED false claim is actually EMITTED somewhere in "
      "the corrected set, so predicate 2 is grading a non-empty population. Zero emitted "
      "quotations would make it pass by having nothing to look at",
      _emitted_tagged > 0, "emitted tagged quotation lines: %d" % _emitted_tagged)

# T455 / C-T448-6 — the transcript footer. `run-all.sh`'s body is `{ ... } | tee`, which
# TRUNCATES: T433 appended a correction footer to TRANSCRIPT-A2-11.txt and the next run of the
# script it documents erased it (measured 1 -> 0), with nothing asserting it. The repair is not
# to re-append it — it is to make run-all.sh EMIT it, inside the teed block, every run. That is
# asserted here rather than in the transcript, because a transcript cannot guard itself.
_runall_abs = os.path.join(ROOT, A2_11_REL + "/run-all.sh")
try:
    with open(_runall_abs, "r", encoding="utf-8") as fh:
        _runall_text = fh.read()
except OSError as exc:
    _runall_text = ""
    refuse("run-all.sh could not be read: %r. Section 10 cannot grade the footer." % exc,
           "REFUSED, never a pass.")
check("run-all.sh REGENERATES its correction footer instead of relying on an appended one — "
      "the `| tee` truncates the transcript on every run, so an appended footer survives "
      "exactly until the next run of the script that documents it (C-T448-6)",
      "CORRECTION INDEX, REGENERATED ON EVERY RUN" in _runall_text,
      "footer marker present in run-all.sh: %s"
      % ("CORRECTION INDEX, REGENERATED ON EVERY RUN" in _runall_text))

print()
if refusals:
    print("REFUSALS: %d" % len(refusals))
    for r in refusals:
        print("  - " + r)
print("FAILURES: %d" % len(fails))
for f in fails:
    print("  - " + f)

if refusals:
    print()
    print("VERDICT: REFUSED (exit 2). The instrument could not measure. This is NOT a pass,")
    print("and run-all.sh adjudicates this section to 0, so a refusal moves it and fails the")
    print("aggregate verdict.")
    sys.exit(2)
if fails:
    print()
    print("VERDICT: FAIL (exit 1). A CAPTURED ORACLE OBSERVATION HAS BEEN MUTATED OR LOST,")
    print("OR THE POPULATION ITSELF HAS MOVED, OR A SCRIPT THAT PRODUCED THE CORPUS HAS")
    print("CHANGED. This is the evidence the whole program grades against. Do not repair it")
    print("by re-capturing and committing over the top: that launders the mutation into the")
    print("record. Establish what changed, and why, first.")
    sys.exit(1)
print()
print("VERDICT: PASS (exit 0). Every captured oracle observation under %s/{out,req}/"
      % CAPREL)
print("is byte-identical to its fork-sha blob, to its HEAD blob and to its MANIFEST digest;")
print("the disk under those directories holds exactly the tracked set and nothing else, all")
print("of it regular files; the 27 fork-sha manifest entries outside them are unchanged")
print("apart from the two adjudicated by digest above; and %d of the %d POST-FORK"
      % (f_graded, len(f_post)))
print("observations still equal the blob at the commit that FIRST ADDED them, apart from the")
print("one adjudicated by digest above. ARM F GRADED ITS WHOLE POPULATION: %d unadjudicated"
      % len(f_at_tip))
print("observations were born at the tip and left ungraded (T455 / C-T448-1 — a non-zero here")
print("FAILS this file; an arm that could not measure part of its own population has not")
print("passed on it), and %d were accepted as born-at-tip by name AND digest. What is still"
      % len(f_tip_adjudicated))
print("NOT reached is stated at boundary (iv-a): DETECTING a fabricated capture needs the")
print("reference oracle, not this file. That is a boundary on DETECTION, and it is no longer")
print("also a fail-open on the VERDICT.")
sys.exit(0)
