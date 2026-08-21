#!/usr/bin/env python3
"""T47 edit 4c - §4.5.1 blind-spot list: T46's two purpose-built ties, and the
new blind spot N46-1 opens (which context supplied the mode).


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
INERT TODAY - its single anchor is gone, exit 1, scratch copy byte-identical afterwards.
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
  BEFORE_SHA256 = `git show 5041778^:docs/adr/DEC-1-schedule-generator-adapter.md`
  AFTER_SHA256  = the deterministic result of running THIS SCRIPT on that
                  exact blob, measured by T178 - it is NOT a committed blob, because commit
                  5041778 carried hand edits alongside this script's output;
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

NAME = "edit4c"

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable.  There is deliberately NO override that can
# reach the ratified DEC-1.
AUTHORISE_TOKEN = (
    "I-AM-REPRODUCING-T47-EDIT-4C-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1")

BEFORE_SHA256 = \
    "f9deda22fecdcab160559920f40370246c66f1adaa902bb881ec4d772472c564"
AFTER_SHA256 = \
    "7b14fa36e5b15f74ec02061bdf4a1fbe6ed526150cb7cce81a0d5f95580e9cda"

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256, AFTER_SHA256,
               guard.RATIFIED_ADR)


old = """  **So the in-charge-arithmetic rounding-mode canary exists and fires.** It is a T44 audit probe and
  **not** part of T40's attested set; promoting it as the canary is `TO_BE_CAPTURED`. **Nothing in
  DEC-1 rested on the false claim** — §4.5.1 fact 4 and §4.1's mode evidence are unaffected — but the
  blind spot it named is closed and this list must not keep asserting it.
"""

new = """  **So the in-charge-arithmetic rounding-mode canary exists and fires.** That one is a T44 audit
  probe and **not** part of T40's attested set. **Revision 10 adds two more, purpose-built and inside
  an attested capture set** (task T46): a `0.021875 %` percent-of-interest instalment fee on a
  period-1 interest of `21,600.00` is exactly `4.725` and the oracle returned **`4.73`**, and
  `0.009375 %` on the same interest is exactly `2.025` and returned **`2.03`** — both `HALF_UP`,
  where `HALF_EVEN` gives `4.72` and `2.02` [VERIFIED: captures `T46-CH-03` and `T46-CH-04`,
  `.softhouse/capture/charges/req/calc-T46-CH-03-tie-pctinterest-4725.json` and
  `out/t46/T46-CH-03-tie-pctinterest-4725-raw.json` and the `-2025` pair, read as exact wire text and
  re-read by this task]. **Three observed ties — and the blind spot they were meant to close is only
  HALF closed, which revision 10 must not overstate:** a tie pins **the mode that ran**; it does
  **not** pin **which of the two `MathContext`s supplied it**, because on Path B they are one
  reference. That second question is the separate and still-open blind spot immediately below. What
  remains for this bullet is **promotion** of one of the three shapes into a vector, not a search.
  **Nothing in DEC-1 rested on the false claim** — §4.5.1 fact 4 and §4.1's mode evidence are
  unaffected — but the blind spot it named is closed and this list must not keep asserting it.
- **WHICH `MathContext` supplies the rounding mode at a charge's scale-2 conversion** (added in
  revision 10 from task T46's finding **N46-1**). The percentage is computed under the **threaded**
  `mc` [`ProgressiveLoanScheduleGenerator.java:445-446`, and `:464-465` on the specified-due-date
  arm] and is then wrapped by the **two-argument** `Money.of(MonetaryCurrency, BigDecimal)`
  [`Money.java:114-116`, ambient read at `:115`], so the scale-2 rounding at [`Money.java:52`] takes
  the **AMBIENT** mode, by §4.1.2's per-construction rule. On Path B the caller sources the threaded
  context **from** the ambient one [`LoanScheduleAssembler.java:753`, `:765`], so the two are one
  reference and **no capture this program holds separates them** — the three ties above included.
  Unlike the 0-decimal-place `inMultiplesOf` leak (§4.4, `Money.java:48-51`), **this one is reachable
  at MNT's two decimal places**, which is why it is worth a vector: a port that threads one context
  everywhere gets the interest right and the charge ties wrong. Separating it needs the tenant
  rounding mode written to differ from the threaded one, i.e. a tenant write. `TO_BE_CAPTURED`
  (§8 item 9(h)); the full derivation is in *Which `MathContext` rounds a CHARGE* above.
"""

s = guard.rep(s, old, new)
guard.commit(s)
