# T289 corrections to this rig — read before you fire anything here or promote anything from it

Added by **T289**, the independent review of T287, on branch `softhouse/t289-review-t287`.
Co-located with the rig on purpose: the mistakes are here, so the corrections are here.
Full reasoning and reproductions: `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T289.md`.

Nothing T287 captured was rewritten. Every `out/` byte is untouched; `MANIFEST.sha256`
verifies 87/87 unchanged.

---

## 1. ALL FOUR PROBES IN THIS RIG ARE LOADED. Two of them are loaded RIGHT NOW.

`req/a1-01`, `req/a1-02`, `req/a2-01`, `req/a2-02` are **valid, balanced, postable manual
journal entries**. GL 4 and GL 2 on tenant `gerege` are both
`manual_journal_entries_allowed = t`, `disabled = f`, `account_usage = 1` (DETAIL), and
debits equal credits. The **only** thing that refuses them is an oracle-side precondition:

| probe | refused only while | state as of 2026-08-23 |
|---|---|---|
| `a1-01-future-far` (2026-12-31) | business date < 2026-12-31 | safe until **2027-01-01** |
| `a1-02-future-boundary-plus1` (2026-08-24) | business date < 2026-08-24 | safe until **2026-08-24 — tomorrow** |
| `a2-01-preclosure-on-date` (2026-01-31) | a GLClosure at office 1 with closingDate ≥ 2026-01-31 exists | **ALREADY LOADED — T287 deleted that closure** |
| `a2-02-preclosure-before` (2026-01-15) | same | **ALREADY LOADED** |

When the precondition lapses the request does not become uninteresting — **it becomes a
successful write**, and **a posted journal entry cannot be deleted**. Unlike the GLClosure
T287 created and removed, the only "undo" is posting more entries.

T287 §7.5 says *"Re-taking arm 2 is cheap now — the recipe is committed and re-runnable"*.
**It is not cheap and it is not safe to re-run as written.** `req/a2-00-create-closure.json`
must be fired first, and the resulting closure id will be **2**, not 1.

**Before firing anything in this rig, run `sh guard-probe-expiry.sh`.** It fails closed and
refuses when any precondition has lapsed. Today it exits **1**.

## 2. The registry row `ledger.opening.balance.and.closure` is NOT misnamed. T287's §1/§7.6/§8 is wrong here.

T287 concluded that lines `:626-640` "contain no opening-balance logic whatsoever", so the
row "overstates", and told the promotion task to *"resolve the name before flipping"*. Its
search was honestly bounded — it says so — but the conclusion mis-steers.

Opening-balance logic exists and **routes through those exact lines**
[pinned `426a23544`, `fineract-provider/.../JournalEntryWritePlatformServiceJpaRepositoryImpl.java`]:

- `:703` `defineOpeningBalance(JsonCommand)`
- `:724` `validateBusinessRulesForJournalEntries(journalEntryCommand)` — **the same guard, the same two refusals**
- reached by `POST /journalentries?command=defineOpeningBalance` [`JournalEntriesApiResource.java:211-212`]
- read side `GET /journalentries/openingbalance` [`:263-274`] → `JournalEntryReadPlatformServiceImpl.retrieveOfficeOpeningBalances:405`

So the row bundles the two things **because they share the guard**. Do not split or rename it.

## 3. There IS an uncaptured opening-balance refusal, and it is cheaper than either arm T287 took.

`:717` `validateJournalEntriesArePostedBefore(contraId)` → `:810-816` throws
`error.msg.journalentry.defining.openingbalance.not.allowed`,
*"Defining Opening balances not allowed after journal entries posted"*, whenever any
non-contra journal entry exists.

On tenant `gerege`: financial-activity type **300 is mapped** (`acc_gl_financial_activity_account`
id 4 → GL 15), and there are **60 journal entries**. So this refusal **fires deterministically**,
throws **before any write**, and needs **no mutation of any kind** — no closure, no office,
no clock dependence. It is the genuinely cheap opening-balance capture, and it is still untaken.

## 4. The residue is public, not just a counter.

T287 recorded `m_portfolio_command_source` 347 → 351. What it did not record is that the two
GLCLOSURE rows are served by the **public audit API**, verified read-only by T289:

- `GET /v1/audits?entityName=GLCLOSURE` → two rows, `processingResult: "Processed"`,
  `resourceId: 1`, `url: "/glclosures/1"` and `"/glclosures/template"`.
- `GET /v1/audits/348` → `commandAsJson` serves T287's full comment string verbatim,
  including the words "T287 TEMPORARY closure".

Any future capture of the audit/command context will observe T287's probe as tenant history.
Say so in that capture rather than encoding it as a parity fact.
