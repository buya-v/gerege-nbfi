# F-2026-09-09 — the corpus is BLIND to the fee and penalty terms of the loan summary

**Status:** OPEN. Cannot be closed by promotion. Needs one new oracle capture.
**Found by:** the driver, while two runs were live, by checking a claim it had just
written into a brief. The claim was "the four `summary-total-outstanding` vectors are
clones"; checking it produced this instead.

## The measurement

`m_loan` summary total outstanding is a four-term sum:

    total = principal + interest + fee + penalty

Every vector that grades it — `LN-L01`, `LN-L03`, `LN-L05`, `LN-L06`
`-summary-total-outstanding` — carries **`fee_outstanding_minor = "0"` and
`penalty_outstanding_minor = "0"`**:

    LN-L01   prin=10000000  int=661853  fee=0  pen=0  -> 10661853
    LN-L03   prin= 9211512  int=561853  fee=0  pen=0  ->  9773365
    LN-L05   prin= 4185009  int=     0  fee=0  pen=0  ->  4185009
    LN-L06   prin=10005050  int=662189  fee=0  pen=0  -> 10667239

And the corpus has no observation to build a better one from. Across **every** capture in
`.softhouse/capture/loan/out/` and `.softhouse/capture/charges/out/`, scanning
`feeChargesOutstanding`, `penaltyChargesOutstanding`, `feeChargesCharged` and
`penaltyChargesCharged` at any depth: **zero non-zero observations.**

## Why it matters

**A port that drops the fee term, or the penalty term, or both, from the summary sum
passes every one of these vectors.** Adding zero is indistinguishable from not adding at
all. The defect is invisible to the whole graded corpus, and it is a natural one — a
four-term sum where two terms are always zero in every example a porter sees is exactly
the shape that gets written as a two-term sum.

The drive register confirms the asymmetry. `loan` has:

    loan-wrong-summary-drops-principal
    loan-wrong-summary-interest-not-outstanding

and **nothing for fee or penalty**. Writing `loan-wrong-summary-drops-fee` today would
register a drive that **kills zero** — and the important part is WHY. Not because the
defect is unobservable in principle; because **no captured observation discriminates it.**
That distinction is the whole content of this finding, and it is the distinction the
inert-drive rule exists to force into the open.

*(This is arithmetic, not a run: with fee = pen = 0 in all four vectors, an implementation
that omits either term computes an identical total. Nothing needed to be executed to know
it, and nothing was — two agents held the tree.)*

## What would close it

**One capture, and it needs the oracle.** A loan carrying a non-zero fee charge and, ideally,
a non-zero penalty, read back through the loan detail/summary endpoint. Then:

* promote a summary vector whose `fee_outstanding_minor` and `penalty_outstanding_minor`
  are non-zero and **differ from each other** (equal values let a term-swap defect survive);
* register `loan-wrong-summary-drops-fee` and `loan-wrong-summary-drops-penalty` and show
  each kills it.

Until that capture exists this stays open. **Do not close it by writing a vector with a
synthesised fee** — never synthesise a value not observed from the oracle.

## What does NOT close it

A fifth `summary-total-outstanding` vector with `fee = pen = 0`. There are four already and
they pin one fact; `LN-L05` is the only one that differs in shape (zero interest, so it
pins the degenerate case). A fifth zero-fee summary is the OH-DEEP-E cloning failure.

## Note for whoever picks this up

`OH-PROM-O`'s brief told it not to add a fifth summary vector. That instruction is correct
but **incomplete** — it does not name this gap, because the driver had not yet found it.
It suppressed no work that run could do: `OH-PROM-O` is forbidden to capture (the oracle
was held by `OH-INV-N` advancing the business date), and no committed capture can close
this. Recorded here rather than silently, per the briefs README: the instruction is half of
why a change exists, and a brief that was incomplete should say so.
