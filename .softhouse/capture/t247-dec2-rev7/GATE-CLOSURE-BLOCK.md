# G-14 closure block — DRAFTED BY `T247` FOR THE DRIVER TO PLACE

**`T247` did NOT edit `.softhouse/gates.md`.** This is the text to append under `## G-14`, *after*
an independent review of `REVISION-7-PROPOSED.md` and *after* the driver has landed revision 7 and
re-run the bar on the landed result. **Do not place it before both of those.** The `BAR ON THE
LANDED RESULT` block is left with blanks on purpose — quoting `T247`'s numbers there would be the
`P-69` defect this gate exists to punish, one level up.

---

```markdown
### CLOSED — DEC-2 revision 7 RATIFIED and LANDED, local fire `<FIRE>`

- **state**: **CLOSED — RATIFIED** · **ratified_by**: the driver · **chosen_by**: `agent`
  · **Buyan retains veto and may reverse this.**
- **route**: `T247` PREPARED revision 7 and landed nothing. `<REVIEWER>` reviewed it INDEPENDENTLY.
  The driver applied the review's findings, ratified, and re-ran the bar on the landed result. The
  same route `G-13` took, one revision later, for the same reason.

**BAR ON THE LANDED RESULT, re-run by the DRIVER and quoted from no worker:**

```
probe line PRESENT and reading: probe = ___
VERDICT: PASS (exit 0) — ___ parity vectors, ___ cells
ledger ___ parity / ___ oracle-refusal / ___ money cells
refused ___ · inadmissible ___ · harness errors ___ · invariant violations ___ · ___ NOT RUN
all 9 census pins == pinned
vector store  <git rev-parse HEAD:.softhouse/vectors>   READ LIVE, MUST BE UNMOVED
.softhouse/vectors/PIN-ledger.json  dec2_revision: 5    DELIBERATELY NOT BUMPED
```

**WHAT WAS CORRECTED.** The opening banner, its four "measured facts", and **twenty-six further
sites** — because a document goes stale on a **date**, not in a paragraph. `T247` re-measured all
eight sites `T246` reported (`L3`, `L7`, `L10`, `L815`, `L819`, `L825`, `L2437`, `L87`) and
**confirmed every line number unmoved**; it then found **nine more inside the banner's own reach**
and **sixteen further down**, including the whole of §8.1 — which restates the banner's four facts
verbatim at the end of the document, where a ratifier reads last — and §8.2, §8.3, §0, §2.2, §4.2,
§4.4's rule paragraph, §4.9(b), §5, §5.3 and the `I-2` invariant row.

**THE FOUR THAT MATTER MOST, because each is a different failure mode:**

1. **`L820`, the `I-2` row — a correction that would have landed at `L819` and stopped.** The `I-1`
   row was on `T246`'s list; the `I-2` row directly beneath it says only *"**NO.** Same reason."* and
   was on nobody's. `P-26` in one line.
2. **§8.1, `L2345-2409` — the banner's four facts, restated in full, 2,300 lines away.** `T246`'s
   seven-site list did not reach it. A revision 7 that had corrected only the named sites would have
   left a fully-formed, plausible, wrong copy of the retracted banner at the exact place §8 tells a
   ratifier to read last.
3. **§4.9(b), `L1304-1311` — right answer, dead ground.** *"THE (b) COLUMN CANNOT CURRENTLY BE
   WRITTEN DOWN"* is false: `class: oracle-refusal` exists and two such vectors pass. *"Every row of
   the (b) table is ungraded today"* is **still true** — for a different reason (`ledger.slot.
   resolution` is `in_graded_domain: false`). **Exactly revision 6's shape, in a different section.**
4. **The banner's fact 3 was STALE in its identifier, not just its line numbers.** *"`run_guards`
   invokes **seven** guards … the **seventh** is `guard_ledger_invariants`"* — at the landed commit
   `run_guards` invokes **eight** (one short-circuiting + seven tallied) and `guard_ledger_invariants`
   is the **sixth** tallied, because `T243` wired `guard_no_fail_open_instruments` after `A2-28`'s
   stamp. **An ordinal used as an identifier goes wrong silently; a name does not.**

**LIVE FALSEHOODS OUTSIDE `docs/adr/`, WHICH REVISION 7 COULD NOT FIX AND DID NOT TOUCH.**
`P-70`'s sharpest row is that DEC-2 §8.3's *"no guard for either exists"* survived **one file over**
in `conformance.sh`, invisible to every sweep because every sweep was scoped to the ADR. So `T247`
swept **all 5,129 tracked files**. It found three, and **one of them was fixed underneath it while it
worked — which is `P-69` happening to the task written to fix `P-69`:**
- **`.softhouse/program.json:720`** — G-12's `blocks` field, *"No ledger vector exists yet (G-11), so
  no vector grades the column."* **FALSE at `T247`'s fork `9b6c596`; ALREADY CORRECTED at `main`
  `a0d5f66`**, by the driver at merge `e36c3ca` on **`T249`'s** finding, in the same fire. `T247`
  found it independently and by a different route (a concept sweep, not a scope review) and reached
  the same conclusion the driver did: **ground false, conclusion true** — no vector grades
  `office_running_balance` / `organization_running_balance`. **Two tasks converging on one stale
  sentence from opposite directions is the argument for the sweep being repo-wide.** No follow-up
  needed; recorded because a finding that is already fixed still has to be reported as found.
- **`.softhouse/gates.md:98`** — inside **this register's own G-11 ratification block**, *"**Nothing
  grades the ledger's money yet**: all 46 passing vectors are `loanschedule`'s and **zero** touch a
  GL account, a mapping, a financial activity or a journal entry."* **STILL LIVE at `a0d5f66`**,
  verified after the merge. Four ledger vectors are journal entries and 21 money cells are graded
  every run. **`FU-T247-2`.** *The gate register that raised G-14 for a false sentence carries the
  same false sentence four screens above the gate.*
- **`.softhouse/gates.md:3561`** — G-12's raising record, *"No `ledger` vector exists yet (G-11 is
  open), so no vector grades the column."* **STILL LIVE at `a0d5f66`.** Same sentence as the
  `program.json` field that was corrected, in the register the correction did not reach.
  **`FU-T247-2`.**

**WHAT REVISION 7 DELIBERATELY DID NOT DO, verified against the landed diff:**
- **No obligation moved.** Not a normative `must`, not a sentinel, not a graded-domain predicate,
  not a §4.2 predicate, not one of §5.3's ten preconditions — their text, identifiers, order and
  DEPENDS-ON column are byte-identical. `§4.4`'s *"I-3 and I-4 must be enforced by a harness-level
  source guard, not by a vector"* is carried forward **verbatim**, and revision 7 adds that **no
  growth of the ledger corpus will ever discharge it**, because a snapshot cannot observe the
  absence of a write.
- **`PIN-ledger.json` stays at `dec2_revision: 5`.** Re-derived, not inherited: `admit.go:49-52`
  compares **vector to pin** and never reads the ADR, so the two are independent quantities.
  Revision 7 changes no obligation, so no vector needs re-stamping; bumping the pin alone makes all
  six ledger vectors INADMISSIBLE, and bumping both moves the store digest every BAR pins (`P-61`).
- **§5.3's preconditions are NOT ticked off.** `T247` measured that the second schema's package
  addresses P-1, P-2, P-3, P-4, P-6, P-7, P-9 and P-10 **by name**, and that the harness *executes*
  the two a declaration alone could not (P-4's comparator: 70 ledger cells; P-10's registry: 6 wrong
  implementations, all killed). It then **refused to certify them**, and said why in the landed
  text: that would be a review of `A2-15` that nobody has done. **`P-5` is named nowhere in the
  ledger package** — `git grep -P '\bP-5\b' -- nexus/internal/apps/ledger` returns nothing — and
  revision 7 says so rather than smoothing it. **`FU-T247-3`** files the re-derivation.
- **Sixteen HISTORY sites were enumerated and left alone.** Every revision-3/4/5 retraction block,
  §5.1.1's retraction table, §10's per-revision entries. The document's practice since revision 3 is
  **restate and refute, never silently reword**, precisely so a later reader can tell "discharged,
  with limits" from "never claimed".

**THE CAUTION SURVIVED, AND IT IS STRONGER THAN THE ONE IT REPLACES, because it is true.** The old
banner warned by claiming zero coverage. The new one warns with a **ratio that discriminates**:
**6 of the 14 capabilities `capabilities-ledger.json` declares are in the graded domain; 8 are
declared OUT, by name**, and the harness prints all eight on every run, derived from that file so a
gap cannot go unprinted [both terms counted — `P-67`]. Ungraded, named in the banner: slot
resolution — *the single largest thing this context does* — accruals, transfers suspense, charge-off,
multi-currency, opening balances and `GLClosure`, reversals, and running balances, on which **`G-12`
is OPEN and `A2-29` measured the oracle's stored balance to be a SECOND SOURCE OF TRUTH, made to
disagree with the derived sum by MNT 2,000,000.00**. Plus: **no vector grades `I-3` or `I-4`.** The
banner ends where it always did — **cutover is a hard `user` gate and nothing here moves it.**

**A PROCESS DEFECT FOUND WHILE FIXING THIS ONE, and closed by revision 7.** Revision 6 landed content
changes **without a §10 revision-history entry and without updating the status block**, so between
`8e8d65d` and revision 7 DEC-2 identified itself as *"DRAFT (revision 5) … NOT RATIFIED"* while being
a ratified revision 6 [`git grep -P '(?i)revision\s+6\b'` over the file returns exactly two lines,
both revision 6's own corrections; instrument calibrated on a positive — `revision 5` → 15 lines —
and a negative — `revision 99` → 0]. **Revision 7 adds §10 entries for both revision 6 and revision
7.** A revision that does not stamp itself is a revision the next reader cannot date — and an
undated document is exactly what `P-69` needs to do its damage.

> **The one-sentence version.** `G-14` was raised because DEC-2's first instruction told every reader
> to believe a fact its own cited command refutes. It is closed because the fact was re-measured, the
> banner now says what is true, and **the warning the banner existed to give is still there and now
> has a denominator.**
```

---

## Follow-ups to file alongside the closure

| id | what | why it is not in revision 7 |
|---|---|---|
| ~~**FU-T247-1**~~ | ~~`.softhouse/program.json:720`~~ — **WITHDRAWN. Already fixed on `main` at `e36c3ca`** by the driver on `T249`'s finding, while `T247` was working. `T247` found it independently at its fork `9b6c596` and reached the same verdict (ground false, conclusion true). Kept struck through rather than deleted, because a finding that was real at the fork and dead at the merge is exactly the `P-69` shape this whole gate is about. | — |
| **FU-T247-2** | `.softhouse/gates.md:98` (inside **G-11's own ratification block**) and `.softhouse/gates.md:3561` (G-12's raising record) both restate *"nothing grades the ledger's money"* / *"no `ledger` vector exists yet"*. **Both verified STILL LIVE at `main` `a0d5f66`**, after the fire's merges. | `gates.md` is outside `T247`'s scope — it is the register `T247` was explicitly told not to touch. |
| **FU-T247-3** | **Independently re-derive that each of §5.3's ten preconditions is ADEQUATELY discharged**, not merely addressed by name. Start with `P-5` — the only one the ledger package does not name — and with whether the two `SchemaContexts()` allowlists are jointly airtight. | Revision 7 measured presence, refused to certify adequacy, and says so in the landed text. |
| **FU-T247-4** | **A staleness detector for measured claims.** Every occurrence of the `G-14` / `P-69` family has been the same shape: a stamped measurement, a moving tree, and no instrument that notices. Candidates: a guard that re-resolves every `.softhouse/conformance.sh:<line>` citation in `docs/adr/` by CONTENT and fails when one no longer resolves (`A2-25`'s `FU-A2-25-3`, recommended in revision 4 and never built); or a check that every `[MEASURED … at commit <sha>]` stamp older than N commits is reported. **This is the fourth revision in a row to be commissioned by staleness. The remedy has been recommended twice and built zero times.** | It is harness work, not ADR work, and `T247`'s scope forbids `.softhouse/conformance.sh`. |
