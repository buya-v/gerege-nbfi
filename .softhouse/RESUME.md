# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260823-080016` CLOSED CLEAN — 8 dispatched, 8 completed, **8 merged**, **0 live at exit**

Every worker was awaited. Nothing was killed. `git status --porcelain` empty at exit.

**BAR at close, run by the driver on the final merged tree — never accepted from a worker's paste:**
```
bash .softhouse/conformance.sh  ->  PASS exit 0
                                    probe line PRESENT, reads `up`
                                    46 parity vectors / 7884 cells
                                    LEDGER: 4 parity + 5 oracle-refusal, 21 money cells
                                    all 9 wrong ledger implementations DIED through the harness
                                    census == pinned (18, now DERIVED)  ·  frontier == pinned (11)
```

> **THIS FIRE'S ID.** It is the **2026-08-23 08:00 local** fire. The driver built the id from the **UTC**
> clock in its launch note and slid the date a day, labelling early records `20260824-000016`. Every
> dispatch record and commit message written before the correction carries the wrong id. See
> `.softhouse/observations/20260823-driver-fire-id-and-date-error.md` — it did not stay contained.

---

# HEADLINE 1: THE LEDGER CORPUS MOVED — 6 → 9 VECTORS, 6 → 9 WRONG IMPLEMENTATIONS

It had been frozen at **6 vectors / 21 money cells** for many fires while `capabilities-ledger.json`
itself printed *"Both are CHEAP captures … nobody has taken them."*

**And the money-path finding is no longer prose.** `:636` is
`!DateUtils.isBefore(closingDate, transactionDate)` — **INCLUSIVE**, refusing `transactionDate <=
closingDate` — while the oracle's own message says *"prior to"*. A port written from the message text gets
a strict `<` and **fails open on exactly the day a period-end adjustment carries.** T295's `LDG-REFUSE-04`
promotes the one capture dated **ON** the closing date — the only relation separating the two readings —
and `ledger-wrong-closure-boundary-exclusive` is registered, executable and **measured KILLED**.

**T294 answered P-92 with CONTENT, not a comment.** T287's four probes are armed because only an
*oracle-side precondition* refuses them; T294's body is **unbalanced by one MNT minor unit**, so it is
unpostable **on its own content** — permanently, clock- and state-independently. That bought an unasked-for
bonus: the oracle had **two** grounds to refuse and answered with the opening-balance code, so **`:717`
beats `:651` by measurement** — the only ordered refusal pair in this corpus.

**T295 settled all four T287 captures: 2 PROMOTED, 2 NOT PROMOTABLE BY MEASUREMENT, 0 PROBES FIRED.**
A2-02's body is **byte-identical** to A2-01's despite a different transaction date, so it cannot diverge on
any graded cell — and the identity is itself the finding: `ACCOUNTING_CLOSED` echoes the **closing** date
(`:637`), `FUTURE_DATE` echoes the **transaction** date (`:631`).

Driver re-measured the oracle first-hand after every ledger merge: `acc_gl_journal_entry` **60 / maxid 64**,
`acc_gl_closure` **0**, distinct transaction ids **26** — unchanged all fire.

# HEADLINE 2: FOUR WORKERS REFUTED A DRIVER FIGURE OR CLAIM, AND ALL FOUR WERE RIGHT

- **T256** — the brief said 30 instruments / 40 files. Re-derived: **92**, and it traced where "30" came
  from (T253's `RUNNABLE: 30`, the *first* literal only). Then found the load-bearing fact: **zero live
  executable hardcodes**, so the 60 remaining sites are archived drives nothing runs, and rewriting them
  would destroy the instrument↔transcript pairing. It fixed **the instruction** instead.
- **T284** — the brief said three frozen call sites. Measured **13 files / 24 invocations, only six the
  defect**; five are correct by design, including one whose "repair" would have destroyed T274's RED arm.
- **T295** — the brief said bump `MONEYCELLS`. It **held at 21** and argued it in place: a refusal vector
  asserts no amount and `cmpMoney` is unreachable via `diffRefusal`. Bumping would record comparisons
  nobody performs.
- **T293** — adjudicating the driver's own census pin, it **upheld the row and killed two of the stated
  reasons**: the justification cited a line T273 had deleted *in the same fire*, and "it restores the state
  it found" is a runtime argument applied to a **static** linter.

# HEADLINE 3: T292 BROKE A FIVE-FIX LOSING STREAK BY FINDING THE ROOT NOBODY HAD WRITTEN DOWN

`walk_rows` was serving **two purposes whose fail-closed directions are OPPOSITE** — detection wants
maximal generosity, coverage wants maximal strictness. T268 widened it for detection and widened coverage;
T286 narrowed it for coverage and lost a bracket further out. **Every link traded one against the other
because both read the same number.**

No sixth shape-patch: the word "bracket" does not appear in the coverage predicate, because it **does not
look at containers at all**. And the other half is a **measured impossibility** — guard #10's ambition is
unreachable by any container-blind rule, because the three `RESCUED_BY_SITE3` rows carry `AS PREDICTED`
with no P-key **by design**. **325 documents, 0 lost refusals — and the zero is CALIBRATED**: plant the
lineage's defect and the same counter reports **28 across 12 fixtures**.

# THE DRIVER'S OWN ERRORS THIS FIRE, ALL FILED RATHER THAN BURIED

1. **Backticks in commit messages were executed.** One merge message absorbed a **6,733-line `git ls-files`
   dump**. Caught before push; all three merges rewritten from message files.
2. **The fire id was built from the UTC clock and slid a day — and it PROPAGATED.** T296 reported probe
   `a1-02` *"armed yesterday (2026-08-24)"*. **False.** Driver-measured: host clock `Sun Aug 23 10:52 +08`,
   oracle business date `2026-08-23`, and the guard says a1-02 **still refuses — it arms TOMORROW.**
   A driver clerical error became a worker's factual claim about an armed, irreversible probe.
3. **An exit status was read through a pipe** (`| tail` → `$?` is *tail's*). Redirected, the probe guard is
   **RED exit 1** as the record says. Same shape as P-84 and T293's F2.
4. **A merge-time widening of T296's capability gate, unreviewed.** Filed as **T306**, with the reasoning
   written into `admit.go` beside the rule — the file a reviewer reads.

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first.** Zero tasks `in_progress`; **zero live workers.**

1. **`T306`** — adjudicate the driver's unreviewed widening. Two of its three arms are keyed on
   `expect.refusal.code`, which is an **OUTPUT** — keying admissibility on what a vector *claims* is close
   to letting the vector authorise itself. Attack that first.
2. **`T308`, `T302`, `T298`** — the independent reviews of T292, T288 and T256. **T308 is the fifth link in
   the R-VPA lineage; four of the five previous links were killed by a reviewer, not by their author.**
3. **`T305`** — F-T296-2: the opening-balance vector **grades the COMMAND, not the PREDICATE**. A port
   matching on the command alone survives the whole corpus, so a port refusing *every* opening balance —
   including on an empty ledger where the oracle **accepts** — is green. Only an **accepting-side** capture
   closes it, and that is irreversible on any tenant worth keeping.
4. **`T303`** — wire T284's registry guard. **T284 refused to cite its own guard as enforced** because
   `conformance.sh` was partitioned away from it. That instinct is right and this program has recorded the
   same lesson five times; T303 exists so it is not the sixth.
5. **`T301`** — the wrapper edits itself while running. Merging T288 grew `fire-program.sh` from 45,665 to
   **64,888 bytes mid-execution**, and zsh reads a script by byte offset.
6. Then `T307`, `T299`, `T304`, `T300` follow-ons, `T270`, `T272`, `T277`, `T279`, `T282`, `T257`, `T258`,
   `T226`, `T235`, `T145`, `T160`, `T174`, `T192`, `T195`, `T266`, `T267`.

## THE STANDING HAZARD — READ BEFORE TOUCHING THE T287 RIG

All four probes in `.softhouse/capture/t287-closure-refusals/req/` are **valid, balanced, postable journal
entries**. Only an oracle-side precondition refuses them, and **when it lapses the request becomes a write
— and a posted journal entry cannot be deleted.** Driver-measured this fire, `exit 1`:

| probe | date | state as of **2026-08-23** |
|---|---|---|
| `a2-01` / `a2-02` | 2026-01-31 / 2026-01-15 | **WOULD POST 2 JOURNAL ENTRIES EACH, NOW** — no GLClosure exists at office 1 |
| `a1-02` | **2026-08-24** | still refuses — **arms TOMORROW** |
| `a1-01` | 2026-12-31 | still refuses — arms 2027-01-01 |

`guard-probe-expiry.sh` is **RED, exit 1**. Run it, and read its exit status **without a pipe**.

## What is NOT true, and must not be inferred from the green bar

- **`T269` MUST NOT BE WIRED.** `F-T290-1b`'s floor on `disagreements` still does not exist, and **T292
  confirms its own rule does not close it** — driven, not assumed. No R-VPA rule may be wired until then.
- The ledger's **accrual, account transfers (gl 17), charge-off, multi-currency and slot resolution** remain
  **ungraded**; the harness prints all eight rows every run. Only the **REFUSAL** side of both date
  boundaries is pinned — the **acceptance** side is `[UNVERIFIED]` and costs permanent journal entries.
- **`G-4`, `G-5`, `G-8`, `G-10`, `G-12` remain OPEN**; `G-4` and `G-5` are hard `user` gates. `G-8`'s region
  is a conservative superset resting on the unproven conjecture `δ ≤ 1`, and **options (b)/(c) must not be
  put to Buyan — unconditionally, with no expiry.**
- Two of the 46 loanschedule vectors have `principal_amortizes_to_zero` switched OFF, legitimately and loudly.
- **Nothing was cut over, and nothing here authorises it.** The gate register at the top of `gates.md` is
  authoritative.

## P-86: cite the rule, or the id AND its sentence — never the id alone
