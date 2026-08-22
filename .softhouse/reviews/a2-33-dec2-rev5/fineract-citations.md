# A2-33 — requirement 6: Fineract citations re-resolved BY CONTENT at `426a23544`

**Pinned checkout:** `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`
[VERIFIED by `A2-33`: `git -C /Users/buv/fineract rev-parse HEAD`; `git status --short` empty].

**First, the scope fact that bounds this requirement.** Revision 5 **introduces no new Fineract
citation and modifies none.** [VERIFIED by `A2-33`: the only `.java` token appearing anywhere in
`git diff 33d19a6 cab9e82 -- docs/adr/DEC-2-gl-accounting-adapter.md` is `JournalEntry.java:79`,
carried through unchanged inside the §4.4 `I-4` row that was rewritten for the F-2 correction.] So no
citation defect here could be a defect *of revision 5*. I re-resolved them anyway, because the brief
said re-verify and do not inherit `A2-31`'s pass.

## Method, stated honestly

The full enumeration and content-resolution of the Fineract citation set was **run by a delegated
read-only search agent under my direction**, instructed to build its own citation list from the
document rather than take mine, to open every cited range with `sed -n`, to read the ADR's
surrounding sentence to learn what was being claimed, and to classify each as
RESOLVES / DRIFTED / FAILS / AMBIGUOUS. **I then spot-verified the three most load-bearing citations
myself, from source, and I report those separately below.** This division is disclosed rather than
implied.

## Result

**54 Fineract citations checked — 54 RESOLVES, 0 DRIFTED, 0 FAILS, 0 AMBIGUOUS.**

The set spans `AccountingConstants.java`, `AccountingProcessorHelper.java`, `AccountingRuleType.java`,
`GLAccountReadPlatformServiceImpl.java`, `GLAccountWritePlatformServiceJpaRepositoryImpl.java`,
`JournalEntry.java`, `JournalEntryRepository.java`, `UpdateTrialBalanceDetailsTasklet.java`,
`LoanProductDataValidator.java`, `PortfolioProductType.java`,
`ProductToGLAccountMappingRepository.java`,
`ProductToGLAccountMappingWritePlatformServiceImpl.java`,
`SavingsProductToGLAccountMappingHelper.java`, `ProgressiveLoanScheduleGenerator.java` and
`db/changelog/tenant/parts/0001_initial_schema.xml`.

`MoneyHelper.java` is **not cited** by DEC-2 at all (`grep -n MoneyHelper` over the ADR returns zero
hits), so there was nothing to verify there.

## The three I opened myself

**These are the ones a wrong answer would actually cost something, so I did not delegate them.**

1. **`JournalEntryRepository.java:61` — the unsigned `SUM`.** [VERIFIED by `A2-33` from source.]
   Lines 53-62 project a **signed** sum
   (`SUM(CASE WHEN je.type = 1 THEN -1 * je.amount ELSE je.amount END)`) as `row[2]` and, four
   projections later at **`:61`**, a bare **`SUM(je.amount)`** as `row[5]`. Two sums, one signed and
   one not, in the same query.

2. **`UpdateTrialBalanceDetailsTasklet.java:81`** — [VERIFIED by `A2-33` from source]
   `tb.setClosingBalance((BigDecimal) row[5]);`. **`row[5]` is precisely the unsigned
   `SUM(je.amount)` above.** So DEC-2 §4.4's `I-3` row is correct on the point that matters to
   `CLAUDE.md`'s first-tier non-negotiable: **`m_trial_balance.closing_balance` is a written, stored,
   UNSIGNED sum wearing a balance's name**, and the ADR's decision **not** to port it (§7) is
   correctly grounded.
   *Correction to the delegated report, made by me:* it gave the path as
   `fineract-accounting/.../journalentry/service/updatetrialbalancedetails/`. The true path is
   **`fineract-accounting/src/main/java/org/apache/fineract/accounting/glaccount/jobs/updatetrialbalancedetails/UpdateTrialBalanceDetailsTasklet.java`**.
   The file and line resolve; the path in that report was wrong and I am recording the right one.

3. **`AccountingProcessorHelper.java:1199-1206`** — [VERIFIED by `A2-33` from source] the loan
   payment-channel override is gated on
   `if (accountMappingTypeId == CashAccountsForLoan.FUND_SOURCE.getValue()) {` **with no
   `paymentTypeId != null` conjunct anywhere in the block**, exactly as the ADR asserts, and in
   deliberate contrast to `:1015` on the working-capital path.

## Four minor imprecisions, recorded and NOT actioned

All four are **pre-existing** (revision 4 and earlier), **not touched by revision 5**, and **not
errors of content** — every one resolves. Fixing them in revision 5 would have been exactly the new
authorship that got revision 2 rejected. They belong to a later revision or to `FU-A2-31-4`'s
re-measure gate.

1. `LoanProductDataValidator.java:744` and `:704` — the cited line carries the parameter; the
   `.ignoreIfNull()` token the sentence turns on is on the **following** line of the same statement.
2. `GLAccountWritePlatformServiceJpaRepositoryImpl.java:151-159` — lines 151-152 are closing javadoc;
   the guard begins at **:153**. The range contains the claim but opens two lines early.
3. `AccountingConstants.java:48` / `:51` — the prose names `CHARGE_OFF_EXPENSE` before
   `GOODWILL_CREDIT` while the cites are in the opposite order. Both constants are at the cited
   lines; only the pairing reads backwards.
4. `ProgressiveLoanScheduleGenerator.java:83` — *"`loanCharges = null`"* is a paraphrase of a
   positional `null` in `generate(mc, loanApplicationTerms, null, null)`; confirming which parameter
   it binds needs the overload at `:87-88`. It is `loanCharges`.

## Class-name ambiguity worth a ratifier's attention (also pre-existing)

Several cited class names exist in more than one module, and the ADR does not always say which:
`JournalEntry.java` (accounting domain vs integration-tests helper),
`ProgressiveLoanScheduleGenerator` (vs `EmbeddableProgressiveLoanScheduleGenerator`),
`LoanProductDataValidator` (vs `WorkingCapitalLoanProductDataValidator`). In every case the cited
line content disambiguates, so nothing FAILS — but a bare class name plus a line number is a weaker
citation than a path plus a line number, and this document mostly uses the weaker form.
