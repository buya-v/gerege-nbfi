# F-2026-09-10 — a loan-produced posting does not fit the `ledger` vector schema

**Status:** DECIDED by the driver. Recorded so the reasoning survives the decision.
**Cost before it was noticed:** three runs, ~970 iterations, zero output.

## What happened

Three runs were dispatched to grade the loan→GL journal-entry captures as `ledger` vectors.
All three produced nothing, with three *different* proximate causes:

| run | events | cause |
|---|---|---|
| `OH-LEDGER-V` | 1026 | capped after 503 iterations of reading |
| `OH-GLVEC-AB` | 291 | LLM-side stall, killed |
| `OH-GLVEC-B` | 442 | killed at ~177 iterations, nothing written |

Three causes, one task, one outcome. That points at the **task**, not the runs.

## The actual obstacle

A `ledger` vector's `request` block models a **REST posting command**
[`.softhouse/vectors/ledger/LDG-01-manual-je-3leg-minor-units.json`]:

    product_id, product_type, accounting_rule, slot_family, slot_code,
    payment_type_id, seam="ledger_rest_posting", office_id, currency,
    transaction_id, manual_entry=true, transaction_amount_major_text,
    accounts[], legs[]

**A loan-produced posting has none of it.** Nobody submits `legs`; a loan disbursement
*generates* them. There is no `transaction_amount_major_text`, no `manual_entry`, no slot.
The observation is **purely a read-back** — and all 17 existing ledger vectors carry
`seam: ledger_rest_posting` precisely because that is the only ledger seam ever captured.

So the runs were being asked to express a read-back in a schema built for a command. That
is a design decision, and **the brief handed it over as "choose the seam name and justify it
in one line"** — treating a schema mismatch as a naming choice. That is the driver's defect,
and it is a different one from
[`F-2026-09-10-navigation-is-the-dominant-failure`](F-2026-09-10-navigation-is-the-dominant-failure.md):
the map was complete this time. **A complete map does not rescue a mis-framed task.**

## The decision

**Grade loan-produced postings in the `loan` context, as a read-back vector.** Reasons, in
order of weight:

1. **The observation IS a read-back**, and `loan` vectors are already that shape — `LN-L07`
   carries `request: {summary: {…observed values…}}` and `seam: loan-summary-outstanding`,
   a descriptive seam name, not a command.
2. **`loan` has a working `cmd/conformance` binary**, so `kills.sh` is the instrument, the
   ordinary one. `ledger` has none — its drives run only through `conformance.sh`'s census,
   which is a second thing for a run to learn.
3. `ledger`'s seventeen drives all subvert an `EntryPoster` that *posts*. A read-back defect
   has no poster to subvert; it belongs where read-back defects already live.
4. It leaves `ledger_rest_posting` meaning exactly one thing, rather than overloading the
   ledger context with two incompatible request shapes.

**Rejected:** inventing a `ledger` read-back seam. It would need a second `request` shape in
a context whose entire harness assumes a posting command, for no gain over `loan`.

## What this does not change

The postings themselves are still ungraded, and still worth grading — the fee pair on
**loan 10** is the only capture that sees a **multi-pair batch balance**, which loan 12
cannot, and no existing drive covers it. The work is real; only its home was wrong.
