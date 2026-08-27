#!/usr/bin/env python3
"""T47 edit 3 - finding 2: installmentAmountInMultiplesOf is honoured or lost
BY CALLER, not by the field.


HARDENED BY T178 (21 August 2026) - P-22, P-48 rule 4, reusing T167's shape.
As shipped by T47 this file ended in

    io.open(DOC, "w", encoding="utf-8").write(s)

with DOC hard-wired to docs/adr/DEC-1-schedule-generator-adapter.md
- a RATIFIED DEC-n, which CLAUDE.md makes a hard `user` gate to amend.  There was no
try, no finally, no except, no atexit, no signal handler and no authorisation
of any kind.  `io.open(path, "w")` opens with O_TRUNC, so the target was
EMPTIED before a single byte of replacement text was written, and any
interruption from that instant until the last flush left it truncated or
half-edited.

REACH, MEASURED ON SCRATCH COPIES ON 21 AUGUST 2026, NOT ASSERTED.
INERT TODAY - refused at its first anchor with `found 0`, exit 1, the scratch copy byte-identical afterwards.
An anchor that does not match today is not a guarantee for tomorrow - the
document is a living artefact and a later revision can restore a phrase - so
this file is hardened regardless of whether it currently applies.

THE EDIT ITSELF DID NOT CHANGE.  Every anchor and every replacement string
below is byte-for-byte T47's.  What changed is the head and the tail:

  * the hard-wired target and the unguarded read are gone; the target now
    arrives from argv under default-deny authorisation;
  * the write is atomic (`mkstemp` in the target's own directory, `st_dev`
    compared, `fsync`, `os.replace`) and is gated on sha256 BOTH on the target
    read and on the candidate text;
  * `rep`'s anchor check exits 1 explicitly - it was `sys.exit(<str>)` before
    and is never a bare `assert`, which `python3 -O` strips.

PINNED CONTENT GATE, and this is what actually closes the bypass.
  BEFORE_SHA256 = `git show f33af09^:docs/adr/DEC-1-schedule-generator-adapter.md`
  AFTER_SHA256  = the deterministic result of running THIS SCRIPT on that
                  exact blob, measured by T178 - it is NOT a committed blob, because commit
                  f33af09 carried hand edits alongside this script's output;
                  the pair is (that blob) -> (this script's deterministic
                  output on it), re-measurable by anyone in one command.
The ratified DEC-1 currently on `main` is sha256
49dc89231ccf0615aa59603f2858025b0d489d48f0bf88df5b122f6c9cc7c9ab and the
frozen contract.go is 0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139;
neither is any script's BEFORE_SHA256, so no run of this file can reach either
artefact's CURRENT contents even if every other guard were stripped.

Guard, exit codes and the argv-token rationale: see `t178_guard.py` beside
this file.  Exit codes are unchanged from t47_edit_1.py's:
0 ok / dry-run ok; 1 anchor mismatch; 2 refused (authorisation or target
policy); 3 refused (unexpected target content); 4 refused (candidate content
is not the historical result); 5 refused (temp file not on the target's
filesystem); 6 post-write verification failed.
"""
import os
import sys

# The guard lives beside this script.  Inserting THIS FILE's own directory at
# the front of sys.path means the module cannot be shadowed from the cwd or
# from PYTHONPATH; a missing or unimportable guard raises ImportError and this
# script exits non-zero having written nothing - it fails CLOSED.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t178_guard as guard  # noqa: E402

NAME = "edit3"

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable.  There is deliberately NO override that can
# reach the ratified DEC-1.
AUTHORISE_TOKEN = (
    "I-AM-REPRODUCING-T47-EDIT-3-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1")

BEFORE_SHA256 = \
    "fc6d17209fd94741c92f22f147a634eaefe0f3468877bdba84eb3621c1d48a0a"
AFTER_SHA256 = \
    "5bbf7efb16c740fe91ba8b6933072eca98a54f2e1fe81024c6028f83c48f54da"

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256, AFTER_SHA256,
               guard.RATIFIED_ADR)


def rep(old, new):
    global s
    s = guard.rep(s, old, new)


# --- §2.2 table row --------------------------------------------------------
rep("| `installmentAmountInMultiplesOf` | The field exists "
    "[`LoanApplicationTerms.java:217`] but the `Builder` has **no setter for it at "
    "all**; the only assignment is in a positional constructor [`:828`] this path never "
    "reaches. Structurally unreachable, not merely unset. |",

    "| `installmentAmountInMultiplesOf` | The field exists "
    "[`LoanApplicationTerms.java:217`] but the `Builder` has **no setter for it at "
    "all**; the only assignment is in a positional constructor [`:828`] this path never "
    "reaches. Structurally unreachable **through this assembler**, not merely unset — "
    "and **not** a property of the field, which another caller honours; see the "
    "per-caller statement below (revision 10). |")

# --- §2.2 consequence paragraph -------------------------------------------
rep("**Consequence, and it is the reason revision 1 was rejected:** for those two "
    "inputs the seam-captured corpus has **zero discriminating power**. A Go port that "
    "honours them and one that ignores them score identically. A contract frozen in a "
    "form that assumes \"vectors pass\" implies \"the contract is covered\" would be "
    "frozen around a hole.",

    "**Whose blind spot this is — stated PER CALLER, because that is what it is a "
    "property of** (added in revision 10 from task T46's finding M-4, which capture "
    "audit T44 raised and T46 closed by re-derivation and by counter-observation). The "
    "table above is a statement about **`LoanApplicationTerms.assembleFrom("
    "LoanRepaymentScheduleModelData, MathContext)`** [`LoanApplicationTerms.java:579-606`] "
    "— the assembler the Path-A embeddable seam runs through — and about **every** "
    "caller that reaches the generator that way, not about the field:\n"
    "\n"
    "| caller | `installmentAmountInMultiplesOf` | evidence |\n"
    "|---|---|---|\n"
    "| the Path-A embeddable seam (this contract's capture path, §3.2) | **LOST** | the "
    "assembler at [`LoanApplicationTerms.java:579-606`] contains **zero** occurrences of "
    "`MultiplesOf` [VERIFIED: the range re-opened and grepped in the pinned checkout by "
    "this task] |\n"
    "| `LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement` | "
    "**LOST — for the same reason, and it is worth naming because it LOOKS wired** | it "
    "reads the ambient context at [`LoanScheduleGeneratorServiceImpl.java:44`], puts "
    "`loanProductRelatedDetail.getInstallmentAmountInMultiplesOf()` into the "
    "`LoanRepaymentScheduleModelData` at [`:56`], and calls "
    "`scheduleGenerator.generate(mc, modelData)` at [`:63`] — the value travels the "
    "whole way and is then dropped by the assembler above [VERIFIED: all three lines "
    "re-opened in the pinned checkout by this task] |\n"
    "| the REST `calculateLoanSchedule` path via `LoanScheduleAssembler` (Path B, §4.7) "
    "| **HONOURED** | *observed*: capture `B-02` (`installmentAmountInMultiplesOf = 100`) "
    "returns period-1 `totalInstallmentAmountForPeriod` **112,100.00** where the `B-01` "
    "baseline returns **112,082.37** [VERIFIED: task T46, "
    "`.softhouse/capture/mathcontext/out/control/B-02-multiplesof100-raw.json`; the same "
    "four Path-B captures §4.7 already cites] |\n"
    "\n"
    "**So DEC-1 must never state this field's behaviour unconditionally, and revision "
    "10 removes the last place it did.** A capture seam's blind spot is a property of "
    "the **caller**, not of the field — the same field is money-moving one call away. "
    "That is exactly why §4.7 keeps the field in the contract and refuses it for Run 1 "
    "rather than declaring it inert, and why §3.2's \"the seam's blind spot is empty\" "
    "is scoped to the seam in the sentence that states it.\n"
    "\n"
    "**Consequence, and it is the reason revision 1 was rejected:** for those two "
    "inputs the **seam-captured** corpus has **zero discriminating power**. A Go port "
    "that honours them and one that ignores them score identically **on that corpus**. "
    "A contract frozen in a form that assumes \"vectors pass\" implies \"the contract is "
    "covered\" would be frozen around a hole.")

# --- §3.2 ------------------------------------------------------------------
rep("**Therefore, inside the graded domain, the seam's blind spot is empty:** every "
    "admissible request is faithfully rendered, and a Path-A capture grades everything "
    "the request carries. That is what licenses freezing this contract on a "
    "seam-captured corpus.",

    "**Therefore, inside the graded domain, the seam's blind spot is empty:** every "
    "admissible request is faithfully rendered, and a Path-A capture grades everything "
    "the request carries. That is what licenses freezing this contract on a "
    "seam-captured corpus. **\"The seam's\" is load-bearing in that sentence and "
    "revision 10 says so rather than leaving it to the possessive** (§2.2, task T46's "
    "M-4): `installmentAmountInMultiplesOf` is dropped by **this assembler and by every "
    "caller that uses it**, and is **honoured** by the REST `calculateLoanSchedule` "
    "path, where a multiple of 100 major units is *observed* to move period 1 from "
    "112,082.37 to 112,100.00 (§4.7, capture `B-02`). The pin is safe because the "
    "graded domain pins the contract field to 0, **not** because the oracle ignores the "
    "input.")

# --- §4.7 disposition ------------------------------------------------------
rep("**Disposition for Run 1: launch WITHOUT it.** Products ship with no installment "
    "rounding; a non-zero value is refused with `ErrNoDiscriminatingVector`. Rounding to "
    "whole 100 ₮ is a legitimate Mongolian feature, but the seam this corpus is captured "
    "through cannot grade it (§2.2), and shipping it now would mean shipping an "
    "unvectored money path.",

    "**Disposition for Run 1: launch WITHOUT it.** Products ship with no installment "
    "rounding; a non-zero value is refused with `ErrNoDiscriminatingVector`. Rounding to "
    "whole 100 ₮ is a legitimate Mongolian feature, but the seam this corpus is captured "
    "through cannot grade it — **and that is a fact about the seam and about every "
    "caller that shares its assembler, not about the oracle, which honours the field on "
    "the REST path** (§2.2's per-caller table, added in revision 10 from task T46's "
    "M-4) — and shipping it now would mean shipping an unvectored money path.")

guard.commit(s)
