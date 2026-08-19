#!/usr/bin/env python3
"""T47 edit 6 - remaining leak sites: A-3's verification level (T46 raised it
from two probes to seven captures), and §8 item 6's now-false coverage claim."""
import io
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DOC = os.path.join(W, "docs/adr/DEC-1-schedule-generator-adapter.md")
s = io.open(DOC, encoding="utf-8").read()


def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("edit6: expected 1 occurrence, found %d for: %.100s" % (n, old))
    s = s.replace(old, new)


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

io.open(DOC, "w", encoding="utf-8").write(s)
print("edit6: ok")
