# T246 — INDEPENDENT review of DEC-2 **revision 6**, as PREPARED (not landed) by `T244`

**Task:** `T246`, run `2026-08-21-run2-tierA-gl-accounting-A2`, context `tierA-gl-accounting`
**Role:** INDEPENDENT REVIEWER. I did not plan, author or prepare revision 6.
**Branch:** `softhouse/T246-review-dec2-rev6`
**Subject:** the two-hunk diff in `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T244-handoff.md` §2,
against `docs/adr/DEC-2-gl-accounting-adapter.md` at revision 5 (`cab9e82`), plus G-13's second item
(the stale status header).
**Gate:** `G-13`. This review is its stated unblock condition.

## Fork point — MEASURED, NOT ASSERTED (P-71), AND IT DISCRIMINATES

```
worktree HEAD on entry                 693c768d752df7a475938df3e4fa3cd72b138e18
origin/main at that instant            693c768d752df7a475938df3e4fa3cd72b138e18
git merge-base HEAD origin/main        693c768d752df7a475938df3e4fa3cd72b138e18
```

`git fetch && git rebase origin/main` then moved me to **`f13bf4a`**, because `origin/main` had
already advanced between two consecutive commands of my own setup (`git rev-parse origin/main`
returned `693c768`; `git log origin/main` one call later showed `f13bf4a` on top). **`main` is not
quiescent — confirmed again, this time inside a single setup block.**

**This measurement DISCRIMINATES, and it falsifies BOTH of P-71's dead rules a third time:**

| candidate rule | predicted fork | measured fork | verdict |
|---|---|---|---|
| "fork = session-start commit" | `477dc2d` (this fire's session start, per `a1b531a`) | `693c768` | **FALSIFIED** |
| "fork = dispatch commit" | `f13bf4a` (`wave 2 dispatched (T243, T246)`, 18:06:17 +08) | `693c768` | **FALSIFIED** |
| "fork = repo HEAD when the worktree was created" | `693c768` (18:04:32 +08) | `693c768` | consistent |

`693c768` is the parent of the dispatch commit and was created **1 m 45 s** before it. This is a
**genuine observation, not a non-observation**: the dispatch commit exists, is distinct, and I did
not fork at it. The surviving duty remains the title's — **measure it**.

**Everything below is stamped at `f13bf4a`** unless it says otherwise.

## Environment, stated in full (P-33, and the correction `reference-oracle.md` took today)

```
reference oracle (Fineract)   https://localhost:8443    probe = up      pin 426a23544e8426a38ae43ae404670a0a7e85b9eb
PostgreSQL                    localhost:5432 (fineract-db-1, postgres:18.3)
database                      fineract_gerege
TENANT                        id = 2, identifier `gerege`, "Gerege T22 Audit Tenant", Asia/Ulaanbaatar
                              (NOT tenant 1 `default` / fineract_default / Asia/Kolkata)
vector-store digest (P-61)    git rev-parse HEAD:.softhouse/vectors = 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d
                              READ LIVE, and UNCHANGED by this task.
sweep engines                 /usr/bin/grep (BSD grep 2.6.0-FreeBSD) and python3 3.9.6 `re`.
                              NEVER bare `grep`, NEVER `rg` (P-75). Every script `set -euo pipefail`.
```

---

# VERDICT

# ACCEPT

**Revision 6's two hunks change the EVIDENTIAL REASON and nothing else. I re-derived every load-bearing
number against the live reference oracle rather than inheriting it, and all four of `T244`'s reversal
terms — including the three that rested on `T244` alone — reproduce EXACTLY. Both sites exist, both are
still false at `f13bf4a`, and an EXHAUSTIVE enumeration (not a pattern match) establishes there is NO
THIRD SITE of this falsehood. No hunk touches an obligation: the invariant statement, column 5's
`Graded today? NO`, the `ErrNoDiscriminatingVector` refusal and the rule paragraph are all untouched
and all still correct. The landing hazard is confirmed from source and DRIVEN RED AND GREEN in four
directions: `PIN-ledger.json` must STAY AT 5.**

**The driver may ratify revision 6 `chosen_by: agent` under CLAUDE.md § Answering gates, exactly as it
ratified revision 5, with Buyan retaining reversal.** I am not authorised to ratify and do not. Cutover,
regulatory sign-off and licence facts are untouched by this review and remain hard `user` gates.

**ACCEPT IS CONDITIONAL ON TWO SINGLE-CLAUSE CORRECTIONS BEING MADE BEFORE THE TEXT LANDS** — `F-2` and
`F-3` below. Both are inside the same evidential correction, neither touches an obligation, and I give
the exact replacement wording. **If the driver applies the stricter bar this document has been rejected
under four times — "any unsupported inference in a ratified contract is a rejection" — then `F-2` is the
finding that carries a REJECT.** I have set the bar at *false claim = reject, true-but-under-scoped =
correct-before-landing*, because revision 4's rejection was explicitly for "**claims this document made
about `main` that were false**", and `F-2`'s claim is true. **The choice is stated so it is visible and
reversible, not buried.**

**AND: I found something LARGER THAN G-13, outside revision 6's scope, which the driver must raise as a
new gate before or with the landing — `F-1`, HIGH.** DEC-2's **opening banner**, the sentence the
document orders the reader to read before any other, says *"NOTHING GRADES THIS CONTEXT'S MONEY.
NOTHING GRADES THIS CONTEXT AT ALL."* **That is FALSE at `f13bf4a`, measured by my own green BAR: 4
ledger parity vectors, 2 oracle-refusal vectors, 70 graded cells of which 21 are money cells in int64
minor units, every run.** It is not grounds to reject revision 6 — it is a *different* falsehood, it
postdates `T244`'s fork, and G-13 does not ask about it — but revision 6 will otherwise land into a
document whose first sentence contradicts it.

---

# FINDINGS, ranked by severity

## F-T246-1 — **HIGH** — DEC-2's BANNER AND §4.4's OWN PREAMBLE ARE NOW FALSE, FOR A DIFFERENT REASON, AND NOBODY HAS RAISED IT. **A NEW GATE.**

**Not grounds to reject revision 6.** Raised so the driver does not land rev 6 believing DEC-2 is then
consistent.

**The mechanism is P-69, at scale, and it is the SAME mechanism that produced G-13.** Measured:

```
2026-08-21 21:29:43 +0800  e18fe5b  DEC-2 revision 1 — both I-5 sites written.   TRUE when written.
2026-08-22 10:22:38 +0800  aae501b  A2-26 commits A2-348 (a reversal).           site 1 + site 2 become FALSE.
2026-08-22 14:24:56 +0800  cab9e82  DEC-2 revision 5 — RATIFIED carrying them.   (false for 4 h 02 m already)
2026-08-22 16:37:56 +0800  1325e8b  A2-15 promotes the FIRST SIX LEDGER VECTORS. banner + §4.4 preamble become FALSE.
                                    DEC-2 HAS NOT BEEN TOUCHED SINCE cab9e82.
```

**The six ledger vectors landed 2 h 13 m after revision 5 was written.** Every sentence in DEC-2 that
says the ledger context is ungraded, or that no `ledger` vector exists, went false in that instant.
Sites, all read at `f13bf4a` [instrument: `sweep-adjacent-staleness.py`, python3 `re`, calibrated on a
known positive and a known negative]:

| line | text | truth at `f13bf4a` |
|---|---|---|
| **L3** | *"⚠ **NOTHING GRADES THIS CONTEXT'S MONEY. NOTHING GRADES THIS CONTEXT AT ALL.**"* | **FALSE** — 21 money cells graded every run |
| **L7** | *"**Not one of them is currently checked by anything.**"* | **FALSE** |
| **L10** | *"**No `ledger` vector exists.** `.softhouse/vectors/` holds `loanschedule/` and `_selftest/` and nothing else [VERIFIED by this task: `ls .softhouse/vectors/`]"* | **FALSE — and the ADR names its own instrument.** Re-running `ls .softhouse/vectors/` returns `ledger/`, `PIN-ledger.json`, `capabilities-ledger.json` besides |
| **L815** | *"for **every row in this table the answer is NO**, because no `ledger` vector of any shape is currently expressible (§5)"* | **FALSE** — six are expressed, admitted and graded |
| **L819** (I-1 col 5) | *"**NO.** §5 — no admissible vector can carry a money cell, or any `ledger` cell."* | **FALSE** — 21 money cells, 6 admissible ledger vectors |
| **L825** (I-7 col 5) | *"today there is no `ledger` conformance PASS to say nothing with"* | **FALSE** |
| **L2437** (§8.3) | *"**Today there is no such PASS to misread.**"* | **FALSE** |

**My own BAR is the measurement** (transcript `bar-output.txt`, run by me at `f13bf4a`):

```
LEDGER (tierA-gl-accounting) — SECOND SCHEMA, SECOND COMPARATOR, SEPARATE COUNTS
    ledger inadmissible     0
    ledger harness errors   0
    ledger cells compared   70 graded, of which 21 are MONEY cells in int64 minor units
  exemption census READ: LEDGER parity vectors        = 4 == pinned 4
  exemption census READ: LEDGER oracle-refusal vector = 2 == pinned 2
  exemption census READ: LEDGER money cells compared  = 21 == pinned 21
```

**Why this is HIGH and not a footnote.** It is in the **first sentence**, under an explicit instruction
to *"Read this before any other sentence in this document, and before quoting any number out of it"*,
and it tells the reader the opposite of the truth in the **safe-sounding** direction — a reader who
believes the ledger is ungraded will not look for what the grading does and does not cover, which is
exactly the misreading §8.3 exists to prevent. **It is the same defect class G-13 is about (a true
measurement that went stale under a merge) at seven more sites and a much louder volume.**

**Recommended:** raise **G-14** — *"DEC-2's banner and §4.4 preamble describe an ungraded context; six
ledger vectors now grade it"* — with the same shape as G-13: evidential-reason-only, obligations
untouched, independently reviewed, ratified `chosen_by: agent`. **It is a bigger edit than revision 6
and must not be smuggled into it.** Note also that revision 6's Hunk A column 5 already writes the TRUE
version of this fact for one row (*"the six `LDG-*` files are the whole ledger corpus"*), so landing rev
6 makes the contradiction **visible** rather than creating it — which is an argument for landing it, not
against.

---

## F-T246-2 — **MEDIUM — MUST BE CORRECTED BEFORE THE TEXT LANDS.** Hunk A cites `16` with no denominator, and the denominator is `60`.

Revision 6's Hunk A says:

> "…**the NEVER-MUTATES half is not** — all 16 rows show `last_modified_on_utc > created_on_utc`, so
> telling *"flags and adds"* from *"flags and rewrites"* needs the WRITE path, which no snapshot
> observes"

**The 16/16 reproduces exactly. So does 60/60, and `T244` did not count it.** Re-measured by me on the
live oracle at `f13bf4a` [`measure-mutation-claim.sh` / `.txt`, calibrated known-false = 0]:

```
population size (the reversal population)                        16
rows with last_modified_on_utc > created_on_utc                  16
rows with last_modified_on_utc = created_on_utc                   0
--- SCOPE CONTROL (P-66), the term T244 did not count ---
all rows in acc_gl_journal_entry                                 60
all rows with last_modified_on_utc > created_on_utc              60      <-- 60 of 60
```

And the per-row dump shows **why**: the `last_modified_on_utc` values are not spread out, they cluster
at **two batch instants** — `02:43:48.45…Z` on rows 33–52 and `02:49:46.98…Z` on rows 59–64 — which is
the signature of the **G-12 running-balance recompute**, not of the reversal. `T244` saw the 02:43:48
cluster and correctly said *"that is G-12's territory"* — and then still wrote the 16 into the ADR
without the 60 beside it.

**Why this matters and is not pedantry.** As drafted, the clause reads as evidence *that the reversal
mutated the rows*, and it is not: the property is true of every journal row in the tenant, including the
44 that were never reversed and never pointed at. **A number that is 100 % of your subgroup and 100 % of
the whole population discriminates nothing** — and putting it into a **ratified** contract as the ground
for a conclusion is a new unsupported inference of exactly the class that rejected this document three
times ("a sentence with a scope, whose scope is on the wrong axis"). **P-67: count BOTH terms and say
where you counted.**

**The conclusion is nevertheless CORRECT**, by a stronger and simpler route: a snapshot never observes a
write at all, so it cannot separate the two hypotheses regardless of any timestamp.

**REQUIRED REPLACEMENT for that clause** (the rest of Hunk A stands):

> — and the timestamps are **not** what shows it: **60 of the 60 rows in `acc_gl_journal_entry` carry
> `last_modified_on_utc > created_on_utc`**, clustered at two batch instants (`02:43:48Z`, `02:49:46Z`)
> that are the **G-12 running-balance recompute**, not the reversal, so the column discriminates nothing
> [RE-MEASURED by `T246` at `f13bf4a`: 16 of 16 **and** 60 of 60, both terms counted]. What the reversal
> demonstrably did set is `reversed` and `reversal_id` **on the original rows**, 8 of 8. The reason I-5's
> NEVER-MUTATES half stays ungraded is the simpler and stronger one: **a snapshot never observes a
> write**, so it cannot separate *"flags and adds"* from *"flags and rewrites"* whatever the timestamps
> say [stated first by `A2-15`, `invariants.go:36-47`].

---

## F-T246-3 — **MEDIUM — MUST BE ADDED BEFORE THE TEXT LANDS.** The P-69 re-measure stamp.

Hunks A and B carry only `[RE-DERIVED by T244 … at commit 477dc2d, 2026-08-22T09:22Z]`. `main` has moved
**at least five times** since (`477dc2d → 8275f8b → 4c97dee → … → 693c768 → f13bf4a`), and P-69 says in
terms that *"a document whose measured claims can go stale between the review and the ratification
cannot be ratified by a review alone; it needs a re-measure gate at the moment of ratification."*

**I am that re-measure.** The landed text must carry **both** stamps, or the ratification once again
publishes drafting-time measurement as ratification-time fact — which is the defect G-13 exists to
correct, reproduced by the correction. Add to both hunks:

> `[RE-DERIVED INDEPENDENTLY by T246 at commit f13bf4a, live oracle probe = up, PostgreSQL
> fineract_gerege, TENANT 2 `gerege` (Asia/Ulaanbaatar), Fineract pin 426a23544 — all four terms
> reproduce: 8 / 8 / union 8 / 16 rows in 3 pairs over 6 transaction ids, 8 of 8 equal amount and
> flipped type_enum.]`

---

## F-T246-4 — **LOW.** The line numbers for the status block are wrong in `gates.md`, in `program.json` and in my own brief.

`gates.md:3782` says *"lines 78-85"*; the T246 brief says *"Lines 78-87"*. **Measured: the status block
is lines 80-88**; 78 and 79 are blank. Line 89 is blank and line 90 begins the substantive
*"Revision 5 changes exactly two things"* paragraph, which is **not** part of the status block and must
not be swept into a re-stamp (see `F-5`). `§9 item 13 (lines 2568-2569)` is **correct**.

---

## F-T246-5 — **LOW.** G-13 item 2 (the status re-stamp) is a SPLIT decision, and framing it as (a) fact vs (b) amendment hides the operative test.

**The argument, as asked, not a preference.**

The (a)/(b) dichotomy is false, because it turns on **size** ("it's only a status line") and size is
precisely the axis the driver already refused to reason on when it overruled `A2-34`: *"the first
amendment waved through as too-small-to-gate sets the precedent for the next."* That refusal is right
and I do not want to reopen it.

**The axis that actually works is OWNERSHIP OF THE PROPOSITION:**

- A proposition the ADR **owns** — what the reference oracle does, what a conforming port must do,
  what this revision changed — is the thing ratification froze. Amending it needs a gate. **Always,
  and irrespective of size.**
- A proposition the ADR **quotes from an authoritative register it does not own** — `gates.md`'s G-11
  state, `tasks.json`'s task states, standing policy P-2 — the ADR has **no authority to state
  differently**. "Amending" it is not an exercise of authority at all; it is a **transcription repair**,
  and the gate that governs it is the gate that governs the register. **G-11 is already CLOSED.**

This test is checkable, it does not depend on magnitude, and it creates no "too small to gate"
precedent. It also has teeth in the other direction: it forbids re-stamping anything the ADR owns,
however trivial it looks.

**Applied to lines 80-88, the answer SPLITS — which is why "just re-stamp it" would be wrong:**

| clause | owner | verdict |
|---|---|---|
| L80 *"Status: DRAFT (revision 5) … NOT RATIFIED"* | `gates.md` (G-11) | **transcription repair** |
| L85-86 *"Gate G-11 remains OPEN — NOT RATIFIABLE in `.softhouse/gates.md` and `.softhouse/program.json`"* | `gates.md` / `program.json` — **it names its own sources, and both contradict it** | **transcription repair** |
| L86-87 *"Ratification requires a FURTHER independent review passing clean AFTER revision 5 under standing policy P-2"* | policy P-2 | **transcription repair** — and the condition is **SATISFIED** (`A2-33`) |
| L87 *"until then `A2-15` (promote GL vectors) stays blocked"* | `tasks.json` | **transcription repair — and it is a THIRD live falsehood nobody has named.** `A2-15` is `status: done`, merged at `1325e8b`, and its six vectors are graded on every run |
| L80-85 the four-rejections history (`A2-31`/`A2-25`/`A2-19`/`A2-14`) | **ADR-owned history** | **PRESERVE AS HISTORY.** Do not delete. It is true and it is the evidence trail |
| L80-81 *"`A2-32` is NOT AUTHORISED to ratify it and does not"* | ADR-owned, historical | **PRESERVE.** True of `A2-32` |
| **L90** *"Revision 5 changes exactly two things and nothing else"* | **ADR-owned, still TRUE** | **OUT OF SCOPE. Must not be touched by a status re-stamp** |

**RECOMMENDATION:** re-stamp **under G-13, on this review**, restricted to the four transcribed
propositions, **preserving the revision history as history** and **not touching line 90**. It should be
written as a NEW status paragraph stating what the document is now (RATIFIED rev 5 by G-11, then rev 6
by G-13), with the old block retained beneath it as the record — the same shape the ADR already uses for
its own retractions.

**The reason to do it now rather than defer it** is the one the driver already identified and I confirm:
leaving it **INVERTS** the protection. A reader of DEC-2 alone is told the document is an unratified
draft that *"`A2-32` is NOT AUTHORISED to ratify"*, which is an invitation to edit it freely — the exact
behaviour the ratification gate exists to prevent. **A protective rule that, left unmaintained, reads as
permission is worse than no rule.**

---

## F-T246-6 — **INFO.** Revision 6 corrects a SECOND falsehood in the same cell, and it is right to.

Revision 5's I-5 cell also says *"Refused with `ErrNoDiscriminatingVector`; **retired by one capture**."*
Revision 6 replaces the retirement condition with *"no reversal capture has been **PROMOTED** to a
vector"*. `T244` disclosed this (under "does not change", as "only its stated ground moves"). **I checked
whether that is an obligation change and it is not — it is the correction of a false claim about the
machinery.** Verified at `f13bf4a`:

- `.softhouse/vectors/README.md:326`: *"`ErrNoDiscriminatingVector` therefore keys off **counterfactual
  coverage**, not off pair difference. The harness computes, for every capability marked
  `in_graded_domain`, whether some **admissible parity vector** kills a named wrong implementation."*
- `.softhouse/vectors/capabilities-ledger.json`: `ledger.reversal.entry` → `in_graded_domain: false`
  [and 14 ledger capabilities enumerated; 6 true, 8 false].

So the refusal **never** keyed off captures. *"Retired by one capture"* was false about the harness from
revision 1, and three captures have now existed for hours without retiring anything — the sentence's own
prediction has been falsified in the field. The replacement is strictly conservative (harder to retire)
and matches the code. **Endorsed.**

**And the code already says so.** `nexus/internal/apps/ledger/conformance/invariants.go:36-47` carries
the corrected reason in terms — *"I-5 IS UNGRADED AND THE REASON HAS CHANGED SINCE DEC-2 WAS WRITTEN …
THAT IS NO LONGER TRUE"*. **The ADR and the Go tree currently CONTRADICT each other on a ratified
contract's stated ground, and revision 6 resolves the contradiction in the code's favour**, which is the
right direction: `A2-15` measured, DEC-2 did not.

---

## F-T246-7 — **INFO.** There is **NO THIRD SITE** of this falsehood. Established by ENUMERATION, not by pattern matching.

Pattern-matching for a *restatement* is the instrument that has failed this document before, so I did
not rely on it. **PASS 1 enumerated every occurrence of the stem `revers` in DEC-2** — a superset of any
regex sweep — and I read all of them:

```
DEC-2, 3031 lines. Stem `revers` (case-insensitive): 9 LINES, 15 OCCURRENCES.
  L271   "Buyan may reverse it at any time before cutover"        unrelated (reverse a decision)
  L380   the @Column list includes `reversed`                     TRUE (schema fact)
  L822   I-4: "a reversal is observable *as a row*, because the
         table carries a `reversed` flag"                          TRUE — and the OPPOSITE of the falsehood
  L823   **SITE 1**                                                FALSE
  L870   "a correction path that mutates a leg … (that is I-5)"    TRUE (a guard-coverage statement, no evidential claim)
  L2304  "Journal-entry writing, reversal … — slice A1"            TRUE (scope)
  L2436  "would mean nothing at all about … reversals …"           TRUE (a limits statement)
  L2568  **SITE 2**                                                FALSE
  L2569  (site 2's continuation)                                   FALSE
```

**Exactly two sites. Both are addressed, by Hunk A and Hunk B respectively.** `T244`'s further claim —
that the phrase matching site 1 does not match site 2 — **confirmed**: `contains?\s+no\s+revers` matches
**L823 only**; `no reversal appears` matches **L2568 only**. Landing Hunk A alone would leave site 2
standing.

**PASS 2** ran a MULTI-LINE matcher (`re.DOTALL`) for the CLAIM rather than the sentence, since T234
found 743 matches spanning a newline: 5 claim patterns, and the only newline-spanning hit in DEC-2 is
`L1952`, which is the unrelated `glAccountType` observation.

**PASS 3** swept **5,088 tracked files** repo-wide and returned 1,489 raw matches. Separating the
populations (`sweep-live-restatements.py`) gives **20 raw / 10 DISTINCT LIVE (file,line) sites** and
**1,469 matches inside transcripts** (1,315 of them in `T244`'s own `sweep-output.txt`, which quotes the
pattern and the line hundreds of times — **a transcript quoting a falsehood as evidence is not a site of
it**, and counting it as one is how a sweep manufactures alarm). Of the 10 LIVE sites, **2 are DEC-2's
and 8 QUOTE the falsehood as a known, correctly-attributed defect**: `RESUME.md:189`, `gates.md:35`,
`gates.md:3757`, `program.json:732`, `tasks.json:2514`, `capabilities-ledger.json:89`,
`invariants.go:38`, `invariants.go:47`. **None asserts it.**

**Calibration, all fail-CLOSED and all passed** [`sweep-third-site.txt`]: both known positives found by
line number (823, 2568); a known negative returning `[]`; a known positive planted in a **dot-prefixed**
file read successfully (the `--ignore-files` hole P-75 measures); PASS 3 re-asserted that both known
sites landed in its own output before any negative was reported.

---

## F-T246-8 — **INFO.** `T244`'s reversal measurement: all four terms REPRODUCE, including the three that rested on `T244` alone.

Instrument `measure-reversals.sh`, transcript `measure-reversals-output.txt`, run by me at `f13bf4a`
against the live oracle. **Calibration first, fail-closed:** three known-false predicates returned `0`;
a known-true predicate returned `60`, equal to the table total.

| term | `T244` | **`T246` (mine)** | |
|---|---|---|---|
| rows `reversed = true` | 8 | **8** | ✓ *(also driver-measured)* |
| rows `reversal_id is not null` | 8 | **8** | ✓ *(also driver-measured)* |
| **UNION** `reversed = true OR reversal_id is not null` | **8, not 16** | **8** | **✓ — and this is the term the driver had NOT measured** |
| intersection | — | **8** | flag and pointer sit on **exactly the same rows**: `A\B = 0`, `B\A = 0` |
| reversing legs (`id IN (select reversal_id …)`) | 8 further | **8** | ✓ — and **disjoint**: 0 of them carry `reversed = true`, 0 carry a `reversal_id` |
| total reversal population | 16 | **16** | ✓ |
| distinct transaction ids | 6 | **6** | ✓ — `a28f54bfdaf3 a28f54c1db73 a28f573f34c7 a28f57412abb a28f605fcdeb a28f614e0263` |
| reversal **pairs** | 3 | **3** | ✓ — 3 originating tx ids, each mapping to one reversing tx id |
| equal `amount` + flipped `type_enum` | 8 of 8 | **8 of 8** | ✓ — and `0` pairs with unequal amount, `0` with unflipped type |

The three pairs, dumped leg by leg rather than asserted:

```
33/34/35 (a28f54bfdaf3, reversed=t) -> 38/39/40 (a28f54c1db73)   3 legs
45/46/47 (a28f573f34c7, reversed=t) -> 50/51/52 (a28f57412abb)   3 legs
59/60    (a28f605fcdeb, reversed=t) -> 63/64    (a28f614e0263)   2 legs
```

**Double-entry holds in INTEGER MINOR UNITS on all six transactions** [my own re-derivation, not in
`T244`'s hunks]: `a28f54bfdaf3` and `a28f54c1db73` 12,500,055 = 12,500,055 · `a28f573f34c7` and
`a28f57412abb` 12,500,062 = 12,500,062 · `a28f605fcdeb` and `a28f614e0263` 100,000,000 = 100,000,000.

**The captures the ADR says do not exist — verified, and they tie to the live rows:**

| capture | request | status | body |
|---|---|---|---|
| `A2-348-je-reverse` | `POST /journalentries/a28f573f34c7?command=reverse`, tenant **`gerege`** | **200** | `{"transactionId":"a28f57412abb"}` — **the reversing tx of live rows 45-47 → 50-52** |
| `A2-349-je-manual-after-reverse` | read-back | **200** | **3** `"reversed":true`, **0** `"reversed":false` |
| `A2-460-je-reverse` | `POST /journalentries/a28f605fcdeb?command=reverse` | **200** | `{"transactionId":"a28f614e0263"}` — **live rows 59-60 → 63-64** |

**The KEPT clauses are kept correctly.** `A2-150-db-final-state.txt` projects neither `reversed` nor
`reversal_id` (`/usr/bin/grep -c 'revers'` = **0**), and its journal section is **6 rows / three balanced
pairs at 1,200,000.000000 = 120,000,000 minor units each**, at lines 65-70 — exactly the range DEC-2's
own I-1 row cites. **The clause is true; the defect was generalising from one snapshot of a 6-row table
to "the corpus", and the table now holds 60.** `A2-8`'s clause is carried `[NOT RE-OPENED HERE]`, as it
has been since revision 1; **scope: I did not open A2-8 either.**

**Population scope (P-66):** `fineract_default` (tenant 1) has **0** journal rows and **0** reversals, so
the whole population is tenant 2's.

---

## F-T246-9 — **INFO.** The landing hazard is confirmed from source AND DRIVEN RED AND GREEN IN FOUR DIRECTIONS (P-22).

**From source**, at `f13bf4a`:

```go
// nexus/internal/apps/ledger/conformance/admit.go:49-51
if opts.Pin != nil {
        if v.DEC2Revision != opts.Pin.DEC2Revision {
                add("dec2_revision %d but the store pins %d", v.DEC2Revision, opts.Pin.DEC2Revision)
```

- **Every** `DEC2Revision` reference in the Go tree: `vector.go:460,479` (the field), `admit.go:50-51`
  (this comparison), `capability.go:80,111,113,155` (the pin's own `> 0` validity check). **There is no
  other consumer.**
- All six `LDG-*` vectors declare `dec2_revision: 5`; `PIN-ledger.json` declares `5`. **Confirmed by
  reading all seven files.**
- **No Go source and no line of `conformance.sh` reads the ADR.** The only `docs/adr` string under
  `nexus/` is a comment in `loanschedule/contract/contract.go:7` naming **DEC-1**; `DEC-2-gl-accounting`
  matches **0 times** across `nexus/` and `.softhouse/conformance.sh`.

**Driven, not reasoned** [`drive-pin-red.sh` / `.txt`, in a `/tmp` scratch copy — **the worktree's
`.softhouse/vectors/` was never written**]:

```
GREEN    pin=5 vectors=5  ->  inspected=6 inadmissible=0 dec2_reasons=0
RED-A    pin=6 vectors=5  ->  inspected=6 inadmissible=6 dec2_reasons=6   "dec2_revision 5 but the store pins 6"  x6
RED-B    pin=5 vectors=6  ->  inspected=6 inadmissible=6 dec2_reasons=6   "dec2_revision 6 but the store pins 5"  x6
GREEN2   pin=6 vectors=6  ->  inspected=6 inadmissible=0 dec2_reasons=0
```

**`GREEN2` is the direction `T244` did not drive, and it matters:** the check is **RELATIVE**, not
"absolute 5", so *"bump both"* is **harness-green** and the argument against it is **not** correctness —
it is **P-61**: bumping both moves `git rev-parse HEAD:.softhouse/vectors` off
`13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`, and every pending task BAR pins that value. (`8275f8b` is
the driver catching exactly that class two commits ago.) **So the recommendation stands, on a stated
reason: LEAVE `PIN-ledger.json` AT 5 and leave the six vectors at 5.**

**The instrument's first run FAILED ITS OWN GREEN CONTROL** (6 inadmissible on unresolvable
`provenance.capture_ref` paths, because the scratch root had no capture tree). It printed the failure
and exited non-zero rather than reporting a number. **That is the fail-CLOSED behaviour the `T238`
dead-`cd` class requires**, and it is recorded here because a silently-passing setup is exactly how this
program has been given confident wrong numbers twice.

---

## F-T246-10 — **INFO.** Revision 6 changes ONLY the evidential reason. Every obligation checked individually.

| obligation | revision 5 | revision 6 | verdict |
|---|---|---|---|
| the invariant statement, col 3 | *"A correction adds a leg pair; it never mutates one"* | **byte-identical** | **UNTOUCHED** |
| col 5, `Graded today?` | **NO** | **NO.** *"Unchanged."* | **UNTOUCHED**, and the new supporting text (six `LDG-*`, `in_graded_domain: false`) is **TRUE** — verified |
| the refusal code | `ErrNoDiscriminatingVector` | `ErrNoDiscriminatingVector` | **UNTOUCHED** (its *ground* moves — `F-6`) |
| the rule paragraph, L828 | *"DEC-2 **obliges** I-1 through I-5 … and **grades none of them today**"* | not in either hunk | **UNTOUCHED** |
| `PIN-ledger.json`, the six vectors, `nexus/` | — | not in either hunk | **UNTOUCHED** — `F-9` |
| col 4's answer | *"UNGRADED TODAY"* | *"PARTLY"* | **evidential.** §4.4 defines col 4 as *"do captured oracle bytes exist … **This is a question about the corpus**"*, and "PARTLY" is the honest answer: the ADDS-A-PAIR half is separable from captured bytes, the NEVER-MUTATES half is not |

**I looked specifically for the temptation `T244` says it looked for, and I did not find it taken.** No
hunk narrows or widens the graded domain, no hunk touches `in_graded_domain`, no hunk changes what a
port must do. **If a later reader concludes I-5's refusal should now be retired, that is a graded-domain
amendment and a separate, larger gate — it must not be folded into a reason-correction, and revision 6
does not fold it in.**

---

# THE BAR — run by me, at `f13bf4a`, pasted from `bar-output.txt`

```
HEAD              : f13bf4af24934544117b4b19bf8df1b2d4b28563
branch            : softhouse/T246-review-dec2-rev6
vector store tree : 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d      <-- READ LIVE, and UNCHANGED after
go: go version go1.26.6 darwin/arm64

conformance exit = 0                                              (bash, never sh)
PROBE LINE — PRESENCE tested FIRST, and it is PRESENT:
  conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
      oracle probe    UP

VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.

    parity vectors          PASS 46   FAIL 0
    inadmissible            0
    harness errors          0
    cells compared          7884 graded, 93 ungraded (never recorded by the capture)
    invariant violations    0
    invariant assertions    0 NOT RUN
    invariant assertions    4 EXEMPTED BY A VECTOR
  LEDGER (tierA-gl-accounting) — SECOND SCHEMA, SECOND COMPARATOR, SEPARATE COUNTS
    ledger inadmissible     0
    ledger harness errors   0
    ledger cells compared   70 graded, of which 21 are MONEY cells in int64 minor units

CENSUS — all NINE pins == pinned:
  exempted assertions (graded) = 4 == pinned 4
  declared exemptions (loaded) = 4 == pinned 4
  GROUNDED                     = 4 == pinned 4
  UNDETERMINED-ON-THE-RECORD   = 0 == pinned 0
  UNGROUNDED                   = 0 == pinned 0
  LEDGER declared exemptions   = 0 == pinned 0
  LEDGER parity vectors        = 4 == pinned 4
  LEDGER oracle-refusal vector = 2 == pinned 2
  LEDGER money cells compared  = 21 == pinned 21

--prove              PROOFS: 23 passed, 0 failed        (exit 0)
go build ./...       0 lines
go vet ./...         0 lines
go test ./... -count=1   exit 0
  ok  github.com/gerege/nexus/internal/apps/ledger                      0.569s
  ok  github.com/gerege/nexus/internal/apps/ledger/conformance          5.090s
  ok  github.com/gerege/nexus/internal/apps/loanschedule                8.717s
  ok  github.com/gerege/nexus/internal/apps/loanschedule/conformance   74.915s
gofmt -l             internal/apps/loanschedule/contract/contract.go     (exactly one; NEVER gofmt -w it, G-3)

THE STORE IS UNCHANGED:
  vector store tree AFTER : 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d
  git status --porcelain -- .softhouse/vectors docs/adr .softhouse/gates.md nexus  ->  (empty)
```

**A green bar means "builds, tests green, known-bad patterns absent, matches the reference oracle on
captured vectors". IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a `user` gate.**

---

# WHAT I DID NOT DO, WITH ITS SCOPE

- **I did not land revision 6.** Out of scope by instruction; it is the driver's act, and only if it
  accepts this review.
- **I did not touch `docs/adr/`, `.softhouse/gates.md`, `.softhouse/vectors/`, `PIN-ledger.json` or
  `nexus/`.** Verified empty in `git status --porcelain` over exactly those paths, after the BAR.
- **I did not open `A2-8`'s grading table.** Carried `[NOT RE-OPENED HERE]`, as revisions 1-6 all do.
  **Scope: the clause is inherited, by me as well as by `T244`.**
- **I did not re-POST any reversal**, and no instrument of mine writes to the oracle — every query is a
  `select`. Mutating the oracle to grade it is the error `A2-34` refused and I refuse it too.
- **I did not pursue the `02:43:48Z` / `02:49:46Z` recompute batches** beyond establishing the 60/60
  denominator. **That is G-12's territory and G-12 is already open.**
- **`F-1` is reported, not fixed.** It needs its own gate and its own independent review; writing the
  correction here would be an agent amending a ratified DEC-n without a gate, which is the rule this
  whole task exists to respect.

# INSTRUMENTS AND TRANSCRIPTS (all under `.softhouse/reviews/t246-dec2-rev6/`)

| instrument | transcript | what it establishes |
|---|---|---|
| `measure-reversals.sh` | `measure-reversals-output.txt` | all 8 reversal terms, calibrated, live |
| `measure-mutation-claim.sh` | `measure-mutation-claim.txt` | 16/16 **and** 60/60; the recompute batches; minor-unit balance |
| `measure-revision-history.sh` | `measure-revision-history.txt` | both sites present in revisions 1-5 and at HEAD; the staleness timeline |
| `drive-pin-red.sh` | `drive-pin-red.txt` | the landing hazard, 4 scenarios RED/GREEN |
| `sweep-third-site.py` | `sweep-third-site.txt` | exhaustive enumeration + multi-line + repo-wide, calibrated |
| `sweep-live-restatements.py` | `sweep-live-restatements.txt` | LIVE (10) vs TRANSCRIPT (1,469) separation |
| `sweep-adjacent-staleness.py` | `sweep-adjacent-staleness.txt` | `F-1`'s seven sites |
| `sweep-vectors-reversal.sh` | `sweep-vectors-reversal.txt` | no vector grades a reversal; LDG-01 grades a reversed original's legs |
| `bar.sh` | `bar-output.txt` | the BAR |

**One observation from `sweep-vectors-reversal.txt` worth carrying, which no hunk states:** `LDG-01`
grades three legs of transaction **`a28f573f34c7`** — which is itself one of the three **reversed
originals** (live rows 45/46/47, `reversed = true`). It projects **no** `reversed` and **no**
`reversal_id` cell, so it grades nothing about the reversal and Hunk A's column 5 is correct as
written. But *"no vector grades a reversal"* is precise only in the sense *"no vector grades the
reversal columns or the reversing legs"* — one vector does grade money cells belonging to a transaction
that was later reversed. **Not a defect, and not grounds for anything; recorded so a later reader who
finds the id in both places is not surprised by it.**
