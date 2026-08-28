# T328 — the sweep for the refuted-claim class, and WHERE I LOOKED

FU-T306-1 named `.softhouse/vectors/capabilities-ledger.json` as carrying a claim T327
falsified. The brief's instruction: *"T305 corrected the same class of refuted rule in three
places, T320 found a fourth. A store wrong in four places may be wrong in five. 'Not found' is
a statement about the search — say where you looked."*

## The search

```
grep -rIl "NEITHER WAS FIRED\|NEITHER FIRED\|neither was fired\|remains uncaptured\
\|backlog B-1\|B-1 and B-2" .softhouse nexus docs
```

23 files. Then, narrowed to LIVE claims (a file that ASSERTS the present state) rather than
HISTORICAL records (a handoff, a review, a capture README, a transcript — each correct as of
its own date, and this store's convention is to leave those visible rather than rewrite them):

```
grep -n "NEITHER WAS FIRED\|NEITHER FIRED\|remains uncaptured\|backlog B-1\|B-1 and B-2\|uncaptured" \
  .softhouse/conformance.sh docs/analysis/tierA-a2-behaviour.md \
  nexus/internal/apps/ledger/conformance/admit.go \
  nexus/internal/apps/ledger/conformance/openingbalance_test.go
grep -rn "NEITHER\|uncaptured\|accepting side" .softhouse/vectors/ledger/LDG-REFUSE-0{4,5}*.json
```

I also read every one of the 14 rows of `capabilities-ledger.json`, not only the two the
follow-up named, because the defect class is "a row whose evidence outlived the measurement".

## FIVE LIVE SITES FOUND. Four repaired here; one was already repaired earlier in this task.

| # | site | the refuted claim | disposition |
|---|---|---|---|
| 1 | `capabilities-ledger.json` → `ledger.refusal.parity`.evidence | *"…is ACCEPTED with HTTP 200 is [UNVERIFIED] in this store … (B-1, B-2) and NEITHER WAS FIRED."* | **REPAIRED.** Old sentence QUOTED inside the correction so a reader who met it elsewhere can find the discharge. Also states what this row still does **not** cover: no vector grades the **precedence** between :630 and :636. |
| 2 | `capabilities-ledger.json` → `ledger.opening.balance.and.closure`.evidence, **opening sentence** | *"TWO OF THE THREE SHAPES ARE NOW OBSERVED"* while the same row says further down *"the row's three named shapes are all represented"* | **REPAIRED** — this is FU-T306-1's self-contradiction proper. The count is now stated **once**, at the top, and it is **six** (both sides of all three shapes). |
| 3 | same row, *"WHAT REMAINS UNCOVERED"* paragraph | *"the ACCEPTANCE side of both boundaries, which cannot be captured without posting a journal entry that cannot be deleted … NEITHER FIRED"* | **REPAIRED**, quoted-and-superseded. |
| 4 | same row, item **(3)** of *"WHAT IS STILL NOT GRADED"* | *"The ACCEPTANCE side of the CLOSURE and FUTURE-DATE boundaries … remains uncaptured"* | **REPAIRED**, and replaced with the T328 paragraph recording what closed it, the load-bearing measurement, and what is *still* ungraded on the row. |
| 5 | `admit.go`, the capability-gate comment block | the shape table read *"the two DATE boundaries — REFUSING SIDE ONLY, accepting side still uncaptured"*, and the paragraph below it concluded *"the date arms KEEP [the precondition]"* | **REPAIRED earlier in this task**, in the same diff as the widening. The table now lists six vectors; T306's paragraph is kept as history behind an explicit SUPERSEDED banner that also records **what T328 measured about it** — the edit it prescribed would have admitted neither vector. |

## THREE SITES INSPECTED AND DELIBERATELY NOT CHANGED

- **`docs/analysis/tierA-a2-behaviour.md:72` — A FALSE POSITIVE OF MY OWN GREP, and I checked
  rather than assumed.** Its `§12 backlog B-1` is that document's **own** §12 backlog item about
  where a Go package boundary must be drawn (`org.apache.fineract.accounting.glaccount` spanning
  four Fineract modules). It has nothing to do with the closure/future-date backlog. Left alone.
- **`.softhouse/vectors/ledger/LDG-REFUSE-04…json` and `LDG-REFUSE-05…json` — CLEAN.** Neither
  `_note` nor `title` nor `rerun_invariant` claims anything about the accepting side; grep
  returned nothing. Their `request.business_date` cells carry a *different*, still-live weakness
  that T329 named — those values were DERIVED from prose rather than measured — and T328 did
  **not** touch them: changing a graded input on a committed refusal vector is a re-observation
  question, not an editorial one. Filed as **FU-T328-3**.
- **Handoffs, reviews, capture READMEs and transcripts** (T295, T305, T306, T320, T327,
  `.softhouse/observations/`, `.softhouse/reviews/T306/`, `.softhouse/reviews/T320/`). These are
  dated records of what was true when they were written, and the two that matter most —
  T306's tripwire prose and T327's README §8 — are already explicit that promotion was the open
  follow-up. Rewriting them would destroy the audit trail the corrections above point back to.
  `.softhouse/tasks.json` and `.softhouse/runs/*.tasks.json` are the plan record, not a claim
  about the store.

## The other direction, checked because a sweep that only removes claims is half a sweep

Every row of `capabilities-ledger.json` marked `in_graded_domain: false` is printed by the
harness on every run from that file, so a row that became stale in the *other* direction (still
declared blind after a capture arrived) would print itself. The run transcript lists all seven
and none of them is the date boundaries. Nothing else moved.
