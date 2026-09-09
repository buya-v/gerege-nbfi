# G-19 residue evidence — the oracle's OWN arithmetic generating sub-minor money

Captured 2026-09-09 by OH-CAP-J while hunting a rounding tie for `charges`. It
answers the one question gate G-19 left open when Buyan ratified the refusal that
morning, and it is preserved here because it bears on CUTOVER, not on any vector.

## What was asked, and what came back

`POST /loans?command=calculateLoanSchedule`, principal `1162502.50`, a 1% charge —
BOTH inputs exact at 2dp:

    projection   periods[0].feeChargesDue  = 11625.025   <- THREE decimals
                 totalFeeChargesCharged    = 11625.03
    persisted    GET /loans/9/charges  amount = 11625.03  <- CLEAN, HALF_UP, 2dp

## Why it matters

G-19 recorded that every residue instance until then had its extra digit **supplied
by a prober**, and reattached to the parallel-run gate the question of whether the
oracle's own arithmetic could GENERATE one. **It can** — from an ordinary percentage
charge on an ordinary principal.

But the hazard is NARROWER than the gate feared: the residue lives in an intermediate
PROJECTION cell, and the oracle rounds HALF_UP before storing. A port reading stored
charges meets no residue; a port reading schedule-projection cells would. That
distinction belongs in the parallel-run assessment.

This is a partial answer to `FU-T352-2`. It does not reopen the ratification: refusing
residue remains correct, and `11625.03` confirms the oracle applies HALF_UP at the same
boundary this port does.

## Files

    calc-XR-tie-1pct.json       the request        sha256 852c0168…
    calc-XR-tie-1pct-out.json   the response       sha256 8e77d452…

Hashes re-verified after the copy out of the session scratchpad.
