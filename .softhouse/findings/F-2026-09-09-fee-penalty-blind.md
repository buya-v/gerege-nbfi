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

---

## UPDATE 2026-09-10 — THE CAPTURE NOW EXISTS. The finding is closable.

`OH-GL-R` created the first accounting-enabled loan product in this oracle and, with it,
loans carrying **non-zero fee and penalty**. The observation this finding said it needed is
now committed at `.softhouse/capture/gl-accounting-surface/out/`.

**Loan 11** (`loan-11-raw.json`) — all four summary terms non-zero, and **fee ≠ penalty**,
which is exactly what this finding specified, because equal values would let a term-swap
defect survive:

    principalOutstanding       100000.0
    interestOutstanding          6618.53
    feeChargesOutstanding         100.0
    penaltyChargesOutstanding      57.0
    totalOutstanding           106775.53

Minor units: `10000000 + 661853 + 10000 + 5700 = 10677553`. **No sub-minor residue**, so
G-19 does not bite and this is a legitimate parity vector.

**Loan 10** (`loan-10-raw.json`) is the complementary shape — `feeChargesOutstanding` **0**,
`penaltyChargesOutstanding` **57** — which discriminates the penalty term alone, and gives a
second, differently-shaped observation rather than a clone.

### What still has to happen — this finding is NOT yet closed

Committing an observation and grading it are different acts. To close it:

1. Promote a summary vector from loan 11 (all four terms non-zero) and, if it carries a
   distinct fact, one from loan 10 (penalty-only).
2. Register **`loan-wrong-summary-drops-fee`** and **`loan-wrong-summary-drops-penalty`**
   and **show each kills**. Until a drive dies on these vectors, nothing is proven — the
   whole point of this finding was that a dropped term is invisible, and a vector that no
   drive tests does not fix that.
3. Re-measure the four existing `*-summary-total-outstanding` vectors; they still pin one
   fact between three of them (L05 excepted) and adding a fifth zero-fee summary remains
   the cloning failure.

Until then this stays **OPEN**, with the blocking reason changed: it was "no capture can
discriminate the term"; it is now "the capture exists and the drives are unwritten."
