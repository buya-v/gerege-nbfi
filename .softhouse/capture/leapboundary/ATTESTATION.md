# T55 — attestation, under the eight-point rule in `.softhouse/reference-oracle.md`

What was asserted **mechanically** about the environment actually in force, and — equally — what was
**not** witnessed. This follows T48's corrected form and repeats neither the "two ambient witnesses"
defect (T37, T39) nor the "attested reads as witnessed" defect (T48 §7).

---

## 1. The two contexts, named separately

* **THREADED** — the `MathContext` object actually passed to the arithmetic.
* **AMBIENT** — `MoneyHelper.getMathContext()` for the tenant.

**On Path B these are the same object, and that is cited, not assumed.**
`LoanScheduleAssembler.java:753` and `LoanScheduleGeneratorServiceImpl.java:44` do
`mc = MoneyHelper.getMathContext()` and pass **that same object** into `generate(mc, …)`
[VERIFIED — the wiring, quoted by T48 §4 and re-checked for this pass]. Every T55 capture is a
Path B capture, so the ambient reading here **is** evidence about the arithmetic. That is the whole
reason Path B was chosen (§ *Which seam* in `PROVENANCE.md`).

## 2. What the preconditions gate asserted, per capture run

`bin/t55-capture.sh` refuses to POST anything until T36's 21-assertion gate passes. Recorded
verbatim in `out/preconditions.txt`; all 21 PASS. The load-bearing ones:

| fact | observed | how it was read |
|---|---|---|
| Image digest | `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` | `docker image inspect` |
| Jar `git.commit.id` | `426a23544e8426a38ae43ae404670a0a7e85b9eb` | `git.properties` **out of the deployed jar** |
| Jar `git.dirty` | `false` | same |
| `MoneyHelper.PRECISION` | **19** | `javap -constants` on the **deployed bytecode inside the running container**, not from source |
| Tenant | `gerege` | `fineract_tenants.tenants` |
| Tenant timezone | `Asia/Ulaanbaatar` (zone id, never an offset) | same |
| `c_configuration.rounding-mode` | **4** = `HALF_UP` | `fineract_gerege.c_configuration` |
| Running JVM's init line | `Initialized rounding mode for tenant 'gerege': HALF_UP`, **since this container's StartedAt** | `docker logs --since StartedAt` |
| PostgreSQL | `PostgreSQL 18.3 (Debian 18.3-1.pgdg13+1) … aarch64` | `select version()` |
| Prohibited engines | **0** hits for `ojdbc` / `oracle.jdbc` / `:1521` / `com.mysql.cj` / `mariadb` / `go-sql-driver` in the container env, and **0** prohibited driver jars in `fineract-provider.jar` | gate assertions P5/P6 |
| MNT | `decimal_places = 2`, enabled for the tenant | `m_currency`, `m_organisation_currency` |

Additionally asserted by `t55-capture.sh` itself:

* the pinned checkout `/Users/buv/fineract` is at `426a23544e…` and `git status --porcelain` is **empty**;
* products **7 / 3 / 4** are ACT/ACT (`days_in_year_enum = 1`), DAILY (`interest_calculated_in_period_enum = 0`),
  `days_in_month_enum = 1`, and carry `daysInYearCustomStrategy` **UNSET / FULL_LEAP_YEAR / FEB_29_PERIOD_ONLY**;
* the three products agree on **22 other schedule-feeding columns** (`count(distinct(...)) = 1`), so
  "these captures differ **only** in the day-count setting" is an assertion, not a claim. Negative
  leg **N8** shows that same SQL returning `2` for a deliberately mismatched triple, so it is not a
  tautology;
* `m_loan` = **0**, `m_product_loan` = **21**, `m_client` = **2** — **before and after**, unchanged;
* `RestartCount` = **0** on both containers, and their `StartedAt` are `2026-08-18T09:51:53Z`
  (fineract) and `2026-08-17T11:30:08Z` (postgres) — neither restarted during or between the
  capture, the determinism re-run and the negative tests.

## 3. A behavioural canary, not a configuration echo

`reference-oracle.md` rule 6: a configuration echo is not a discriminator. Two canaries ran.

* **The rounding mode, behaviourally.** T36's half-cent tie
  (`1,162,502.50 × 0.018 = 20,925.045`) is asserted by the gate **before** the captures and returned
  **`20925.05`** — the `HALF_UP` answer; `HALF_EVEN` would return `20925.04`. That is the
  arithmetic answering, not a row in `c_configuration`. Observed: `out/preconditions.txt`.
* **The re-derivation's own precision sensitivity.** Negative leg **N9** drives the re-derivation
  off (19, HALF_UP) and requires it to stop reproducing the oracle. At **precision 8** it does:
  ARM agreement falls **29 → 22 of 36 periods**. So the agreement at (19, HALF_UP) is a real
  reproduction, not an insensitive identity.

## 4. **What was NOT witnessed** — stated so "attested" does not read as "witnessed"

This is the section T48 §7 exists to force, and T55's answer is partly negative.

* **Precision 19 vs 12 is NOT witnessed by these captures.** Negative leg N9 shows the ARM
  re-derivation reproducing the oracle on the **same 29 of 36 periods** at precision 12 as at
  precision 19. No T55 shape separates them. For this axis, (19, …) is **provenance** — the
  compile-time constant `MoneyHelper.PRECISION = 19` [VERIFIED: `fineract-core/.../MoneyHelper.java:35`,
  `:91-93`], read out of the deployed bytecode by the gate — and **not** a discrimination.
  `TO_BE_CAPTURED` for this arm; T39's separating shape (50 M / 360 months) was not re-run here.
* **HALF_UP vs HALF_EVEN is NOT witnessed by these captures' own values.** N9 shows identical
  agreement at HALF_EVEN: no T55 shape lands a tie at the rounding boundary. HALF_UP **is**
  behaviourally witnessed for the tenant, by T36's half-cent canary in the gate (§3) — but that is
  a different request, and the distinction is recorded rather than blurred.
* **Path A and Path A2 were not used.** No claim is made here about either seam. Path A is
  excluded on evidence (it drops the independent variable — `PROVENANCE.md` § *Which seam*), and
  Path A2's admissibility as a capture path remains the open `user` question T48 left it as.
* **The enumeration of ambient leaks is not claimed complete.** It has been wrong twice in this
  program (T43 P1-T43-2, T46 N46-1). No T55 capture carries a **charge**, so the T46 N46-1 charge
  rounding leak is not reached; that is an observation about reach, not a completeness claim.
* **No claim that the recipe would reject a correctly-configured run of a *wrong* oracle.** No fire
  has a second Fineract build. `[UNVERIFIED]`, unchanged from T48.

## 5. No float, anywhere in a stored or compared value

* The raw responses are **float-shaped on the wire** — Fineract's REST layer serialises
  `BigDecimal` as a JSON *number* (finding **T44-X1**). Following T46's decision the raw bytes are
  kept unmodified as the canonical artefact.
* Every raw file has an **exact-text sidecar** `*-exact.json` in which every number is a JSON
  **string** carrying the literal characters that were on the wire, produced with
  `json.loads(text, parse_float=str, parse_int=str)` so **no binary double is ever constructed**.
  All 33 sidecars carry **zero** bare JSON numbers, checked by `analysis/t55-analyse.py`.
* **All comparison and all re-derivation runs off the sidecars**, via `decimal.Decimal` built from
  exact decimal text. Money differences are reported in **integer minor units**.
* Negative leg **N7** removes `parse_float=str, parse_int=str` from the sidecar writer and requires
  the guard to catch it — it does. The float guard is not inert.
* The only non-integer input is the **rate** `21.6` (a rate, not money). It is written as exact
  decimal text in the request and Fineract parses request numbers to `BigDecimal`; the
  re-derivation uses `Decimal("21.6") / Decimal(100)`. Comparison rule: exact string equality of
  `Decimal` values, never a tolerance (finding **T17-F6** — a transcribed 12-dp factor hides
  divergence in digits 13+).

## 6. Determinism

| set | first run | re-post | result |
|---|---|---|---|
| all 33 Path B captures | `out/LB-*-raw.json` | `out/rerun/LB-*-raw.json` | **byte-identical, 33 of 33** |

`bin/t55-determinism.sh` re-posts the **same committed request files**, so a change in the
authoring code cannot hide in the re-run.

## 7. The recipe is proved FAILABLE on nine axes

See `NEGATIVE-TESTS.md`. **9 of 9 legs breached as required**, recorded in
`NEGATIVE-TESTS-OUTPUT.txt`.

## 8. `(19, tenant mode)` is the LOAN-PATH rule

Every T55 capture is on the loan path, so the rule applies. It is **not** a Fineract-wide rule —
see `reference-oracle.md`'s corrected N-3 inventory (savings/deposits use `DECIMAL64` and
`MathContext(15|10, …)`; one precision-8 site is in **share accounts**).

## Digests

```sh
cd .softhouse/capture/leapboundary && find . -type f | sort | xargs shasum -a 256
```

Per-capture digests of the raw responses are recorded in `out/DIGESTS.txt` by the capture script.
