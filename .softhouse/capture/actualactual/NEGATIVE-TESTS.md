# T48 — the recipe is proved FAILABLE on eight axes

`patterns.md`: *"A precondition script is only worth what its negative run proves. An assertion suite
that has never failed has not been tested."*

`src/negative-tests.sh` runs `src/run-actualactual.sh` in eight deliberately wrong configurations and
**requires** each to exit non-zero with a `BREACH` line naming the breach. If any leg PASSes, the
negative-test script itself exits 1 — because then the recipe is not failable on that axis and its PASS
means nothing. Recorded output: `NEGATIVE-TESTS-OUTPUT.txt`.

| leg | wrong configuration | breach the recipe named |
|---|---|---|
| N1 | expected commit set to all-zeros | `pinned checkout is at 426a2354…, expected 0000…` |
| N2 | expected image digest set to all-zeros | `image id is sha256:e596…, expected sha256:0000…` |
| N3 | expected seam-class digest set to all-zeros | `seam class sha256 is bf397f0b…, expected 0000…` |
| N4 | the seam class actually byte-drifted (one comment line appended, then restored) | `seam class under src/ has DRIFTED from the pinned original` — and the restore is then `diff`ed against the pinned original and proved byte-identical |
| N5 | **threaded** rounding mode forced to `HALF_EVEN` | `negative-test threaded rounding-mode override was LEFT SET: HALF_EVEN` + `T48-CTL-Q0a: THREADED rounding mode HALF_EVEN, expected HALF_UP` (and on every other non-calibration capture) |
| N6 | **threaded** precision forced to 12 | `negative-test precision override was LEFT SET: 12` + `THREADED precision 12, expected 19` |
| N7 | tenant rounding ordinal forced to 1 (`DOWN`) | `negative-test tenant rounding override was LEFT SET: 1` + `AMBIENT MoneyHelper MathContext is 'precision=19 roundingMode=DOWN'` |
| N8 | expected ambient context set to a value the oracle does not hold (`HALF_DOWN`) | `AMBIENT MoneyHelper MathContext is 'precision=19 roundingMode=HALF_UP', expected '… HALF_DOWN'` |

**Result: 8 of 8 legs breached as required, and the seam class was restored byte-identical.**

Two axes deserve comment.

* **N5 and N6 are the behavioural canary for Path A / Path A2.** `reference-oracle.md` rule 6 says a
  configuration echo is not a discriminator and the attestation must carry a value that differs by
  rounding mode *for whichever context it claims governs*. On these seams the threaded context governs,
  so the canary must move the **threaded** mode — which is exactly what N5 and N6 do. (The Path B legs
  additionally carry T36's half-cent tie, run before every post.)
* **N7 is the ambient leg, and it is deliberately kept separate from N5/N6.** Forcing the tenant ordinal
  changes the **ambient** context and nothing else on these seams; it is a check that the harness
  reports the tenant configuration truthfully, not evidence about the arithmetic. Conflating the two is
  the defect found in T37 and T39, and this suite does not repeat it.

## What the negative tests do NOT prove

They prove the recipe rejects a *misconfigured* run. They cannot prove the recipe would reject a
*correctly configured run of a wrong oracle* — no fire has a second Fineract build to test that against.
`[UNVERIFIED]` and out of reach here.
