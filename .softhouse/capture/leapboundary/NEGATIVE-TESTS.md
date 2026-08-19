# T55 — the recipe is proved FAILABLE on nine axes

`patterns.md`: *"A precondition script is only worth what its negative run proves. An assertion
suite that has never failed has not been tested."*

`bin/t55-negative-tests.sh` runs parts of the T55 recipe in nine deliberately wrong configurations
and **requires** each to exit non-zero with a message naming the breach. If any leg PASSes, the
negative-test script itself exits 1 — because then the recipe is not failable on that axis and its
PASS means nothing. Recorded output: `NEGATIVE-TESTS-OUTPUT.txt`.

| leg | wrong configuration | breach the recipe named |
|---|---|---|
| **N1** | expected pinned commit set to all-zeros | `BREACH: pinned checkout is at 426a23544e…, expected 0000…` |
| **N2** | the preconditions gate run against a tenant that does not exist | `tenant 't55-no-such-tenant' has no row in fineract_tenants.tenants` |
| **N3** | one money cell perturbed by **one minor unit** in memory | `I3 period splits sum to the period total : row1 parts=616201.94 total=616201.93` **and** `I5 interest portions sum to totalInterestCharged : sum=32403.87 total=32403.86` |
| **N4** | re-derivation rounding mode forced to `HALF_EVEN` | `re-derivation rounding mode is HALF_EVEN, ratified value is HALF_UP (T55_NEG_ROUND override was LEFT SET)` |
| **N5** | re-derivation precision forced to 12 | `re-derivation precision is 12, ratified production value is 19 (T55_NEG_PREC override was LEFT SET)` |
| **N6** | a shape that **does** differ asserted as the non-leap control | `LB-LEAPIN is the T48-N4 non-leap CONTROL and must report 0 cells; it reported 23` |
| **N7** | the sidecar writer with `parse_float=str, parse_int=str` **removed** | `LB-DEC15IN-p3-exact.json contains a bare JSON number` (and every other sidecar) |
| **N8** | the matched-products SQL run over a deliberately mismatched triple (3, 4, **8**) | `MISMATCH DETECTED: distinct tuples = 2 for products 3/4/8` |
| **N9** | the re-derivation driven off `(19, HALF_UP)` | `CANARY OK: precision 8 breaks the re-derivation (29 -> 22 of 36)` |

**Result: 9 of 9 legs breached as required.**

Four legs deserve comment.

* **N3 is the only leg that tests the *data*, not the configuration.** It perturbs a single money
  cell by one minor unit and requires two independent invariants to catch it. A suite that only
  checks the environment would pass a capture whose numbers had been edited.

* **N6 tests the thing most likely to produce a false negative in this pass.** T55's headline claim
  includes several **zero** cell counts, presented as proven non-discrimination. A comparator that
  returned 0 unconditionally would produce exactly those zeroes while proving nothing. So
  `t55-analyse.py` refuses to pass unless **both** a non-zero and a zero appear among the
  `p7 vs p4` rows, and unless the two shapes *named* as controls are the zeros; N6 shows that
  assertion firing.

* **N7 tests the WRITER, not the reader.** Poisoning a raw file with a float is *not* a valid test,
  because `parse_float=str` correctly neutralises it — so the leg instead removes
  `parse_float=str, parse_int=str` from the sidecar writer, which is the change that would actually
  put money through a binary double, and requires the guard to catch it.

* **N9 is the behavioural canary, and it records its own LIMIT.** N4 and N5 stop at a settings
  assertion, which is a configuration echo and not a discriminator. N9 bypasses that and drives the
  arithmetic. Observed table, at `(precision, mode)` against 36 re-derived periods:

  | setting | ARM reproduces the oracle on | reading |
  |---|---|---|
  | `(19, HALF_UP)` | **29 of 36** | baseline, the ratified setting |
  | `(12, HALF_UP)` | **29 of 36** | **IDENTICAL — no T55 shape separates 19 from 12** |
  | `(8, HALF_UP)` | **22 of 36** | breaks, so the re-derivation *is* precision-sensitive |
  | `(19, HALF_EVEN)` | **29 of 36** | **IDENTICAL — no T55 shape has a tie at the rounding boundary** |

  The leg therefore requires only what it can prove: that a wrong precision breaks the
  re-derivation. The two identical rows are **recorded, not hidden** — they are the reason
  `ATTESTATION.md` §4 states that precision 19-vs-12 and HALF_UP-vs-HALF_EVEN are **provenance**
  here and not witnessed by these values. (HALF_UP *is* witnessed for the tenant, by T36's
  half-cent tie inside the preconditions gate — a different request, and the distinction is kept.)

  The 7 periods where ARM does not reproduce the oracle at the baseline are **not failures**: all
  seven are `p4` (`FEB_29_PERIOD_ONLY`) legs where the oracle correctly took the **PLAIN** branch,
  and all seven are attributed `PLAIN` — `LB-LEAPIN-p4` p2, `LB-LEAPOUT-p4` p1 and p2,
  `LB-DEC15IN-p4` p1, `LB-DEC15OUT-p4` p1, `LB-MULTI3-p4` p1, `LB-HALFYR-p4` p2. (Two of those,
  `LB-LEAPOUT-p4` p1 and `LB-HALFYR-p4` p2, are non-crossing periods where the arm cannot fire at
  all and effect (a) acts instead.) The analysis **fails** on any period it cannot attribute to one
  of the two branches; there are none in this set.

## What these legs do NOT prove

They prove the recipe rejects a *misconfigured* run and a *tampered* capture. They cannot prove it
would reject a *correctly configured run of a wrong oracle* — no fire has a second Fineract build to
test that against. `[UNVERIFIED]`, unchanged from T48.
