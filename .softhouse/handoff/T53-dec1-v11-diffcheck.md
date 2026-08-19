# T53 — DEC-1 revision 10 → revision 11, the diff-scoped check

Independent reviewer. I did not plan or write revision 11. Scope as briefed: the diff
`ab861fa..ce64da2` over `docs/adr/DEC-1-schedule-generator-adapter.md` and
`nexus/internal/apps/loanschedule/contract/contract.go`, not a ninth full re-derivation.

Environment: pinned Fineract checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb`,
`git status --porcelain` **empty before and after** (re-checked at the end). No Gradle run.
Reference oracle **reachable** this fire (`actuator/health` → `{"status":"UP"}`,
`fineract-fineract-1` up 21 h, `fineract-db-1` up 44 h, PostgreSQL 18.3 only). One **read-only
`SELECT`** was taken; no write, no restart, no re-tenant. **No Go toolchain exists on this host**
(`which go` → not found; `/usr/local/go/bin`, `/opt/homebrew/bin/go`, `~/go/bin` all absent), so
nothing here claims the package compiles.

---

## Verdict

**ACCEPTED WITH REQUIRED CHANGES.** No P0. No P1. **Six P2 errata**, none of which touches a money
statement, a type, a field, an enum member or a graded-domain predicate.

All nine items landed, and — on the checks I could re-derive myself — **landed correctly**. The
arithmetic correction is right, and I recomputed the whole chain in integer minor units from
scratch. The bound held on everything load-bearing: §3.1's predicate block is **byte-identical**,
§4.4's pin *values* are identical, §8 item 1's promotion rule is byte-identical, and every
normative arithmetic section — §4.1.1, §4.3.1, §4.3.2 — plus §4.1, §4.2, §4.7, §4.8, §4.10 and
§4.11 is **byte-identical**. `contract.go` is comment-only, proved a third way. All 47 named
`file:line` citations the diff adds (32 in the ADR, 15 in `contract.go`) are **in range**, and I
opened the load-bearing ones.

The errata are: one inaccurate sentence in the ratifier-facing status line, four bare `:NNN`
citations that mis-resolve under the document's own convention (all of which point at lines that
are *correct* under the intended file — I opened each), one wrong method name, one mis-placed
`[SUPERSEDED]` marker, and one `[UNVERIFIED]` block that **I closed** and that now under-claims.

**I found no reason not to ratify** once these six are applied. I would not ratify with them
in place, because §1 makes the frozen text expensive to amend and P2-T53-1 is a false sentence
about the revision in the paragraph a ratifier reads first — exactly the "known-wrong sentences
are not frozen" argument the driver used to decline revisions 8 and 10.

---

## Item-by-item: did each of the nine land, and land correctly?

### P1-T49-1 — §2.2's component count and §3.2's "exactly" claim — **LANDED, CORRECT**

I counted the components myself against the seam rather than accepting the arithmetic.

Three of the record's 19 components do not survive `assembleFrom(modelData, mc)` →
`Builder.build()` → `toLoanConfigurationDetails()`:

1. `installmentAmountInMultiplesOf` — field at `LoanApplicationTerms.java:217`; **grep over the
   whole file returns exactly one assignment, at `:828`**, inside a positional constructor this
   path never reaches. No Builder setter. [VERIFIED: I opened `:215-219`, `:824-830`, and grepped.]
2. `daysInYearCustomStrategy` — set at `:604`, Builder field `:380`, setter `:567-569`, and the
   private `LoanApplicationTerms(Builder)` copy constructor `:304-351` never copies it out.
   [VERIFIED: I opened `:304-310`, `:325-340`, `:560-582`, `:600-608`.]
3. `interestRecognitionOnDisbursementDate` — **replaced, not dropped**. `assembleFrom` sets it
   (`:603`), the copy constructor *does* copy it out (`:327-328`) — and
   `toLoanConfigurationDetails()` (`:1746-1756`) never reads the field.

So **16 of 19**. The arithmetic is right and I checked it moved consistently: `17 of 19` → `16 of
19` in the §2.2 heading and at `contract.go:50`; "Two of the record's 19 components" → "Three"
(§2.2); "those two inputs" → "those **three** inputs" (§2.2 consequence); "The two components" →
"The **three**" and "exactly the two" → "exactly the three" (§3.2). A grep for `17 of (them|19)`,
`two of the record`, `exactly the two`, `those two inputs` returns **only** the corrective
sentences and the historical bullet that quotes the old wording. **No stale count survives.**

**The positional-argument count re-derived by me, not taken from T52.** `toLoanConfigurationDetails()`
passes 23 arguments (`:1749-1755`); `LoanConfigurationDetails`'s constructor takes 23 parameters
(`:67-76`). Counting position by position, argument 16 is
`isInterestChargedFromDateSameAsDisbursalDateEnabled != null && isInterestChargedFromDateSameAsDisbursalDateEnabled`
[`LoanApplicationTerms.java:1753`] and parameter 16 is `boolean interestRecognitionOnDisbursementDate`
[`LoanConfigurationDetails.java:72`], assigned at `:92`, returned by
`isInterestRecognitionOnDisbursementDate()` at `:201-203`. **23 = 23, and 16 = 16.** [VERIFIED by
opening both files.]

**§3.2's third bullet states its pin as a §4.4 pin, not a §3.1 predicate** — required by T49, and
it does, explicitly: *"Note the asymmetry deliberately: this one is pinned by two §4.4 PINS rather
than by a §3.1 predicate — the same materially weaker reason §4.1.2 already records for
`Money.java:130-132`. A future reader relaxing either pin must re-derive this bullet."* That is the
honest form, and the "strengthened rather than weakened" framing is defensible **because** it is
carried with that caveat: the claim moved from "the two dropped inputs are pinned" to "every input
the seam fails to deliver is pinned", which now rests on three pins. Nothing licenses less.

I re-derived the two gates myself rather than taking them:

- `ProgressiveEMICalculator.java:1579` is inside `getFractionPeriodDueDateForEndOfYear` (`:1578-1584`),
  which has **exactly one caller** — `:1560`, inside `calculatePeriodFractions` — reached only from
  `:1527`, under `if (partialPeriodCalculationNeeded)` whose first conjunct is
  `daysInYearType == DaysInYearType.ACTUAL` (`:1505-1507`). §3.1 pins `DayCountFixed30Over360`.
  **Gated shut.** [VERIFIED: grep for all callers + `:1500-1512`, `:1524-1540`, `:1545-1568`, `:1574-1590`.]
- `:194` is inside `buildLoanApplicationTerms`, whose **only caller** is `:167`, inside
  `addFullTermTrancheDisbursement`, whose **only caller** is `:144`, under
  `isAllowFullTermForTranche() && numberOfRepayments > 0 && action == DISBURSEMENT` (`:142-143`).
  §4.4 pins `allowFullTermForTranche = false`. **Gated shut.** [VERIFIED: grep for all callers.]

### B-1 — the alias crosses configuration scopes — **LANDED, CORRECT, AND THE DISTINCTION SURVIVES EVERYWHERE**

The scope-crossing is real and I verified both ends:

- `isInterestChargedFromDateSameAsDisbursalDateEnabled` comes from
  `this.configurationDomainService.isInterestChargedFromDateSameAsDisbursementDate()`
  [`LoanScheduleAssembler.java:370-371`], key
  `interest-charged-from-date-same-as-disbursal-date` [`GlobalConfigurationConstants.java:45`],
  handed to the long positional `assembleFrom` at [`LoanScheduleAssembler.java:559`].
- `interestRecognitionOnDisbursementDate` is
  `loanProduct.getLoanProductRelatedDetail().isInterestRecognitionOnDisbursementDate()` with a
  **per-request override** [`LoanScheduleAssembler.java:537-541`], and
  `LoanProductConstants.INTEREST_RECOGNITION_ON_DISBURSEMENT_DATE` is in
  `LoanScheduleValidator.java:78`'s supported-parameter set.
- The alias field is assigned **only** at `LoanApplicationTerms.java:847`
  [VERIFIED: grep returns exactly one `this.` assignment], in a positional constructor the Path-A
  assembler never reaches. It is `Boolean` (`:236`), so on Path A it is `null` → `:1753` yields
  **`false` unconditionally**.

So a port genuinely **cannot** fix this by wiring "the other product field". Confirmed.

**The live-slot / inert-setting distinction survives every place it was written, and I checked
each one for collapse.** The four sites are §2.2, §4.4's table row, §6.7, and `contract.go`'s
`GenerateRequest` pinned-inputs list. All four state **both** results and label them:

- §2.2: *"What was observed, and it is two separate results that must not be collapsed. **The slot
  is LIVE.** … 79 of 153 cells … 52 of 164 cells … **The product setting is INERT.** … 0 differing
  cells … eight shapes …"*
- §4.4: *"…the product/request setting moving 0 cells on 8 shapes across both readers…"* alongside
  the porting rule and the 6-of-6 boundary result.
- §6.7: *"…the field it is named for is a per-product, per-request setting that observably moves
  nothing… Exposing the product setting would put a field in the contract that changes no money;
  exposing the global setting would put a tenant configuration value into a per-request contract."*
- `contract.go` (`GenerateRequest` pinned inputs): *"THE SLOT IS LIVE (79 of 153 and 52 of 164
  cells against its own controls) AND THE PRODUCT SETTING IS INERT."*

**No site collapses the two.** I looked specifically for a sentence that says only "the setting
moves nothing" without the live-slot half, and found none.

Every number cross-checked against the source handoff:
79 of 153 with `interestDue 21245.90 → 21304.11`; 52 of 164 with `loanTermInDays 242 → 181`;
20 compared SQL columns on products 17/18; 0 differing cells on 8 shapes; 31 December on **6 of 6**
and 1 January on **0 of 6**, product flag `true` on half; four `R13` crossing periods
discriminating nothing; Path-A2 twins 35 of 115 against Path-A's 0 of 87.
[VERIFIED: `.softhouse/handoff/T51-alias-and-tranche-captures.md` lines 23-25, 131, 151, 161-163,
185-189, 211-212, 262-264; `.softhouse/handoff/T48-actualactual-captures.md` lines 96, 283, 369.]

### P1-T49-2 — the false ACT/ACT claims — **LANDED AT ALL THREE SITES; MY OWN GREP FINDS NO FOURTH**

Three sites corrected: §4.9, `contract.go`'s `DayCountActualActual` comment, and `contract.go`'s
`FrequencyYears` comment (the third leak T52's own grep found). I ran an independent grep over
both artefacts for
`un-re-derived|not been re-derived|no independent re-derivation|no capture (in )?the corpus|nobody
has compared|plausible numbers|until a capture exists|largest .* hole`.

**Every hit is either the corrective sentence itself, a historical statement explicitly framed as
what an earlier revision said, or unrelated** (`contract.go:188` "No capture in the corpus varies
it" about `MinorUnitDigits`; `:265` about a different field; §4.10's "revision 4 flagged that arm …
and **revision 5 retires that caveat**", which is correct history). **No fourth live leak.**

**The refusal is unchanged and only the stated reason moved.** Proved mechanically:
`DayCountActualActual` and `ErrNoDiscriminatingVector` both survive in the **non-comment** code,
and the non-comment code is byte-identical between revisions 10 and 11 (see below). The new
grounds are the right ones — *captured is not promoted* (§8 item 1, which is **byte-identical**
across the revision) and the §4.4 `daysInYearCustomStrategy` amendment.

### P1-T49-3 — the arithmetic — **LANDED, CORRECT; I RE-DERIVED THE WHOLE CHAIN**

See *Re-derivations I performed* below. `2,160,000 × 21,875 = 47,250,000,000` is right,
`472,500,000` is right for the **major**-unit multiplicand `21,600`, `4.73`/`2.03`/`HALF_UP` are
unchanged and I confirmed them independently, and **no floating point entered the corrected text**
(the whole chain is integer multiplication and division by powers of ten).

### P2-T49-4 — "eight capture sets" — **LANDED; ALL EIGHT DIRECTORIES EXIST**

`ls .softhouse/capture/*/` returns exactly nine entries: `actualactual`, `audit-t44`, `charges`,
`dec1-binding`, `mathcontext`, `out`, `pathb`, `periodratio` — the eight named — plus `src`, which
is not claimed as a capture set. Sub-artefacts cited by the new text also exist:
`mathcontext/out/t50-tier1.json`, `t50-tier2.json`, `t50-tier1-assert.txt`, `t50-tier2-assert.txt`,
`out/negative/`; `charges/out/t46/`, `t48/`, `t51/`;
`actualactual/{ATTESTATION,PROVENANCE,REPRODUCE}.md`. The two "same directory now also holds"
claims check out: `periodratio/ATTESTATION-T46.md` exists, and `charges/out/` holds `t46`, `t48`
and `t51`.

### P2-T49-5 — omitting `amount` is HTTP 400 on 5 of 5 — **LANDED AT EVERY SITE THAT MADE THE OLD CLAIM**

Four sites: §4.5.1 fact 4 (the "untried by every capture" clause **deleted**), §4.5.1's blind-spot
bullet, §8 item 9(g), and revision 10's own history bullet, which carries
`[SUPERSEDED IN REVISION 11: …]`. A grep for `untried by every capture|untried by EVERY` returns
only the corrective text and that marked history entry. Underlying observation verified in
`T48-actualactual-captures.md` line 204: HTTP 400 on **5 of 5** legs, `chargeTimeType` 1, 2, 8, 12,
`FLAT` and `PERCENT_OF_AMOUNT`, `validation.msg.loan.charges.amount.cannot.be.blank`.

### P2-T49-6 — §8 item 5's CAPTURED status and T48-N4's trap — **LANDED, AND STATED IN A FORM A HARNESS AUTHOR CANNOT MISS**

§8 item 5 gains `**STATUS: CAPTURED, NOT YET PROMOTED**` in its first line, and the trap is a
separate emphasised paragraph, repeated verbatim in `contract.go` under `DayCountActualActual`:

> **ANY VECTOR PROMOTED FOR THIS ARM MUST CROSS A LEAP-YEAR BOUNDARY WITH A NON-ZERO FIRST SEGMENT.**

I checked the condition is **complete**, not just present. T48 records *two* coincidence traps:
equal-length years, **and** a period starting on 31 December (first segment zero days, so `f`
collapses to `days / L(endYear)`) [`T48-actualactual-captures.md` §6]. The ADR's condition —
"cross a leap-year boundary **with a non-zero first segment**" — excludes **both**. Correct.

**T49's rejected hypothesis was not "fixed".** §8 item 5 reads: *"The vectors remain outstanding
and **this item is not false as written** — it asks for vectors, no vector is promoted, and
'captured is not promoted' is this document's own discipline (item 1)."* T52 did not go in the
rejected direction.

### B-2 — N46-1 / N46-3: is this an ERRATUM or an AMENDMENT? — **T52'S JUDGEMENT IS SOUND**

This is the load-bearing call of the pass and I tested it rather than accepting it.

The question is whether admitting the finding forces a **graded-domain predicate** to move. It does
not, for three independent reasons, each of which I verified at source:

1. **The N46-1 loci are unreachable on the graded path.** The two charge sites are
   `ProgressiveLoanScheduleGenerator.java:445-446` and `:464-465`, inside `calculateInstallmentCharge`
   (`:433-452`) and `calculateSpecificDueDateChargeWithPercentage` (`:454-468`). Both are reachable
   only from the `:87` overload. The Path-A entry point at `:81-84` delegates
   `generate(mc, loanApplicationTerms, null, null)` at `:83` — **`loanCharges` hard-wired `null`**.
   [VERIFIED: I opened `:78-92` and `:430-470`.] `GenerateRequest` carries no charge.
2. **The N46-3 sites are all down-payment computations** and `DownPaymentPercentage` is pinned to
   `Rate{0, 1}`. At 0 %, `MathUtil.percentageOf(principal, 0, …)` is exactly zero and no rounding
   decision exists, whatever mode governs.
3. **On the shipped server the two contexts are one object.** `LoanScheduleAssembler:753` reads
   `MoneyHelper.getMathContext()` and `:765` threads *that same reference*; `getMathContext()`
   serves one instance per tenant from `mathContextCache.computeIfAbsent(...)`
   [`MoneyHelper.java:91-93`]. [VERIFIED: I opened all three.] So the two modes are always equal on
   the oracle and nothing Fineract produces is wrong.

§4.1's decision — `Rounding{SignificantDigits, RateFactorScale, Mode}`, one `Mode` — therefore
remains sufficient, and §4.1 is **byte-identical** across the revision. **No predicate moves.
Erratum, not amendment. Ratification does not need a gate on this account.**

I also checked the *mechanism* the new text asserts, because it is the sharp claim: the two-argument
`Money.of(MonetaryCurrency, BigDecimal)` [`Money.java:114-116`] supplies
`MoneyHelper.getMathContext()` at `:115`; the constructor stores it (`:42`) and the scale-2
quantisation at `:52` reads it back through `getMc()` (`:494-496`). So `:52` takes the **ambient**
mode here **because the two-argument factory put the ambient context in the field** — the threaded
`mc` at `:446` is consumed only inside the `divide`. The §9 citation string
[`Money.java:52`, `:494-496`, `:40`, `:42`] is exactly the right four lines for that mechanism.
`MathUtil.percentageOf(value, percentage, int precision)` at `:472-473` builds
`new MathContext(precision, MoneyHelper.getRoundingMode())` — ambient mode, pinned precision —
so "two overloads of one helper are two specifications" is a correct reading of the source.
`MoneyHelper.initializeTenantRoundingMode` is `public static` over a `ConcurrentHashMap` (`:54-64`)
and `getRoundingMode()` throws `IllegalStateException` for an uninitialised tenant (`:79`), so
T50's in-process separation and its vacuity canary are both mechanically possible.

T50's published figures cross-check: 2016 + 1400 = **3,416** cells; S1/S6 and L1/L2 at **7/7**
ambient against **0/7** threaded; MNT-scale pair `1005025.12` vs `1005025.13` (S1/V4, L1/W4);
42/42 and 35/35 absence cases throwing; the three-argument `Money.of` counterfactual (S2)
completing **42/42**; **9** corruption rejections (N1…N9). [VERIFIED:
`.softhouse/handoff/T50-ambient-vs-threaded-rounding.md` lines 15, 17-18, 112, 140-176, 202,
212-245, 357-365.]

### B-3 — T50-N1 as backlog, T50-N2 in five places — **LANDED; THE FREEZE ARGUMENT IS CONSISTENT**

**T50-N1** is filed as §8 item **4a** plus a §4.1.2 hazard bullet, and both say in terms that the
graded domain is **not** enlarged: *"revision 11 records it here and in §8 item 4 and does not
enlarge the domain to accommodate it"*. §3.1 is byte-identical, which is the mechanical proof that
it did not. I verified the source claim: `LoanApplicationTerms`'s Builder constructor threads
`builder.mc` through all three operations (`:329-338` — guard `:329`, threaded `Money.of` `:330-332`,
multiple `:334`, `else` `:337`) while the positional constructor is fully ambient (`:863`
one-argument `Money.zero`, `:865-866` `percentageOf(…, 19)` inside a two-argument `Money.of`,
`:868` two-argument `roundToMultiplesOf`), and `LoanScheduleAssembler.java:548` calls the long
positional `assembleFrom`. **Correct as written.**

**T50-N2** landed in §2.2, §3.2, §4.5, §4.5.1's blind-spot list, §8 item 9, §9 and `contract.go`'s
package doc — seven places, at least the five claimed.

**I specifically checked §2.2 / §3.2 / §5 for the contradiction the brief warned about, and there
is none.** §3.2's freeze licence still reads *"a Path-A capture grades everything the request
carries"*, which is **exactly true** of `GenerateRequest` as frozen, and the added paragraph says
it *"would **stop** being true of any future request shape that did [carry a charge]"* — which is
the sharper claim, not a contradiction. §5's admissibility paragraph is unchanged and still points
at §2.2, §3.2 and §4.5 for the blind spots. The weaker "the request record carries no charge"
phrasing survives in §4.1.2, §4.3.2, §4.5.1's closing and one `contract.go` comment — but in every
one of those the sentence is **true**, is doing a different job (P4 / the M4-M5 table / "nothing
here moves the contract"), and the structural form is present in every section that licenses the
freeze. **No contradiction found.**

---

## Re-derivations I performed

### 1. The corrected charge chain, from scratch, in integer minor units

Period-1 interest `21,600.00` = **2,160,000** minor units. Percentage `0.021875 %` = integer
**21,875** scaled by `10^6`. Charge = `amount × pct ÷ 100`:

```
2,160,000 × 21,875
  = 2,160,000 × 20,000  =  43,200,000,000
  + 2,160,000 ×  1,875  =   4,050,000,000
  ------------------------------------------
                        =  47,250,000,000      <-- revision 11's value. CORRECT.
47,250,000,000 ÷ 10^6 ÷ 100  =  47,250,000,000 ÷ 10^8  =  472.5   minor units
```

`472.5` is **exactly half a minor unit above 472**. `HALF_UP` → **473** minor = **`4.73`**;
`HALF_EVEN` → 472 (even) = `4.72`. The oracle returned `4.73`. Correct.

```
2,160,000 ×  9,375
  = 2,160,000 × 9,000   =  19,440,000,000
  + 2,160,000 ×   375   =     810,000,000
  ------------------------------------------
                        =  20,250,000,000
20,250,000,000 ÷ 10^8   =  202.5  minor units → HALF_UP 203 = `2.03`; HALF_EVEN 202 = `2.02`
```

The oracle returned `2.03`. Correct.

Major-unit form, which is what the oracle's `BigDecimal`s actually carry:
`21,600 × 21,875 = 472,500,000`, `÷ 10^8 = 4.725`; `21,600 × 9,375 = 202,500,000`, `÷ 10^8 = 2.025`.
Correct.

**So revision 10's `2,160,000 × 21,875 = 472,500,000` was wrong by exactly a factor of 100, and
`472,500,000` is precisely the major-unit product — revision 11's diagnosis is right, not merely
its correction.** The chain as rewritten is integer throughout; no floating-point value appears in
it. The only number that changed is the intermediate; `4.73`, `2.03` and `HALF_UP` are unchanged
and I reproduced all three.

I also checked the chain against the source it claims to describe: at
`ProgressiveLoanScheduleGenerator.java:445-446` the oracle computes
`amount.multiply(loanCharge.getPercentage()).divide(BigDecimal.valueOf(100), mc)` — the multiply is
**exact** (no `mc`), the divide is at precision 19 where `4.725` is representable exactly, and the
two-argument `Money.of` then quantises at `Money.java:52`. **No rounding loss before the tie, so
the tie is genuine and the mode is what decides it.** The ADR's account is faithful.

### 2. T48-N4's trap, derived independently

`calculatePeriodFractions` (`:1550-1568`) walks calendar years accumulating
`days(segment) ÷ Year.of(y).length()`, with the interior boundary supplied by
`getFractionPeriodDueDateForEndOfYear` — **1 January of the next year** (`:1580`) or
**31 December** (`:1582`). The segments **telescope** under either choice, so the total day count
is the same; therefore *when every year touched has the same length*, both boundary choices give
`Σ dᵢ / L = (Σ dᵢ) / L`, which is also what the plain branch computes
(`rateFactorByRepaymentPeriod(interestRate, actualDaysInPeriod, ONE, daysInYear, ONE, ONE, mc)`,
`:1950-1963`). **Both the flag and the arm become invisible together.** That is the mechanism, and
it independently explains T51's `R13` rows: `16/365 + 366/366 + 15/365` versus
`17/365 + 366/366 + 14/365` — a day moves from 2025's bucket into 2023's, both denominators 365,
so the sum is unchanged and both readings return `281214.25`. The ADR's "that is T48-N4's trap
reappearing" is a correct identification of the same identity.

*Stated precisely, because "coincide exactly" deserves it:* the identity is exact **as rationals**,
and the two arms perform different numbers of `divide(…, mc)` roundings at 19 significant digits,
so what is guaranteed is agreement of the rationals plus agreement to 19 significant digits in
practice. T48 states it the same way and backs it with an observation
(`T48-CAL-S5`, `oracleRateFactorMatchesExactRederivation = true`). I raise no finding; a reader
should simply not read "exactly" as a claim of bit-identity across a differing number of roundings.

### 3. The positional-argument alignment

23 arguments at `LoanApplicationTerms.java:1749-1755` against 23 parameters at
`LoanConfigurationDetails.java:67-76`, counted position by position by me. Position 16 on both
sides. Reported above.

### 4. `16 of 19`

19 components; 3 do not survive (one unreachable through the Builder, one not copied out of the
Builder, one silently replaced downstream). 19 − 3 = 16. Correct.

---

## The bound: did anything move that should not have?

**Nothing did.** Section-level hashing of the whole ADR (v10 vs v11):

**Byte-identical (19 sections):** §1, §2, §2.1, **§3.1**, §3, §3.3, §4, **§4.1**, **§4.1.1
(normative)**, §4.2, §4.3, **§4.3.1 (normative)**, **§4.3.2 (normative)**, §4.6, §4.7, §4.8,
§4.10, §4.11, §7.

**Changed (10 sections):** §2.2, §3.2, §4.1.2, §4.4, §4.5, §4.5.1, §4.9, §5, §6, §8, §9.
(§2.2's heading is the `17`→`16` correction, so it registers as renamed.)

Within the changed sections I checked the things that must not move:

- **§3.1's predicate block: byte-identical** (`sha256 5856aa17f32f…`, both).
- **§4.4's pin table: name and value columns identical**, six rows,
  `false / true / false / null / null / null`. Only one row's justification text grew.
- **§8 item 1 (the promotion rule): byte-identical.**
- **§4.1.2's normative rule sentence** ("which `MathContext` scales a value … is decided by the
  construction, never by the arithmetic that produced the value") is in the diff's **context**
  lines, not its changed lines — unchanged.
- **No type, field, enum member or graded-domain predicate moved** in `contract.go` — proved
  mechanically below, not asserted.

**"Exactly one number changed" is FALSE as literally written, and that is P2-T53-1.** The diff
changes at least four numeric facts: `472,500,000` → `47,250,000,000` (§4.5.1); `17 of 19` →
`16 of 19` (§2.2 heading, `contract.go:50`); `two` → `three` dropped components (§2.2 ×2, §3.2 ×2);
`FIVE` → `EIGHT` capture sets (§5 ×2). Three of those four were **required by T49** (P1-T49-1,
P2-T49-1), so they are sanctioned changes, not a breach of the bound — but the sentence a ratifier
reads first says they did not happen. The narrower claim in the very next clause — **"No number a
Go port must produce changes"** — is the one I checked and it is **true**.

Mechanical corroboration: over the ADR diff, the only numeric token present in removed text and
absent from added text is `202,500,000` — the old major-unit intermediate, which the rewritten
chain expresses differently. (`47,` is a tokenizer artefact from the task id `T47,`.)

---

## `contract.go` comment-only: how I checked

Three ways, the third independent of the first two.

1. **Line-class filter over the diff.** Strip `+`/`-`, trim leading whitespace, drop lines that are
   blank or begin with `//`. **0 lines remain**, added or removed.
2. **No block comments exist.** `grep -c '/\*'` returns **0** in both revisions, so a `/* … */`
   cannot be hiding code from check 1.
3. **A string-aware Go lexer, written for this review.** I extracted both blobs
   (`git show ab861fa:… > /tmp/cg_v10.go`, `ce64da2:… > /tmp/cg_v11.go`; 2416 vs 2547 lines) and ran
   a tokenizer that tracks interpreted strings, raw strings and rune literals — so a `//` inside a
   string cannot be mistaken for a comment — stripping comments and blank lines and trimming
   trailing whitespace. Result:

   ```
   /tmp/cg_v10.go  96 non-comment lines
   /tmp/cg_v11.go  96 non-comment lines
   81f30828f092c659bec3b001040b049527a7261a8cf3ee53d63316286c5f6011  cg_v10.stripped
   81f30828f092c659bec3b001040b049527a7261a8cf3ee53d63316286c5f6011  cg_v11.stripped
   diff → IDENTICAL
   ```

   **Same sha256. 96 = 96.** `DayCountActualActual` (line 32 of the stripped file) and
   `ErrNoDiscriminatingVector` (line 94) both survive unchanged.

This confirms T52's claim and the driver's independent parse, by a method that does not share their
failure mode.

**I did not and cannot claim the package compiles.** No Go toolchain exists on this host. Static
reasoning only: the non-comment code is byte-identical to a revision that was previously accepted,
so if revision 10 compiled, revision 11 compiles. That is an inference from identity, not a build.

---

## Citations added, and the lines I opened

I ran a per-line resolver over the added text of both artefacts and then opened the load-bearing
ones by hand in the pinned checkout.

**Named citations (`File.java:NNN`) added by the diff: 32 in the ADR, 15 in `contract.go`.
ALL 47 IN RANGE. 0 out of range.** T49's record is not broken on named citations.

Opened and confirmed to say what they are cited for:

| Citation | Cited for | Verdict |
|---|---|---|
| `LoanApplicationTerms.java:217`, `:828` | field exists, sole assignment in a positional ctor | correct |
| `LoanApplicationTerms.java:304-351`, `:325-340` | private Builder copy ctor; `:327-328` copies the flag out | correct |
| `LoanApplicationTerms.java:329-338`, `:863-869` | threaded vs ambient down payment | correct (guard `:329`, `Money.of` `:330-332`, `:334`, `else` `:337`; `Money.zero` `:863`, `percentageOf(…,19)` `:866`, `roundToMultiplesOf` `:868`) |
| `LoanApplicationTerms.java:379`, `:508-509`, `:603` | Builder field, setter, `assembleFrom` sets it | correct |
| `LoanApplicationTerms.java:563-565`, `:579` | `build()` → `new LoanApplicationTerms(this)`; the seam's `assembleFrom` | correct |
| `LoanApplicationTerms.java:847` | **sole** assignment of the alias | correct (grep: exactly one) |
| `LoanApplicationTerms.java:880`, `:1740`, `:1746-1756`, `:1753` | 2 assignments, 1 read, the alias in slot 16 | correct line-wise; **method name wrong — see P2-T53-4** |
| `LoanConfigurationDetails.java:72`, `:92`, `:201-203` | param 16, assignment, getter | correct |
| `LoanScheduleAssembler.java:370-371`, `:537-541`, `:548`, `:559`, `:753`, `:765` | global read, product+override, positional call, the flag passed, ambient read, threaded pass | correct, all six |
| `GlobalConfigurationConstants.java:45` | the key string | correct, verbatim |
| `LoanScheduleValidator.java:78` | supported request parameter | correct |
| `ProgressiveEMICalculator.java:142-143`, `:167`, `:194` | tranche guard, sole caller, the second reader | correct |
| `ProgressiveEMICalculator.java:1505-1507`, `:1526-1531`, `:1533-1539` | the ACTUAL conjunct, the partial arm, the plain switch | correct |
| `ProgressiveEMICalculator.java:1550-1568`, `:1578-1584`, `:1580`, `:1582`, `:1969-1980` | fractions, boundary, 1 Jan, 31 Dec, partial rate factor | correct, all five |
| `ProgressiveLoanScheduleGenerator.java:81-84`, `:83`, `:87`, `:433-452`, `:445-446`, `:454-468`, `:464-465` | entry point, the literal `null`, the overload, both charge methods and both loci | correct, all seven |
| `MoneyHelper.java:54-64`, `:79`, `:91-93` | public static initialiser, the throw, per-tenant cache | correct |
| `Money.java:40`, `:42`, `:48-51`, `:52`, `:114-116`, `:115`, `:154`, `:494-496` | ctor, the stored `mc`, the 0-dp gate, the quantisation, the 2-arg factory, its ambient read, the hard-coded ambient, `getMc()` | correct, all eight |
| `MathUtil.java:472-473` | the `int` overload building the ambient `MathContext` | correct |

**Bare `:NNN` citations: 71 resolve in range against a same-line anchor; 4 mis-resolve** (P2-T53-2)
**and 2 more have no anchor at all on their line** (P2-T53-3). All six point at lines that are
**correct under the intended file** — I opened each. So there is **no false statement about the
source**, only ambiguity.

One small point in revision 11's favour: the ADR cites `calculateInstallmentCharge` as `:433-452`,
which is right (the signature begins at 433); **T50's own handoff writes `[:432-452]`, which is off
by one.** Revision 11 did not inherit the error.

---

## Restatement grep (my own, not T52's)

Seven greps over both artefacts, run by me:

| # | Pattern | Live stale hits |
|---|---|---|
| 1 | `un-re-derived`, `no independent re-derivation`, `no capture in the corpus`, `nobody has compared`, `plausible numbers`, `until a capture exists`, `largest .* hole` | **0** |
| 2 | `17 of (them\|19)`, `honours 17`, `two of the record`, `exactly the two`, `those two inputs`, `the two components` | **0** |
| 3 | `five capture sets`, `FIVE capture`, `none of the five` | **0** |
| 4 | `untried by every capture`, `omits .amount. entirely`, `m_charge.amount governs when` | **0** |
| 5 | `tenant write`, `written to differ`, `re-tenant` | **0 live** — all hits are the refutation, or history carrying `[SUPERSEDED IN REVISION 11]` |
| 6 | `TO_BE_CAPTURED` | **0 live for 9(h)/N46-1** — §8 item 9(h) reads CLOSED; the remaining ones are (a)–(e), genuinely open. One placement wart: see P2-T53-5 |
| 7 | `request record carries no charge` | 4 residual sites, **all true and all doing a different job**; the structural form is present in every freeze-licensing section |

**No fourth leak.**

---

## The two open items — closed or still open

### 1. The tenant-global flag value — **CLOSED. It is FALSE.**

The oracle was reachable, so I took the read-only measurement T52 could not.

```
$ curl -sk https://localhost:8443/fineract-provider/actuator/health
{"status":"UP","groups":["liveness","readiness"]}
$ docker ps
fineract-fineract-1   Up 21 hours (healthy)   fineract:latest
fineract-db-1         Up 44 hours (healthy)   postgres:18.3
$ docker exec fineract-db-1 psql -U postgres -Atc "select datname from pg_database order by 1;"
fineract_default / fineract_gerege / fineract_tenants / postgres / root / template0 / template1
$ docker exec fineract-db-1 psql -U postgres -d fineract_gerege -Atc \
    "select name, enabled, value, date_value, string_value from c_configuration
     where name = 'interest-charged-from-date-same-as-disbursal-date';"
interest-charged-from-date-same-as-disbursal-date|f|0||
```

`enabled = f`. And the flag is read as `property.isEnabled()`:

```java
// ConfigurationDomainServiceJpa.java:296-300
public boolean isInterestChargedFromDateSameAsDisbursementDate() {
    final GlobalConfigurationPropertyData property = getGlobalConfigurationPropertyData(
            GlobalConfigurationConstants.INTEREST_CHARGED_FROM_DATE_SAME_AS_DISBURSAL_DATE);
    return property.isEnabled();
}
```

**So `isInterestChargedFromDateSameAsDisbursalDateEnabled` is `false` on the `gerege` tenant**,
`LoanApplicationTerms.java:1753` yields `false`, and `getFractionPeriodDueDateForEndOfYear` takes
the **31 December** branch at `ProgressiveEMICalculator.java:1582`. That is **exactly** the branch
T51 observed on **6 of 6** discriminating crossing periods. The inference is now a measurement,
and revision 11's `[UNVERIFIED]` block in §2.2 **under-claims**. See P2-T53-6.

**Discipline observed as instructed.** PostgreSQL only. One `SELECT`, no `INSERT`/`UPDATE`/`DELETE`,
no schema change, no restart, no re-tenant. Before/after counts taken and **identical**:
`c_configuration` **74 → 74**, `m_product_loan` **21 → 21**, `m_charge` **18 → 18**; containers
unchanged (`Up 21 hours` / `Up 44 hours`, no restart). Pinned checkout `git status --porcelain`
**empty before and after**, HEAD still `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

### 2. `go build` — **STILL OPEN. Environment gap, not a defect.**

`which go` → not found. `/usr/local/go/bin`, `/opt/homebrew/bin/go`, `~/go/bin` all absent. No
toolchain to install one from within scope. **I make no claim that the package compiles**, and I do
not hold this against T52. What I *can* say is stronger than a heuristic: the **non-comment content
of `contract.go` is byte-identical** to revision 10's (same sha256 after a string-aware comment
strip), so compilation status is unchanged by this revision, whatever it is.

---

## P0

**None.** No false money statement, no un-derived arithmetic, no moved predicate, no promoted
vector, no contract change.

---

## P1

**None.**

---

## P2

### P2-T53-1 — the status line says the revision changed one number; it changed four

**Exact sentence** (§ Status, line 3):

> It changes exactly ONE number, and that number is an arithmetic error rather than a rule:
> revision 10's own worked check in §4.5.1 asserted `2,160,000 × 21,875 = 472,500,000`, which is
> wrong by a factor of 100, and revision 11 corrects it to `47,250,000,000`.

**Why it is wrong.** Revision 11 also changes `17 of 19` → `16 of 19` (§2.2 heading and
`contract.go:50`), `two` → `three` dropped components (§2.2 twice, §3.2 twice), and `FIVE` →
`EIGHT` capture sets (§5 twice). The revision-11 bullet three paragraphs below says so itself
("§2.2's heading said the seam honours **17 of 19** … Both are false"; "§5 said **FIVE** capture
sets exist; there are **eight**"), so the status line is contradicted inside its own section. The
three count corrections were **required** by T49, so nothing improper happened — but this is the
paragraph a ratifier reads first, and §1 makes it expensive to fix after freezing. It is the same
class prior rounds graded in P2-T43-2 and P2-T49-1.

**Replacement text:**

> It changes exactly one number **in the arithmetic**, and that number is an arithmetic error
> rather than a rule: revision 10's own worked check in §4.5.1 asserted
> `2,160,000 × 21,875 = 472,500,000`, which is wrong by a factor of 100, and revision 11 corrects
> it to `47,250,000,000`. **Three counts of the evidence also change, each because a review
> required it**: the seam honours **16** of 19 components rather than 17 and fails to deliver
> **three** rather than two (T49's P1-T49-1), and **eight** capture sets exist rather than five
> (T49's P2-T49-1). **No number a Go port must produce changes.**

### P2-T53-2 — four bare `:NNN` citations added by revision 11 mis-resolve under the document's own convention

All four point at the **right line of the right file**; the defect is that the *written* citation
resolves to a different file under the last-named-file convention this document otherwise follows.
T49's audit recorded **0 ambiguous**; revision 11 breaks that record in five places (four in the
ADR, one in `contract.go`).

**(a) `:559` after `GlobalConfigurationConstants.java:45` — three sites in the ADR plus one in
`contract.go`.** Exact form (§4.4's table row; §2.2's revision-history bullet and §9's
aliased-input obligation carry the same construct):

> [`LoanScheduleAssembler.java:370-371`, key at `GlobalConfigurationConstants.java:45`, passed at `:559`]

`GlobalConfigurationConstants.java` is **99 lines**, so `:559` cannot be in it. The intended and
correct target is `LoanScheduleAssembler.java:559` — I opened it; it is where the flag is passed
into the long positional `assembleFrom`.

**Replacement** — spell the file out, in all four places:

> [`LoanScheduleAssembler.java:370-371`, key at `GlobalConfigurationConstants.java:45`, passed at `LoanScheduleAssembler.java:559`]

**(b) `:847` after `LoanConfigurationDetails.java:72` — §4.4's table row.** Exact form:

> [`LoanConfigurationDetails.java:72`, assigned `:92`, returned `:201-203`]. On **Path A** that
> alias is assigned only at [`:847`], unreachable through this assembler

`LoanConfigurationDetails.java` is **210 lines**. The intended and correct target is
`LoanApplicationTerms.java:847` — I opened it; grep confirms it is the sole assignment.
§2.2 and §9 both spell this one out in full; only §4.4 is bare.

**Replacement:** `…assigned only at [`LoanApplicationTerms.java:847`], unreachable through this
assembler…`

### P2-T53-3 — two added citations in §4.5.1 have no file anchor on their line, and the nearest named classes are the wrong ones

**Exact sentence** (§4.5.1, "What T50 observed at this locus"):

> Across **3,416 published cells** — 2,016 transcribing the site expressions against the oracle's
> own `Money`/`MoneyHelper` classes and 1,400 entering `calculateInstallmentCharge` [`:433-452`]
> and `calculateSpecificDueDateChargeWithPercentage` [`:454-468`] themselves by reflection

The nearest named classes on the line are `Money` and `MoneyHelper`; `MoneyHelper.java` is **190
lines**, so both ranges are out of range under that reading. The intended and correct file is
`ProgressiveLoanScheduleGenerator.java`, and both ranges are right there — I opened `:430-470`.

**Replacement:** `…entering `calculateInstallmentCharge`
[`ProgressiveLoanScheduleGenerator.java:433-452`] and
`calculateSpecificDueDateChargeWithPercentage` [`:454-468`] themselves by reflection…`

### P2-T53-4 — §2.2 names a method that does not exist

**Exact clause** (§2.2, the `interestRecognitionOnDisbursementDate` table row):

> over the whole class the field is *assigned* twice — at `:327-328` from the Builder and at `:880`
> in the positional constructor — and *read* exactly once, by `getLoanProductRelatedDetail()` at
> `:1740`, which is a different method

`grep -c 'getLoanProductRelatedDetail' LoanApplicationTerms.java` returns **0**. The method that
contains line 1740 is **`toLoanProductRelatedDetail()`**, declared at `:1727`.
(`getLoanProductRelatedDetail()` does exist — on `LoanProduct`, called from
`LoanScheduleAssembler.java:366`, `:537` and `:557` — which is precisely why the wrong name here is
confusing in a paragraph about which object holds what.) The line number, the assignment count and
the substantive claim are all **correct**.

**Replacement:** `…and *read* exactly once, by `toLoanProductRelatedDetail()` [`:1727`] at `:1740`,
which is a different method…`

### P2-T53-5 — a stale `TO_BE_CAPTURED` label sits after its own `[SUPERSEDED]` marker

In the **revision-10** history bullet (§ Revision history, the `N46-1` entry), the marker is placed
mid-bullet:

> …separating them needs a tenant write. **[SUPERSEDED IN REVISION 11: that blocker is REFUTED …
> task T50 separated them in process and confirmed the ambient mode governs, 7 of 7. See §4.5.1.]**
> **`TO_BE_CAPTURED`, §8 item 9(h)**, and it is the sharpest remaining charge blind spot.

A reader greping `TO_BE_CAPTURED` lands on a live-looking label **after** the correction. §8 item
9(h) itself is correct and says CLOSED, so nothing false is asserted — but this is the precise
shape of the T2-class leak the program grades, left in the one section whose job is to say what is
still open.

**Replacement:** move the marker to the end of the bullet, so it reads
`…separating them needs a tenant write. **`TO_BE_CAPTURED`, §8 item 9(h)**, and it is the sharpest
remaining charge blind spot. **[SUPERSEDED IN REVISION 11: that blocker is REFUTED …]**`

### P2-T53-6 — §2.2's `[UNVERIFIED]` block is now closed by measurement, and renders broken

**Exact text** (§2.2, immediately after the observation paragraph):

> `[UNVERIFIED: the VALUE of the tenant-global `interest-charged-from-date-same-as-disbursal-date`
> flag on the `gerege` tenant during T51's captures. T51 did not read it, and this task did not
> contact the oracle. … the global flag's value is inferred from that and not measured.]`

Two problems. **First**, it is no longer unverified: I read it (above) and it is **false**
(`c_configuration.enabled = f`), consumed as `property.isEnabled()`
[`ConfigurationDomainServiceJpa.java:296-300`], which is exactly the 31-December branch T51
observed 6 of 6. **Second**, the block is wrapped in a single backtick and contains backticked
identifiers, so the code span closes at the first inner backtick and the remainder renders as
prose.

**Replacement:**

> **[VERIFIED in re-review T53 by a read-only `SELECT` against the `gerege` tenant database: the
> `c_configuration` row `interest-charged-from-date-same-as-disbursal-date` has `enabled = f`, and
> `ConfigurationDomainServiceJpa.isInterestChargedFromDateSameAsDisbursementDate()` returns
> `property.isEnabled()` [`ConfigurationDomainServiceJpa.java:296-300`]. So the tenant-global flag
> was **false** during T51's captures, `LoanApplicationTerms.java:1753` yields `false`, and the
> oracle takes the 31-December branch [`ProgressiveEMICalculator.java:1582`] — which is what T51
> observed on 6 of 6 discriminating crossing periods. The value is now measured, not inferred. No
> value was written; row counts before and after were identical.]**

The `[UNVERIFIED]` caveat should be deleted, and §4.4's porting-rule phrase "under the tenant
configuration T51 observed" can be tightened to "under the `gerege` tenant configuration, measured
`false`".

---

## Recommendation on ratification

**Apply the six P2 errata, then ratify.** I re-derived the arithmetic, re-counted the components,
re-derived the reachability of both alias readers and of T48-N4's trap, opened all 47 named
citations the diff adds, proved `contract.go` comment-only by a method independent of both prior
checks, hashed every section of the ADR to establish what did and did not move, ran my own
seven-pattern restatement grep, and closed the one honest `[UNVERIFIED]` by measurement against the
live oracle. **I found no P0 and no P1, and no reason not to ratify.**

The six errata are all documentation-accuracy defects — a mis-stated bound, five under-anchored or
mis-named citations, a mis-placed marker, and a caveat that is now stale in the *conservative*
direction. None of them changes a number, a predicate, a pin or a refusal. But the argument for
fixing them first is the driver's own, twice used: **ratification freezes, and known-wrong
sentences are not the thing to freeze.** P2-T53-1 in particular is a false sentence in the
paragraph a ratifier reads first, and it is trivially fixable now and a gate away from fixable
afterwards.

Three things I want on the record for whoever ratifies:

1. **The erratum-versus-amendment call on N46-1/N46-3 is correct**, and I tested it rather than
   accepting it. Admitting the finding moves **no** graded-domain predicate, for three independent
   reasons verified at source: the charge loci are unreachable from Path A (`loanCharges` is
   hard-wired `null` at `ProgressiveLoanScheduleGenerator.java:83`); the N46-3 sites are all
   down-payment computations pinned to `Rate{0, 1}`; and on the shipped server the two contexts are
   one object. §3.1 and §4.1 are byte-identical, which is the mechanical proof. **Ratification does
   not need a gate on this account.**
2. **Nothing was promoted.** §8 item 1's promotion rule is byte-identical, G-1 is open, no vector
   is admitted, `DayCountActualActual` is still refused with `ErrNoDiscriminatingVector`, and the
   document still reads `Status: DRAFT (revision 11)`.
3. **The oracle is reachable and I used it read-only.** If the next fire wants the ACT/ACT
   admissibility condition discharged, the flag value is now known (`false` → 31 December), so the
   boundary a promoted vector must reproduce is settled — but the vector itself must still cross a
   leap-year boundary with a non-zero first segment, or it grades nothing.
