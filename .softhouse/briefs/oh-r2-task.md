# R2 — a vector must record the conditions it was captured under

WORKING DIRECTORY: /Users/buv/oh-gerege-r2   (branch feat/R2-vector-params)
NEVER commit to `main`. NEVER touch the other worktrees or the oracle.

## The defect, stated as a fact
Every one of the 67 vectors in .softhouse/vectors/ is silent about the tenant
parameters in force when it was captured. Their keys are: schema, case_id,
context, class, title, dec1_revision, _note, capabilities_required,
graded_against, retires_when_capability_graded. None of these says which
rounding mode, currency, precision or timezone produced the numbers.

This is not hypothetical. Between 2026-09-01 and 2026-09-03 the reference
oracle's tenant changed from `gerege` (HALF_UP, ordinal 4, Asia/Ulaanbaatar) to
`default` (HALF_EVEN, ordinal 6, Asia/Kolkata). NOT ONE of the 67 vectors could
detect it. The program only learned of it because a task went and queried the
tenants table by hand.

A vector that does not record its own conditions is not evidence. It is a number
with a story attached.

## What to build
1. Extend the vector schema with a REQUIRED `tenant_params` object:
       "tenant_params": {
         "rounding_mode": "HALF_EVEN", "rounding_ordinal": 6,
         "precision": 19, "currency": "MNT", "minor_units": 2,
         "timezone": "Asia/Kolkata"
       }
   Field names and shape are yours to choose if the existing schema suggests
   better ones; the CONTENT is not optional.

2. The harness must REFUSE to grade a vector whose recorded parameters differ
   from the parameters the tree is being run under. Not warn. Refuse, non-zero,
   naming both sides. A mismatch is exactly the drift described above.

3. BACKFILL HONESTLY, OR NOT AT ALL. The 67 existing vectors were captured under
   conditions nobody recorded. You may know some of them from git history or
   capture logs. Where the evidence is genuinely there, backfill and cite it in
   the vector. Where it is NOT, mark the vector `"tenant_params": "UNRECORDED"`
   and make the harness treat UNRECORDED as gradeable-but-flagged, NOT as a
   silent pass. DO NOT GUESS A PARAMETER AND WRITE IT DOWN AS FACT. An invented
   provenance is worse than a missing one.

4. A test that FAILS if a new vector is added without tenant_params.

## What NOT to do
- Do not capture, synthesise or modify any vector's numbers.
- Do not touch the oracle.
- Do not change any rounding behaviour in the Go code.
- Do not edit generator.go:357's refusal — a different task owns it.

## DONE means: paste RAW output with exit codes for
   cd nexus && go build ./... && go test ./...
   the harness REFUSING a deliberately mismatched vector (show both sides)
   the count: how many of 67 you backfilled with evidence, how many are UNRECORDED

Report exit codes. Never say complete / done / goal achieved. Say plainly how
many vectors you could NOT establish provenance for. That number is the honest
measure of how much of the existing corpus is evidence and how much is a claim.
