# F-2026-09-10 — NAVIGATION, not difficulty, is what kills runs in this programme

**Status:** OPEN as a briefing rule. Four cap-deaths, three of them this cause.
**Found by:** the driver, after the fourth run in two days reached its 500-iteration
limit having written **nothing at all**.

## The measurement

| run | events at death | committed | cause |
|---|---|---|---|
| `OH-GAP-M` | 1017 | nothing | navigation — reverse-engineering investor source |
| `OH-INV-N` | 1026 | nothing | navigation — reverse-engineering COB step config |
| `OH-GL-R` | 1012 | 71 files, **0 commits** | ran out mid-work; salvage later reverted |
| `OH-LEDGER-V` | 1026 | nothing | navigation — 11,847-line ledger conformance package |

Three of four died **reading**. None hit a conceptual wall; each ran out of budget
assembling a map of an unfamiliar subsystem.

## The control that proves it is navigation and not difficulty

**`OH-INV-Q` reached a verdict in 23 minutes** on the question `OH-GAP-M` and `OH-INV-N`
had each spent a full budget failing. The only difference was the brief: it handed over the
four `curl` calls the driver had verified, and said *do not read Java to rediscover them*.

The same control repeated at the ledger. After `OH-LEDGER-V` died at `type EntrySide`, the
driver found what it needed **in four commands**:

* `EntrySide` — `internal/apps/ledger/money.go:211-215`, `EntryCredit = 1`, `EntryDebit = 2`
* `RegisterWrong(name, defect, poster)` — `internal/apps/ledger/conformance/impl.go:140`,
  called from `:1243` onward, sixteen worked examples in a row

503 iterations against four commands. The knowledge was cheap; **finding out where to look
was the whole cost.**

## Why it keeps happening — and it is the driver's defect, not the agents'

Every one of those briefs stated **what to establish** and left **where it lives** as an
exercise, against an unfamiliar subsystem, under a fixed budget. That is a reasonable ask
of a person with a week; it is a budget-killer for an agent with 500 iterations, because
reading is the most expensive thing it can do and it cannot tell in advance how deep the
tree goes.

Two of the runs also **corrected the driver's own facts** — `ExternalTransferData.java:34`
not `:16` (a line number taken from a comment-stripped view), and twelve product-3 mapping
rows not eleven. So the briefs were not merely incomplete; where they did assert specifics,
some were wrong.

## The rule

**A brief must carry the map, not just the destination.** Before dispatching into an
unfamiliar package, the driver spends the five minutes to name:

1. **The exact file:line of the thing to be modified or registered**, and one worked
   example already in the tree to copy.
2. **The type or constant definitions** the task turns on, with their values.
3. **The instrument** that measures the result, and how it is invoked *for that context* —
   including when it does not work the usual way (`ledger` has no `cmd/conformance` binary;
   its drives run through `conformance.sh`'s census).
4. **An explicit "do not go and rediscover this"**, naming the hole the last run fell into.
5. A **budget checkpoint**: commit by iteration N or stop exploring and write down what you
   have.

Items 1-3 cost the driver minutes and save an agent hundreds of iterations. Item 4 matters
because an agent that distrusts a brief will re-derive it anyway — `OH-CAP-J` ignored an
*inverted* instruction and reasoned from the arithmetic, correctly. Item 5 is what turns a
cap-death from a total loss into a partial one.

## The counter-rule, so this is not read as "hand the agent the answer"

Do **not** state a conclusion the run is supposed to establish. `OH-INV-W`'s brief asserted
that product 3's mapping set would unblock settlement; the run proved it FALSE and said so
loudly, which is exactly right. Hand over **navigation** — where things are, what they are
called, how to measure. Never hand over the **verdict**.
