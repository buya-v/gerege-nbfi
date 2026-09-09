# R2a — the MECHANISM only: a vector must be able to declare its conditions

WORKING DIRECTORY: /Users/buv/oh-gerege-r2a  (branch feat/R2a-vector-params-mechanism)
NEVER commit to `main`. NEVER touch the other worktrees or the oracle.

## SCOPE IS DELIBERATELY NARROW — read this first
A previous attempt at this task spent its entire budget researching the provenance
of 67 existing vectors and wrote NOTHING. That research is a SEPARATE task (R2b).
You are building the mechanism, and only the mechanism. Do not backfill. Do not
investigate .softhouse/capture/. Do not open more than two existing vectors, and
only to learn the schema's shape.

If you finish early, STOP AND REPORT. Do not start the backfill.

## Why this exists
Between 2026-09-01 and 2026-09-03 the reference oracle's tenant changed from
`gerege` (HALF_UP, ordinal 4, Asia/Ulaanbaatar) to `default` (HALF_EVEN,
ordinal 6, Asia/Kolkata). NOT ONE of the 67 vectors could detect it, because a
vector records no statement of the conditions it was captured under. The drift
was found only because someone queried the tenants table by hand.

## Build exactly these four things
1. A `tenant_params` object in the vector schema:
       "tenant_params": {
         "rounding_mode": "HALF_UP", "rounding_ordinal": 4,
         "precision": 19, "currency": "MNT", "minor_units": 2,
         "timezone": "Asia/Ulaanbaatar"
       }
   Follow whatever naming the existing schema suggests; the CONTENT is fixed.

2. The harness REFUSES (non-zero, naming both sides) when a vector's recorded
   params differ from the params the tree is being graded under. Not a warning.

3. An ABSENT `tenant_params` is treated as UNRECORDED: gradeable but FLAGGED in
   the output, never a silent pass. All 67 existing vectors are in this state and
   must keep grading — do not break the current corpus.

4. A test that FAILS if a vector is added with no `tenant_params`.

## What NOT to do
- Do not edit or backfill any existing vector.
- Do not change any rounding behaviour in the Go code.
- Do not touch generator.go's `ungraded("rounding.Mode is not HALF_UP...")` refusal.
- Do not touch .softhouse/guards/ledgerguard (another task owns it).

## DONE means: paste RAW output with exit codes for
   cd nexus && go build ./... && go test ./...
   the harness REFUSING a deliberately mismatched vector, both sides visible
   the harness still GREEN on the existing 67 (UNRECORDED must not break them)

Report exit codes. Never say complete / done / goal achieved. If you cannot make
the existing corpus keep grading, say so plainly and stop.
