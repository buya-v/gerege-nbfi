# t388-accrual-capture — THE FIRST ACCRUAL OBSERVATIONS IN THIS PROGRAM

**RAW OBSERVED CAPTURE. NOTHING HERE IS PROMOTED.** No file under `.softhouse/vectors/` was
created, edited or read-for-write by this task; promotion is a separate follow-on.

The bar has printed the same sentence on every conformance run for weeks:

> `ledger.accrual.entry` — **ENTIRELY UNGRADED** … **NOT ONE JOURNAL ENTRY IN THIS TENANT
> ARRIVED THROUGH A RECEIVABLE SLOT.**

**It is now false.** Nine journal entries arrived through a receivable slot — three
`INTEREST_RECEIVABLE` (slot 7), three `FEES_RECEIVABLE` (slot 8), three
`PENALTIES_RECEIVABLE` (slot 9) — and **no GL account that any promoted vector reads was
moved to get them.**

Start with **`ORACLE-STATE-MOVED-BY-T388.md`**. It is the record of what this capture
permanently did to the shared reference oracle, the derived blast-radius list, and the P0
before/after table.

## The expensive route, which T352 named as correct and declined to pay for

T352 measured the cheap route down to one missing ingredient — a loan on product 28, whose
accrual mapping is already complete and whose accrual job is already active — and then refused
it, because product 28's slot 9 resolves to **gl 16, a promoted leg of LDG-01, LDG-02 and
LDG-03**, through a mapping A2-314/403 hold inadmissible. T388 pays the expensive route
instead: **thirteen new GL accounts, a new ACCRUAL_PERIODIC product, a new client, a new
loan**, so that the accrual posts into accounts nothing grades.

## Files

| path | what |
|---|---|
| `ORACLE-STATE-MOVED-BY-T388.md` | **read first.** What moved, what did not, the blast radius, the P0 check |
| `env.sh`, `cap11.sh`, `capsql.sh`, `manifest.sh` | the capture rig, byte-identical copies of `.softhouse/capture/t352-a2-next-tranche/`'s. Copied rather than edited, because those files have produced committed evidence (T114) |
| `10-mkreq-glaccounts.py` | emits the thirteen GL-account bodies from one table |
| `11-derive-forbidden-set.py` | **DERIVES** the set of GL accounts any promoted vector reads, and checks disjointness. `--check a,b,c` exits 1 on overlap |
| `20-create-glaccounts.sh` | the thirteen `POST /glaccounts` calls, each with a task-naming `Idempotency-Key` |
| `30-casualty-sweep-t388.sh` | **where I looked** for things this movement invalidated. 18 selectors, calibrated both ways, exit status read. Run it AFTER `git add -A` |
| `req/` | every request body, as sent |
| `sql/` | every query, as executed |
| `out/` | every observation: `.req` wire bytes + `.req.sha256`, `.http` record incl. the key sent, `.status`, `.json`; and for SQL `.sql` + `.sql.sha256` + `.psql` + `.txt` |
| `out/PROBES-APPEND-T388.tsv` | **an unpaid obligation.** The attribution rows for `t363-oracle-baseline/PROBES.tsv`, staged here because that file is outside this task's write grant |

## The observations, and what each one proves

| capture | proves |
|---|---|
| `T388-B01`, `T388-B02`, `T388-B03`, `T388-B04`, `T388-B05` | the BEFORE state, taken before anything was written, so the record is a diff |
| `T388-D01` | the forbidden set `{1,2,4,6,8,10,15,16,17,18,21,22}`, derived from all 64 vectors |
| `T388-D02` | T388's accounts 35–47 are disjoint from it. Exit 0 |
| `T388-D03` | the same checker RED-DRIVEN: `--check 16,41` → intersection `[16]`, FAIL, exit 1 |
| `T388-G01`..`G13` | thirteen clean GL accounts created, ids 35–47, each with its slot named in the body |
| `T388-P02` | the new ACCRUAL_PERIODIC product 63, `accounting_type = 3`, MNT, 13 clean slots |
| `T388-P03` | client 3 — ovog / patronymic / given name, registration number `УБ90051423` |
| `T388-P04` | **a refusal, recorded as data.** HTTP 400, charge amount mandatory. The key is burned |
| `T388-P05`, `P06`, `P07` | loan 8 applied, approved, disbursed — every one with an `Idempotency-Key` |
| `T388-P08` | the schedule BEFORE accrual: interest, fee and penalty on all six instalments |
| `T388-A01` | **the accrual trigger**, `POST /runaccruals` `tillDate 15 April 2026`, fired MANUALLY |
| `T388-A02` | **the nine receivable-slot entries with their slot decode**, plus the double-entry check in integer minor units |
| `T388-A03`, `A04`, `A05` | the same three accruals read back **at the contract boundary**, `GET /journalentries` |
| `T388-A06` | product 63's mapping read back |
| `T388-A07` | loan 8 after accrual |
| `T388-S01` | the AFTER state, including the twelve-account P0 table |
| `T388-SW01` | the casualty sweep, 18 selectors, exit 0, calibrated positive and negative |

## What a reader must not conclude from this directory

- **Not that accrual is graded.** Nothing is promoted; `ledger.accrual.entry` is still outside
  the graded domain and the bar will still say so.
- **Not that the SCHEDULED JOB was observed.** The accrual was triggered by hand through
  `POST /runaccruals`, which reaches `addPeriodicAccruals(tillDate)` by the same path job 16
  does but with the date supplied by the caller. This is not evidence about the scheduler.
- **Not that these amounts are a parity claim.** They are one loan's observed accrual on one
  set of terms. A parity vector needs the promotion task to decide what is graded, and the
  ratified `MathContext (19, HALF_UP)` question applies to it exactly as it does to every other
  vector in this store.
