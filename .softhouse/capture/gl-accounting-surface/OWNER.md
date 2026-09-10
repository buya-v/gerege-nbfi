# OWNER — capture/gl-accounting-surface

**Subject:** the loan→GL posting surface: the accounting-enabled loan product
(`OHLGR-Accrual-Loan`, id 3, `ACCRUAL PERIODIC`), its `OHLGR-*` GL accounts, the
charges/loans carrying non-zero fee and penalty, and the journal entries they post.

**Owns the finding:** `F-2026-09-09-fee-penalty-blind` (the corpus was blind to the
fee and penalty terms of the loan summary; every prior summary vector carried
fee = 0 AND penalty = 0).

**What is here:** `(request, response)` pairs for every write that created the new
charges, the new loan `OHLGT-L03`, and the read-backs of the loan summary, the
transactions and the journal entries. `req/` holds the exact request bytes that were
sent; `out/` holds the oracle responses.

**Byte-stability (the P-25 defect this rig exists to fix):** every numeric token in a
`req/*.json` body is an integer or a JSON string — never a `100.00` that re-emits as
`100.0` under a binary-double round trip. Request bodies are written as literal bytes
and posted with `--data-binary`; nothing is re-serialised through `json.dumps` of a
parsed number. The amounts `100` (fee) and `57` (penalty) differ, so a term-swap
defect cannot survive. See `bin/common.sh` and `bin/step01-charges.sh`.

**Additive only:** the writes create new rows keyed on `OHLGT-` external ids. No
product, client, or loan is modified; products 1 and 2 stay `NONE`, loans 10 and 11
are read-only observations. Every SQL read is read-only against the `default` tenant.

**Provenance of the summary vectors:** `.softhouse/vectors/loan/LN-L07-*.json`
(loan 12, fee 100.00, penalty 57.00) and `LN-L08-*.json` (loan 10, fee 0, penalty
57.00) transcribe `out/loan-12-raw.json` and `out/loan-10-raw.json` respectively.
