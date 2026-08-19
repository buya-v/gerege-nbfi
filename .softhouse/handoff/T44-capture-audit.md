# T44 — independent audit of this fire's three capture sets

**Task:** T44, branch `softhouse/T44-capture-audit`, worker `auditor`.
**Full review:** `.softhouse/reviews/T44-capture-audit.md`. Evidence, scripts and re-run outputs:
`.softhouse/capture/audit-t44/**`.

**Reference oracle (Fineract) reachability, this fire: REACHABLE**, so this audit **re-executed**
work rather than only reading it [VERIFIED: `actuator/health` → `{"status":"UP"}`;
`fineract-fineract-1` + `fineract-db-1` healthy; image
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`; pinned checkout
`426a23544e8426a38ae43ae404670a0a7e85b9eb` clean].

**Storage:** raw audit evidence only. **Nothing promoted, nothing contract-shaped** — gate **G-1**
is open. The three audited subtrees, `dec1-binding/`, `src/`, `out/`, `pathb/`, `docs/adr/**`,
`nexus/**` and T43's `reviews/T43*` / `t43-probe/` were **read only, never written**.

---

## Verdicts

| set | task | verdict | findings |
|---|---|---|---|
| `.softhouse/capture/periodratio/` | T39 | **ACCEPTED WITH REQUIRED CHANGES** | F39-1, F39-2 (P1); F39-3, F39-4 (P2) |
| `.softhouse/capture/charges/` | T40 | **ACCEPTED WITH REQUIRED CHANGES** | A-1…A-4 (P1); A-5…A-8 (P2) |
| `.softhouse/capture/mathcontext/` | T42 | **ACCEPTED WITH REQUIRED CHANGES** | M-1…M-4 (P1); M-5…M-11 (P2) |
| cross-cutting | — | — | T44-X1 (P2) |

**No set was rejected, and no synthesised number was found in any of the three** — the single thing
this audit most needed to rule out. Every published figure traced to an observed oracle response or a
source literal at the cited `file:line`, with **one** exception (**A-2**), where the line is real but
says the opposite of what it is cited for.

**What the three sets share is not a bad number; it is a narrower proof than the handoff claims.**
In T39 the month-end family grades a *pair* of behaviours rather than the one it names; in T40 the
corpus cannot see which of two inputs supplies the charge amount; in T42 the shapes chosen to reach a
leak do not reach it. In each case the **conclusion survives and the coverage claim does not** — which
is `patterns.md`'s *coverage is what a corpus can distinguish* landing for the sixth consecutive round.

**Two findings were reached independently by two audit legs with no shared context** — M-1/M-2 and
M-5. By this program's own standard that is the strongest evidence it generates.

---

## The findings, one line each

**`periodratio` (T39)**

- **F39-1 (P1)** — the four month-end captures do **not** grade the month-end special case: over
  59,130 swept `(start, period)` pairs, the reading that omits it *and* computes whole-months the
  obvious way is **identical to the oracle on every one**, because the special case is exactly a
  compensation for `ChronoUnit.MONTHS.between`'s packed month-end undercount (701 firings = 701
  disagreements, 0 divergences).
- **F39-2 (P1)** — `ATTESTATION.md` §4 offers "two independent witnesses" to the `MathContext` that
  are both **ambient** and are in fact **one cache write logged and read back**
  [`MoneyHelper.java:59-64`, `:74-82`, `:91-94`] — verbatim the defect T42 raised against T37, and
  T42's correction list names T35/T36/T37 and **not T39**.
- **F39-3 (P2)** — the **threaded** `MathContext` is echoed as *intent* (`c.precision()`/`c.mode()`,
  `CapturePeriodRatio.java:286-287`), never off the object built at `:261`, so assertion 10 is
  tautological with respect to the object handed to `generate`.
- **F39-4 (P2)** — the month-end line citations (`:1429-1434`, `:1426-1436`) do not delimit the
  special case, which is `:1432-1433`; and §3 N-1's prose says `:1509` where its own tag says the
  correct `:1508`.

**`charges` (T40)**

- **A-1 (P1)** — T42 rule 4's **wiring citation is entirely absent** (zero grep hits across the set
  and the handoff), so a Path B ambient reading is presented as the effective `MathContext` with
  nothing tying it to the arithmetic.
- **A-2 (P1)** — D-1's sole citation, `AbstractCumulativeLoanScheduleGenerator.java:504`, is the
  separated-path site the progressive generator has verbatim at `:486` — the one place the two
  generators **agree**; the real evidence is `:392` + `ScheduleCurrentPeriodParams.java:144-145`
  (independently confirmed by me). D-1's conclusion stands; its citation refutes it.
- **A-3 (P1)** — the observed money came from the **request** `amount`, not the attested
  definitions: `{"chargeId":4,"amount":0.001875}` returns `0.41`, not `810.00`; the
  `charges_as_persisted` SHA-256s are not load-bearing for any money value, and **no capture can
  tell which source governs**.
- **A-4 (P1)** — C5 (`totalRepaymentExpected == Σ rows`) is a legitimate *discrimination probe* (it
  produced D-1) but **not an invariant**; shipped in `invariants.py` it is the assertion DEC-1 §9
  forbids, and a **correct** Go port would fail it on 15 of 21.
- **A-5 (P2)** — §11's proof that no half-cent tie exists at that base is false; `0.001875 %` of
  `21,600.00` is exactly `0.405` and the oracle returned **0.41**, supplying the in-charge-arithmetic
  rounding canary T40 declared impossible.
- **A-6 / A-7 / A-8 (P2)** — disbursement-row charge fields serialise at the raw `BigDecimal` scale
  and every tool normalises it away; 15 of 19 `bin/` scripts hard-code an ephemeral worktree path so
  the recipe breaks once it is pruned; and the `c_configuration` row plus the `MoneyHelper` init line
  are counted as two assertions when they are one ambient witness.

**`mathcontext` (T42)** — judged under its own eight-point rule, as the brief required. **The rule is
the right rule and nothing here disturbs it**; applying it to T39 and T40 is what produced F39-2, A-1
and A-8.

- **M-1 (P1)** — N-3's `new MathContext(10, …)` count is **9 published, 5 actual** (the nine cited
  `file:line`s are the union of the four precision-15 and five precision-10 sites), and
  `reference-oracle.md` has already folded in the derived total as **13** where it should be **9**.
  *Found independently by both audit legs.*
- **M-2 (P1)** — N-3's *"every hard-coded `MathContext` outside the loan modules is in
  savings/deposits"* is **false**: `ShareAccountCharge.java:240` is `new MathContext(8, …)` in **share
  accounts**, and precision 8 (also `SavingsAccountCharge.java:562`) is missing from the finding
  entirely. *Both legs.*
- **M-3 (P1)** — the coverage rationale behind E1 is refuted by T42's own data:
  `installmentAmountInMultiplesOf` is dropped by `LoanApplicationTerms.assembleFrom`, so the
  three-argument `Money.roundToMultiplesOf` site was **never reached** — N-1's second half is tagged
  `[VERIFIED … observed]` for an unexecuted site, and 4 of the 13 E1 shapes are byte-identical, giving
  **10 distinct observations, not 13**.
- **M-4 (P1, new oracle fact)** — `LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement`
  (`:56`, `:63`) **also silently drops `installmentAmountInMultiplesOf`**, so the field is honoured or
  lost depending on which production caller builds the schedule. *Stated carefully: the REST
  `calculateLoanSchedule` path via `LoanScheduleAssembler` does honour it — capture `B-02` stands.*
- **M-5 (P2)** — T42 fails its **own ratified rule 2** on capture 1 (214 of 354 cases echo the intent,
  not the object), and capture 1 is the one carrying E1. Capture 2 complies fully. *Both legs.*
- **M-6 … M-11 (P2)** — E3's only machine assertion is a `grep -c`, leaving the same-local-slot claim
  unasserted; "no committed capture is mis-valued" is unqualified where it is ratified and its leg 1 is
  a self-report; `NEGATIVE-TESTS.md` mis-describes which branch N4 fires, so the **vacuity guard has
  never been exercised**; four `file:line` drifts inside `[VERIFIED]` tags; E2's "Path A = 0 cells" is
  a replication of E1's ambient rows; and `controls-output.txt` publishes 2 summary lines rather than
  the 172 cells it claims.

**Cross-cutting**

- **T44-X1 (P2)** — the **Path B captures are float-shaped on the wire**: 9,122 bare unquoted
  non-integer JSON numbers across the charges responses (245 distinct, max scale 6) against **0** in
  every Path A payload, where money is a JSON string. No value is corrupted today (0 of 245), but
  **41 of 245 lose their text** (`"1200000.00" → 1200000.0`), and the rule is *exact text*. Any
  promoted Path B vector must be compared as exact decimal text, never through a JSON number —
  Go's `encoding/json` into `interface{}` yields `float64` by default.

---

## What I re-ran against the live oracle, and what it showed

| leg | result |
|---|---|
| seam source vs the pinned original, all three sets | `sha256 bf397f0b…a80714`, `diff` silent — identical, computed by me |
| full re-execution of `run-periodratio.sh`, fresh `--rm` container | PASS; payload **byte-identical**, `sha256 898435d8…5b3a2` — T39's published digest is real |
| that recipe in a failing configuration | wrong seam sha → **exit 1**; `-Dt39.mathContextRoundingMode=DOWN` (the **threaded** axis) → **exit 1**, 17 named breaches |
| 11 of T40's 21 requests re-issued byte-verbatim + the control | **all byte-identical**, including `XR-01`'s HTTP 403 body |
| T40's preconditions in a failing configuration (tenant `default`) | **exit 1**, five named breaches including the behavioural canary |
| independent re-derivation of the interest column from pinned source | R2 reproduces **131/132**; R1 fails **39/132** — P0-T34-1 confirmed independently |
| independent C1–C10 re-implementation over the charges corpus | matches `INVARIANTS.md` cell for cell |
| both `mathcontext` payloads re-executed, fresh `--rm` containers | **byte-identical** (`f2a037a1…`, `f7ffeb2a…`) |
| T42's negative legs N4 and N5 re-run | both **exit 1** naming the breach |
| Path B wiring re-read off the **deployed bytecode** with an independent `javap` | confirmed — class `d5ef3989…711ea`, local slot 9 → `generate` |
| E1 recomputed by the parent auditor | **11 generated / 2 threw**, the 2 being exactly the 0-dp shapes; the ambient read threw on all 13, so the probe is live |
| provenance sweeps | **110/110** (T39), **> 60** (T40), all E1/E2/§3 numbers and the four cell totals (T42) traced, **0 synthesised** |

---

## What the orchestrator should do

1. **Do not promote anything yet** — G-1 is still open, and promotion is not an audit's call either.
2. **Correct `reference-oracle.md` first, because it already carries two of these.** Its folded-in
   N-3 total of **13** `new MathContext(15|10, …)` should be **9** (4 × precision 15, 5 × precision 10),
   plus **2 × precision 8**, one of them in **share accounts, not savings/deposits** (M-1, M-2). And
   its "no committed capture is mis-valued" needs T42 §7's qualification travelling with it (M-7).
3. **Apply the required changes** before any of these become vectors. The load-bearing ones:
   **F39-1** — relabel the month-end family, and have DEC-1 pin the **packed** whole-months rule
   normatively *alongside* the special case; neither clause is safe stated alone, and T41's F-1
   reached the same seam independently.
   **A-2** — fix D-1's citation (`:392` + `ScheduleCurrentPeriodParams.java:144-145`, not `:504`),
   because ratified decision **C-1 rests on it**.
   **A-3** — the vector fixture is the **request bytes**; the definition row does not govern the money.
   **A-4** — C5 out of the conformance harness; a *correct* port fails it on 15 of 21.
   **M-3** — retag N-1's second half `[UNVERIFIED as behaviour]`.
4. **Add T39 to T42's amended-attestations list** in `reference-oracle.md` — F39-2 is the same defect
   T42 corrected in three other handoffs and missed in the fourth. Fix the threaded echo in both
   `CapturePeriodRatio.java` and `CaptureMathContext.java` (F39-3, M-5); `CaptureMathContext2.java`
   already shows what compliance looks like.
5. **Raise the new `TO_BE_CAPTURED` items:** a **packed-vs-naive whole-months** discriminator, which
   cannot come from the month-end family and must come from `calculatePeriodRatio`'s
   `YEARS`/`WEEKS`/`DAYS` arms; a **charge-arithmetic rounding tie** (A-5 supplies the shape —
   `0.001875 %` of `21,600.00` = `0.405` → oracle `0.41`); the **three-argument
   `Money.roundToMultiplesOf` ambient path**, believed covered and inert (M-3);
   `installmentAmountInMultiplesOf` through the second production caller (M-4);
   `OVERDUE_INSTALLMENT` penalties; `minCap`/`maxCap`; the cumulative generator.
6. **For `patterns.md`:** *when a capture claims to grade behaviour X, name the mis-port a porter would
   actually write and check the corpus against **that**, not against the tidiest alternative.* Both P1s
   in T39 and T42's M-3 are the same error — a null hypothesis chosen for symmetry rather than for
   plausibility. And: *an inventory inside a `[VERIFIED]` transcription is the cheapest thing in the
   program to get wrong and the most expensive to inherit* — M-1 reached `reference-oracle.md`
   unchallenged in one fire.

---

## Unverified

- **My independent model is not a complete specification** — it predicts the *interest* column from
  the previous row's observed balance and does not model the EMI solver or the re-adjust loop. It
  reproduces 131 of 132 interest cells; the one miss is common to all four readings.
  `[VERIFIED for the interest column on these 16 captures; UNVERIFIED as a general model]`
- **R2 ≡ R4 is verified on the swept domain**, not proved — 59,130 pairs, 2023-2025, terms
  {6, 12, 36}, `RepaymentEvery = 1`, MONTHS. `[VERIFIED on the swept domain; UNVERIFIED outside it]`
- **T39's 415/116 and T42's cell totals** are reproduced from committed analysis output; my
  independent counts are different statistics that corroborate direction and sign without
  re-deriving the totals. `[VERIFIED as committed output; UNVERIFIED as an independent recount]`
- **T39's N-2 51,729-pair sweep is uncommitted** and not reproducible from committed files; I did not
  reproduce it, and my own sweep is a different experiment.
- **The `charges` and `mathcontext` legs were run by delegated auditors** on disjoint write surfaces.
  I independently re-verified every finding a ratified artefact rests on — **A-2**, **M-1/M-2**,
  **M-3/M-4**, **M-5**, and E1's 11/2 split — and each held. **A-1, A-3, A-5 … A-8 and M-6 … M-11 I did
  not re-verify myself.** `[VERIFIED on the leg's evidence; UNVERIFIED by the parent auditor]`
- **T44-X1's "0 of 245 change value"** is measured at the magnitudes and scales present in the
  committed charges captures. It must not be read as "floats are safe here" — 41 of 245 already lose
  their *text*, and the rule is exact text.
- **A-3's request-over-definition precedence** is observed on one percentage and one flat charge.
  `[VERIFIED on those two; UNVERIFIED as a general rule]`
- **Generalisation.** These sets grade the shapes they contain and nothing else. Every "blind spot"
  list in the review is a statement about what I could show, not a proof of completeness — assume
  the next audit finds something, as every prior one has, including this one.
