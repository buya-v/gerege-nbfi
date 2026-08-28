# The driver's gloss on P-84 drifted from P-84, and the driver propagated it into ~14 worker prompts

*Fire `20260828-080001`. Caught by **T331**, which read the definition instead of inheriting the gloss.*

## What P-84 actually says

> **P-84 — "EXIT 2 WITH NO PROBE LINE" IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE.**
> The first BAR after merging `A2-23` exited 2 with **no probe line printed at all**. Under the rule as it
> stands that is emphatically **not** an oracle outage — four exit-2 paths precede the probe, and a failed
> HARD guard is one of them. **The cause was `p5-probe.sh`, merged minutes earlier, moving the frontier
> 10 → 11.**

[VERIFIED: `.softhouse/patterns.md:2813-2819`.] **It says nothing about money.** It is a rule for
distinguishing a **HARD-guard refusal** from an **oracle outage**, and its one recorded instance is an
**instrument-hygiene** guard — not a money guard.

## What the driver wrote instead

In every batch-1 through batch-4 worker prompt, and in the `tasks.json` descriptions of **T330, T331 and
T332**:

> *"P-84 — read the probe line's PRESENCE before its value. Exit 2 with NO probe line printed is a failed
> HARD guard — **a money non-negotiable** — never an oracle outage."*

## The actual source of the drift, which is instructive

`SKILL.md` is **correct**. It says a `guard_no_float_in_vectors` failure — *a money non-negotiable* — exits 2
in silence, i.e. it offers the float guard as **one example** of a HARD guard whose failure is silent. The
driver compressed *"one of the HARD guards is the money guard"* into *"a failed HARD guard **is** a money
violation"* — an **existential turned universal**, which is a smaller and much more natural slip than
inventing a rule, and is exactly why it survived fourteen prompts unremarked.

## Materiality: LOW, and the reason is P-86's own lesson turned on the driver

**No worker was misdirected.** Every prompt carried the **full operative rule text** beside the gloss —
*read the presence before the value; four exit-2 paths precede the probe; never an oracle outage* — so the
instruction that governed behaviour was correct even where the gloss was not. **Five separate tasks hit
`exit 2` with the probe line absent or present during this fire (T330, T325, T328, T145, T331) and all five
classified it correctly.** The number was decoration; the sentence carried the instruction. That is
`P-86` verbatim, and the driver is now its third recorded instance.

**Where it did bite:** T331 was told to *"argue the tier, do not inherit it"* and found the brief's stated
premise false. Had it inherited the gloss, it would have justified a HARD tier on a reason that does not
exist. **The gloss's cost was not a wrong action; it was a wrong reason offered for a right action** — and
that is precisely the thing an independent worker is for.

## What was corrected, and what deliberately was not

- **`tasks.json` descriptions** — corrected in place, because a pending task's description is a **live
  prescription** for work not yet done. `T332` was pending and is now fixed.
- **Merged handoffs, reviews and commit messages** (`T277.md:501`, `T306.md:97`, `T326.md:714` and `:947`,
  `.softhouse/observations/20260827-dead-path-frontier-pin-encodes-host-state.md:47`) — **NOT edited.**
  They are committed evidence and a historical record of what the driver actually said, and T114's ruling
  plus T277's and T322's precedent both hold that such sites are corrected **forward**, never rewritten.
  This file is that forward correction.

## The rule, restated so the next driver does not repeat it

**Do not paraphrase a pattern into a prompt. Quote its title, or cite the id and its sentence together.**
An id used as an identifier goes wrong silently — and so does a gloss, one layer earlier, because a gloss is
a restatement and **a corrected cardinal rots in every place it was restated** (`P-80`). The driver wrote
that sentence into three task briefs this fire while violating it.
