# Decisions — Fineract as the Gerege NBFI core

Recorded by the driver from Buyan's answers on 13 Sep 2026. Each decision is **Buyan's**, and it applies to the
**Fineract-core road explored in this folder**. It does not edit `CLAUDE.md` or the Go-port program, which stays
suspended while the spike runs.

| # | Question | Buyan's decision | Consequence for the spike |
| --- | --- | --- | --- |
| FD-1 | Run the 1–2 week spike? | **Yes.** The Go port stays suspended meanwhile. | All spike work lives in `gerege-fineract/`; no other folder is touched. |
| FD-2 | Money stored as decimals instead of whole minor units | **Relaxed** for a Fineract core. | Accept Fineract's `DECIMAL(19,6)`. The Gerege edge refuses any amount finer than the currency's minor unit (MNT: 2 digits). Still no floating point, anywhere. |
| FD-3 | Stored balances instead of always-derived ones | **Relaxed** for a Fineract core. | Fineract's stored balances are caches. The journal stays the source of truth, and a reconciliation job proves the caches match it. |
| FD-4 | Name fields | **Relaxed** for a Fineract core. | Ovog, patronymic and given name map onto Fineract's name fields (a documented mapping), or live in a data table behind a Gerege API. The spike picks one with evidence. |
| FD-5 | Hovd (+07) business date | **Ulaanbaatar time** for the whole company. | One tenant, time zone Asia/Ulaanbaatar. |
| FD-6 | Who operates the Java service | **Gerege's own team.** | The spike must leave runnable, documented operations (build, start, stop, upgrade) that a small team can own. |

## Unchanged — still hard rules on this road

- PostgreSQL only. **Oracle Database is prohibited.** "The oracle" means the Fineract reference instance, never Oracle
  Database.
- No floating point in any money path, including intermediate calculation. HALF_UP rounding at precision 19; MNT is ISO
  4217 496 with 2 minor digits; Asia/Ulaanbaatar.
- The ledger is double-entry, and corrections are reversing entries.
- `Idempotency-Key` is mandatory on every money-movement request.
- No deposit-taking is ever enabled: the deployment is an NBFI (Law on Non-Banking Financial Activities, Art. 12.1.3
  and 12.1.4). Savings is never described as insured, protected or guaranteed.
- National ID is 10 characters: 2 Cyrillic letters and 8 digits, validated structurally.
- No US payment rails or vendors. The Mongolian rails are Banksuljee RTGS above MNT 5,000,000 and ACH+ at or below it,
  with the threshold taken from config.
- The standing Fineract reference instance (tenants `gerege` and `default`) is never written. SQL against it is
  read-only.
- Cutover, FRC / parallel-run sign-off and licence facts remain Buyan's gates.
