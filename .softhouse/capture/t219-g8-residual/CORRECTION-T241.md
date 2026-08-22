# CORRECTION — pointer: this directory carries the same defective TOTAL-INTEREST law

**Filed by `T241`. Nothing in this directory is edited.**

`src/site3.py` here is **byte-identical** to `../t229-g8-site3/src/site3.py`
(`sha256 36701476f41de4280bd51deee49ac26028b78a86ed52e0db0c4d89debddf1996`) — T219 used T229's
instrument unmodified, which is exactly right and is why the defect travelled with it. Its docstring
and its `predictedTotalInterestMinor` field both assert

> `TOTAL INTEREST = n*E + B  for any unrescued cell`

and **that is false.** `n·E + B` is the modelled schedule's **TOTAL REPAYMENT**; the total interest
is `n·E + B − TOTAL PRINCIPAL`, and the two coincide only where the loan repays no principal at all.

**`prediction.json` in this directory carries the wrong value as data**, on the two PARTIAL cells:
`predictedTotalInterestMinor` reads `4503001` for `T219-R600p0-N3000-B3001` and `6751499` for
`T219-R600p0-N3000-B4499`, where the oracle observed `4503000` and `6750000`. Those figures are the
predicted total **repayment** and are correct read that way — the oracle's
`totalRepaymentAmount` is `45030.01` and `67514.99`. **`prediction.json` is a registered pre-probe
prediction and MUST NOT be edited**; read the field with this correction beside it.

**The full correction, the re-derivation and the whole-corpus evidence are in
`../t229-g8-site3/CORRECTION-T241.md`.** It affects **no verdict here**: `src/classify_t219.py`
grades on `predictedOutcome` and `predictedTotalPrincipalMinor`, and every T219 cell verdict stands
exactly as reported.
