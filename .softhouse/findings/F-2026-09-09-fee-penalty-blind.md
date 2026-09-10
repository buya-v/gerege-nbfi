# F-2026-09-09 — the corpus is BLIND to the fee and penalty terms of the loan summary

**Status:** **CLOSED 2026-09-10 by OH-GL-T.** The byte-stable re-capture exists, the
fee/penalty-bearing summary vectors `LN-L07`/`LN-L08` are promoted, and both drives
`loan-wrong-summary-drops-fee` and `loan-wrong-summary-drops-penalty` kill. See the
final UPDATE below. (Original opening: OPEN. Cannot be closed by promotion. Needs one
new oracle capture.)
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

## UPDATE 2026-09-10 — the observation EXISTS but is NOT admissible yet

`OH-GL-R` created the first accounting-enabled loan product in this oracle
(`id 3 OHLGR-Accrual-Loan`, `ACCRUAL PERIODIC`, additive — products 1 and 2 untouched and
still `NONE`) and with it loans carrying **non-zero fee and penalty**. It reached the
500-iteration limit with 71 files on disk and zero commits.

**The observation this finding asked for was produced.** Loan 11 carries all four summary
terms non-zero with **fee ≠ penalty**, which is what this finding specified, because equal
values would let a term-swap defect survive:

    principalOutstanding 100000.0  interestOutstanding 6618.53
    feeChargesOutstanding 100.0    penaltyChargesOutstanding 57.0
    totalOutstanding     106775.53

Minor units `10000000 + 661853 + 10000 + 5700 = 10677553` — no sub-minor residue. Loan 10
is the complementary shape (fee **0**, penalty **57**), discriminating the penalty term
alone. Journal entries 17-22 are balanced double-entry (loan 10: debits 100100.0 == credits
100100.0; loan 11: 100000.0 == 100000.0).

### WHY IT IS NOT IN THE TREE — the wire-float guard refused it, correctly

The driver committed the salvage, ran the bar, and the bar **REFUSED with a failed HARD
guard** — no verdict available, which is not a pass:

    REFUSED — a numeric token in a capture request body is NOT byte-preserved under a
    binary-double round trip. This is the P-25 defect T163 found in resolve7.py: the money
    that reaches the reference oracle is not the money that was written.
      req/charge-OHLGR-Fee-Flat-100.json:1      100.00 -> 100.0
      req/charge-OHLGR-Penalty-Flat-57.json:1    57.00 -> 57.0
      req/loan-OHGLR-L01-submit.json:21,22      100.00 -> 100.0, 57.00 -> 57.0
      req/loan-OHGLR-L02-submit.json:21,22      100.00 -> 100.0, 57.00 -> 57.0

The record is **not** falsified: `bin/step03-charges.sh:24` sends the body as a shell
single-quoted literal containing `"amount":100.00`, and `req/` is a faithful byte-copy of
what was sent. The defect is that **the request we sent the oracle carries a numeric token
that is not byte-stable**, which is precisely the hazard the guard exists to catch.

**The salvage commit was REVERTED rather than trimmed.** Dropping `req/` would have turned
the bar green by deleting the artefact that failed, which is the "green bar bought with a
defeatable predicate" this programme refuses. The 72 files are preserved outside the repo
at `/Users/buv/gerege-oracle-snapshots/gl-accounting-surface-evidence/`; nothing is lost.

### What closes this now — and it is cheap, because the oracle state persists

Product 3, the 11 GL accounts and both loans **still exist in the oracle**. A re-capture
needs only byte-stable request bodies:

1. Write charge and loan request amounts as byte-stable tokens (`100`, `57` — or splice the
   placeholder into template bytes; `.softhouse/capture/tierA-a2/resolve8.py` is the worked
   example the guard names). **Never re-serialise a request body through `json.dumps` of a
   parsed number.**
2. Re-issue the charge and loan creation against product 3, capture the `(request, response)`
   pair, and commit both.
3. Then promote the summary vector and register **`loan-wrong-summary-drops-fee`** and
   **`loan-wrong-summary-drops-penalty`**, showing each kills. A vector no drive tests does
   not fix a defect that was invisible by construction.

Status stays **OPEN**, blocking reason changed twice today: from "no capture can
discriminate the term", to "the capture exists but its request bodies are not byte-stable."

---

## UPDATE 2026-09-10 — CLOSED: byte-stable re-capture, two vectors, both drives kill

`OH-GL-T` fixed the narrow defect and finished. The new capture is additive and lives at
`.softhouse/capture/gl-accounting-surface/` (named for its subject; `OWNER.md` inside).
It creates two NEW charges on product 3 — `OHLGT-Fee-SDD-100` (amount token `100`) and
`OHLGT-Penalty-SDD-57` (amount token `57`) — and a NEW loan `OHLGT-L03` (oracle id 12)
carrying both, then captures the `(request, response)` pair for every call.

**Why the guard now passes.** Every numeric token in `req/*.json` is an integer or a JSON
string; `100` and `57` are their own shortest round-trip reprs, so they survive the one
genuine Java `double` on the POST /charges path. The self-check over the committed
request bodies reports `req files=5 numeric tokens=26 NOT byte-stable=0`, and the
conformance wire-float census reports `float-shaped tokens PRESENT 380, ALTERED 0`. No
request body is re-serialised through `json.dumps` of a parsed number; the templates are
literal bytes posted with `--data-binary` (`bin/common.sh:34-35`).

**The vectors.** Both transcribe the oracle's `summary` block, nothing computed:

    LN-L07  OHLGT-L03 (loan 12)  prin=10000000 int=661853 fee=10000 pen=5700 -> 10677553
    LN-L08  OHGLR-L01 (loan 10)  prin=10000000 int=661853 fee=    0 pen=5700 -> 10667553

`LN-L07` is the finding's requested shape: all four buckets non-zero and fee ≠ penalty, so
a term-swap defect cannot survive. `LN-L08` is the second, differently-shaped observation
(fee 0, penalty non-zero) that discriminates the penalty term alone.

**The drives kill, measured in the same session with live controls**
(`.softhouse/briefs/tools/kills.sh loan <impl>`):

    loan-wrong-summary-drops-fee            -> 1  (LN-L07)
    loan-wrong-summary-drops-penalty        -> 2  (LN-L07, LN-L08)
    loan-wrong-summary-drops-principal      -> 7  (control, live)
    loan-wrong-summary-interest-not-outstanding -> 6  (control, live)

Neither new drive is inert: `drops-fee` was inert before this capture (every prior summary
vector had fee = 0) and now kills on `LN-L07`; `drops-penalty` kills on two vectors. The
two controls prove the instrument was live, so the non-zero counts are measurements, not
artefacts of a dead tool. The register now has:

    loan-wrong-summary-drops-fee
    loan-wrong-summary-drops-penalty

**Correction to the previous UPDATE:** the oracle has **12** `OHLGR-*` GL accounts
(ids 5-16), not 11 — observed live via `GET /glaccounts` on 2026-09-10. That is more than
the brief expected, not less. Products 1 and 2 are still `NONE`; loans 10 and 11 are
untouched; nothing was SQL-inserted.

**Full evidence, with the oracle-state verification table:**
`.softhouse/capture/gl-accounting-surface/evidence/OHGLT-EVIDENCE.md`.

---

## NOTE 2026-09-10 — the same loan's terms are now visible on the investor details seam

`OH-INV-Y` settled transfer 28 on loan 12, and `details` carries the same four terms this
finding is about, non-zero and different:

    totalPrincipalOutstanding 100000.0  totalInterestOutstanding 6618.53
    totalFeeChargesOutstanding   100.0  totalPenaltyChargesOutstanding 57.0
    totalOutstanding         106775.53  totalOverpaid                   0.0

That is a **second, independent surface** carrying the fee/penalty discrimination this
finding needed — the loan summary read path closed it, and the investor details path now
shows the same decomposition. Note `totalOverpaid` is **0.0**, so this observation does
**not** discriminate whether overpaid is included in the total: 106775.53 either way.
