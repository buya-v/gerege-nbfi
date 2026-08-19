# T43 — handoff: independent re-review of DEC-1 revision 8

**Branch:** `softhouse/T43-dec1-v8-rereview`
**Full review:** `.softhouse/reviews/T43-DEC-1-v8-rereview.md`
**Probes:** `.softhouse/reviews/t43-probe/`
**Oracle contacted:** no. No container, no Gradle, no HTTP. Every observation quoted from a committed capture with its id.

---

## Verdict

**ACCEPTED WITH REQUIRED CHANGES. No P0, no rejection-grade finding.**

Read this the way it is meant: **the review found no reason not to ratify.** Nothing
below moves money inside the graded domain, nothing changes a type / field / enum
member / graded-domain predicate, and nothing leaves the specification incomplete for
a port inside the Run-1 graded domain. Under §1 and standing policy P-2 the driver may
take the ratification decision on this review and carry the corrections as a revision-9
erratum.

Eight consecutive rounds have now found a defect. This round's three P1s are all the
same shape and it is a **weaker** shape than the previous seven: in each case the
document's *sentence* is right and the *evidence pinned under it* is not. The previous
seven were wrong about the money.

---

## Findings

### P1-T43-1 — C-1's distinguishing citation is the line the two generators SHARE
§4.5.1 (C-1 mechanism), §4.5.1 blind-spot bullet 4, §9 obligation, revision-8 history.
`AbstractCumulativeLoanScheduleGenerator.java:504` is cited as where the cumulative
generator "adds fee and penalty to the running total on every period". It is that
generator's `updatePeriodsWithCharges`, **character-for-character identical** to
`ProgressiveLoanScheduleGenerator.java:486`, which the same paragraph cites as the
progressive generator's only post-seed charge contribution. Both serve only the
separated charge set. The line that actually distinguishes the two is the cumulative
main loop: `:352` + `:392` via `ScheduleCurrentPeriodParams.fetchTotalAmountForPeriod()`
[`:144-146`], which is `principal + interest + fee + penalty`, against the progressive
`:137`'s `principal + interest`.
**Conclusion and decision C-1 stand.** The citation, read literally, refutes them.
Corroborated by T40's own captures: `FC-19` and `FC-21`, the two separated-path
charges, are exactly the two that **pass** invariant C5.
*Fix:* re-cite `:352`/`:392`/`ScheduleCurrentPeriodParams.java:144-146` at all four
places, and say that `:504` and `:486` are the same line in two files.

### P1-T43-2 — §4.1.2's "exactly these call sites" is incomplete by three
§4.1.2 (and §4.1's parallel list). The enumeration of ambient `MoneyHelper` reads omits
`Money.java:130-132` (`Money.zero(CurrencyData)`, ambient at `:131`), `:224-234`
(`plus(Iterable<Money>)`, two-arg `Money.of` at `:233`) and `:261-267` (`plus(double)`,
two-arg `Money.of` at `:266`).
And the closing bullet — "every remaining site sits on the installment-multiple or
`multipliedBy(double)` path, **which the graded domain excludes**" — is false of
`:130-132`: it is reached from `ProgressiveEMICalculator.java:182` on the
`allowFullTermForTranche` arm, which is a **§4.4 pin**, not a §3.1 predicate. That is
the same "excluded by a pin, a materially weaker reason" caveat revision 8 already had
to add once from T42, missed a second time on the same enumeration.
**P4 still stands, by observation:** T42's absence probe shows no in-graded-domain
Path-A shape reads the ambient context (the 2 of 13 that threw are the 0-dp shapes
`MinorUnitDigits == 2` excludes). The defect is in the source argument, which §4.1
explicitly says is what makes the claim sufficient.
*Fix:* add the three sites; name `:182`; restate the closing bullet as "excluded by the
graded domain **or by a §4.4 pin**".

### P1-T43-3 — M4 does not decide which row an INSTALMENT charge lands on
§4.3.2's M4 row and §9's membership obligation say M4 decides "which row a CHARGE lands
on". `getCumulativeAmountOfCharge` computes `isDue` (= M4) at
`ProgressiveLoanScheduleGenerator.java:403` and the
`loanCharge.isInstalmentFee() && isInstallmentChargeApplicable` arm at `:404-405`
**does not read it** — an `INSTALMENT_FEE` charge is applied to **every** repayment row
with no membership test at all. M4 governs only the three `isDue`-gated arms
(`OVERDUE_INSTALLMENT`, percentage `SPECIFIED_DUE_DATE`, flat `SPECIFIED_DUE_DATE`).
Observed in the corpus: `FC-02` (flat instalment) moves 12 charge cells, `FC-07` (flat
specified-due-date) moves 1; `FC-15` carries 2,500.00 fee on all twelve rows and its
7,500.00 penalty on period 3 alone.
**This is the one that would mis-price.** A port implementing the table as written puts
an instalment fee on one row instead of twelve — MNT 27,500 on `FC-02`'s shape — which
is exactly the failure the table exists to prevent ("a port that assumes one convention
throughout is wrong somewhere"). Nothing moves inside today's graded domain, because
`GenerateRequest` carries no charge.
*Fix:* qualify M4 in §4.3.2 and §9; consider naming "no membership test at all" as the
fifth convention.

### P2s
- **P2-T43-1** §4.5.1: the stated progressive `totalRepaymentExpected` semantics omit
  the down-payment term at `ProgressiveLoanScheduleGenerator.java:345`.
- **P2-T43-2** revision history says T41's model compares **1,224** cells of T39's 15
  parity-setting captures; §4.1.1 and §8 3e say **1,239** (which is what T39's own table
  sums to). Both are probably right for different leaf sets; the document does not say
  so. Same sentence says "four corpora" and lists five.
- **P2-T43-3** §4.3.1's discriminate table gives `T37-3c` cell `R2.principal` as the
  first witness for `n = NumberOfRepayments`; the cited probe output says `R2.balance`.

---

## Verified clean (so coverage is cumulative)

**~70 `file:line` citations re-opened in the pinned checkout — all correct**, including
every citation load-bearing for a money claim: the rate-factor snippet and its two
senses (`:1950-1963`, `:1969-1980`, `:1922-1927`), both day counts, the `periodRatio`
definition end to end (`:1419-1459`, `:1461-1481`, `:1426-1436`, `:1441-1458`), the
`daysInMonth` narrowing (`:1508` is right, T39's `:1509` is wrong; two call sites only,
confirmed by grep), `DateUtils.java:308-317`, §4.2's re-anchor, the whole per-period
interest computation (`InterestPeriod.java:145-158` with operations at `:155`/`:156`/
`:157`), the whole EMI re-adjust loop (`:1258-1308`, `:1778-1789`, `:2027-2031`,
`EmiAdjustment.java:31-56`) — **every line number in §4.3.1's normative block is
right** — the residual (`:1160-1219`, `:1202-1210`), all four membership rules, the
M4-staleness mechanism (independently re-derived and confirmed), the plan row shapes,
`Money`/`MoneyHelper`, `LoanChargeValidator.java:59-67` (the guard really is one-sided),
and §2.2's two dropped components.

**Corpus claims verified independently by this review:**
- **All seven §8 binding items are captured and all seven separate** — checked item by
  item against the committed discriminate outputs. T41's claim is true.
- 415/415 and 116/116; the 15 parity-setting captures total 1,239 cells; the
  disjointness of 3e and 3f is visible in the same table on all 15.
- `FC-15`: Σ `totalDueForPeriod` 1,411,888.47 − `totalRepaymentExpected` 1,359,988.47 =
  **MNT 51,900.00** exactly; fees 45,000 + penalties 21,900 = **66,900**. Computed here
  from the raw capture in exact `Decimal`.
- **`CTRL-B-01`, `FC-17` and `FC-20` hash identically** (`713a3560…c062009`), verified
  by `shasum` here — C-2's premise is directly observed.
- **T40's control reproduces all four of T36's Path-B digests byte for byte**, verified
  by `shasum` here.
- §4.5.1 fact 4's four rounding-locus figures, read from the raw captures.

**Structural claims verified by diff:** revision 8's `contract.go` diff contains
**zero non-comment lines**; §3.1's block is byte-identical to revision 7's; the ADR
block and `contract.go`'s are content-identical.

**An independent from-text model** of §4.2's re-anchor and §4.1.1 steps A–C
(`.softhouse/reviews/t43-probe/t43_stepb.py`, exact integer/date arithmetic, no float)
reproduces `T39-ME-B`'s observed `periodRatio` vector **and** the omitted-case vector,
and `T39-P0-A`'s drift vector, exactly. It also **independently confirms F-1**: packed
rule + special case ≡ clamped-step rule − special case on all six periods. **The surface
T41 got wrong on its first attempt is right in revision 8.**

**Surfaces T32 named as least examined, now worked:** the down-payment path, currency /
scale handling, the balance roll-forward and both zero clamps, the plan's per-row
cumulative outstanding, and the `SAME_AS_REPAYMENT_PERIOD` early-return branch (opened
expecting a Path-A/Path-B gap; §4.9 already states it correctly). All clean.

---

## Recommendation

Ratify. Carry P1-T43-1, P1-T43-2 and P1-T43-3 plus the three P2s as a revision-9
erratum that reopens no decision. P1-T43-3 is the one that matters for the future: §9
has already turned M4 into a standing obligation, and as written it would mis-price an
instalment fee.
