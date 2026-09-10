# F-2026-09-10 — drive-to-vector ratio is only meaningful for rich-request contexts

**Status:** DECIDED. Recorded to prevent a repeat mis-pick.
**Cost of learning it:** one near-miss dispatch, caught before the run was launched.

## What the ratio suggested, and where it lied

Ranking contexts by drives-per-vector picked out four apparent weak spots:

    loanschedule  50 vectors / 2 drives   0.04
    parties       16 vectors / 4 drives   0.25
    loanproduct   15 vectors / 4 drives   0.27
    charges       12 vectors / 4 drives   0.33

Two of those were real and two were artefacts. The discriminator is **how much the
corpus's request actually VARIES** — a port can only be caught ignoring a field the
vectors vary, so a context whose request has few varying fields has a small defect space
and needs few drives.

    CONTEXT        VECTORS  VARYING  CONSTANT  SEAMS
    ledger              17       22         6      2
    loan                18       16         6      8
    loanschedule        50       11         7      3
    charges             12        7         5      1
    provisioning         8        4         6      2
    shares               7        3        11      3
    savings              6        3         4      4
    branch               6        3         2      3
    parties             16        2         0      3
    loanproduct         15        2         0      1
    workingcapital       5        1         0      2
    cob                  6        1         0      1
    collateral           4        0         4      4

`parties` and `loanproduct` are **enum/vocabulary contexts**: their whole request is
`{stored|name, vocabulary}`, and their vectors grade stored-value-to-vocabulary mappings.
There are only so many ways to get an ordinal wrong, and their four drives already cover
ordinal-swap, legal-form, sibling-name, qualified-code and days360/365. **They are
adequately covered, not weak.** Dispatching against the ratio would have burned a budget
finding nothing.

`loanschedule` and `charges` were genuinely weak, and the technique worked on both:

    loanschedule  2 -> 8 drives  (OH-LSDRIVE-I), plus a zero-kill finding
    charges       4 -> 9 drives  (OH-CHDRIVE-J), plus two stale ZERO comments corrected

## The rule

**Before dispatching a drive-coverage task, count the VARYING request fields.** The task
is worth a run when a context has many varying fields and few drives. It is not worth a run
when the request is two fields wide, however many vectors there are.

## The residual this surfaced — a CORPUS gap, not a drive gap

`shares` has **11 CONSTANT fields**, the most of any context: its 7 vectors are near-clones
across eleven dimensions, varying only 3. `collateral` varies **nothing** (4 constant, 0
varying). Those are weaknesses in the OBSERVATIONS, not in the drives — no drive can catch
a port ignoring a field every vector holds fixed.

**Fixing that needs new captures, not new drives**, and therefore the oracle. It is the
natural successor to this campaign and is recorded here rather than acted on immediately.
