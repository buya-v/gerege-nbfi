# F-2026-09-10 — the OH-JE-C brief names a loan-10 journal capture that is not on `main`

**Status:** RESOLVED — the observation is committed under a different path; LN-L09 cites that path.
**Cost:** none once located; the values were verified against the committed file before promotion.

## What the brief said

OH-JE-C names

    .softhouse/capture/gl-accounting-surface/out/journalentries-loan-10-raw.json

as "the only capture that sees this" — the four-leg, two-pair batch of loan entityId 10. That
path **does not exist on `main`**.

## What is actually there

The path was added by the OH-GL-R salvage (`08b711eb`) and removed by the honest revert
(`173b5446`) that followed it: the salvage's request bodies carried money tokens that were not
byte-preserved through a binary-double round trip (`100.00 -> 100.0`), and the wire-float guard
refused them. Nothing was trimmed; the whole salvage was reverted. The re-capture
(`ed0207a2`, byte-stable, wire-float census ALTERED 0) committed the same loan→GL surface
under `journalentries-all-raw.json`, and did **not** recreate the per-loan filename.

The loan-10 batch is in that committed file. Re-read directly from the working tree (not from
memory):

    pageItems, entityType=LOAN, entityId=10
      L17  OHLGR-Loan-Portfolio   DEBIT   100000.0
      L17  OHLGR-Fund-Source      CREDIT  100000.0
      L18  OHLGR-Income-From-Fees CREDIT     100.0
      L18  OHLGR-Fund-Source      DEBIT      100.0
      sum debits 100100.0 == sum credits 100100.0

Loan 12 is the single pair L20 (100000.0 each way), as the brief says, and stays unusable for
grading the property.

## Consequence

`LN-L09-journal-entry-batch-balance.json` cites
`.softhouse/capture/gl-accounting-surface/out/journalentries-all-raw.json`
(sha256 `a400082a1b2974ccd6ec660789810b1ba1f8812a21024da230002ffee3a9913d`),
`capture_case_id` `L17`. No value was synthesised and no re-capture is needed: the observation
the brief wanted is committed, just under the aggregate filename. The brief's per-loan name is
stale, not a missing capture.
