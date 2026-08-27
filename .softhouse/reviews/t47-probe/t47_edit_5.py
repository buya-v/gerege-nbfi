#!/usr/bin/env python3
"""T47 edit 5 - §8 item 9's TO_BE_CAPTURED list: (f) gains T46's two ties,
new (h) for N46-1; §9's capture-programme bullet.


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

NAME = "edit5"

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable.  There is deliberately NO override that can
# reach the ratified DEC-1.
AUTHORISE_TOKEN = (
    "I-AM-REPRODUCING-T47-EDIT-5-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1")

BEFORE_SHA256 = \
    "f9deda22fecdcab160559920f40370246c66f1adaa902bb881ec4d772472c564"
AFTER_SHA256 = \
    "e0b1a30d7c69d170cf9fe49f453c23e1031be098efa4415a9416b540154fc71f"

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256, AFTER_SHA256,
               guard.RATIFIED_ADR)


def rep(old, new):
    global s
    s = guard.rep(s, old, new)


# --- §8 item 9(f) ----------------------------------------------------------
rep("(f) a percentage landing on an exact half-cent tie, which pins the rounding mode "
    "inside the charge arithmetic specifically — **revision 9 records that T44's audit "
    "probe `AP-5` already FOUND one and observed `0.405 → 0.41`, refuting T40's claim "
    "that none exists, so what remains is promotion of that shape into the set rather "
    "than a search** (§4.5.1); and (g) **a shape in which the request `amount` differs "
    "from the persisted `m_charge.amount`**, which no capture in the set does and which "
    "T44's `AP-5`/`AP-6` show decides the money (finding A-3, §4.5.1).",

    "(f) a percentage landing on an exact half-cent tie, which pins the rounding **mode** "
    "inside the charge arithmetic specifically — **revision 9 records that T44's audit "
    "probe `AP-5` already FOUND one and observed `0.405 → 0.41`, refuting T40's claim "
    "that none exists, so what remains is promotion of that shape into the set rather "
    "than a search**; **revision 10 adds that task T46 built two more INSIDE an attested "
    "set** — `T46-CH-03` (`4.725 → 4.73`) and `T46-CH-04` (`2.025 → 2.03`), both "
    "`HALF_UP` — so this sub-item is now three observed shapes away from a search and "
    "one promotion away from discharged (§4.5.1); (g) **a shape in which the request "
    "`amount` differs from the persisted `m_charge.amount`**, which no capture in T40's "
    "set does and which T44's `AP-5`/`AP-6` show decides the money (finding A-3, "
    "§4.5.1) — **revision 10 records that task T46 closed the QUESTION by capture, "
    "seven shapes for seven, the request governing every time across four "
    "`charge_calculation_enum` values and both fee and penalty** [VERIFIED: "
    "`.softhouse/capture/charges/out/t46/DEFVSREQ.txt`, captures `T46-CH-01`…`T46-CH-07`], "
    "**so what remains here is promotion, and the `[UNVERIFIED as a general rule across "
    "charge types]` qualifier still stands for the enum values T46 did not try**; and "
    "**(h) a shape in which the TENANT rounding mode DIFFERS from the threaded one, put "
    "to a charge percentage that lands on a tie** — the only thing that can decide "
    "**which** `MathContext` supplies the mode at [`Money.java:52`] for a charge, since "
    "on Path B the caller sources one from the other and every capture in the program "
    "has them equal (revision 10, task T46's **N46-1**; §4.1.2, §4.5.1). It needs a "
    "tenant write on a running server, so it belongs to a task that owns the oracle and "
    "may restart or re-tenant it. **This is the sharpest remaining charge blind spot, "
    "because unlike the `inMultiplesOf` leak it is reachable at MNT's two decimal "
    "places.**")

# --- §9 capture-programme bullet ------------------------------------------
rep("**Revision 9 adds two entries to that machine-readable list** (capture audit T44): "
    "a record from the month-end family cannot grade **either clause of that pair on its "
    "own** (F39-1), and a record from the charge set cannot grade **which input supplies "
    "the charge amount** and must name the **request bytes** as its fixture (A-3).",

    "**Revision 9 adds two entries to that machine-readable list** (capture audit T44): "
    "a record from the month-end family cannot grade **either clause of that pair on its "
    "own** (F39-1), and a record from the charge set cannot grade **which input supplies "
    "the charge amount** and must name the **request bytes** as its fixture (A-3). "
    "**Revision 10 sharpens the first and adds a third** (task T46): the month-end "
    "record's limitation is not a gap but a **proved property** — neither clause is "
    "separable by any vector on any arm of `calculatePeriodRatio`, so the record must "
    "say \"not separable\" and not \"not yet separated\" (§4.1.1 step B, §8 item 3f); and "
    "**a record promoted from the charge set cannot grade WHICH `MathContext` supplied "
    "the rounding mode at the charge's scale-2 conversion**, because on Path B the "
    "threaded context and the ambient one are a single reference "
    "[`LoanScheduleAssembler.java:753`, `:765`] and every capture in the program has "
    "them equal (N46-1; §4.1.2, §4.5.1, §8 item 9(h)).")

guard.commit(s)
