#!/usr/bin/env python3
"""T47 edit 1 - §4.1.1 step B: pin the packed rule, replace 'not yet captured'
with the T46 non-separability proof.

HISTORY.  This script performed the ADR edit committed as bf67a85 (19 Aug
2026).  Both of its anchors were themselves rewritten by DEC-1 revisions 11
and 12, so it can no longer apply to the ratified document at all, and its
only remaining legitimate use is REPRODUCING that historical edit on a SCRATCH
COPY of the revision-9 text.

HARDENED BY T167 (21 Aug 2026) - P-22, P-48 rule 4.  As shipped by T47 this
file ended in

    io.open(DOC, "w", encoding="utf-8").write(s)

with DOC hard-wired to docs/adr/DEC-1-schedule-generator-adapter.md - a
RATIFIED DEC-n, which CLAUDE.md makes a hard `user` gate to amend.  There was
no try, no finally, no except, no atexit, no signal handler and no
authorisation of any kind.  `io.open(path, "w")` opens with O_TRUNC, so the
document was EMPTIED before a single byte of replacement text was written, and
any interruption from that instant until the last flush left it truncated or
half-edited.  T156's guard sweep scored this file GUARDED because the word
"trap" appears three times in it - all three inside prose strings this script
WRITES INTO the ADR.  The file was scored safe by the text it was writing.

Three things changed; THE EDIT ITSELF DID NOT.  Every anchor and every
replacement string below is byte-for-byte T47's, and an authorised run is
checked to reproduce bf67a85's ADR blob exactly (AFTER_SHA256).

  1. ATOMIC WRITE.  The new text goes to a temp file created with
     tempfile.mkstemp(dir=<the target's OWN directory>) - the same directory,
     therefore the same filesystem by construction, and additionally asserted
     by comparing st_dev - is fsync'd, and is then moved onto the target with
     os.replace(), which is atomic on POSIX.  The target is never opened for
     writing at all.  No trap is needed and none is used: an interruption
     leaves either the whole old file or the whole new one and never a
     mixture, INCLUDING under SIGKILL, which no handler could have caught.
     The one `finally` below is ordinary temp-file cleanup on the catchable
     paths, not a correctness guard - correctness comes from os.replace.
  2. CONTENT GATE.  The target's sha256 must equal BEFORE_SHA256 or the run
     refuses having written nothing, and the candidate text's sha256 must
     equal AFTER_SHA256 before anything is moved into place.  A rewriter that
     will edit whatever it finds is how a half-edited file gets edited again.
  3. DEFAULT-DENY AUTHORISATION.  Nothing is hard-wired and there is no
     default target.  A run must pass --target explicitly; the target must lie
     OUTSIDE this repository working tree, must not sit under any directory
     named `adr`, and must not be named like the ADR itself; and the run must
     carry the literal --authorise token below.  The token is an argv word and
     deliberately NOT an environment variable: an env var is exported once in
     a wrapper, inherited by every child process and then forgotten, whereas
     an argv token must be retyped at every single invocation, says in its own
     text what it is authorising, and is recorded in the process table and in
     the shell transcript.  There is deliberately NO override that reaches the
     real ADR: amending a ratified DEC-n is a `user` gate, and a gate is not
     crossed by a work-in-progress probe script from 19 August 2026.

Exit codes: 0 ok / dry-run ok; 1 anchor mismatch; 2 refused (authorisation or
target policy); 3 refused (unexpected target content); 4 refused (candidate
content is not the historical result); 5 refused (temp file not on the
target's filesystem); 6 post-write verification failed.
"""
import hashlib
import io
import os
import sys
import tempfile

# The exact phrase that authorises a run.  Long, self-describing, argv-only.
AUTHORISE_TOKEN = (
    "I-AM-REPRODUCING-T47-EDIT-1-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1")

# sha256 of docs/adr/DEC-1-schedule-generator-adapter.md immediately BEFORE
# and AFTER the commit this script produced.
#   BEFORE = `git show bf67a85^:docs/adr/DEC-1-schedule-generator-adapter.md`
#   AFTER  = `git show bf67a85 :docs/adr/DEC-1-schedule-generator-adapter.md`
BEFORE_SHA256 = \
    "32539607c6b43a23d17300b588c70f9fb643c9d554e280cb7a81a2e9847468f0"
AFTER_SHA256 = \
    "4f2387c821a01953503c77c2c70730bf72657c994491110c5ae3bc27a866dc37"

ADR_BASENAME = "DEC-1-schedule-generator-adapter.md"

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
REPO_ADR = os.path.join(W, "docs/adr", ADR_BASENAME)

USAGE = """\
REFUSED.  This script rewrites a document in place and has no default target.

  usage: t47_edit_1.py --target <path-to-a-SCRATCH-COPY> \\
                       --authorise=%s \\
                       [--dry-run]

The edit it carries was applied to docs/adr/%s
- a RATIFIED DEC-n.  CLAUDE.md: "Any change to a ratified DEC-n or the frozen
adapter contract" is a `user` decision gate, and no agent may cross it.  This
script therefore refuses to write anywhere inside the repository working tree,
under any directory named `adr`, or to any file with the ADR's own name, and
it offers no flag that lifts those refusals.
""" % (AUTHORISE_TOKEN, ADR_BASENAME)


def die(code, msg):
    sys.stderr.write("edit1: REFUSED (%d): %s\n" % (code, msg))
    sys.exit(code)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def parse_args(argv):
    target = None
    authorised = False
    dry_run = False
    for a in argv:
        if a.startswith("--target="):
            target = a.split("=", 1)[1]
        elif a == "--target":
            die(2, "--target needs a value (use --target=PATH)")
        elif a.startswith("--authorise="):
            if a.split("=", 1)[1] != AUTHORISE_TOKEN:
                die(2, "--authorise token does not match; nothing written")
            authorised = True
        elif a == "--dry-run":
            dry_run = True
        else:
            die(2, "unknown argument %r" % a)
    if target is None or not authorised:
        sys.stderr.write(USAGE)
        sys.exit(2)
    return target, dry_run


def resolve_target(path):
    rp = os.path.realpath(path)
    repo = os.path.realpath(W)
    if rp == os.path.realpath(REPO_ADR):
        die(2, "target IS the ratified DEC-1 ADR (%s); amending it is a "
               "`user` gate and this script has no override" % rp)
    if rp == repo or rp.startswith(repo + os.sep):
        die(2, "target %s is inside the repository working tree %s; this "
               "script writes only to scratch copies outside it" % (rp, repo))
    if "adr" in rp.split(os.sep):
        die(2, "target %s sits under a directory named `adr`" % rp)
    if os.path.basename(rp) == ADR_BASENAME:
        die(2, "target %s is named like the ratified ADR" % rp)
    if not os.path.isfile(rp):
        die(2, "target %s is not an existing regular file" % rp)
    return rp


def atomic_write(path, data):
    """Write `data` over `path` atomically: temp file in the SAME directory,
    fsync, os.replace.  os.replace is atomic on POSIX when source and
    destination are on one filesystem; a temp file created in the target's own
    directory is on that filesystem by construction, and st_dev is compared
    below as well.  No signal handling is used or needed."""
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".t47-edit1-", suffix=".tmp")
    try:
        if os.stat(tmp).st_dev != os.stat(path).st_dev:
            die(5, "temp file %s is not on the target's filesystem" % tmp)
        os.fchmod(fd, os.stat(path).st_mode & 0o7777)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)
    dfd = os.open(d, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


TARGET, DRY_RUN = parse_args(sys.argv[1:])
TARGET = resolve_target(TARGET)

raw = io.open(TARGET, "rb").read()
before = sha256_bytes(raw)
if before != BEFORE_SHA256:
    die(3, "target sha256 %s != expected pre-edit %s; this is not the "
           "revision-9 document this edit applies to, and NOTHING was written"
           % (before, BEFORE_SHA256))

sys.stderr.write(
    "edit1: AUTHORISED run on scratch target %s (sha256 %s)\n"
    % (TARGET, before))

s = raw.decode("utf-8")


def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("edit1: expected 1 occurrence, found %d for: %.90s" % (n, old))
    s = s.replace(old, new)


# ---------------------------------------------------------------- 1a
rep(
    "**A port must implement the packed rule WITH the special case, or the "
    "clamped-step rule WITHOUT it; taking the packed rule and dropping the "
    "special case double-charges alternate periods, and that combination is "
    "the one a careless port lands on.**",

    "**Revision 10 PINS the packed rule as this document's normative reading of "
    "`k`, together with the special case** — the pin is stated normatively at "
    "the end of the next paragraph, and what forced it is that task T46 **proved** "
    "the two clauses are not separable by any capture on any arm of this routine. "
    "Taking the packed rule and **dropping** the special case double-charges "
    "alternate periods, and that combination is the one a careless port lands on. "
    "(This document calls the other whole-months function the **clamped-step** "
    "rule; task T46 calls the same function **naive**. One function, two names; no "
    "claim below turns on which is used.)")

# ---------------------------------------------------------------- 1b
old282 = (
    "**What that does NOT show, and revision 9 states it because the difference "
    "decides what a vector is worth.** The refuted reading is `packed rule ∧ no "
    "special case`. It is **not** the reading a careless porter most naturally "
    "writes, which is `clamped-step rule ∧ no special case` — and that one is "
    "**indistinguishable from the oracle** on this whole family and far beyond it. "
    "Task T44 measured it: over **59,130** `(ScheduleStartDate, repayment period)` "
    "pairs across 1,095 start dates in 2023–2025 × terms {6, 12, 36}, "
    "`RepaymentEvery` 1, MONTHS, the special case fires on **701** periods, the "
    "packed and clamped-step whole-months functions disagree on **exactly those "
    "same 701**, and the two whole readings differ on **0** [VERIFIED: "
    "`.softhouse/capture/audit-t44/analysis/t44_r2_vs_r4_sweep-output.txt`; **and "
    "re-derived independently by task T45 inside this document's own from-text "
    "model**, reproducing T44's 59,130 / 701 / 701 / 0 digit for digit — "
    "`.softhouse/reviews/t45-probe/t45-extra-output.txt`, leg C3]. **One trap worth "
    "recording, because it is what makes this measurement easy to get wrong:** the "
    "sweep must build its boundaries with §4.2's **re-anchor**, not with plain "
    "`plusMonths`. On plain `plusMonths` boundaries the special case fires **zero** "
    "times over the same 59,130 pairs and the sweep silently proves nothing — "
    "T45's first run did exactly that. **The special case is precisely a "
    "compensation for the packed rule's month-end undercount, and the two errors "
    "cancel on every input.** This is F-1's ambiguity, measured — and it is why "
    "step B pins the pair rather than either clause, and why §8 item **3f** grades "
    "the **pair** and not the special case alone.")

# T167: was `assert`, which `python3 -O` strips - the anchor check would then
# vanish and the replace below would silently do nothing.
if s.count(old282) != 1:
    die(1, "edit1b anchor not found / not unique (count=%d)"
           % s.count(old282))

new282 = (
    "**What that does NOT show — and revision 10 replaces revision 9's \"not yet "
    "captured\" with \"NOT CAPTURABLE\", because task T46 proved it.** The refuted "
    "reading is `packed ∧ no special case`. It is **not** the reading a careless "
    "porter most naturally writes, which is `clamped-step ∧ no special case` — "
    "and that one is not merely uncaptured. It is **observationally identical to "
    "the oracle on every input**, and **no capture on any arm of "
    "`calculatePeriodRatio` can ever separate the special case by itself.** That is "
    "a stronger and a different statement from revision 9's, and it is carried by "
    "**three kinds of evidence, which revision 10 keeps distinct rather than "
    "flattening into one word.**\n"
    "\n"
    "**(i) A closed form — a RE-DERIVATION, performed independently by this task "
    "from [`ProgressiveEMICalculator.java:1419-1459`] and [`DateUtils.java:308-317`] "
    "and agreeing with T46's.** Write `pm(d) = d.year × 12 + d.month` for the "
    "proleptic month, `k = pm(b) − pm(a)`, and `len(b)` for the length of `b`'s "
    "month. At every reachable call site `a ≤ b`, because the seed is either "
    "`ScheduleStartDate` — the **first** repayment period's `FromDate` "
    "[`ProgressiveLoanInterestScheduleModel.java:209-211`] — or this period's own "
    "`FromDate` [`:1477-1480`]. Then, for `k ≥ 1`:\n"
    "\n"
    "```\n"
    "packed(a, b) = k − [a.day > b.day]                       # ChronoUnit.MONTHS.between, :1435\n"
    "clamped(a, b) = k − [min(a.day, len(b)) > b.day]         # largest j with a.plusMonths(j) <= b\n"
    "\n"
    "packed(a, b) != clamped(a, b)  <=>  b.day == len(b)  AND  a.day > b.day\n"
    "```\n"
    "\n"
    "**The right-hand side is verbatim the predicate at [`:1432`]** — "
    "`targetDateLastDay == targetDateDay && seedDateDay > targetDateDay`. The "
    "equivalence is exact: `min(a.day, len(b)) > b.day` implies `a.day > b.day`, so "
    "the two indicators can differ only when `a.day > b.day` **and** "
    "`min(a.day, len(b)) ≤ b.day`; given the first conjunct the second forces "
    "`len(b) ≤ b.day`, and `b.day ≤ len(b)` always, so `b.day = len(b)`. When they "
    "differ, `packed` is one **less** than `clamped`. **And when the predicate "
    "fires the oracle measures to `FromDate.plusDays(1)` [`:1433`]**, which is the "
    "**1st** of the next month: `pm` rises by one, and the predicate itself forces "
    "`a.day > b.day = len(b) ≥ 28`, so `a.day ≥ 29 > 1` and "
    "`packed(a, b+1 day) = (k+1) − 1 = k = clamped(a, b)`. **Therefore "
    "`k_oracle ≡ k_clamped`, identically, on the whole reachable domain: the "
    "special case IS the compensation for the packed rule's month-end undercount, "
    "and neither clause is separately observable.** *(One boundary this task "
    "re-derived and T46 did not state: at `k = 0` Java's truncation-toward-zero "
    "makes `packed = 0` where the floor form would give `−1`. It is unreachable "
    "here — `a ≤ b` with `pm(a) = pm(b)` forces `a.day ≤ b.day`, so neither the "
    "predicate at [`:1432`] nor the divergence above can fire. Recorded because a "
    "port that transcribes the closed form instead of `MONTHS.between` must "
    "reproduce the truncation, not a floor.)*\n"
    "\n"
    "**(ii) An EXHAUSTIVE MEASUREMENT inside the pinned oracle image — an "
    "observation of the oracle JVM's own `java.time`, and neither a re-derivation "
    "nor a capture of loan money** [VERIFIED: task T46, "
    "`.softhouse/capture/periodratio/analysis/T46MonthDiffExhaustive.java`, output "
    "`analysis/t46_monthdiff_exhaustive-output.txt`, compiled and run in a throwaway "
    "container on the pinned image, `java.vm.version 21.0.11+10-LTS`]. Over **every** "
    "ordered pair `a ≤ b` of civil dates in 2000-01-01 … 2040-12-31:\n"
    "\n"
    "| quantity | count |\n"
    "|---|---|\n"
    "| ordered date pairs swept | **112,147,776** |\n"
    "| the [`:1432`] predicate FIRES | **45,253** |\n"
    "| `packed ≠ clamped` | **45,253** |\n"
    "| fires **and** `packed == clamped` | **0** |\n"
    "| does not fire **and** `packed ≠ clamped` | **0** |\n"
    "| `k_oracle ≠ k_clamped` | **0** |\n"
    "| `k_oracle ≠ k_packed` | **45,253** |\n"
    "\n"
    "T44's earlier sweep is a **subset of this one by construction**: over **59,130** "
    "`(ScheduleStartDate, repayment period)` pairs across 1,095 start dates in "
    "2023–2025 × terms {6, 12, 36}, `RepaymentEvery` 1, MONTHS, the special case "
    "fires on **701** periods, the two whole-months functions disagree on **exactly "
    "those same 701**, and the two whole readings differ on **0** [VERIFIED: "
    "`.softhouse/capture/audit-t44/analysis/t44_r2_vs_r4_sweep-output.txt`; **and "
    "re-derived independently by task T45 inside this document's own from-text "
    "model**, reproducing T44's 59,130 / 701 / 701 / 0 digit for digit — "
    "`.softhouse/reviews/t45-probe/t45-extra-output.txt`, leg C3; **and both figure "
    "sets re-derived a third time from this document's own text by task T47**, "
    "`.softhouse/reviews/t47-probe/t47-monthend-output.txt`]. **One trap worth "
    "recording, because it is what makes the 59,130-pair form of this measurement "
    "easy to get wrong:** that sweep must build its boundaries with §4.2's "
    "**re-anchor**, not with plain `plusMonths`. On plain `plusMonths` boundaries "
    "the special case fires **zero** times over the same 59,130 pairs and the sweep "
    "silently proves nothing — T45's first run did exactly that. The "
    "112,147,776-pair form has no such trap, because it sweeps date pairs directly "
    "and builds no schedule.\n"
    "\n"
    "**(iii) The escape route revision 9 named is CLOSED, and closed by an "
    "observation rather than by an argument.** Revision 9 wrote that a "
    "discriminator for the special case alone \"must come from "
    "`calculatePeriodRatio`'s `YEARS` / `WEEKS` / `DAYS` arms\" [`:1405`, `:1407`, "
    "`:1408`] and recorded the item as `TO_BE_CAPTURED`. Task T46 captured all "
    "three arms and none of them delivers one. **`WEEKS` and `DAYS` cannot separate "
    "the two rules at all**: `seed.plus(k, WEEKS)` is `+7k` days and "
    "`seed.plus(k, DAYS)` is `+k` days, so nothing ever clamps and the packed and "
    "clamped-step functions coincide identically — measured **0** separations in "
    "the same 112,147,776-pair sweep. **`YEARS` does separate — on 165 pairs, every "
    "one a 29 February seed against a 28 February target — but the `YEARS` arm is "
    "UNREACHABLE.** `calculatePeriodRatio` computes the `YEARS` ratio at [`:1405`] "
    "and the result is handed to "
    "`calculateRateFactorPerPeriodBasedOnRepaymentFrequency` [`:1598-1610`], whose "
    "`switch` carries arms for `DAYS`, `WEEKS` and `MONTHS` and "
    "`default -> throw new UnsupportedOperationException(\"Invalid repayment frequency\")` "
    "at [`:1609`] [VERIFIED: `:1598-1610` re-opened in the pinned checkout by this "
    "task]. *Observed*: both `T46-YR-A` (the 29 February separator shape) and "
    "`T46-YR-B` (an ordinary seed) return "
    "`java.lang.UnsupportedOperationException: Invalid repayment frequency` "
    "[VERIFIED: task T46, `.softhouse/capture/periodratio/out/t46-periodratio-arms.json`]. "
    "**So the last place a separating shape could have lived returns no schedule at "
    "all.**\n"
    "\n"
    "**Consequence, NORMATIVE — and this is what revision 10 changes in this "
    "subsection.** Of the four combinations of the two clauses, **exactly one is "
    "wrong**:\n"
    "\n"
    "| whole-months rule | month-end special case | agrees with the oracle? |\n"
    "|---|---|---|\n"
    "| **packed** [`:1435`] | **present** [`:1426-1436`] | **YES — this IS the oracle, and it is what this document pins** |\n"
    "| clamped-step | absent | YES — identical on all 112,147,776 swept pairs |\n"
    "| clamped-step | present | YES — the case is inert on top of the clamped-step rule, since it yields `k` either way |\n"
    "| **packed** | **absent** | **NO — diverges on 45,253 of 112,147,776 pairs; refuted on 116 of 116 discriminating cells** |\n"
    "\n"
    "**This document specifies the oracle's own two clauses — packed `k` WITH the "
    "special case — and a port must implement that pair.** A port that implements "
    "the clamped-step rule with no special case is conformant, and revision 10 says "
    "so plainly rather than leaving the reader to infer it; but the pinned reading "
    "is the packed pair, because a specification that names the compensation without "
    "naming the thing it compensates for is one careless edit away from the only "
    "wrong combination in the table. **A blind spot that is proved UNCLOSABLE is a "
    "different fact from one that is merely uncaptured, and a `TO_BE_CAPTURED` that "
    "can never succeed is a defect in this document — which is why §8 item 3f no "
    "longer carries one.** §8 item **3f** therefore grades the **pair** and states "
    "that separating the special case alone is impossible; §9 obligation (f) pins "
    "the pair; and the honest statement about the seven witnesses is that a port "
    "with two cancelling defects passes them **and is correct on this arm**, which "
    "is a better outcome than an open vector request that could never be filled.")

s = s.replace(old282, new282)

# ---------------------------------------------------------------- T167 write
new_bytes = s.encode("utf-8")
after = sha256_bytes(new_bytes)
if after != AFTER_SHA256:
    die(4, "candidate content sha256 %s != the historical post-edit blob %s; "
           "this run would NOT reproduce bf67a85, so nothing was written"
           % (after, AFTER_SHA256))

if DRY_RUN:
    print("edit1: dry-run ok - %s -> %s, nothing written" % (before, after))
    sys.exit(0)

atomic_write(TARGET, new_bytes)

landed = sha256_bytes(io.open(TARGET, "rb").read())
if landed != AFTER_SHA256:
    die(6, "post-write sha256 %s != %s" % (landed, AFTER_SHA256))
sys.stderr.write("edit1: wrote %s atomically; sha256 %s\n" % (TARGET, landed))
print("edit1: ok")
