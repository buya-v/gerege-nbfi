# OH-INV — repair the investor I-3 violation. The template is already in this repo.

Repo: /Users/buv/oh-gerege-inv   Branch: fix/OHINV-investor-i3 (checked out)

## What is wrong, and it is already argued

Read `.softhouse/reviews/i3-adjudication/ADJUDICATION.md` first — all ten investor sites are
adjudicated verdict **A, REAL VIOLATION**, with the argument and citations. You are not
re-deciding that. You are repairing it.

It is ONE violation across two regions of `nexus/internal/apps/investor/postgres.go`:

    Insert       (~:108-120)   writes the loan-outstanding snapshot into five Fineract
                               `*_outstanding_derived` columns of
                               m_external_asset_owner_transfer_details
    loadDetails  (~:187-215)   SELECTs those columns back into the aggregate's balance
                               fields, returned as authoritative by FindByID / FindByLoanID

The write and the read-back close the loop I-3 refuses. Repairing one without the other
fixes nothing: drop the INSERT alone and a decoded balance is still trusted; drop the SELECT
alone and the write path remains.

## The template is in-tree — follow it, do not invent

`nexus/internal/apps/savings/postgres.go` is the SAME defect already repaired. Read it,
especially the comments at :26-37 and the read model at :235-238. It states the rule:

    "no INSERT here names a balance column ... no SELECT here reads one back into a field,
     because a decoded balance is a number this port did not derive, arriving through the
     SELECT instead of the INSERT and trusted just the same"

Do for investor what savings does: **stop writing the derived columns, stop selecting them,
and derive the value where it is needed.** Keep the same doc-comment discipline — say in the
file why the columns are absent, so the next reader does not "restore" them.

## What must stay true

* `ExternalAssetOwnerTransferDetails` and its `[VERIFIED:]` citations STAY. A prior task in
  this programme made a finding vanish by deleting the ported type and its citation. That is
  evidence destruction. **You may not delete a type, field or citation to make a finding go
  away** — you may stop PERSISTING a value, which is a different act.
* The existing investor vector must still grade: `INV-01-transfer-read`, parity_pass=1.
  Verify with
  `cd nexus && go run ./internal/apps/investor/conformance/cmd/conformance --root <repo>`.
* `go build ./...` and `go test ./...` clean.

## The finding count WILL change, and that is the point

`ledgerguard` currently reports **38**. A correct repair removes the ten investor findings,
leaving **28**. State the number you observe.

**Do NOT edit `.softhouse/guards/ledger-invariants.baseline`.** Under DEC-2 §4.4.2
obligation 3 the baseline is not editable by whoever changed the finding set — the driver
does that separately, after verifying the repair. Expect the bar to REFUSE while the baseline
still lists rows your repair cleared; that refusal is correct and is not yours to silence.

## Write as you go

Commit after the INSERT repair, before starting the SELECT repair. Four runs in this
programme burned 400-600 events and produced nothing because they held work to the end.
Whatever is not on disk did not happen.

## Constraints

* Touch only `nexus/internal/apps/investor/`. Not another context, not a harness, not a guard.
* NEVER remove an assertion, a refusal or a test. Adding is fine.
* Money is integer minor units; no floating point on any money path.
* PostgreSQL only.

## Report

The finding count before and after; the investor verdict line; what you changed in each of
the two regions; and how the value is now derived where a caller needs it. If any caller
genuinely needs a stored snapshot and cannot derive it, SAY SO rather than forcing a repair
that breaks a reader — an honest blocked report beats a silent regression.
