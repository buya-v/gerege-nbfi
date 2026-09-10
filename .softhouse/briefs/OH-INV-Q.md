# OH-INV-Q — settle the investor transfer seam. THE NAVIGATION IS ALREADY SOLVED.

Worktree: `/Users/buv/oh-gerege-invq` (branch `feat/OHINVq`)
Work ONLY in that directory.

## TWO RUNS HAVE DIED ON THIS QUESTION. READ WHY BEFORE YOU START.

`OH-GAP-M` and `OH-INV-N` both hit the 500-iteration limit on this task and **both wrote
nothing at all**. Roughly a thousand iterations, zero artefacts. Neither failed on a
blocker. Both failed on **navigation**: they tried to reverse-engineer Fineract's COB
business-step configuration out of Java source — `ConfigJobParameterServiceImpl`,
`BusinessStepCategory`, `LoanBusinessStepCategoryServiceImpl`, `CommandWrapperBuilder` —
and ran out of budget before reaching an endpoint.

Four `curl` calls answer what they spent a thousand iterations on. Those calls are below.
**Do not read Java to rediscover them.** If you find yourself in `fineract-cob/` working
out how step configuration is stored, stop: that is the exact hole both predecessors fell
into, and it is already filled.

The driver has verified against the live oracle, this morning:

* `GET /jobs/LOAN/available-steps` returns **12** steps and
  **`EXTERNAL_ASSET_OWNER_TRANSFER` IS AMONG THEM.** The investor module is enabled
  (`InvestorModuleIsEnabledCondition` reads `fineract.module.investor.enabled`).
* `GET /jobs/LOAN_CLOSE_OF_BUSINESS/steps` currently returns **six** configured steps and
  the investor step is **not** one of them. That, and only that, is why no transfer has
  ever settled here.
* Business date is **2026-09-01**, COB date **2026-08-31**.
* Transfer 1 on loan 6 is **`PENDING`**, `purchasePriceRatio` `"97.25"`, `details` **absent**.

## THE PATH. Four steps. Take them first, before any analysis.

Tenant header `Fineract-Platform-TenantId: gerege` on every call. `curl -k -u mifos:password`.
Base `https://localhost:8443/fineract-provider/api/v1`.

1. **Add the step to the COB config.** `PUT /jobs/LOAN_CLOSE_OF_BUSINESS/steps` with the
   six existing steps PLUS `EXTERNAL_ASSET_OWNER_TRANSFER`. **`GET` the current config
   first and build the body from what it returns** — do not retype the six from this
   brief; if the config has drifted you would silently drop a step.
2. **Advance the business date past the settlement date** (`2026-09-01`).
   `enable-business-date` is the one configuration row you may change.
3. **Run COB** and confirm the transfer moved `PENDING` → `ACTIVE`/settled.
4. **Read it back.** `GET /external-asset-owners/transfers?loanId=6`. `details` should now
   be present, carrying the six derived balances.

**Snapshot the database before step 1** (`pg_dump -Fc`), as `OH-INV-N` correctly did. If
any step fails, say what happened and stop — a half-run COB is worth reporting, not
papering over.

If step 1 or 3 refuses, **that refusal is itself a finding**: capture the exact status and
error body, record it, and fall back to Finding A below, which needs none of this.

## FINDING A — the purchase price is an ORACLE GAP, established from source. CONFIRM ONLY.

The transfer purchase price (97.25% of an outstanding balance) is not merely uncaptured:
**Fineract never computes it anywhere.** Established by the driver at pinned commit
`426a23544`, all re-checkable in seconds — **do not re-derive this**:

1. `purchasePriceRatio` is a **`String`** — `data/ExternalTransferData.java:16`.
2. **All seven** non-test call sites of `getPurchasePriceRatio()` in the whole codebase are
   **setter-to-setter copies**, not one an operand: `enricher/LoanAccountDataV1Enricher.java:49`;
   `service/LoanAccountOwnerTransferServiceImpl.java:128`, `:144`;
   `service/ExternalAssetOwnersWriteServiceImpl.java:322`, `:348`;
   `service/serialization/serializer/investor/InvestorBusinessEventSerializer.java:102`;
   `cob/loan/LoanAccountOwnerTransferBusinessStep.java:327`.
3. `fineract-investor/src/main/java` has **99 Java files and ZERO `multiply` calls**.
4. `service/AccountingServiceImpl.java` — which creates the transfer's journal entries —
   contains **zero** occurrences of `urchasePrice`. Its amounts are the outstanding
   components at **face value**, accumulated with `.add` at `:193`, `:220`, `:235`, `:250`,
   `:261`, posted at `:273`/`:277`.

**Your confirmation:** once the transfer has settled, `GET /transfers/{transferId}/journal-entries`
and show the posted amounts equal the **outstanding**, not 0.9725 × it. Capture it. Then
record the gap in the investor MANIFEST with those four items and the endpoints checked.

**A documented gap is a SUCCESSFUL OUTCOME.** But state it from what you OBSERVED — and if
the oracle contradicts any of the four items, **the oracle wins and you say so loudly.**
`OH-GAP-M` found a MANIFEST "documented gap" that was **false** and had survived for weeks
into the published record.

## FINDING B — the seam that IS observable. This is the real work.

`domain/ExternalAssetOwnerTransferDetails.java:83-88`:

    private void updateTotalOutstanding() {
        this.totalOutstanding = MathUtil.add(getTotalPrincipalOutstanding(), getTotalInterestOutstanding(),
                getTotalFeeChargesOutstanding(), getTotalPenaltyChargesOutstanding());
    }

and `service/ExternalAssetOwnersTransferMapper.java:48` maps `details` onto the read
endpoint. Four properties, each a real way a port goes wrong. **Register a drive for each
and promote a vector only where a capture actually SEES it.**

1. **`totalOverpaid` is EXCLUDED from the total.** `setTotalOverpaid` (`:87-90`) is the ONLY
   component setter that does not call `updateTotalOutstanding()`. A port that folds
   overpaid in — added or subtracted — is wrong. `OH-GAP-M`'s agent guessed "− overpaid" in
   its final message, so this is a mistake a real reader made.
2. **The total is RECOMPUTED on every component setter** (`:63-81`), never independently
   written — I-3 in Fineract's own code.
3. **Null coalesces to ZERO, not to a refusal** — `Objects.requireNonNullElse(x, ZERO)`.
4. **Columns are `scale = 6, precision = 19`** (`:45-61`) — they can hold sub-minor digits.
   A trap, not a target: see the residue rule below.

## THE RULE ON INERT DRIVES

**A drive that kills ZERO is a finding to resolve, never something to merge.** Either
promote a vector that sees it, or **delete it with the argument**. Say which, per drive, in
the commit message. **Report the kill count for every drive.** Never let one merge inert.

## Measuring it

`.softhouse/briefs/tools/kills.sh <ctx> <impl> [worktree]`, `redcount.sh`, `ohwatch.sh`.
**Repaired 2026-09-09**: they no longer print a silent `0` on failure — they exit 2 with
empty stdout and a reason on stderr. **An empty result means the MEASUREMENT FAILED, not a
zero-kill drive.** Control-test before trusting any number:

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1

If a control is wrong, the instrument is wrong — not the tree.

## Rules of evidence
- **Cite `file:line`** for any claim about what the port or the oracle computes or refuses.
- **Never synthesise a value you did not observe.** Every vector carries `capture_ref`,
  `capture_sha256`, `citation`; re-verify the hash after writing.
- **SQL is READ-ONLY.** Never write the `default` tenant.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  MNT = ISO 496, minor unit 2.
- Balances **derived, never written** (I-3); append-only (I-4).
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`. HALF_UP and HALF_EVEN differ
  ONLY on an exact half-minor tie **whose TRUNCATED value is EVEN** (0.025 → .03 vs .02;
  0.035 → .04 under both). `OH-CAP-J` stated this INVERTED; this form is correct.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08. The `scale = 6` columns
  mean residue CAN appear: if it does, **REFUSE it — never write a parity vector for a
  residue value.** Record the observation and move on.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `investor`.** Wandering outside it is a rejection.

## The bar, before you claim done
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh`. Expect exit 2 as the
§4.4.2 recorded decision with the ledger finding set at **exactly 12 (class, file) pairs** —
that is green. Report every drive's kill count and every capture's sha256.

## Budget
You have ~500 iterations. **Two predecessors spent theirs on navigation and wrote nothing.**
Take the four steps above FIRST. If you are 100 iterations in without a settled transfer or
a recorded refusal, stop exploring and write down what you have.
