# T149 — capture the HALF_UP/HALF_EVEN tie as a PARITY VECTOR

WORKING DIRECTORY: /Users/buv/oh-gerege-t149   (branch fix/T149-tie-vector)
NEVER commit to `main`. NEVER touch /Users/buv/gerege-nbfi or the other worktrees.

## Why this is first
A decision has been taken to change the ratified rounding mode from HALF_UP to
HALF_EVEN. It has NOT been applied yet, and it must not be applied by you.

The reason it is not applied yet: **0 of 46 vectors carry either tie answer.**
Nothing in the parity corpus would notice which rounding mode is in force. Changing
a money rule while the instrument that measures it is blind is how a silent
regression reaches production. So the instrument comes first. That is this task.

## The tie, already solved and measured (T136/T149)
    1,162,502.50 x 0.018 = 20,925.045
      HALF_UP    -> 20925.05
      HALF_EVEN  -> 20925.04
T136 established that the two product rows differ in 89 columns by only `id`, so
the rounding mode is the SOLE cause of the difference.

## The oracle
  https://localhost:8443/fineract-provider/actuator/health   -> {"status":"UP"}
  container `gerege-oracle-db`, db `fineract_default`, user `postgres`
  It has ONE tenant: `default`, Asia/Kolkata, rounding ordinal 6 = HALF_EVEN.
  The `gerege` tenant (HALF_UP) NO LONGER EXISTS. Do not try to create it.
  Do not modify the oracle in any way.

## What to do
1. Capture the tie case from the LIVE oracle under the `default` tenant. It will
   answer 20925.04 (HALF_EVEN). Store it as a parity vector under
   .softhouse/vectors/ following the existing vector schema.
   CAPTURE ONLY. Synthesise nothing, transcribe nothing, hand-write nothing.
2. Record the tenant parameters ON the vector: rounding mode name AND ordinal,
   currency, minor units, timezone. Existing vectors do not carry these, and that
   omission is why the corpus cannot tell one mode from another. Yours must.
3. **PROVE THE VECTOR DISCRIMINATES.** The Go tree currently implements HALF_UP.
   Graded against it, your new vector MUST FAIL — expected 20925.04, got 20925.05.
   A vector that passes against both modes has measured nothing.
   Show that failure in your report. It is the deliverable, not an error.

## What ALREADY EXISTS — do not rebuild it
The port is NOT hardcoded to HALF_UP. `Rounding{Precision, Mode}` is already
threaded explicitly through the schedule generator, and BOTH modes are already
defined (`contract.RoundingHalfUp`, `contract.RoundingHalfEven`;
`loanproduct.RoundHalfUp`, `RoundHalfEven`). What blocks HALF_EVEN is one honest
refusal in generator.go:357 --

    if req.Rounding.Mode != contract.RoundingHalfUp {
        return ungraded("rounding.Mode is not HALF_UP, which is the only mode
                         any capture was taken at")
    }

-- which refuses to grade a mode NO CAPTURE EXISTS FOR. That refusal is correct
today. Your captured vector is what makes it wrong. DO NOT edit that line: the
next task relaxes it to "refuse any mode with no capture", once your capture is
the evidence that HALF_EVEN has one.

## What NOT to do
- Do NOT change the rounding mode in the Go code. That is the NEXT task.
- Do NOT retire REFUSE-02-half-even-ungraded.json. That is the next task too.
- Do NOT edit any guard, harness or gate to make something pass.
- Do NOT provision, alter or restart the oracle or its database.

## DONE means: paste RAW output including exit codes for
   cd nexus && go build ./... && go test ./...
   the grading run showing your new vector FAILING against the HALF_UP tree,
   with both numbers visible (20925.04 expected, 20925.05 produced)

Report exit codes. Never say complete / done / goal achieved. If you cannot
capture from the live oracle, say so plainly and stop — a truthful refusal beats
a synthesised vector.
