#!/usr/bin/env python3
"""T527 -- REFUSE when the recorded task state CLAIMS work that `origin` has never heard of.

WHY THIS EXISTS, MEASURED NOT INFERRED.
On 2026-09-04 the driver measured, from `/home/user/gerege-nbfi`:

    for sha in 1abd3a11 857dd4d8 5c4233fc 8ff5ff15 84dc208e; do
      git rev-parse --verify -q $sha^{commit} || echo "ABSENT $sha"; done
    git ls-remote --heads origin 'refs/heads/softhouse/*' \\
      | grep -oE 'T[0-9]+' | sort -tT -k2 -n | tail -1

Every one of those five shas was ABSENT, and the highest task id pushed to `origin` was
`T497`. Nothing above T497 was ever pushed. Yet `.softhouse/tasks.json` ON MAIN recorded
`T508` and `T509` and `T515` as `done`, `T510` as `needs_retry` and `T512` as
`needs_conditions`, each with a `note` naming the branch and the commit that "landed".
`T509` is the program's recorded critical path. `T502`/`T511`/`T516`/`T519` survived only
because their MERGE commits carried their content onto main; the five above did not merge,
so their entire content is on one laptop and the record says otherwise.

That is `P-85` one level out. `P-85` is an orchestrator that committed its lock, its
dispatch record and its in-flight manifest and NEVER PUSHED THEM, so "the only evidence a
second orchestrator could read said the opposite of the truth". Here the unpushed state is
five workers' whole output, and the evidence that lies is `tasks.json` itself.

WHY NO EXISTING INSTRUMENT CAUGHT IT.
  * `ready-tasks.py` already warns when work bearing a task id is ALREADY ON MAIN (the
    T286 arm). That is the OPPOSITE direction. It has no arm for "this task claims a
    branch or a commit that origin has never heard of".
  * `conformance.sh` grades the TREE. The tree was fine. The defect is in what the tree
    ASSERTS about work that is not in it.

WHAT THIS TOOL DOES.
For every task in `.softhouse/tasks.json` AND every `.softhouse/runs/*.tasks.json` archive
whose status is terminal-or-awaiting-review, it extracts every BRANCH name and every
COMMIT id the record claims -- from the `branch` / `branch_mac` / `branch_cloud` / `tip` /
`merged_commit` fields AND from the free-text `note` -- and refuses, naming each one, when
origin has never heard of it.

THE SHAS LIVE IN THE NOTES. Not one of the five incident tasks has a `tip` or a
`merged_commit` field; all five carry their sha in the prose of `note` ("landed 1abd3a11
on softhouse/T508-..."). A field-only reader would have scored this incident CLEAN, which
is why the free-text arm is not optional and is not a nicety.

FAIL CLOSED (`P-45`). If origin cannot be reached, or the object store cannot be brought
level with origin, this REFUSES with exit 3 and a DISTINCT banner. It never passes when it
could not look. This program has recorded that a guard which passes when it cannot look
enforces nothing at least five times over, and an offline pass here would have reported
THIS VERY INCIDENT green.

EXEMPT NOTHING SILENTLY (task rule 4). Three exemptions exist and all three are printed:
  1. PRUNED-PROVED -- a branch legitimately deleted after its merge landed. Recognised
     ONLY by `git merge-base --is-ancestor <sha> origin/main` on a LANDING commit the SAME
     task claims FOR THAT BRANCH. NEVER by trusting a note that says it was merged: a note
     is exactly what was wrong here, and every one of the five incident notes says the
     work landed. "LANDING" is EARNED, not assumed -- see the ROLE paragraph above
     `CLAIM_ANCHORS`.
  2. BASELINE -- see the BASELINE section below. Enumerated item by item, by EXACT
     subject, in a committed file; and it is FROZEN BY GENERATION as well as by name, so
     `--write-baseline` cannot waive a claim from a task id above `frozen_above`.
  3. UNCLASSIFIED-HEX -- hex tokens in a note that this tool did not read as a commit
     claim. Counted and sampled on every run so the reader can see what was not checked.
     See "WHY THE COMMIT EXTRACTOR IS CONTEXT-ANCHORED" below.

WHY THE COMMIT EXTRACTOR IS CONTEXT-ANCHORED, AND WHAT THAT COSTS.
A bare `\\b[0-9a-f]{8}\\b` over the notes yields 250 distinct tokens, 95 of which resolve
to nothing -- and the overwhelming majority of those 95 are NOT unpushed commits. They are
sha256 digests and tree hashes, e.g.

    T84   "canonical sha256 01b41d9c...3101b IDENTICAL"
    T176  "Byte-identity proven (48687 bytes, sha256 fecea4b2...)"
    T487  "ATTESTED IDENTICAL to the graded tree, 265f9192b6eea682f8975ec57dfebf201442f7cd"
    T228  "21 money cells, store 8968c559"

plus commit ids belonging to the PINNED FINERACT CHECKOUT, which is a different repository
and whose objects this repo has never held. Refusing on those would bury the five real
findings under ~90 false ones, and a guard nobody can read is a guard nobody runs (`P-45`
again, from the other side). So a hex token is read as a CLAIMED COMMIT only inside a
claim phrase -- "landed X", "merged as X", "commit X", "tip X", "COMPLETE @ X", a
"(X)" immediately after a branch name, or inside a stack/base clause.

THE COST IS REAL AND IS NOT HIDDEN: a note that claims a commit in a phrasing this tool
does not know is NOT CHECKED. The count and a sample of every unclassified hex token is
printed on every run, precisely so that the size of the blind spot is a number on the
screen rather than an assumption. Adding an anchor is a one-line change; the anchor list
is `CLAIM_ANCHORS` below.

BASELINE -- WHAT IT WAIVES AND WHY IT IS NOT A SILENT PASS.
Run over the whole record on 2026-09-04 this produces several hundred findings, and the
overwhelming majority are historical: branches from `A2-*` and `T38`..`T501` pruned long
ago and landed by a squash commit that named neither the branch nor left a per-task
artefact, plus their tip shas, so no proof of landing survives in git. They are not
evidence of loss; they are evidence that this control did not exist while they were being
retired. Refusing on all of them every fire would make the report unreadable, and an
unreadable report is an unread one.

So there is an ENUMERATED baseline file
(`.softhouse/capture/t527-branch-published/baseline.json`), generated by
`--write-baseline`, listing each waived `<task-id>\\t<exact branch or commit>` pair. It
is printed in full on every run under "WAIVED (baseline)". Because every key is an EXACT
subject, the file can only forgive claims that already existed when it was written -- it
has no wildcard and no prefix, so it cannot forgive a commit that does not exist yet.

`--write-baseline` REFUSES BY NAME to waive anything from T508, T509, T510, T512, T515,
T520, T522, T523 or the commits 1abd3a11 / 857dd4d8 / 5c4233fc / 8ff5ff15 / 84dc208e, and
prints what it refused. `--selftest` case `G-BASELINE-EXCLUDES-INCIDENT` asserts the
shipped file honours that.

T536 -- AND BY GENERATION, WHICH IS THE PART THAT PROTECTS THE NEXT ONE. A name list is a
blocklist of the incident that already happened; T528 F-3 measured it and a brand-new task
claiming a lost branch and a lost commit was laundered by ONE `--write-baseline` run,
which printed "REFUSED TO WAIVE 0 finding(s)" while doing it. The baseline now carries
`frozen_above` (T527, the generation at which this control was introduced) and
`--write-baseline` refuses ANY finding whose task id sorts above that line, or whose id it
cannot date at all. Deleting `baseline.json` does not lift the line -- the tool falls back
to the `FROZEN_ABOVE` constant here. Raising it is a one-line diff in a committed file
that says, in effect, "everything between the old and the new line is history, not lost
work". See `capture/t527-branch-published/t536-incident3.py`, which drives a synthetic
incident under an id no blocklist has ever heard of, plus the anti-vacuity cell proving a
HISTORICAL id is still waivable.

WHAT THIS TOOL STILL DOES NOT DO. It refuses when the RECORD claims work origin has never
heard of. It does not, and cannot, tell you that a task which claims nothing has lost
nothing: a terminal task with no branch field and a note that names neither a branch nor a
sha is invisible to both arms. The UNCLASSIFIED-HEX count is the measured part of that
blind spot; the unmeasured part is silence in the record itself.

CONSEQUENCE, STATED SO IT IS NOT MISTAKEN FOR A BUG: this tool is RED on `main` today,
naming the incident, and it stays red until either those branches reach origin or the
notes are corrected to say the work is UNRECOVERED. Editing this tool is not the repair.

Usage:
  python3 .softhouse/bin/check-branch-published.py [--repo DIR] [--json]
                                                   [--baseline PATH] [--write-baseline]
                                                   [--full-baseline] [--timeout SECS]
  python3 .softhouse/bin/check-branch-published.py --selftest [--keep]

There is deliberately NO flag that lets this pass without contacting origin. A `--offline`
or `--no-fetch` escape hatch is the `P-91` burden inversion: the caller that most wants it
is the caller whose claim is least checkable.

Exit codes:
  0   CLEAN -- every claim is backed by origin, or waived by a printed exemption
  2   REFUSE -- unbacked claims, each one named
  3   REFUSE -- CANNOT ESTABLISH ORIGIN. Distinct from 2 on purpose: 2 means "I looked and
      the record is wrong", 3 means "I could not look". Never a pass.
  64  usage error
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Terminal-or-awaiting-review. A task in one of these states has stopped moving, so its
# recorded branch and commit are CLAIMS ABOUT FINISHED WORK, which is exactly what must be
# backed by origin. `pending` and `in_progress` are excluded: a task that has not run yet,
# or is running right now, is expected to have nothing on origin. `in_progress` is
# ready-tasks.py's own problem and it has three patterns' worth of machinery for it.
CHECKED_STATUSES = {"done", "merged", "needs_retry", "needs_conditions", "parked"}

BRANCH_FIELDS = ("branch", "branch_mac", "branch_cloud")
COMMIT_FIELDS = ("tip", "merged_commit")

# A branch name as this pipeline spells it. Anchored on the `softhouse/` prefix because
# that is the only namespace workers push to, and because an unanchored branch-shaped
# pattern over free prose matches half the English language.
#
# TWO DELIBERATE NARROWINGS, both measured against the real notes:
#   * the lookbehind rejects `.softhouse/...`, which is the REPOSITORY DIRECTORY and
#     appears in almost every note (`.softhouse/reviews/A2-11/`,
#     `.softhouse/guards/ledgerguard/main.go`). Without it the first run of this tool
#     produced 445 findings, of which dozens were file paths reported as missing
#     branches -- a report that loud is a report nobody reads.
#   * the name is ONE segment: every branch this pipeline has ever pushed is
#     `softhouse/<one-segment>` (`git ls-remote --heads origin`, 47 refs, 2026-09-04).
#     Allowing `/` inside made `softhouse/guards/ledgerguard/main.go` a branch name.
BRANCH_RE = re.compile(r"(?<![A-Za-z0-9._/+-])softhouse/[A-Za-z0-9._+-]+")

# Trailing punctuation that prose puts after a branch name. `.` is deliberately NOT
# stripped from the middle -- `softhouse/T253b-harness-portability-mac` is a real name.
BRANCH_TRIM = ".,;:)]}'\"`"

# A FILE, not a branch. T512's note says the skill "named softhouse/SKILL.md as the
# offender", meaning `.claude/skills/softhouse/SKILL.md`, and the tool reported a missing
# branch called `softhouse/SKILL.md`. One false name in a report about missing work is one
# too many -- it is exactly the sort of detail that lets a reader dismiss the other 300.
NOT_A_BRANCH = re.compile(r"\.(md|sh|py|go|json|txt|ya?ml|zsh|xml|java|sql|csv)$", re.I)

HEX = r"[0-9a-f]{8,40}"
HEX_TOKEN = re.compile(r"(?<![0-9a-zA-Z])(" + HEX + r")(?![0-9a-zA-Z])")

# CLAIM ANCHORS -- EXTRACTION ONLY. Each pattern must capture the sha in group("sha").
# A hex token is read as a commit CLAIM only if some anchor captures it; every claimed
# commit must exist and be reachable from an origin ref, whatever its role. Grow this list
# when a new phrasing shows up in the UNCLASSIFIED-HEX sample -- that sample exists to
# tell you when to.
#
# T536 -- THE DEFAULT IS NOW `REFERENCE` AND THESE ANCHORS NO LONGER CARRY A ROLE.
# T527 tagged each anchor LANDING or REFERENCE with LANDING as the effective default: two
# entries were REFERENCE and everything else -- including the whole `stack ...` region --
# proved landing. T528 measured what that costs (`reviews/t528-review-t527/REVIEW.md`
# F-1): SEVEN of twelve base-citation paraphrases read as proof of landing, and rewording
# T509's real note on main from `merge base 10baca08` to `merge-base commit 10baca08` --
# ONE WORD -- moved `UNBACKED-BRANCH T509` out of the findings and into the waivers.
# Tagging anchors is a blocklist of phrasings; a blocklist of phrasings closes the
# phrasings someone thought of.
#
# So LANDING IS NOW EARNED, NOT ASSUMED. Extraction and proof are two different questions:
#   * these anchors decide WHETHER A HEX TOKEN IS A COMMIT CLAIM (must exist on origin);
#   * `LANDING_PROMOTIONS` / `LANDING_BINDINGS` below decide WHETHER IT PROVES ANYTHING,
#     and nothing else can. A new extraction anchor added tomorrow inherits REFERENCE and
#     therefore cannot silently clear a missing branch -- which is the property T527's
#     table did not have and is the whole point of the inversion.
#   LANDING   -- the note claims this commit IS this task's work. Only a LANDING commit
#                may prove the merged-and-pruned exemption.
#   REFERENCE -- the note names the commit for orientation (a base, a merge base, another
#                task's landing, a divergence point). It must still exist -- a note citing
#                a vanished commit is still a broken record -- but it proves NOTHING.
# The first build of this tool treated every anchored sha as proof, and T508's note --
# "landed 1abd3a11 on softhouse/T508-... (Driver-verified scope, merge-base 10baca08)" --
# CLEARED ITS OWN MISSING BRANCH, because 10baca08 is the BASE the branch grew from and is
# of course an ancestor of main. A merge base is the one commit guaranteed to be on main
# whether or not a single line of the work ever landed. That is the exact shape of the
# defect this tool exists to catch, reproduced inside the tool.
CLAIM_ANCHORS = [
    # "landed 1abd3a11 on softhouse/T508-..."   (all five incident notes)
    re.compile(r"\blanded\s+(?P<sha>" + HEX + r")\b", re.I),
    # "Merged as 6f29dd39 + be8f593d"  /  "MERGED at ..."  /  "merge commit X"
    re.compile(r"\bmerged?\s+(?:as|at|commit)\s+(?P<sha>" + HEX + r")\b", re.I),
    # "merge base 10baca08" / "merge-base 1762794b" -- the BASE, never the work
    re.compile(r"\bmerge[ -]base\s+(?P<sha>" + HEX + r")\b", re.I),
    # "BASE ON softhouse/T510-... (5c4233fc)" written as "based on X" -- also the base
    re.compile(r"\bbased?\s+on\s+(?P<sha>" + HEX + r")\b", re.I),
    # "commit 4394e141" / "at commit X" / "merge-base commit X"
    re.compile(r"\bcommit\s+(?P<sha>" + HEX + r")\b", re.I),
    # "tip 61185eed"
    re.compile(r"\btip\s+(?:is\s+)?(?P<sha>" + HEX + r")\b", re.I),
    # "COMPLETE @ a0139c5d" -- and also "branched from main @ X", which is why the bare
    # `@` form extracts but does not promote (see LANDING_PROMOTIONS).
    re.compile(r"@\s*(?P<sha>" + HEX + r")\b"),
    # "softhouse/T510-savings-fold-reversal (5c4233fc)" -- a branch, then its tip
    re.compile(r"softhouse/[A-Za-z0-9._/+-]+\s*\(\s*(?P<sha>" + HEX + r")\s*\)"),
    # T528 F-4. Three genuine unpushed-branch claims were sitting in the NOT-CHECKED
    # bucket because no anchor knew these two phrasings:
    #   T335 "branch softhouse/T335-... has 3 commit(s) ahead of main, head d09585f58"
    #   T312 "T297 hiding c1a3888a (4 commits) and T305 hiding 060f00330 (8)"
    # Both are claims about work on a branch that is not on origin, i.e. exactly what this
    # tool exists to find. They extract as REFERENCE: `head X`/`hiding X` describes a
    # branch tip that is by construction NOT on main.
    re.compile(r"\bhead\s+(?:is\s+)?(?P<sha>" + HEX + r")\b", re.I),
    re.compile(r"\bhiding\s+(?P<sha>" + HEX + r")\b", re.I),
]

# REGION ANCHOR. If a clause opens a stack/base description, every hex token inside it to
# the end of the sentence is a commit claim. This is what catches `5c4233fc` -- T510's
# tip, named only inside T515's note as "stack 78a17873/2e1a09df (T501) -> 5c4233fc
# (T510) -> 84dc208e", and one of the five the driver measured absent.
# T536/D2: a `stack ...` clause is a DEPENDENCY CHAIN OF OTHER TASKS' COMMITS. By
# construction it is a base description, so it extracts and never promotes.
CLAIM_REGIONS = [
    re.compile(r"\bstack\b[^.\n]{0,240}", re.I),
]

# ------------------------------------------------------- LANDING, WHICH MUST BE EARNED
#
# T536/F-1. The ONLY four unbound phrasings that promote a claimed sha to LANDING. Each
# one asserts, in the task's own voice, that this commit IS the work. Measured against
# the real record: these four carry 66 of the 73 legitimate merged-and-pruned waivers
# (`--measure-waivers` reproduces the count), and the pipeline's own merge vocabulary
# `MERGED at <sha> by fire ...` is the second of them.
LANDING_PROMOTIONS = [
    re.compile(r"\blanded\s+(?P<sha>" + HEX + r")\b", re.I),
    re.compile(r"\bmerged?\s+(?:as|at|commit)\s+(?P<sha>" + HEX + r")\b", re.I),
    re.compile(r"\btip\s+(?:is\s+)?(?P<sha>" + HEX + r")\b", re.I),
    # A bare "@ X" is a base citation as often as a landing ("branched from main @ X"),
    # so the verb has to be there. T528 case C. The verb list is this pipeline's own
    # vocabulary for "my work is at this commit", measured from the notes:
    # "COMPLETE @ 1f90ee76", "APPROVED WITH CONDITIONS @ 026954a4", "MERGED at ...".
    re.compile(r"\b(?:COMPLETE|COMPLETED|DONE|MERGED|LANDED|DELIVERED|APPROVED)\b"
               r"[^.\n@]{0,32}@\s*(?P<sha>" + HEX + r")\b", re.I),
]

# BOUND landings: the phrase names the sha AND the branch it landed on, so it proves that
# ONE branch (T528 F-2) and nothing else. `<branch> (<sha>)` is included here rather than
# in LANDING_PROMOTIONS because "based on softhouse/TP-pushed (X)" is a BASE citation
# wearing the same shape -- binding it to TP-pushed makes it harmless without a special
# case (T528 case E).
LANDING_BINDINGS = [
    # "landed 709e51c3 on softhouse/T516-t514-conditions"
    re.compile(r"\b(?:landed|merged?\s+(?:as|at|commit))\s+(?P<sha>" + HEX +
               r")\s+(?:on|onto|to|into)\s+(?P<br>softhouse/[A-Za-z0-9._+-]+)", re.I),
    # "softhouse/T510-savings-fold-reversal (5c4233fc)"
    re.compile(r"(?P<br>softhouse/[A-Za-z0-9._+-]+)\s*\(\s*(?P<sha>" + HEX + r")\s*\)"),
]

# ------------------------------------------------------------- THE DOMINANT VETOES
#
# T536/V. A sha whose immediate left context carries a BASE-CITATION word is REFERENCE
# no matter which promotion caught it. "Dominant" means it wins over the promotion: this
# is what makes the classifier a whitelist with a veto rather than a race between
# patterns. `[^.\n]{0,40}$` keeps the window inside one clause -- a sentence boundary
# ends the citation.
BASE_WORDS = re.compile(
    r"\b(merge[ -]base|based?\s+on|branch(?:ed)?\s+from|fork(?:ed)?|diverge[sd]?|"
    r"rebased?\s+onto|cherry-?picked|ahead\s+of|behind|hiding|head|supersed(?:es|ed)|"
    r"cut\s+from|stacked?\s+on|on\s+top\s+of)\b", re.I)

# T536/V2. A sha with a DIFFERENT task's id beside it is that task's commit, not this
# one's. T528 found both directions in the wild, so both are checked:
#   leading  -- "reviewed T400 which landed X"      (case G)
#   trailing -- "supersedes the work merged as X by T400"  (case L, which T528's own
#               sizing left open and condition 1 asks to close)
# Occurrences of a branch THIS TASK CLAIMS are masked out first, because
# `softhouse/T476-t472-repair` is this task's own branch name and the ids inside it are
# not another task speaking.
#
# The TRAILING arm is narrower than the leading one, and deliberately: a task id that
# merely FOLLOWS a sha is usually a co-actor, not an owner. On the real record
# "MERGED at 01a7a05a with T382" is T374's own merge commit landed alongside T382, and a
# bare trailing arm costs that waiver for nothing. Only an ATTRIBUTION preposition
# transfers ownership, which is exactly the shape of case L ("merged as X by T400").
OTHER_TASK_BEFORE = re.compile(r"\b(?P<tid>T\d+[a-z]?|A2-\d+)\b")
OTHER_TASK_AFTER = re.compile(
    r"^[\s,;:)\-]*(?:by|for|from|belonging\s+to|owned\s+by)\s+"
    r"(?P<tid>T\d+[a-z]?|A2-\d+)\b", re.I)

# The gap between a veto word and the sha it is supposed to be talking about. If ANOTHER
# hex token sits in that gap, the veto word is describing THAT sha, not this one --
# "6 commits on top of T466 11afb281, tip a6bf50a3" is T477's own tip, and a window that
# reaches over `11afb281` to reach `a6bf50a3` costs a legitimate waiver for nothing.
VETO_WINDOW = 40


def _veto_gap(before, end_of_word):
    """The text between a matched veto word and the sha, or None when the word is out of
    range, on the far side of a sentence boundary, or already spoken for by another sha."""
    gap = before[end_of_word:]
    if len(gap) > VETO_WINDOW or "." in gap or "\n" in gap:
        return None
    if HEX_TOKEN.search(gap):
        return None
    return gap

# Contexts that mean "this hex is NOT a commit in THIS repository". Matched against the
# ~60 characters preceding the token. A token vetoed here is reported as UNCLASSIFIED-HEX
# with the reason, never silently dropped.
#
#   digest/tree/store/manifest -- sha256 digests and tree hashes. T84 "canonical sha256
#     01b41d9c", T176 "sha256 fecea4b2", T487 "ATTESTED IDENTICAL to the graded tree,
#     265f9192...", T228 "store 8968c559". None of these is a commit.
#   fineract/pinned/upstream -- THE PINNED FINERACT CHECKOUT IS A DIFFERENT REPOSITORY.
#     T1 "Fineract commit 426a23544 (== pinned ...)" and T526 "pinned /home/user/fineract
#     @ 426a23544" are correct records of an upstream commit this repo has never held.
#     Refusing on them would be the tool asserting that Fineract's history belongs on
#     Gerege's origin, which is false.
DIGEST_CONTEXT = re.compile(
    r"(sha256|digest|attested|tree|subtree|store|manifest|canonical|bytes|hash"
    r"|fineract|pinned|upstream)"
    r"[^.\n]{0,60}$", re.I)


class Refuse(Exception):
    """Raised for the exit-3 arm. Carries the distinct banner text."""

    def __init__(self, reason, detail=""):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


# --------------------------------------------------------------------------- git


class Git(object):
    def __init__(self, repo, timeout=90):
        self.repo = repo
        self.timeout = timeout

    def run(self, *args, **kw):
        """Return (rc, stdout, stderr). A timeout or a missing git is rc None -- the
        program DID NOT ANSWER, which is never the same as answering 'no'."""
        try:
            p = subprocess.run(("git",) + args, cwd=self.repo, capture_output=True,
                               text=True, timeout=kw.get("timeout", self.timeout))
        except subprocess.TimeoutExpired:
            return None, "", "timed out after %ss" % kw.get("timeout", self.timeout)
        except OSError as e:
            return None, "", str(e)
        return p.returncode, p.stdout, p.stderr

    def out(self, *args, **kw):
        rc, so, se = self.run(*args, **kw)
        return so if rc == 0 else ""


def establish_origin(g, announce=None):
    """Make the question ANSWERABLE, or raise Refuse (exit 3). Never returns a partial
    answer, because a partial answer here reads as a pass.

    `announce` is called with one line per WRITE this function performs. T528 F-10: this
    is a report that silently mutates the object store -- it runs `git fetch --unshallow`
    and `git fetch +refs/heads/*:refs/remotes/origin/*` -- and a reader was never told.
    The writes are still the right call (ancestry is undecidable across a graft boundary,
    and refusing would halt the program on every CI clone), but a side effect nobody is
    told about is the same species of defect this tool exists to catch.

    Returns (branch_tips, reachable_commits, main_sha).
    """
    say = announce or (lambda _s: None)
    rc, so, se = g.run("rev-parse", "--git-dir")
    if rc != 0:
        raise Refuse("NOT A GIT REPOSITORY", "%s: %s" % (g.repo, se.strip()))

    rc, so, se = g.run("ls-remote", "--heads", "origin")
    if rc is None:
        raise Refuse("ORIGIN DID NOT ANSWER", "git ls-remote --heads origin: %s" % se.strip())
    if rc != 0:
        raise Refuse("ORIGIN UNREACHABLE",
                     "git ls-remote --heads origin exited %d: %s" % (rc, se.strip()))
    tips = {}
    for line in so.splitlines():
        if "\t" not in line:
            continue
        sha, ref = line.split("\t", 1)
        if ref.startswith("refs/heads/"):
            tips[ref[len("refs/heads/"):]] = sha.strip()
    if not tips:
        # An origin with zero branches is indistinguishable, from here, from an origin
        # that answered with a shrug. Refuse rather than declare every claim unbacked.
        raise Refuse("ORIGIN LISTED NO BRANCHES",
                     "ls-remote succeeded and returned no refs/heads/*; refusing to "
                     "treat that as 'origin has nothing', which would condemn every "
                     "claim in the record")

    # A SHALLOW clone cannot answer ancestry for anything older than its boundary, so
    # every historical claim would read as unbacked and the five real ones would be
    # invisible in the noise. This repo WAS shallow (4 grafts, 153 commits on main;
    # `git fetch --unshallow` took 1.6s and yielded 2944). Deepen, or refuse.
    if g.out("rev-parse", "--is-shallow-repository").strip() == "true":
        say("WROTE: repository was SHALLOW; ran `git fetch --unshallow origin` so that "
            "ancestry against origin/main is decidable at all.")
        rc, so, se = g.run("fetch", "--unshallow", "--quiet", "origin")
        if rc != 0 or g.out("rev-parse", "--is-shallow-repository").strip() == "true":
            raise Refuse("REPOSITORY IS SHALLOW AND COULD NOT BE DEEPENED",
                         "ancestry against origin/main is not decidable here; "
                         "`git fetch --unshallow origin` said: %s" % (se.strip() or "(nothing)"))

    # Bring the object store level with origin. Additive: it writes refs/remotes/origin/*
    # and fetches objects. It does NOT prune, because nothing below reads a
    # remote-tracking ref -- origin's ref set comes from `ls-remote` above, so a stale
    # refs/remotes entry cannot widen the reachable set.
    say("WROTE: `git fetch origin +refs/heads/*:refs/remotes/origin/*` -- additive, no "
        "--prune. This report brings the object store level with origin before it reads "
        "it; without that, every claim would look unbacked.")
    rc, so, se = g.run("fetch", "--quiet", "origin",
                       "+refs/heads/*:refs/remotes/origin/*")
    if rc != 0:
        raise Refuse("COULD NOT FETCH FROM ORIGIN",
                     "git fetch exited %s: %s" % (rc, se.strip()))

    missing = [b for b, sha in tips.items()
               if g.out("cat-file", "-t", sha).strip() != "commit"]
    if missing:
        raise Refuse("ORIGIN'S OWN TIPS ARE NOT IN THE OBJECT STORE",
                     "fetch reported success but %d origin tip(s) are still absent "
                     "locally, e.g. %s -- the reachability set below would be a lie"
                     % (len(missing), ", ".join(sorted(missing)[:3])))

    if "main" not in tips:
        raise Refuse("ORIGIN HAS NO main BRANCH",
                     "the merged-and-pruned exemption is proved against origin/main and "
                     "there is no origin/main to prove it against")

    # Everything origin can see, computed from origin's OWN tips rather than from
    # remote-tracking refs.
    rc, so, se = g.run("rev-list", *sorted(set(tips.values())))
    if rc != 0:
        raise Refuse("COULD NOT ENUMERATE ORIGIN'S HISTORY",
                     "git rev-list over %d origin tips exited %s: %s"
                     % (len(set(tips.values())), rc, se.strip()))
    reachable = set(so.split())
    return tips, reachable, tips["main"]


# --------------------------------------------------------------- claim extraction


def _note_text(t):
    n = t.get("note")
    if isinstance(n, list):
        return "\n".join(str(x) for x in n)
    return n if isinstance(n, str) else ""


def _clean_branch(b):
    b = b.rstrip(BRANCH_TRIM)
    return None if NOT_A_BRANCH.search(b) else b


def _mask(text, spans):
    """Blank out `spans` in `text`, keeping every other offset identical. Used to hide
    this task's OWN branch names from the different-task veto: the `T476` inside
    `softhouse/T476-t472-repair` is this task's own name, not another task speaking."""
    if not spans:
        return text
    buf = list(text)
    for lo, hi in spans:
        for i in range(max(0, lo), min(len(buf), hi)):
            buf[i] = "\x00"
    return "".join(buf)


def _base_cited(masked, at):
    """T536/V. Is the sha at `at` preceded, within one clause and with no other sha in
    between, by a base-citation word? Dominant over every promotion."""
    before = masked[max(0, at - 100):at]
    for m in BASE_WORDS.finditer(before):
        if _veto_gap(before, m.end()) is not None:
            return m.group(1)
    return None


def _other_task_beside(masked, at, end, tid):
    """T536/V2. Return the id of a DIFFERENT task named immediately before or after the
    sha at [at, end), or None. Both directions, because T528 found both in the wild."""
    before = masked[max(0, at - 100):at]
    for m in OTHER_TASK_BEFORE.finditer(before):
        if m.group("tid") == tid:
            continue
        if _veto_gap(before, m.end()) is not None:
            return m.group("tid")
    m = OTHER_TASK_AFTER.search(masked[end:end + 60])
    if m and m.group("tid") != tid:
        return m.group("tid")
    return None


def extract_claims(task):
    """Return (branches, commits, unclassified_hex, landing).

    `branches` and `commits` are dicts {value: [where, ...]} so the report can say which
    field or which phrase made the claim. `unclassified_hex` is every hex token in the
    note that no anchor captured -- printed, never silently dropped.

    `landing` is T536's replacement for T527's per-anchor role, and it is the whole of
    F-1 and F-2:
        landing["task_wide"] -- {sha: why}. Shas the task claims, in its own voice, as
            ITS OWN landed work, with no branch attached. These may prove only a branch
            the task names in a `branch`/`branch_mac`/`branch_cloud` FIELD.
        landing["bound"]     -- {branch: {sha: why}}. A phrase that named the sha AND the
            branch together. This proves THAT BRANCH and no other (T528 F-2: on `main`
            today T476's landing sha waives T467's branch and T477's waives T466's,
            because T527 scoped the proof to the task instead of to the branch).
    Everything not in `landing` is REFERENCE, which is now the default rather than the
    exception.
    """
    branches, commits = {}, {}

    for f in BRANCH_FIELDS:
        v = task.get(f)
        if isinstance(v, str) and v.strip():
            # Some records spell a branch field as prose ("softhouse/X (deleted after
            # merge)"), so run the branch pattern over the field too rather than trusting
            # the whole string to be a ref name.
            found = BRANCH_RE.findall(v)
            for b in (found or [v.strip()]):
                name = _clean_branch(b)
                if name:
                    branches.setdefault(name, []).append("field %s" % f)

    landing = {"task_wide": {}, "bound": {}}
    tid = str(task.get("id") or "")

    for f in COMMIT_FIELDS:
        v = task.get(f)
        if isinstance(v, str) and v.strip():
            m = HEX_TOKEN.search(v.strip())
            if m:
                commits.setdefault(m.group(1), []).append(("field %s" % f, "LANDING"))
                # An explicit `tip` / `merged_commit` FIELD is the task speaking about
                # itself in a structured slot; there is no phrasing to paraphrase, so it
                # earns LANDING outright.
                landing["task_wide"].setdefault(m.group(1), "field %s" % f)

    note = _note_text(task)
    own_branch_spans = []
    for m in BRANCH_RE.finditer(note):
        name = _clean_branch(m.group(0))
        if name:
            branches.setdefault(name, []).append("note")
            own_branch_spans.append((m.start(), m.start() + len(name)))
    # Also mask the branch NAMES that came from fields, wherever they occur in the note.
    for name in list(branches):
        for m in re.finditer(re.escape(name), note):
            own_branch_spans.append(m.span())
    masked = _mask(note, own_branch_spans)

    field_branches = {b for b, w in branches.items()
                      if any(x.startswith("field ") for x in w)}

    claimed_spans, vetoed = set(), {}

    def offer(sha, span):
        """A hex token an anchor captured. Two vetoes apply even to anchored tokens,
        because an anchor is a phrase and a phrase can span a clause that carries
        something else entirely. NOTE: this only records that the sha is CLAIMED (and so
        must exist on origin). It says nothing about landing -- see `promote`."""
        if sha.isdigit():
            # `20260829` is a valid hex string AND this program's fire-id / date format.
            # The `stack ...` region anchor swallowed "fire 20260829-080002" on T466/T467
            # and reported the DATE as a lost commit. A real all-digit short sha is
            # possible (about 2% of 8-char oids) and would be missed here; that is the
            # cheaper error, and it is reported below rather than hidden.
            vetoed[span] = (sha, "all-digit: indistinguishable from a fire id or a date")
            return
        before = note[max(0, span[0] - 60):span[0]]
        if DIGEST_CONTEXT.search(before):
            vetoed[span] = (sha, "digest / foreign-repo context")
            return
        commits.setdefault(sha, []).append(("note: %r" % _snippet(note, span[0]),
                                            "REFERENCE"))
        claimed_spans.add(span)

    def promote(sha, span, branch=None):
        """T536. The ONLY route from REFERENCE to LANDING. Every veto is DOMINANT: it
        wins over the promotion pattern, so a base citation cannot be re-phrased into a
        proof."""
        if span not in claimed_spans:      # all-digit / digest -- never a claim at all
            return
        at, end = span
        why = None
        base = _base_cited(masked, at)
        if base:
            why = "V: base-citation word %r beside it" % base
        else:
            other = _other_task_beside(masked, at, end, tid)
            if other:
                why = "V2: names %s, a different task" % other
        if why:
            for i, (where, _role) in enumerate(commits.get(sha, [])):
                if where == ("note: %r" % _snippet(note, at)):
                    commits[sha][i] = (where, "REFERENCE")
            return
        w = "note: %r" % _snippet(note, at)
        for i, (where, _role) in enumerate(commits.get(sha, [])):
            if where == w:
                commits[sha][i] = (where, "LANDING")
        if branch:
            landing["bound"].setdefault(branch, {}).setdefault(sha, w)
            # A bound landing feeds the task-wide set ONLY when the branch it names is
            # one of the task's own branch FIELDS. That is what stops "based on
            # softhouse/TP-pushed (X)" -- another task's branch and its tip -- from
            # clearing this task's own missing branch (T528 case E).
            if branch in field_branches:
                landing["task_wide"].setdefault(sha, w)
        else:
            landing["task_wide"].setdefault(sha, w)

    for rx in CLAIM_ANCHORS:
        for m in rx.finditer(note):
            offer(m.group("sha"), m.span("sha"))
    for rx in CLAIM_REGIONS:
        for region in rx.finditer(note):
            for m in HEX_TOKEN.finditer(region.group(0)):
                offer(m.group(1),
                      (region.start() + m.start(1), region.start() + m.end(1)))

    # Promotion runs AFTER every extraction, so a sha is a claim first and a proof second.
    # BINDINGS FIRST, and a bound span is then EXCLUDED from the unbound pass: "landed X
    # on <branch>" must prove <branch> and not the task at large, or F-2 reopens through
    # the very phrase that names the branch.
    bound_spans = set()
    for rx in LANDING_BINDINGS:
        for m in rx.finditer(note):
            br = _clean_branch(m.group("br"))
            if br:
                bound_spans.add(m.span("sha"))
                promote(m.group("sha"), m.span("sha"), branch=br)
    for rx in LANDING_PROMOTIONS:
        for m in rx.finditer(note):
            if m.span("sha") in bound_spans:
                continue
            promote(m.group("sha"), m.span("sha"))

    unclassified = []
    for m in HEX_TOKEN.finditer(note):
        if m.span(1) in claimed_spans:
            continue
        if m.span(1) in vetoed:
            unclassified.append((m.group(1), vetoed[m.span(1)][1]))
            continue
        before = note[max(0, m.start(1) - 60):m.start(1)]
        if m.group(1).isdigit():
            kind = "all-digit: indistinguishable from a fire id or a date"
        elif DIGEST_CONTEXT.search(before):
            kind = "digest / foreign-repo context"
        else:
            kind = "no claim anchor matched"
        unclassified.append((m.group(1), kind))
    return branches, commits, unclassified, landing


def _snippet(text, at, width=52):
    lo = max(0, at - 24)
    return text[lo:lo + width].replace("\n", " ")


def load_records(repo):
    """Every task in tasks.json AND in every runs/*.tasks.json archive. Returns a list of
    (source, task). Archives are included because a claim does not stop being a claim when
    the run that made it is filed away -- and the archive is where 153 of the 467
    terminal-status records live."""
    out, sources = [], []
    cur = os.path.join(repo, ".softhouse", "tasks.json")
    if os.path.exists(cur):
        sources.append(cur)
    sources += sorted(glob.glob(os.path.join(repo, ".softhouse", "runs", "*.tasks.json")))
    if not sources:
        raise Refuse("NO TASK RECORDS FOUND",
                     "looked for %s and %s" % (cur,
                                               os.path.join(repo, ".softhouse", "runs",
                                                            "*.tasks.json")))
    for p in sources:
        try:
            with open(p) as fh:
                d = json.load(fh)
        except (ValueError, OSError) as e:
            # An unreadable record is not an empty record. Refusing here is the same
            # fail-closed rule as the origin arm: a file this tool cannot parse is a file
            # whose claims it cannot check.
            raise Refuse("UNREADABLE TASK RECORD", "%s: %s" % (p, e))
        tasks = d.get("tasks") if isinstance(d, dict) else d
        if not isinstance(tasks, list):
            raise Refuse("TASK RECORD HAS NO tasks LIST", p)
        for t in tasks:
            if isinstance(t, dict):
                out.append((os.path.relpath(p, repo), t))
    return out


# ------------------------------------------------------------------------- check


def check(repo, baseline_path, timeout=90):
    g = Git(repo, timeout=timeout)
    writes = []
    tips, reachable, main_sha = establish_origin(g, announce=writes.append)
    records = load_records(repo)

    baseline = load_baseline(baseline_path)
    frozen_above, frozen_src = load_frozen_above(baseline_path)

    findings = []          # (severity, kind, task, source, subject, detail)
    waived = []
    ok_counts = {"branch-on-origin": 0, "branch-pruned-proved": 0, "commit-reachable": 0}
    unclassified = []
    checked_tasks = 0

    # Resolve a claimed sha once: full oid if git knows it, else None.
    resolved_cache = {}

    def resolve(sha):
        if sha not in resolved_cache:
            rc, so, se = g.run("rev-parse", "--verify", "--quiet", sha + "^{commit}")
            resolved_cache[sha] = so.strip() if rc == 0 and so.strip() else None
        return resolved_cache[sha]

    for source, t in records:
        if t.get("status") not in CHECKED_STATUSES:
            continue
        checked_tasks += 1
        tid = str(t.get("id") or "<no id>")
        branches, commits, unclass, landing = extract_claims(t)
        for sha, kind in unclass:
            unclassified.append((tid, sha, kind))

        # --- commit arm. THE BASELINE APPLIES TO THIS ARM TOO -- see the loop below the
        # task loop, which waives against `baseline` "to both arms alike", and
        # `baseline.json`, which carries 9 UNBACKED-COMMIT entries (T122, T329, T351 x2,
        # T369, T370, T472, T473, T474). T527 shipped a comment here saying the opposite
        # ("Never baselined"); T528 F-6 caught it. In a guard whose thesis is "the record
        # asserted something the tree does not support", a comment asserting something
        # the code does not do is the same defect one level in.
        proved_task_wide = []                 # LANDING shas, no branch attached
        proved_bound = {}                     # branch -> proving sha (T536/F-2)
        for sha in sorted(commits):
            where = commits[sha][0][0]
            full = resolve(sha)
            if full is None:
                findings.append(("REFUSE", "UNBACKED-COMMIT", tid, source, sha,
                                 "claimed at %s -- resolves to no commit in this "
                                 "repository, and the object store is level with origin"
                                 % where))
                continue
            if full not in reachable:
                findings.append(("REFUSE", "LOCAL-ONLY-COMMIT", tid, source, sha,
                                 "claimed at %s -- exists locally as %s but is reachable "
                                 "from NO origin ref" % (where, full[:12])))
                continue
            ok_counts["commit-reachable"] += 1

        def on_main(sha):
            full = resolve(sha)
            if full is None or full not in reachable:
                return False
            rc, _, _ = g.run("merge-base", "--is-ancestor", full, main_sha)
            return rc == 0

        for sha in sorted(landing["task_wide"]):
            # A REFERENCE commit (a merge base, a base-of, another task's landing) is on
            # main by construction. Letting it prove anything would clear every branch
            # whose note records its own starting point -- which is most of them. Only
            # what `extract_claims` PROMOTED to LANDING gets this far.
            if on_main(sha):
                proved_task_wide.append(sha)
        for br, shas in landing["bound"].items():
            for sha in sorted(shas):
                if on_main(sha):
                    proved_bound[br] = sha
                    break

        # --- branch arm.
        # T536/F-2. THE PROOF IS SCOPED TO THE BRANCH, NOT TO THE TASK. T527 collected
        # `proved_on_main` across the whole task and then applied it to EVERY branch the
        # task named, so on `main` today T476's landing sha waives T467's branch and
        # T477's waives T466's -- another task's work cleared by this task's commit. A
        # landing sha now waives (a) the branch a phrase binds it to, or (b) a branch the
        # task names in its own `branch`/`branch_mac`/`branch_cloud` FIELD.
        field_branches = {b for b, w in branches.items()
                          if any(x.startswith("field ") for x in w)}
        for b in sorted(branches):
            if b in tips:
                ok_counts["branch-on-origin"] += 1
                continue
            # THE ONLY BENIGN EXEMPTION, and it is proved by git topology, not by a note.
            # `git merge-base --is-ancestor <sha> origin/main` on a commit THIS SAME TASK
            # claims AS ITS OWN LANDED WORK. Every one of the five incident notes says
            # the work landed; not one of them can produce a sha that satisfies this.
            if b in proved_bound:
                ok_counts["branch-pruned-proved"] += 1
                waived.append(("PRUNED-PROVED", tid, b,
                               "branch absent from origin, but %s -- which the note binds"
                               " to THIS branch -- is an ancestor of origin/main (%s)"
                               % (proved_bound[b], main_sha[:12])))
                continue
            if b in field_branches and proved_task_wide:
                ok_counts["branch-pruned-proved"] += 1
                waived.append(("PRUNED-PROVED", tid, b,
                               "branch absent from origin, but it is this task's own "
                               "branch field and %s is an ancestor of origin/main (%s)"
                               % (proved_task_wide[0], main_sha[:12])))
                continue
            why = ("claimed at %s -- absent from `git ls-remote --heads origin`, and no "
                   "LANDING commit this task claims for THIS BRANCH is an ancestor of "
                   "origin/main" % branches[b][0])
            if proved_task_wide and b not in field_branches:
                why += ("; this task's landing sha %s proves only the branch(es) it names"
                        " in a branch field, not this one (T536/F-2)"
                        % proved_task_wide[0])
            findings.append(("REFUSE", "UNBACKED-BRANCH", tid, source, b, why))

    # Apply the baseline LAST and to both arms alike, so that everything it waives has
    # first been produced as a finding and can be printed as a waiver. See
    # `write_baseline` for why an exact-subject baseline cannot launder a future
    # incident, and for the five tasks it is forbidden to contain.
    kept = []
    for f in findings:
        key = "%s\t%s" % (f[2], f[4])
        if key in baseline:
            waived.append(("BASELINE", f[2], f[4], "%s -- %s" % (f[1], baseline[key])))
        else:
            kept.append(f)
    findings = kept

    stale = sorted(set(baseline) - {"%s\t%s" % (w[1], w[2]) for w in waived
                                    if w[0] == "BASELINE"})
    return {
        "repo": repo,
        "origin_branches": len(tips),
        "origin_main": main_sha,
        "checked_tasks": checked_tasks,
        "findings": findings,
        "waived": waived,
        "stale_baseline": stale,
        "ok_counts": ok_counts,
        "unclassified": unclassified,
        "writes": writes,
        "frozen_above": frozen_above,
        "frozen_above_source": frozen_src,
    }


# ---------------------------------------------------------------------- baseline


DEFAULT_BASELINE = os.path.join(".softhouse", "capture", "t527-branch-published",
                                "baseline.json")


def load_baseline(path):
    if not path or not os.path.exists(path):
        return {}
    with open(path) as fh:
        d = json.load(fh)
    return {e["key"]: e.get("why", "") for e in d.get("waived", [])}


def load_frozen_above(path):
    """T536/F-3. The GENERATION at or below which a claim may be baselined at all.

    Read from the committed `baseline.json` when it carries one, else the module
    constant. DELETING THE BASELINE FILE THEREFORE DOES NOT RESET THE FREEZE LINE -- it
    falls back to T527, the generation at which this control was introduced. Both sources
    are committed files, so raising the line is a one-line diff a reviewer sees; nothing
    derives it from the data being waived, which is the whole point (a line computed from
    the findings would always sit above them)."""
    src = "module constant"
    val = FROZEN_ABOVE
    if path and os.path.exists(path):
        try:
            with open(path) as fh:
                d = json.load(fh)
            if isinstance(d, dict) and d.get("frozen_above"):
                val, src = str(d["frozen_above"]), os.path.basename(path)
        except (ValueError, OSError):
            pass                      # a malformed baseline is handled by load_baseline
    return val, src


def task_ordinal(tid):
    """A sortable generation for a task id, or None when the id is not a form this
    program has ever used. `None` means REFUSE: an id this tool cannot place in time
    cannot be shown to be historical."""
    if not tid:
        return None
    m = re.fullmatch(r"[Tt](\d+)[a-z]?", tid.strip())
    if m:
        return (1, int(m.group(1)))
    m = re.fullmatch(r"[Aa]2-(\d+)", tid.strip())
    if m:
        return (0, int(m.group(1)))    # the A2-* generation predates every T-id
    return None


# THE 2026-09-04 INCIDENT, BY NAME. `--write-baseline` REFUSES to waive a finding from
# any of these tasks, and `--selftest` asserts the shipped baseline contains none of them.
#
# WHY A BASELINE IS SAFE AT ALL, and this is the load-bearing argument a reviewer should
# attack first: every entry is keyed on `<task-id>\t<exact subject>` -- an exact branch
# name or an exact commit id. Waiving `T474\t409c7693` therefore cannot waive `1abd3a11`,
# or any commit that does not exist yet. A baseline of this shape can only ever forgive
# claims that were already in the file when it was written; it has no wildcard and no
# prefix.
#
# WHAT IT STILL COSTS, said plainly: a LATER regeneration would waive whatever is unbacked
# at that moment, which is how a baseline launders a fresh incident. Two things stand
# against that -- this lock-out list, and the fact that `--write-baseline` prints every
# key it is about to add. Neither is a substitute for a reviewer reading the diff of
# `baseline.json`, and a diff to that file should be read as a claim that work was lost.
INCIDENT_TASKS = ("T508", "T509", "T510", "T512", "T515", "T520", "T522", "T523")
INCIDENT_SHAS = ("1abd3a11", "857dd4d8", "5c4233fc", "8ff5ff15", "84dc208e")

# T536/F-3. THE FREEZE LINE. `INCIDENT_TASKS` / `INCIDENT_SHAS` above are a BLOCKLIST OF
# THE INCIDENT THAT ALREADY HAPPENED, and T528 measured what that protects: nothing else.
# A brand-new task recording a branch and a commit that never reached origin was
# laundered by ONE `--write-baseline` run, which printed "REFUSED TO WAIVE 0 finding(s)"
# while doing it -- an assurance in the run that lost the work.
#
# So the baseline is frozen BY GENERATION as well as by name: `--write-baseline` refuses
# any finding whose task id sorts ABOVE this line, and any id it cannot place in time at
# all. A historical claim has, by definition, a historical id. A future incident is by
# construction above the line and is unwaivable without a human editing this constant or
# `frozen_above` in the committed baseline -- a one-line diff a reviewer will see.
FROZEN_ABOVE = "T527"


def baseline_refusal(tid, subject, frozen_ordinal, frozen_above):
    """Why `--write-baseline` may not waive this finding, or None if it may."""
    # Case-folded: T528 found the name lock-out was case-sensitive, and this repo already
    # carries lowercase ids (`softhouse/t297-review-t295`), so `t508` slipped past it.
    if tid.upper() in tuple(x.upper() for x in INCIDENT_TASKS):
        return "2026-09-04 incident task"
    if subject[:8].lower() in tuple(s.lower() for s in INCIDENT_SHAS):
        return "2026-09-04 incident commit"
    ordinal = task_ordinal(tid)
    if ordinal is None:
        return ("task id %r is not a form this tool can place in time; an id it cannot "
                "date cannot be shown to be historical" % tid)
    if frozen_ordinal is None or ordinal > frozen_ordinal:
        return ("above the freeze line %s -- this is a claim from AFTER the control "
                "existed, so it is a live incident, not history" % frozen_above)
    return None


def write_baseline(repo, path, res, frozen_above, frozen_src):
    entries, refused = [], []
    frozen_ordinal = task_ordinal(frozen_above)
    for sev, kind, tid, source, subject, detail in res["findings"]:
        why_not = baseline_refusal(tid, subject, frozen_ordinal, frozen_above)
        if why_not:
            refused.append((tid, kind, subject, why_not))
            continue
        entries.append({"key": "%s\t%s" % (tid, subject), "task": tid, "kind": kind,
                        "subject": subject, "source": source,
                        "why": "pre-existing when this control was introduced (T527, "
                               "2026-09-04); no proof of landing survives in git"})
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump({
            "generated_by": "T527 .softhouse/bin/check-branch-published.py --write-baseline",
            "generated_at_origin_main": res["origin_main"],
            "note": ("Keys are exact <task-id>\\t<branch-or-commit> pairs, so this file "
                     "can only forgive claims that already existed when it was written. "
                     "Every entry is printed on every run under WAIVED (baseline). "
                     "Removing an entry re-arms the check for that subject. A DIFF TO "
                     "THIS FILE IS A CLAIM THAT WORK WAS LOST -- read it as one."),
            "frozen_above": frozen_above,
            "frozen_above_note": (
                "T536/F-3. --write-baseline REFUSES to waive any finding whose task id "
                "sorts above this generation, or whose id it cannot date. The name "
                "lock-out below protects the incident that already happened; this line "
                "protects the ones that have not. Raising it is a claim that everything "
                "between the old and new line is HISTORY rather than LOST WORK -- read a "
                "diff to this field as that claim. Deleting this file does not lift the "
                "line: the tool falls back to FROZEN_ABOVE in "
                "check-branch-published.py."),
            "refuses_to_waive": {"tasks": list(INCIDENT_TASKS),
                                 "commits": list(INCIDENT_SHAS)},
            "waived": sorted(entries, key=lambda e: e["key"]),
        }, fh, indent=1)
        fh.write("\n")
    return entries, refused


# ------------------------------------------------------------------------ report


BASELINE_SAMPLE = 12          # T528 F-9; --full-baseline lifts it


def render(res, out=sys.stdout, full_baseline=False):
    p = lambda s="": print(s, file=out)
    sample = 10 ** 9 if full_baseline else BASELINE_SAMPLE
    findings = res["findings"]
    p("=" * 78)
    if findings:
        p("check-branch-published: REFUSE -- %d claim(s) origin has never heard of"
          % len(findings))
    else:
        p("check-branch-published: CLEAN")
    p("=" * 78)
    p("origin: %d branches, main=%s | records checked: %d terminal-or-awaiting-review "
      "tasks" % (res["origin_branches"], res["origin_main"][:12], res["checked_tasks"]))
    p("backed: %d branch(es) on origin, %d pruned-but-proved-on-main, %d commit(s) "
      "reachable from an origin ref"
      % (res["ok_counts"]["branch-on-origin"], res["ok_counts"]["branch-pruned-proved"],
         res["ok_counts"]["commit-reachable"]))
    p("baseline freeze line: %s (from %s) -- a claim from a LATER generation cannot be "
      "baselined." % (res.get("frozen_above"), res.get("frozen_above_source")))
    # T528 F-10. This report writes to the object store. Say so, in the report.
    for w in res.get("writes", []):
        p("  %s" % w)
    if findings:
        p()
        p("UNBACKED CLAIMS -- the record asserts work that is not on origin:")
        for sev, kind, tid, source, subject, detail in sorted(findings,
                                                              key=lambda f: (f[1], f[2])):
            p("  %-18s %-9s %s" % (kind, tid, subject))
            p("      %s" % detail)
            p("      recorded in %s" % source)
    waived_baseline = [w for w in res["waived"] if w[0] == "BASELINE"]
    waived_proved = [w for w in res["waived"] if w[0] == "PRUNED-PROVED"]
    p()
    p("WAIVED (merged-and-pruned, PROVED by `git merge-base --is-ancestor <sha> "
      "origin/main`): %d" % len(waived_proved))
    for _, tid, b, why in sorted(waived_proved):
        p("  %-9s %s" % (tid, b))
        p("      %s" % why)
    p()
    p("WAIVED (baseline -- enumerated by exact subject in the committed baseline file, "
      "which cannot")
    p("forgive a subject that did not exist when it was written): %d"
      % len(waived_baseline))
    # T528 F-9. This tool argues that an unreadable report is an unread one, and then
    # printed all 314 baseline waivers on every invocation, pushing the READY list to
    # line 587 of 684. The enumeration still exists -- it lives in the committed
    # baseline file, item by item, which is where a reviewer reads it -- so what belongs
    # here is the count, a sample, and where to look.
    for _, tid, b, why in sorted(waived_baseline)[:sample]:
        p("  %-9s %-52s %s" % (tid, b, why.split(" -- ")[0]))
    if len(waived_baseline) > sample:
        p("  ... %d more. THE FULL LIST IS THE COMMITTED FILE, one line per waiver:"
          % (len(waived_baseline) - sample))
        p("      %s" % DEFAULT_BASELINE)
        p("      Re-run with --full-baseline to print every entry here instead.")
    if res["stale_baseline"]:
        p()
        p("STALE BASELINE ENTRIES -- waived but no longer claimed anywhere (%d). Harmless,"
          % len(res["stale_baseline"]))
        p("but they are dead weight; regenerate with --write-baseline.")
        for k in res["stale_baseline"][:20]:
            p("  %s" % k.replace("\t", "  "))
    unc = res["unclassified"]
    p()
    p("UNCLASSIFIED HEX IN NOTES -- NOT CHECKED (%d occurrence(s), %d distinct)."
      % (len(unc), len({u[1] for u in unc})))
    p("These are hex tokens no claim anchor captured. Most are sha256 digests and tree")
    p("hashes; some belong to the pinned Fineract checkout, a different repository. If a")
    p("real commit claim is sitting in here, the phrasing needs an anchor in CLAIM_ANCHORS.")
    seen = set()
    shown = 0
    for tid, sha, kind in unc:
        if sha in seen:
            continue
        seen.add(sha)
        shown += 1
        if shown > 12:
            break
        p("  %-9s %-42s (%s)" % (tid, sha, kind))
    if len({u[1] for u in unc}) > 12:
        p("  ... %d more distinct; re-run with --json for the full list"
          % (len({u[1] for u in unc}) - 12))
    p()
    if findings:
        p("WHY THIS MATTERS: on 2026-09-04 five tasks -- T508, T509 (the program's")
        p("recorded critical path), T510, T512, T515 -- were recorded terminal on main")
        p("with notes naming commits that exist on one laptop and nowhere else. The tree")
        p("was clean; what was wrong was what the tree ASSERTED about work not in it.")
        p("REPAIR is one of two things, and neither is editing this tool: push the branch")
        p("to origin, or correct the note to say the work is UNRECOVERED.")
    return 2 if findings else 0


# ---------------------------------------------------------------------- selftest


def _sh(cwd, *args, **kw):
    env = dict(os.environ)
    env.setdefault("GIT_AUTHOR_NAME", "t527")
    env.setdefault("GIT_AUTHOR_EMAIL", "t527@example.invalid")
    env.setdefault("GIT_COMMITTER_NAME", "t527")
    env.setdefault("GIT_COMMITTER_EMAIL", "t527@example.invalid")
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)
    if p.returncode != 0 and not kw.get("ok_fail"):
        raise AssertionError("fixture step failed: %s\n%s\n%s"
                             % (" ".join(args), p.stdout, p.stderr))
    return p


def _write_tasks(repo, tasks):
    d = os.path.join(repo, ".softhouse")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "tasks.json"), "w") as fh:
        json.dump({"run_id": "selftest", "tasks": tasks}, fh, indent=1)


def _fixture(base):
    """A bare `origin` plus a work repo, with:
       - main pushed
       - `softhouse/TP-pushed` pushed and still present on origin
       - `softhouse/TM-merged` merged into main and DELETED from origin (sha kept)
       - one local-only commit, never pushed anywhere
    Returns (repo, facts).
    """
    origin = os.path.join(base, "origin.git")
    repo = os.path.join(base, "work")
    _sh(base, "git", "init", "--quiet", "--bare", "-b", "main", origin)
    os.makedirs(repo)
    _sh(repo, "git", "init", "--quiet", "-b", "main")
    _sh(repo, "git", "remote", "add", "origin", origin)
    with open(os.path.join(repo, "README"), "w") as fh:
        fh.write("root\n")
    _sh(repo, "git", "add", "-A")
    _sh(repo, "git", "commit", "--quiet", "-m", "root")
    _sh(repo, "git", "push", "--quiet", "-u", "origin", "main")

    # a branch that stays on origin
    _sh(repo, "git", "checkout", "--quiet", "-b", "softhouse/TP-pushed")
    with open(os.path.join(repo, "p.txt"), "w") as fh:
        fh.write("p\n")
    _sh(repo, "git", "add", "-A")
    _sh(repo, "git", "commit", "--quiet", "-m", "TP work")
    pushed_sha = _sh(repo, "git", "rev-parse", "HEAD").stdout.strip()
    _sh(repo, "git", "push", "--quiet", "origin", "softhouse/TP-pushed")

    # a branch that is merged into main and then deleted from origin
    _sh(repo, "git", "checkout", "--quiet", "main")
    _sh(repo, "git", "checkout", "--quiet", "-b", "softhouse/TM-merged")
    with open(os.path.join(repo, "m.txt"), "w") as fh:
        fh.write("m\n")
    _sh(repo, "git", "add", "-A")
    _sh(repo, "git", "commit", "--quiet", "-m", "TM work")
    merged_sha = _sh(repo, "git", "rev-parse", "HEAD").stdout.strip()
    _sh(repo, "git", "push", "--quiet", "origin", "softhouse/TM-merged")
    _sh(repo, "git", "checkout", "--quiet", "main")
    _sh(repo, "git", "merge", "--quiet", "--no-ff", "-m", "merge TM",
        "softhouse/TM-merged")
    _sh(repo, "git", "push", "--quiet", "origin", "main")
    _sh(repo, "git", "push", "--quiet", "origin", "--delete", "softhouse/TM-merged")
    _sh(repo, "git", "branch", "--quiet", "-D", "softhouse/TM-merged")

    # a commit that exists locally and on no origin ref
    _sh(repo, "git", "checkout", "--quiet", "-b", "softhouse/TL-local")
    with open(os.path.join(repo, "l.txt"), "w") as fh:
        fh.write("l\n")
    _sh(repo, "git", "add", "-A")
    _sh(repo, "git", "commit", "--quiet", "-m", "TL work")
    local_sha = _sh(repo, "git", "rev-parse", "HEAD").stdout.strip()
    _sh(repo, "git", "checkout", "--quiet", "main")
    _sh(repo, "git", "branch", "--quiet", "-D", "softhouse/TL-local")

    main_sha = _sh(repo, "git", "rev-parse", "main").stdout.strip()
    return repo, {"origin": origin, "pushed": pushed_sha[:8], "merged": merged_sha[:8],
                  "local": local_sha[:8], "main": main_sha[:8]}


def _run_check(repo, baseline=None):
    """Run the checker in-process and return (rc, text)."""
    import io
    buf = io.StringIO()
    try:
        res = check(repo, baseline, timeout=60)
    except Refuse as r:
        print("=" * 78, file=buf)
        print("check-branch-published: REFUSE -- CANNOT ESTABLISH ORIGIN", file=buf)
        print("reason: %s" % r.reason, file=buf)
        print(r.detail, file=buf)
        return 3, buf.getvalue()
    rc = render(res, out=buf)
    return rc, buf.getvalue()


def selftest(keep=False):
    """Every RED case is run TWICE: once with its subject, once with the subject REMOVED.
    A control that cannot fail is worse than none (`P-22`), and a control that cannot PASS
    is a control nobody keeps. So each case asserts both directions."""
    cases, failures = [], 0
    base = tempfile.mkdtemp(prefix="t527-selftest-")

    def case(name, want_rc, want_in, tasks, baseline=None, mangle=None):
        nonlocal failures
        d = os.path.join(base, name)
        os.makedirs(d)
        repo, f = _fixture(d)
        _write_tasks(repo, tasks(f) if callable(tasks) else tasks)
        if mangle:
            mangle(repo, f)
        rc, text = _run_check(repo, baseline)
        ok = (rc == want_rc) and all(w in text for w in want_in)
        cases.append((name, ok, rc, want_rc, text))
        if not ok:
            failures += 1
        print("  %-42s %s  (rc=%s want=%s)"
              % (name, "PASS" if ok else "FAIL", rc, want_rc))
        if not ok:
            print("    wanted substrings: %r" % (want_in,))
            print("    ---- output ----")
            for ln in text.splitlines():
                print("    " + ln)
        return text

    T = lambda **kw: dict({"id": "TX", "status": "done"}, **kw)

    print("check-branch-published --selftest")
    print()
    print("GREEN CONTROLS -- the check must be able to PASS:")
    case("G-CLEAN-branch-on-origin", 0, ["CLEAN"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed")])
    case("G-PRUNED-MERGED-proved-ancestor", 0,
         ["CLEAN", "merged-and-pruned, PROVED", "softhouse/TM-merged"],
         lambda f: [T(id="TM", branch="softhouse/TM-merged",
                      note="landed %s on softhouse/TM-merged" % f["merged"])])
    # ANTI-VACUITY FOR THE GREEN ONE. The case above passes only because the sha proves
    # the content is on main -- not because the branch is somehow still visible. Strip the
    # sha and the SAME fixture, with the SAME pruned branch, must go RED. Without this the
    # green case would be indistinguishable from a check that never looked at the branch.
    case("G-PRUNED-anti-vacuity-proof-removed", 2,
         ["UNBACKED-BRANCH", "softhouse/TM-merged"],
         lambda f: [T(id="TM", branch="softhouse/TM-merged",
                      note="merged and the branch was deleted, trust me")])
    case("G-not-terminal-status-is-not-checked", 0, ["CLEAN"],
         lambda f: [dict(id="TZ", status="pending",
                         branch="softhouse/TZ-never-pushed")])

    print()
    print("RED CASES -- each must go RED, and each is re-run with its subject REMOVED")
    print("to prove the RED is caused by the subject and not by the fixture:")

    # 1. claimed branch that does not exist on origin
    case("R1-branch-absent-from-origin", 2,
         ["UNBACKED-BRANCH", "softhouse/TN-never-pushed", "TN"],
         lambda f: [T(id="TN", branch="softhouse/TN-never-pushed")])
    case("R1-control-subject-removed", 0, ["CLEAN"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed")])

    # 2. claimed sha that resolves to nothing -- the incident's exact shape, in a note
    case("R2-sha-does-not-resolve", 2,
         ["UNBACKED-COMMIT", "1abd3a11"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed",
                      note="landed 1abd3a11 on softhouse/TP-pushed")])
    case("R2-control-sha-removed-from-note", 0, ["CLEAN"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed",
                      note="landed on softhouse/TP-pushed")])

    # 2b. the sha lives ONLY in the note, in a stack clause -- 5c4233fc's exact shape
    case("R2b-sha-only-in-a-stack-clause", 2,
         ["UNBACKED-COMMIT", "5c4233fc"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed",
                      note="stack 78a17873/2e1a09df (T501) -> 5c4233fc (T510)")])
    case("R2b-control-stack-clause-removed", 0, ["CLEAN"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed",
                      note="the reversal repair itself is SOUND and was preserved")])

    # 3. sha resolves but is on no origin ref
    case("R3-sha-resolves-but-on-no-origin-ref", 2,
         ["LOCAL-ONLY-COMMIT"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed",
                      note="landed %s on softhouse/TP-pushed" % f["local"])])
    case("R3-control-same-note-with-a-pushed-sha", 0, ["CLEAN"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed",
                      note="landed %s on softhouse/TP-pushed" % f["pushed"])])

    # 4. origin unreachable -- MUST be a distinct verdict, never a pass
    def break_origin(repo, f):
        _sh(repo, "git", "remote", "set-url", "origin",
            os.path.join(os.path.dirname(repo), "no-such-origin.git"))
    case("R4-origin-unreachable-is-exit-3", 3,
         ["CANNOT ESTABLISH ORIGIN"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed")],
         mangle=break_origin)
    case("R4-control-origin-restored", 0, ["CLEAN"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed")])

    # 4b. the fail-closed arm must dominate: an origin-unreachable run over a record that
    # is ALSO full of unbacked claims must still be 3, not 2 and not 0.
    case("R4b-unreachable-dominates-a-dirty-record", 3,
         ["CANNOT ESTABLISH ORIGIN"],
         lambda f: [T(id="TN", branch="softhouse/TN-never-pushed",
                      note="landed 1abd3a11 on softhouse/TN-never-pushed")],
         mangle=break_origin)

    # 5. REGRESSION CONTROL for a defect this tool shipped and then had removed: a
    #    `merge base <sha>` citation used to satisfy the merged-and-pruned exemption, and
    #    T508's own note -- which cites its merge base 10baca08 -- CLEARED ITS OWN MISSING
    #    BRANCH. The base is on main whether or not the work ever landed.
    case("R5-merge-base-does-not-prove-a-branch", 2,
         ["UNBACKED-BRANCH", "softhouse/TN-never-pushed"],
         lambda f: [T(id="TN", branch="softhouse/TN-never-pushed",
                      note="done and scope-checked (merge base %s)" % f["main"])])
    case("R5-control-same-sha-claimed-as-LANDING", 0,
         ["CLEAN", "merged-and-pruned, PROVED"],
         lambda f: [T(id="TN", branch="softhouse/TN-never-pushed",
                      note="landed %s on softhouse/TN-never-pushed" % f["main"])])

    # 5b. T536 / T528 F-1. THE CLASS, NOT THE PHRASING. R5 above is one phrasing of a
    #     base citation; T528 built twelve and SEVEN of them read as proof of landing,
    #     because `LANDING` was the DEFAULT and only two anchors were tagged `REFERENCE`.
    #     One of the seven -- case B -- is T509's own note on `main` one word apart:
    #     rewording `merge base 10baca08` to `merge-base commit 10baca08` moved
    #     `UNBACKED-BRANCH T509` out of the findings and into the waivers, 21 -> 20.
    #     Each case below is the SAME fixture with the SAME genuinely-absent branch and a
    #     sha that IS on origin/main; the note is the only variable. Every one must
    #     REFUSE, and `A5b-GREEN-genuine-landing` is the paired control that must PASS --
    #     without it this block would be satisfied by a checker that refuses everything.
    for nm, note in [
        ("B-merge-base-COMMIT-worded", "done; merge-base commit %s, scope clean"),
        ("C-branched-from-at", "branched from main @ %s; work is on the branch"),
        ("E-base-branch-paren",
         "based on softhouse/TP-pushed (%s) -- stacked on top"),
        ("G-review-cites-another-task",
         "reviewed T400 which landed %s; my own work is on the branch"),
        ("H-diverges-at", "diverges from origin/main at commit %s"),
        ("K-stack-region-base", "stack %s (T400 base) -> my work"),
        ("L-supersedes", "supersedes the work merged as %s by T400"),
    ]:
        case("A5b-" + nm, 2, ["UNBACKED-BRANCH", "softhouse/TN-never-pushed"],
             lambda f, _n=note: [T(id="TN", branch="softhouse/TN-never-pushed",
                                   note=_n % f["main"])])
    case("A5b-GREEN-genuine-landing", 0, ["CLEAN", "merged-and-pruned, PROVED"],
         lambda f: [T(id="TN", branch="softhouse/TN-never-pushed",
                      note="landed %s on softhouse/TN-never-pushed" % f["main"])])
    # The four legitimate phrasings the pipeline actually writes must all still prove.
    # 66 of the 73 real merged-and-pruned waivers hang off these.
    for nm, note in [
        ("MERGED-at-by-fire", "MERGED at %s by fire cloud-20260905-1200."),
        ("COMPLETE-at", "COMPLETE @ %s. VERDICT APPROVED."),
        ("tip", "DONE on the branch, tip %s, scope clean."),
    ]:
        case("A5b-GREEN-" + nm, 0, ["CLEAN", "merged-and-pruned, PROVED"],
             lambda f, _n=note: [T(id="TN", branch="softhouse/TN-never-pushed",
                                   note=_n % f["main"])])

    # 5c. T536 / T528 F-2. THE PROOF IS SCOPED TO THE BRANCH, NOT THE TASK. A task that
    #     names two branches and landed one waived BOTH, so on `main` T476's landing sha
    #     was clearing T467's branch and T477's was clearing T466's.
    case("A5c-two-branches-one-landing-waives-exactly-one", 2,
         ["UNBACKED-BRANCH", "softhouse/TX-someone-elses",
          "merged-and-pruned, PROVED", "softhouse/TN-never-pushed"],
         lambda f: [T(id="TN", branch="softhouse/TN-never-pushed",
                      note="landed %s on softhouse/TN-never-pushed; branched from "
                           "softhouse/TX-someone-elses" % f["main"])])
    case("A5c-control-the-landing-branch-alone-is-CLEAN", 0,
         ["CLEAN", "merged-and-pruned, PROVED"],
         lambda f: [T(id="TN", branch="softhouse/TN-never-pushed",
                      note="landed %s on softhouse/TN-never-pushed" % f["main"])])

    # 6. the digest veto must veto, and must veto because of the digest word.
    case("R6-control-digest-context-is-not-a-claim", 0, ["CLEAN", "digest / foreign-repo"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed",
                      note="byte-identity proven, canonical sha256 1abd3a11 over 3 files")])
    case("R6-anti-vacuity-same-hex-without-the-digest-word", 2,
         ["UNBACKED-COMMIT", "1abd3a11"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed",
                      note="byte-identity proven, landed 1abd3a11 over 3 files")])

    # 7. the `tip` FIELD is read as well as the note.
    case("R7-tip-field-is-read", 2, ["UNBACKED-COMMIT", "deadbe1f"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed", tip="deadbe1f")])
    case("R7-control-tip-field-holds-a-pushed-sha", 0, ["CLEAN"],
         lambda f: [T(id="TP", branch="softhouse/TP-pushed", tip=f["pushed"])])

    # 8. the baseline waives EXACTLY the subject it names and nothing adjacent to it.
    print()
    print("EXEMPTION CONTROLS -- the waivers must waive exactly what they claim to:")
    d = os.path.join(base, "B-baseline")
    os.makedirs(d)
    repo, f = _fixture(d)
    _write_tasks(repo, [T(id="TN", branch="softhouse/TN-never-pushed",
                          note="landed 1abd3a11 on softhouse/TN-never-pushed")])
    blp = os.path.join(repo, "bl.json")
    with open(blp, "w") as fh:
        json.dump({"waived": [{"key": "TN\tsofthouse/TN-never-pushed", "why": "legacy"}]},
                  fh)
    rc, text = _run_check(repo, blp)
    # The branch key is waived; the COMMIT claim on the same task, one key away, is not.
    ok = rc == 2 and "REFUSE -- 1 claim(s)" in text \
        and "UNBACKED-COMMIT" in text and "1abd3a11" in text \
        and "\n  UNBACKED-BRANCH" not in text \
        and "TN        softhouse/TN-never-pushed" in text
    cases.append(("B-baseline-waives-only-the-named-subject", ok, rc, 2, text))
    failures += 0 if ok else 1
    print("  %-42s %s  (rc=%s want=2)"
          % ("B-baseline-waives-only-the-named-subject", "PASS" if ok else "FAIL", rc))
    if not ok:
        for ln in text.splitlines():
            print("    " + ln)

    # 8b. T536 / T528 F-3. THE FREEZE LINE. A finding whose task id sorts ABOVE
    #     `frozen_above` cannot be waived by regenerating the baseline, and a finding
    #     BELOW it still can -- both directions, because a control that refuses
    #     everything is a broken tool, not a frozen one.
    print()
    print("FREEZE-LINE CONTROLS -- --write-baseline must refuse a LIVE incident and")
    print("still accept a HISTORICAL one:")
    for nm, tid, want_waived in [("above-the-line-is-REFUSED", "T791", 0),
                                 ("below-the-line-is-waivable", "T42", 1),
                                 ("undatable-id-is-REFUSED", "rescue-x", 0),
                                 ("case-folded-incident-id-is-REFUSED", "t508", 0)]:
        d = os.path.join(base, "F-" + nm)
        os.makedirs(d)
        repo, f = _fixture(d)
        _write_tasks(repo, [T(id=tid, branch="softhouse/%s-never-pushed" % tid)])
        blp = os.path.join(repo, "fz.json")
        with open(blp, "w") as fh:
            json.dump({"frozen_above": FROZEN_ABOVE, "waived": []}, fh)
        res_f = check(repo, blp, timeout=60)
        fa, fsrc = load_frozen_above(blp)
        ents, refs = write_baseline(repo, blp, res_f, fa, fsrc)
        ok = len(ents) == want_waived and len(refs) == (1 - want_waived)
        cases.append(("F-" + nm, ok, 0, 0, ""))
        failures += 0 if ok else 1
        print("  %-42s %s  (waived %d, refused %d: %s)"
              % ("F-" + nm, "PASS" if ok else "FAIL", len(ents), len(refs),
                 refs[0][3] if refs else "-"))

    # 6. the committed baseline must not contain the five incident tasks
    print()
    print("INCIDENT CONTROL -- the shipped baseline must not waive the defect it was")
    print("generated beside:")
    shipped = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        DEFAULT_BASELINE)
    if os.path.exists(shipped):
        keys = load_baseline(shipped)
        bad = sorted({k.split("\t")[0] for k in keys} & set(INCIDENT_TASKS))
        bad += sorted(k for k in keys if k.split("\t")[-1][:8] in INCIDENT_SHAS)
        ok = not bad
        print("  %-42s %s  (%d entries, incident tasks present: %s)"
              % ("G-BASELINE-EXCLUDES-INCIDENT", "PASS" if ok else "FAIL", len(keys),
                 bad or "none"))
        cases.append(("G-BASELINE-EXCLUDES-INCIDENT", ok, 0, 0, ""))
        failures += 0 if ok else 1
    else:
        print("  %-42s FAIL  (no baseline file at %s)"
              % ("G-BASELINE-EXCLUDES-INCIDENT", shipped))
        failures += 1

    print()
    print("%d case(s), %d failure(s)" % (len(cases), failures))
    if keep:
        print("fixtures kept at %s" % base)
    else:
        shutil.rmtree(base, ignore_errors=True)
    return 0 if failures == 0 else 1


# ---------------------------------------------------------------------------- cli


def cli(argv):
    # <root>/.softhouse/bin/<this> -> the repo root is three dirnames up.
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    baseline = None
    as_json = do_write = do_selftest = keep = full_baseline = False
    timeout = 90
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--json":
            as_json = True
        elif a == "--selftest":
            do_selftest = True
        elif a == "--keep":
            keep = True
        elif a == "--full-baseline":
            # T528 F-9: the enumeration is available, it is just no longer the default.
            full_baseline = True
        elif a == "--write-baseline":
            do_write = True
        elif a in ("--repo", "--baseline", "--timeout"):
            if i + 1 >= len(argv):
                print("usage error: %s needs a value" % a, file=sys.stderr)
                return 64
            i += 1
            if a == "--repo":
                repo = os.path.abspath(argv[i])
            elif a == "--baseline":
                baseline = os.path.abspath(argv[i])
            else:
                try:
                    timeout = float(argv[i])
                except ValueError:
                    print("usage error: --timeout wants seconds, got %r" % argv[i],
                          file=sys.stderr)
                    return 64
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            print("usage error: unknown argument %r" % a, file=sys.stderr)
            return 64
        i += 1

    if do_selftest:
        return selftest(keep=keep)

    if baseline is None:
        baseline = os.path.join(repo, DEFAULT_BASELINE)

    try:
        res = check(repo, baseline, timeout=timeout)
    except Refuse as r:
        # EXIT 3. DISTINCT FROM 2 ON PURPOSE. `P-45`: a guard that passes when it cannot
        # look enforces nothing, and an offline pass here would have scored the 2026-09-04
        # incident GREEN.
        # T528 F-8. In --json mode the banner goes to STDERR and the document to STDOUT,
        # the same way round as every other arm. T527 had them swapped here, so a caller
        # parsing this tool's stdout got prose exactly in the arm it most needs to detect.
        out = sys.stderr if as_json else sys.stdout
        print("=" * 78, file=out)
        print("check-branch-published: REFUSE -- CANNOT ESTABLISH ORIGIN", file=out)
        print("=" * 78, file=out)
        print("reason: %s" % r.reason, file=out)
        if r.detail:
            print("        %s" % r.detail, file=out)
        print(file=out)
        print("THIS IS NOT A PASS. Nothing was checked. The record may be claiming work", file=out)
        print("that origin has never heard of and this run could not tell you either way.", file=out)
        if as_json:
            json.dump({"verdict": "CANNOT_ESTABLISH_ORIGIN", "reason": r.reason,
                       "detail": r.detail}, sys.stdout, indent=1)
            print()
        return 3

    if do_write:
        frozen_above, frozen_src = load_frozen_above(baseline)
        entries, refused = write_baseline(repo, baseline, res, frozen_above, frozen_src)
        print("FREEZE LINE: %s (from %s). A finding whose task id sorts ABOVE this line, "
              % (frozen_above, frozen_src))
        print("or whose id cannot be dated, CANNOT be waived by regenerating this file.")
        print()
        print("wrote %d waiver(s) to %s" % (len(entries), baseline))
        for e in entries:
            print("  WAIVE  %-18s %-9s %s" % (e["kind"], e["task"], e["subject"]))
        print()
        # T528 F-3: T527 printed "REFUSED TO WAIVE 0 finding(s) -- these are the
        # 2026-09-04 incident and no regeneration may launder them" in a run that had
        # just laundered a fresh critical path. Zero refusals is NOT an assurance, so it
        # no longer reads as one.
        print("REFUSED TO WAIVE %d finding(s):" % len(refused))
        for tid, kind, subject, why_not in refused:
            print("  KEEP   %-18s %-9s %-46s %s" % (kind, tid, subject, why_not))
        if not refused:
            print("  (none: every finding in this run is at or below the freeze line %s "
                  "and outside" % frozen_above)
            print("  the named incident. That is a statement about THIS RUN, not an "
                  "assurance that")
            print("  the file is safe -- read the diff to %s as a claim that work was "
                  "lost.)" % os.path.basename(baseline))
        return 0

    if as_json:
        json.dump({
            "verdict": "REFUSE" if res["findings"] else "CLEAN",
            "origin_main": res["origin_main"],
            "checked_tasks": res["checked_tasks"],
            "findings": [{"kind": k, "task": t, "source": s, "subject": subj,
                          "detail": d}
                         for _, k, t, s, subj, d in res["findings"]],
            "waived": [{"kind": w[0], "task": w[1], "branch": w[2], "why": w[3]}
                       for w in res["waived"]],
            "unclassified_hex": [{"task": t, "hex": h, "why": k}
                                 for t, h, k in res["unclassified"]],
            "stale_baseline": res["stale_baseline"],
        }, sys.stdout, indent=1)
        print()
        return 2 if res["findings"] else 0

    return render(res, full_baseline=full_baseline)


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
