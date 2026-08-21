#!/usr/bin/env python3
"""T47 edit 6 - remaining leak sites: A-3's verification level (T46 raised it
from two probes to seven captures), and §8 item 6's now-false coverage claim.


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
  BEFORE_SHA256 = `git show 77b1825^:docs/adr/DEC-1-schedule-generator-adapter.md`
  AFTER_SHA256  = the deterministic result of running THIS SCRIPT on that
                  exact blob, measured by T178 - it is NOT a committed blob, because commit
                  77b1825 carried hand edits alongside this script's output;
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

NAME = "edit6"

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable.  There is deliberately NO override that can
# reach the ratified DEC-1.
AUTHORISE_TOKEN = (
    "I-AM-REPRODUCING-T47-EDIT-6-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1")

BEFORE_SHA256 = \
    "8a39c22620c9036e67cd0750739d1e3c6be2c6e034639d2a2d8292989575cf75"
AFTER_SHA256 = \
    "be252dba2218b18b15d10138f9c5802ba6c2026c4c82c100f0e78a024bb2c5fe"

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256, AFTER_SHA256,
               guard.RATIFIED_ADR)


def rep(old, new):
    global s
    s = guard.rep(s, old, new)


# --- §4.5.1 fact 4, A-3 verification level --------------------------------
rep("""   is ignored**, observed on one percentage and one flat charge
   `[VERIFIED on those two; UNVERIFIED as a general rule across charge types]`. **Consequence for""",

    """   is ignored**, observed by T44 on one percentage and one flat charge, and **re-observed by task
   T46 on SEVEN purpose-built captures inside an attested set — `T46-CH-01`…`T46-CH-07`, request
   governing 7 for 7 across four `charge_calculation_enum` values, two `charge_time_enum` values and
   both fee and penalty** [VERIFIED: `.softhouse/capture/charges/out/t46/DEFVSREQ.txt`; e.g.
   `T46-CH-01`, definition `3.750000 %` against request `1.25`, definition would give `810.00` and
   the oracle returned **`270.00`**]. `[VERIFIED on nine captures across two tasks; UNVERIFIED as a
   general rule across the charge types not tried — `charge_calculation_enum` 5 and 9 and
   `charge_time_enum` 2 were not re-tested with a disagreeing amount, and whether `m_charge.amount`
   governs when the request OMITS `amount` is untried by every capture in the program]`.
   **Consequence for""")

# --- §4.5.1 blind spot, "which INPUT supplies the charge amount" ----------
rep("""  probes show the **request** value is authoritative on one percentage and one flat charge, and
  `m_charge.amount` is ignored [VERIFIED: `.softhouse/capture/audit-t44/charges/out/probes/`, `AP-5`,
  `AP-6`]. **A vector promoted from this set must name the request bytes as its fixture.**
  `[UNVERIFIED as a general rule across charge types]` — a systematic sweep is `TO_BE_CAPTURED`.""",

    """  probes show the **request** value is authoritative on one percentage and one flat charge, and
  `m_charge.amount` is ignored [VERIFIED: `.softhouse/capture/audit-t44/charges/out/probes/`, `AP-5`,
  `AP-6`]. **Revision 10 records that task T46 closed the question by capture rather than by probe**
  — seven shapes, request governing **7 for 7**, across `charge_calculation_enum` 1, 2, 3 and 4 and
  `charge_time_enum` 1 and 8, fee and penalty [VERIFIED:
  `.softhouse/capture/charges/out/t46/DEFVSREQ.txt`, captures `T46-CH-01`…`T46-CH-07`, each re-issued
  byte-identically]. **A vector promoted from this set must name the request bytes as its fixture**,
  and that requirement is unchanged — what changed is that it now rests on nine captures rather than
  two probes. `[UNVERIFIED for the charge types not tried: `charge_calculation_enum` 5 and 9,
  `charge_time_enum` 2, and — untried by EVERY capture in the program — whether `m_charge.amount`
  governs when the request omits `amount` entirely]` — a systematic sweep is `TO_BE_CAPTURED`.""")

# --- §8 item 6's coverage claim, now false --------------------------------
rep("**`RepaymentEvery > 1` acquires a second reason in revision 7**: it is the only "
    "place `periodRatio`'s whole-period return value (§4.1.1 step C's `m − k − 1`) can be "
    "anything but 1, so no capture exercises that branch at all.",

    "**`RepaymentEvery > 1` acquires a second reason in revision 7**: it is the only "
    "place `periodRatio`'s whole-period return value (§4.1.1 step C's `m − k − 1`) can be "
    "anything but 1. **Revision 10 corrects the clause that followed it — \"so no capture "
    "exercises that branch at all\" is no longer true** (task T46). *Observed* on the "
    "Path-A seam: `T46-RE-2` and `T46-RE-2ME` at `RepaymentEvery` 2 and `T46-RE-3` at 3, "
    "plus the `WEEKS` arm on `T46-WK-A`/`T46-WK-B`/`T46-WK-C` (`T46-WK-C` at "
    "`RepaymentEvery` 2), the `DAYS` arm on `T46-DY-A`/`T46-DY-B` (`T46-DY-B` at 10), and "
    "the `YEARS` arm **throwing** `UnsupportedOperationException` on "
    "`T46-YR-A`/`T46-YR-B` [VERIFIED: "
    "`.softhouse/capture/periodratio/out/t46-periodratio-arms.json`]. **The item stays "
    "open because it asks for VECTORS and these are attested raw observations** (item 1) "
    "— and because what a capture *covers* is not what it *discriminates*: measured "
    "across 186 repayment periods, `T46-RE-3` separates the `RepaymentEvery` reading on 3 "
    "periods and `T46-RE-2ME` separates the special-case-omitted reading on 2, while "
    "`T46-WK-*`, `T46-DY-*`, `T46-RE-2` and the control `T46-ARM-CTL` separate **nothing** "
    "among those readings [VERIFIED: "
    "`.softhouse/capture/periodratio/analysis/t46_arms_ratio-output.txt`]. **What DID "
    "close is T44's blind spot 3**: before `T46-RE-3` a port could get the multiplier "
    "right and `RepaymentEvery` wrong and pass every capture; it no longer can.")

guard.commit(s)
