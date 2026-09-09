# OH-INV-N — settle the investor purchase price, and promote the seam that IS observable

Worktree: `/Users/buv/oh-gerege-invn` (branch `feat/OHINVn`)
Work ONLY in that directory. The oracle is UP — probe before assuming.

## READ THIS FIRST: two-thirds of this task is already done, and NOT by you

OH-GAP-M was dispatched at this question and hit its 500-iteration limit mid-sentence.
The driver has since finished its source analysis independently. **Do not re-derive what
is below.** You are being asked to CONFIRM it against the live oracle and then do the part
neither of us can do from source. If you spend your run re-reading `fineract-investor`,
you have wasted it.

## FINDING A — the purchase price is an ORACLE GAP, and it is a gap BY CONSTRUCTION

The transfer purchase price (97.25% of an outstanding balance) is not merely uncaptured.
**Fineract never computes it, anywhere, in any form.** The evidence, all in the pinned
checkout at `426a23544`, all re-checkable in seconds:

1. `purchasePriceRatio` is a **`String`** — `data/ExternalTransferData.java:16`. It has no
   integer-minor-unit form and INV-01's own `_note` already says so.
2. **All seven** non-test call sites of `getPurchasePriceRatio()` in the entire codebase
   are **setter-to-setter copies**. Not one is an operand:
   `enricher/LoanAccountDataV1Enricher.java:49`,
   `service/LoanAccountOwnerTransferServiceImpl.java:128` and `:144`,
   `service/ExternalAssetOwnersWriteServiceImpl.java:322` and `:348`,
   `service/serialization/serializer/investor/InvestorBusinessEventSerializer.java:102`,
   `cob/loan/LoanAccountOwnerTransferBusinessStep.java:327`.
3. `fineract-investor/src/main/java` has **99 Java files and ZERO `multiply` calls.**
4. `service/AccountingServiceImpl.java` — which creates the transfer's journal entries —
   contains **zero** occurrences of the substring `urchasePrice`. Its amounts are the
   outstanding components at **face value**, accumulated with `.add` at `:193`, `:220`,
   `:235`, `:250`, `:261` and posted at `:273`/`:277`.

**Therefore the transfer's journal entries post 100% of outstanding, not 97.25%**, and no
endpoint can expose a settled purchase amount because no such amount is ever produced.

### Your job on Finding A — CONFIRM, then RECORD. Do not re-argue it.

Confirm on the LIVE oracle, because a claim about a running system deserves one
observation and this is cheap:

* `GET /external-asset-owners/transfers/{transferId}/journal-entries` for an **executed**
  transfer, and show the posted amounts equal the **outstanding**, not 0.9725 × it.
* Capture it. That capture is the evidence for the gap.

Then record it as a **permanent ORACLE GAP** in the investor MANIFEST — with the four
numbered items above and the endpoints you checked — so nobody reopens it in three weeks.

**A documented gap is a SUCCESSFUL OUTCOME.** It retires a question permanently. The
precedent is OH-CAP-I. The counter-precedent is OH-GAP-M question 2, where a MANIFEST
"documented gap" turned out to be **false** and had survived for weeks into the published
record — so state the gap in terms of what you OBSERVED, and if the oracle contradicts any
of the four items above, **the oracle wins and you say so loudly.**

## FINDING B — the seam that IS observable, and this is the real work

`domain/ExternalAssetOwnerTransferDetails.java:83-88` derives a money field:

    private void updateTotalOutstanding() {
        this.totalOutstanding = MathUtil.add(getTotalPrincipalOutstanding(), getTotalInterestOutstanding(),
                getTotalFeeChargesOutstanding(), getTotalPenaltyChargesOutstanding());
    }

and `service/ExternalAssetOwnersTransferMapper.java:48` **maps `details` onto the read
endpoint**. So this derived value is observable through the API. It is absent from
`.softhouse/capture/investor/out/transfer-read-loan-6-raw.json` only because that
transfer is **`PENDING`** and has no details row yet — **not** because the endpoint hides
it. Getting it requires driving the transfer to settlement (the COB step at
`cob/loan/LoanAccountOwnerTransferBusinessStep.java`), which is why this needs the live
oracle and could not be settled from source.

### The properties to test. THESE, not a number of files.

You are measured on **defects provably caught**, never on file count. OH-DEEP-E was given
a vector-count target and produced 18 files carrying 10 distinct facts; eight were
discarded at review. Do not repeat it.

Four properties are genuinely discriminating here. Each is a real way a port goes wrong:

1. **`totalOverpaid` is EXCLUDED from the total.** `setTotalOverpaid` at `:87-90` is the
   ONLY component setter that does not call `updateTotalOutstanding()`. A port that folds
   overpaid in — added OR subtracted — is wrong. **OH-GAP-M's own agent guessed
   "− overpaid" in its final message**, so this is a defect a real reader actually made.
2. **The total is RECOMPUTED on every component setter** (`:63-81`), never independently
   written. That is I-3 in Fineract's own code. A port that stores it as an independent
   field diverges the moment one component changes.
3. **Null coalesces to ZERO, not to a refusal** — `Objects.requireNonNullElse(x, ZERO)` on
   every setter. A port that refuses or NULLs a missing component is wrong.
4. **The columns are `scale = 6, precision = 19`** (`:45-61`) — the column can hold
   **sub-minor digits**. See the residue rule below; this one is a trap, not a target.

For each property: register a `investor-wrong-*` drive that models it, and promote a
vector only where a capture actually SEES it.

### THE RULE ON INERT DRIVES — read it twice

**A drive that kills ZERO is a finding to resolve, never something to merge.** Resolve it
one of two ways, and say which in the commit message:
  * promote a vector that sees it, or
  * **delete the drive with the argument for why the defect is unobservable.**
Never let one merge inert. Report the kill count for every drive you register.

### Measuring it

Use `.softhouse/briefs/tools/kills.sh <ctx> <impl> [worktree]` and `redcount.sh`. **They
were repaired on 2026-09-09** and no longer print a silent `0` on failure — they exit 2
with an empty stdout and a reason on stderr. If you get an empty result, the MEASUREMENT
FAILED; it is not a zero-kill drive. Control-test before trusting any number:

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1

If a control is wrong, the instrument is wrong — not the tree.

## Rules of evidence
- **Cite `file:line`** for any claim about what the port or the oracle computes or refuses.
  A claim without a file:line is not an argument.
- **SQL is READ-ONLY.** Never write the `default` tenant. `enable-business-date` is the
  only configuration row you may change.
- **Never synthesise a value you did not observe.** Every vector carries `capture_ref`,
  `capture_sha256` and a citation; re-verify the hash after writing.
- Oracle: `https://localhost:8443/fineract-provider/api/v1`, self-signed, `curl -k`.

## Non-negotiables (a violation is a rejection, not a discussion)
- Money is **integer minor units**. No float in any money path, ever, **including
  intermediates** — no `float64`, no `math/big.Float`. MNT = ISO 496, minor unit 2.
- Balances are **derived, never written** (I-3); append-only (I-4).
- **HALF_UP**, ordinal 4, precision 19, tz `Asia/Ulaanbaatar`. HALF_UP and HALF_EVEN differ
  ONLY on an exact half-minor tie **whose TRUNCATED value is EVEN** (0.025 → .03 vs .02;
  0.035 → .04 under both). Note the earlier brief OH-CAP-J stated this INVERTED; the form
  here is the correct one.
- **Sub-minor residue is REFUSED** — ratified 2026-09-09, gate G-19, DEC-2 predicate G-08.
  The `scale = 6` columns in Finding B mean a residue value CAN appear. If one does,
  **REFUSE it — never write a parity vector for a residue value.** Record the observation
  and move on.
- **PostgreSQL only.** Never a MySQL/MariaDB/Oracle driver or dialect. "The oracle" here
  means the Fineract reference implementation, never Oracle Database, which is prohibited.
- **One bounded context.** You are in `investor`. Wandering outside it is a rejection.

## The bar, before you claim done
From the worktree: `go build ./...`, `go test ./...`, then `bash .softhouse/conformance.sh`.
Expect exit 2 as the §4.4.2 recorded decision with the ledger finding set at **exactly 12
(class, file) pairs** — that is green. Any other non-zero exit is a failure you must fix.
Report the kill count of every drive, and the sha256 of every capture a vector cites.
