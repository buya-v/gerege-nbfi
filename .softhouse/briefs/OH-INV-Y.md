# OH-INV-Y — map ASSET_TRANSFER(100), settle the transfer, confirm the purchase-price gap

Worktree: `/Users/buv/oh-gerege-invy` (branch `feat/OHINVy`)
Work ONLY in that directory. You hold the oracle.

## THIS IS THE FIFTH RUN AT THIS QUESTION. READ WHAT THE OTHER FOUR ESTABLISHED.

**Do not re-derive any of it.** Three of the four died with nothing written, all from
re-researching things that were already known.

* **`OH-GAP-M`, `OH-INV-N`** — died at the iteration cap reverse-engineering Fineract source.
* **`OH-INV-Q`** — drove COB and got a refusal: `ProductToGLAccountMappingNotFoundException`,
  because loan **product 2 has `accountingRule: NONE`**.
* **`OH-INV-W2`** — created transfer **17** on **loan 12 / product 3** (accounting-enabled),
  which **cleared** that gate and refused at a deeper one:

      FinancialActivityAccountNotFoundException: Financial Activity with Id 100
        FinancialActivityAccountRepositoryWrapper.java:48
        <- InvestorAccountingHelper.java:120

`ASSET_TRANSFER(100, "assetTransfer", GLAccountType.ASSET)` is real
[`AccountingConstants.java:439`], the lookup takes the **organization** branch, and tenant
`gerege` seeds only financial activities **101** and **102**. Both earlier runs **refused to
manufacture** the missing reference data, correctly.

**Buyan has now authorised creating it, through the API.** That is your first step.

## THE MAP — all of it. Do not go looking for these.

**Create the mapping** — `POST /v1/financialactivityaccounts`
[`FinancialActivityAccountsApiResource.java:117`], body is exactly two fields
[`…ApiResourceSwagger.java:53-56`]:

    {"financialActivityId": 100, "glAccountId": <id>}

**The GL account to map it to: `glAccountId` 6, `OHLGR-Transfers-Suspense`, glCode
`OHLGR-10011`, type ASSET, usage DETAIL.** `OH-GL-R` created it for exactly this purpose.
**Verify it still exists and is ASSET/DETAIL before using it**; if it does not, say so and
choose another ASSET DETAIL account, naming your reason.

**Worked examples already in the tenant** — `GET /v1/financialactivityaccounts` returns:

    id=1  financialActivity 101 cashAtMainVault -> glAccount 1 SEED-Provisioning-Asset
    id=2  financialActivity 102 cashAtTeller    -> glAccount 1 SEED-Provisioning-Asset

**Other ASSET DETAIL accounts, if you need one:** 5 `OHLGR-Loan-Portfolio`,
7 `OHLGR-Interest-Receivable`, 8 `OHLGR-Fees-Receivable`, 9 `OHLGR-Penalties-Receivable`,
1 `SEED-Provisioning-Asset`.

**The state you inherit** (verify, do not assume): transfer **17** on **loan 12**, status
**PENDING**, `purchasePriceRatio` **"97.25"**, `details` absent; business date **2026-09-02**;
`LOAN_CLOSE_OF_BUSINESS` carries `EXTERNAL_ASSET_OWNER_TRANSFER` at order 7; product 3 is
`ACCRUAL PERIODIC` with **12** mapping rows.

**Running COB:** `POST /v1/jobs/{id}?command=executeJob` returns **202 with an empty body** —
that is normal, and the empty body IS the observation; record the status line. **The
investor step is caught PER-LOAN**, so a job-level success does not mean the step succeeded.
Read the per-loan outcome. `OH-INV-Q` detected a WARN-and-SKIP exactly this way.

## The path

1. Verify the state above.
2. **`pg_dump -Fc` snapshot** to `/Users/buv/gerege-oracle-snapshots/`. **Never commit a
   `.dump`** — `*.dump` under `capture/` is gitignored.
3. Create the ASSET_TRANSFER(100) mapping. Capture the request and the response.
4. Re-run COB. Capture the job response and the per-loan outcome.
5. Read back the transfer and
   **`GET /v1/external-asset-owners/transfers/17/journal-entries`**.

## THE CONFIRMATION THIS RUN EXISTS FOR

Established from pinned source `426a23544` — **confirm, do not re-derive**:
`purchasePriceRatio` is a **`String`** [`ExternalTransferData.java:34` — **:34, not :16**,
which is licence header]; all seven non-test `getPurchasePriceRatio()` sites are
setter-to-setter copies; `fineract-investor` has **99 files and ZERO `multiply` calls**;
`AccountingServiceImpl` has **zero** occurrences of `urchasePrice` and accumulates
face-value outstanding with `.add` [`:193,:220,:235,:250,:261`], posting at `:273,:277`.

**With a settled transfer, show the posted journal entries equal the OUTSTANDING, not
`0.9725 × outstanding`.** Loan 12's outstanding is ~100000 principal, so the two differ by
~2750 — obvious at a glance. **Capture it. That capture is the confirmation.**

**If the oracle contradicts any of the four items, the ORACLE WINS and you say so loudly.**
`OH-GAP-M` found a MANIFEST "documented gap" that was **false** and had survived weeks into
the published record. `OH-INV-W2` proved a driver premise false and said so — that is the
standard.

**If it refuses again, the refusal IS the result.** Capture status, error body and the
source line that raised it. **Do not SQL-insert anything.** The only reference data you may
create is the ASSET_TRANSFER(100) mapping above, through the API.

## FINDING B — the details seam, if it settles
`ExternalAssetOwnerTransferDetails.java:83-88` derives
`totalOutstanding = principal + interest + fees + penalties`; the mapper exposes `details`
at `ExternalAssetOwnersTransferMapper.java:48`. `OH-INV-Q` found the details table empty and
**deleted all four candidate drives with the argument** rather than merging them inert. A
settled transfer makes them observable for the first time:

1. **`totalOverpaid` is EXCLUDED.** `setTotalOverpaid` (`:87-90`) is the only component
   setter that does not call `updateTotalOutstanding()`. `OH-GAP-M`'s agent guessed
   "− overpaid" — a mistake a real reader made.
2. Recomputed on **every** component setter (`:63-81`) — I-3 in Fineract's own code.
3. **Null coalesces to ZERO, not a refusal** — `Objects.requireNonNullElse(x, ZERO)`.
4. Columns are **`scale = 6, precision = 19`** (`:45-61`) — a **trap, not a target**: if a
   residue value appears, **REFUSE it**, never vector it.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument.** Say which, per drive; report every
kill count. **Prove the instrument was live** — controls, plus
`investor-wrong-blank-status` and `investor-wrong-fabricates-transfer`, which each kill 1.

## Measuring it
    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1
**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** If a control is wrong, the instrument is wrong.

## Rules of evidence
- **Request bodies must be BYTE-STABLE** under a binary-double round trip. Integer tokens;
  never re-serialise through `json.dumps` of a parsed number. A run this week had its whole
  salvage **reverted** by that HARD guard over `100.00 -> 100.0`. **Check your own `req/`
  before committing.**
- **Cite `file:line`**, from the FILE, not a comment-stripped view.
- **Never synthesise a value you did not observe.** `capture_ref`, `capture_sha256`,
  `citation`; re-verify after writing.
- **SQL is READ-ONLY.** Never write the `default` tenant.
- **Beware unterminated quotes.** A `docker exec … psql -tAc "SELECT …` with no closing
  quote **hung a run to death** this week; `C-c` does not rescue it. Prefer the REST API.
- Capture directory named for its **SUBJECT** with an `OWNER.md`; names freeze at first
  commit.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Double-entry, append-only.** Balances derived, never written (I-3).
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `investor`.**

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings at **exactly 12 (class, file) pairs**, wrong-ledger
census **17**. **Run it EARLY.**

~500 iterations. **Commit by iteration 150** even if incomplete — four runs have died at the
cap, one salvage was reverted outright, and a committed capture survives what an
uncommitted one does not.
