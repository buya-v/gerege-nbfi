# T22 handoff — independent audit of the Path B captures

Branch `softhouse/T22-pathb-capture-audit-v2`. Full audit: `.softhouse/reviews/T22-pathb-capture-audit.md`.
Verdict: **ACCEPTED WITH REQUIRED CHANGES** (6 × P0, 8 × P1).

## What I did

- **Reproduced all four captures three ways**, all byte-for-byte identical to the committed
  `out/B-0*-raw.json`: (1) committed request bytes against the existing `default` tenant; (2) re-hashed the
  killed worker's `t22-probe` outputs, which were produced through freshly created products 5–8 — an
  independent reproduction I verified rather than trusted; (3) **a genuinely fresh tenant I provisioned**
  (`gerege`, PostgreSQL db `fineract_gerege`, `Asia/Ulaanbaatar`, `rounding-mode = 4`), where the products
  land at ids 1–4 exactly as `REPRODUCE.md` assumes.
- **Asserted every engine precondition.** Image digest matches; the jar's own `git.properties` carries
  `426a23544e…` with `git.dirty=false`; `org.postgresql.Driver` + `jdbc:postgresql://db:5432/…`; PostgreSQL
  18.3; **zero** hits for `ojdbc|oracle.jdbc|:1521|com.mysql.cj|mariadb` in the container env, the jar
  (only driver is `postgresql-42.7.11.jar`), the empty `/app/plugins`, or `docker-compose-postgresql.yml`.
- **Verified both differentials isolate AND persist**, by diffing `to_jsonb(m_product_loan)` column by
  column in PostgreSQL: products 1↔2 differ only in `installment_amount_in_multiples_of`, 3↔4 only in
  `days_in_year_custom_strategy` (plus id/name/short_name). Payment-allocation rows identical.
- **Re-derived five schedules digit-for-digit from the pinned PROGRESSIVE source** in a model written from
  scratch (`t22-audit/t22_rederive.py`), including the final-installment residual-absorption rule
  (`ProgressiveEMICalculator.java:1202-1205`), at both HALF_UP and HALF_EVEN.
- **Mechanically checked ten property invariants on all four captures plus six of my own** — the first time
  anyone has. All pass, including "every money literal is exactly representable in integer minor units".
- **Settled the cross-path claim**: `B-01` money == pass-3 `P-MNT-1M2` in all 12 periods and all totals.
- **Settled both of the orchestrator's non-claims** with new probes at production settings.

## What I concluded

- **Path B does grade both fields Path A drops.** `installmentAmountInMultiplesOf` moves 12/12 periods;
  `daysInYearCustomStrategy` does too — but only via `FEB_29_PERIOD_ONLY`, because I proved
  `FULL_LEAP_YEAR` is byte-identical to the field being unset (probe `TP7` ≡ `B-03`). `B-04` is the vector
  with the discriminating power.
- **The report's rounding rule is wrong.** It says the EMI is "raised to the next multiple"; the oracle
  rounds to the **nearest** multiple under the tenant rounding mode (`Money.java:163-171`). I observed it
  rounding **down**: principal 1,190,000 → unrounded EMI `111,148.35` → applied `111,100.00`. This is P0
  because DEC-1 would have inherited the false rule.
- **The captures ran at HALF_EVEN, not the ratified HALF_UP** — proved by the server's own log
  (`Initialized rounding mode for tenant 'default': HALF_EVEN`, 2026-08-17, spanning the capture fire) and
  by `c_configuration.rounding-mode = 6`. And **the mode is live on this path**: at principal 1,162,502.50
  the two tenants return `20,925.05` vs `20,925.04` in period 1. The four captures are nevertheless
  mode-insensitive — established by re-observing them at HALF_UP, not by assumption.
- **Gap (a), timezone, is metadata only** — proved, not argued: the fresh `Asia/Ulaanbaatar` tenant returned
  the same four SHA-256 digests.
- **Non-claim (i):** `daysInYearCustomStrategy` has **zero** isolated effect under `SAME_AS_REPAYMENT_PERIOD`
  (probes `TP5` ≡ `TP6`, byte-identical), and the source says why unconditionally
  (`ProgressiveEMICalculator.java:1510-1516` returns with `daysInYear = 12` before reading it).
- **Non-claim (ii):** `daysInYearType`/`daysInMonthType` **do** move a progressive schedule under `DAILY`
  (`TP7` ≠ `TP8`) and are **inert** under `SAME_AS_REPAYMENT_PERIOD` (`TP9` ≡ `B-01`).
- **New unpinned behaviour found:** the EMI re-adjust loop (`ProgressiveEMICalculator.java:1258-1308`) can
  absorb a `multiplesOf` rounding difference entirely — my first rounding-mode probe (`TM1`) was neutralised
  by it, and both modes converged to the same schedule. No vector pins this. A Go port that implements the
  rounding but not the loop will diverge.

## What I could not settle, and what settling it needs

1. **`B-03`/`B-04` are not independently re-derived.** They run the DAILY + cross-year *partial-period* arm
   (`ProgressiveEMICalculator.java:1400-1414`, `calculatePeriodFractions` `:1550-1568`), a materially
   different code path from the one I modelled. Their numbers are reproduced, invariant-clean and internally
   consistent, but nobody has rebuilt them from source. **Needs:** extending `t22_rederive.py` with
   `calculatePeriodFractions` and the `rateFactorByRepaymentPartialPeriod` branch — a few hours, no oracle
   access required.
2. **The EMI re-adjust loop is unvectored.** **Needs:** a capture engineered to force ≥1 iteration of
   `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` and to leave a visible trace, then a matching
   Path-B vector.
3. **Whether any *other* Path B vector is mode-sensitive.** I proved the mode is live in general and
   insensitive for these four. Every future capture must assert the mode rather than inherit it.
4. **Nothing about paid/partial/multi-disbursement schedules.** Every capture on record is a clean unpaid
   schedule from `calculateLoanSchedule`. The whole `getDueAmounts` / repayment-processing surface is
   unvectored on Path B.

## State left on the oracle (mine vs not mine)

**No loan was persisted** — `select count(*) from m_loan` = 0 in both tenants.

- **New tenant `gerege`** (db `fineract_gerege`, `Asia/Ulaanbaatar`, `rounding-mode = 4`): currencies MNT+USD,
  clients 1–2, loan products 1–4 (the corpus, verbatim payloads) and 5–12 (`TP5..TP9`, `TM1`, `TM2`, `TR1`
  probes). **This tenant is the recommended capture target from now on** — it is the only one at ratified
  Gerege settings.
- **Tenant `default`**: I added only loan products **9 (`TM1`)** and **10 (`TM2`)** for the two-tenant
  rounding-mode probe. Products **5–8 (`T2A..T2D`) are the killed worker's**, not mine. I changed no
  configuration on `default`.
- **`fineract-fineract-1` was restarted twice** (17:50 and 17:51 local) — unavoidable, because tenants and
  `MoneyHelper` rounding modes are read only at startup and the runtime re-init endpoint
  (`InternalConfigurationsApiResource:87-92`) is `@Profile(TEST)`. Server is healthy.

All audit scripts, requests and raw captures are committed under `.softhouse/capture/pathb/t22-audit/`.
