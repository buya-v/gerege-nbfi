# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260823-080004` CLOSED CLEAN — 8 dispatched, 8 completed, 7 merged, **0 live at exit**

Every worker was awaited. Nothing was killed. `git status --porcelain` empty at exit.

**BAR at close: `PASS exit 0`, probe line PRESENT and reads `up`, 46 parity vectors / 7884 cells — with
`/tmp/t234_matrix2.txt` ABSENT.** That last clause is the fire's headline; see below.

---

# HEADLINE 1: THE BAR NO LONGER DEPENDS ON A 24-BYTE FILE IN `/tmp` — `T273` VERIFIED FIXED

Driver-verified on the merge result, both directions:

```
BEFORE T273 :  rm /tmp/t234_matrix2.txt  ->  EXIT 2, probe lines printed 0
AFTER  T273 :  rm /tmp/t234_matrix2.txt  ->  PASS exit 0, probe = up, 46 vectors / 7884 cells
                                             and the file is NOT recreated
```

**This is the first green bar on this host reproducible from a clean checkout** rather than resting on residue
a previous run happened to leave. The file is still absent as this manifest is written, after a full
multi-hour, eight-agent fire.

**`T285` earned that by splitting the branch instead of grading it as one thing.** It APPROVED T273 proper
(`7e85a3e`…`9da1d87`) and **REJECTED the commit that arrived on top** (`2ae2c8c`), with a *measured* cut line:

> `80-host-state-bracket.py` decides "out of repo" by prefix against `git rev-parse --show-toplevel`. Every
> agent worktree lives **under** the main checkout. **Delta = 7 rows from a worktree, 2 from the main
> checkout. The pin is 7.**

**The driver reproduced it** (`VERDICT … 2 row(s) differ`) and reverted `2ae2c8c` at `cd07c06`. Merging it
would have made the **daily unattended fire exit 2 with no probe line** — the exact ambiguous signal T273 was
filed to remove. T285 also settled that `rm` is a **strictly stronger** reboot simulation: the harness reads
`os.path.exists`, not how the file went away, so the reboot case need never be observed.

**The race has FOUR independent confirmations by four different routes** — `T271` incidentally while working
on `t219`; the driver's own mtime measurement (`Aug 22 22:50` → `Aug 23 08:37` on a host with 5½ days uptime,
recorded in `.softhouse/observations/20260823-tmp-residue-race.md`); `T283` hitting exit 2 mid-session when
the file *"vanished on its own"*; and `T285` watching it vanish twice with no action of its own. **T285 was
deliberately NOT told about the driver's observation**, so its adjudication stayed its own.

# HEADLINE 2: THE FIRST NEW LEDGER CAPTURE IN MANY FIRES — AND ALL FOUR PROBES WERE ARMED (P-92)

**`T287`** took the two refusals the registry itself prints as *"CHEAP captures … nobody has taken them"*. It
re-derived its citation before sending anything, and **refuted the driver's own brief on the load-bearing
point**: a `GLClosure` is **not** irreversible — `GLClosure.java:50` carries `is_deleted` but **no
`@SQLDelete`**, so `repository.delete()` is a genuine hard delete. It flagged that its whole justification
rested on that rather than quietly relying on it, placed the closure **before the earliest existing entry** so
the plan was safe *even if the delete had failed*, and noted the driver's suggested fallback (a dedicated
office) would have been **worse** — offices have no delete at all.

**Driver-verified first-hand:** `acc_gl_closure` **0**, `acc_gl_journal_entry` **60 / maxid 64** (the ledger
never moved), `acc_gl_closure_id_seq is_called=t` (**disclosed residue — the next closure is id 2, not 1**),
`m_portfolio_command_source` 351.

**`T289` then found what `T287` had not claimed.** Every probe body is a **valid, balanced, postable journal
entry**; the only thing refusing them is a **precondition in the oracle**, and when it lapses the request
**becomes a write** — and a posted journal entry cannot be deleted.

| probe | date | armed |
|---|---|---|
| `a2-01` / `a2-02` | 2026-01-31 / 2026-01-15 | **NOW** — T287 deleted the closure that refused them |
| `a1-02` | **2026-08-24** | **tomorrow** |
| `a1-01` | 2026-12-31 | 2027-01-01 |

All four carry the comment **`"Expected REFUSED, writes nothing"`** — false as of T287's own delete — and
T287 §7.5 told the promotion task *"re-taking arm 2 is cheap now, the recipe is committed and re-runnable."*
**`guard-probe-expiry.sh` is merged and driver-verified RED (exit 1)**, printing *"Firing this POSTS 2 JOURNAL
ENTRIES into the reference oracle, PERMANENTLY."*

`T289` also **overturned T287's registry adjudication** by looking where T287 declined to: `defineOpeningBalance:703`
reaches the same cited guard at **`:724`**, so `ledger.opening.balance.and.closure` is **coherent, not
misnamed — DO NOT RENAME OR SPLIT IT** — and it named a **cheaper untaken capture** at `:810-816` needing
**no mutation and no clock**.

**Money-path finding for the port, verified at `:636`:** `!DateUtils.isBefore(closingDate, transactionDate)`
— the closure boundary is **INCLUSIVE**, while the message says *"prior to"*. A port written from the message
text gets a strict `<` **and fails open on exactly the day a period-end adjustment carries.**

# HEADLINE 3: FIVE FIXES FOR ONE FAIL-OPEN, ALL LOSING THE SAME WAY (P-91)

`T259` (printed REFUSED, exited GREEN) → `T268` (second fail-open) → `T281` rejected → `T286` (found a
**third inside the in-flight repair for the second**, plus a **fourth**: `--help` → `SystemExit(0)` → exit 0
**with no probe line**) → **`T291` REJECTED T286.**

`T286` chose *"a record is a row reached through a list"* over *"the root doesn't count"* **precisely because**
it had measured the root phrasing losing to a one-line evasion. `T291` beat the replacement with **two
characters** — wrap the fixture header in `[ ]` — giving **exit 0 GREEN, `predicates=0`, where the pre-`T268`
rule exits 1 REFUSED**: a **lost refusal**, the exact criterion `T281` used to reject `T268`. Also at depth 2
and 4, as a list-of-lists, and as a **top-level JSON array** — the shape this program's own `t286-legs.json`
uses. **Reproduced inside `T286`'s own sweep, unmodified: 42 fixtures, 4 lost refusals, FAIL.**

**`T292` is the retry and is told NOT to patch the bracket** — a sixth shape-patch is the predicted output and
will be rejected. The question is whether a **fail-closed-by-construction** formulation exists (invert the
burden: make the document *demonstrate* coverage in a form the rule constructs rather than recognises), **or a
measured argument that none does.**

**Corollary that bit here:** `T286` offered *"32 passed, 0 failed, **0 SKIPPED**"* as proof; `T291` measured
that **the battery returns exit 0 with legs SKIPPED** (23/0/9 → 0). The rig is inside the trust boundary of
what it grades.

# HEADLINE 4: `T290` CONFIRMED T271'S MONEY EXACTLY AND OVERTURNED ITS READING

`T290` built an instrument that reads only the raw gz and `prediction.json`, with an `open`/`gzip.open`
**interposer that hard-errors on any path containing `classify`/`acknowledged`**, `parse_float=Decimal`, and
`assert type(v) is int` on every operand. It reproduced `T271` exactly: `carriers=7 agreeREG=4 agreeCORR=6
agreeUNCOND=7 structureHolds=6`, row sums equal to the capture's own header totals 7 of 7.

- **`F-T290-2` (MAJOR):** *"out of domain" is a **post-hoc narrowing***. P2 is registered **"on every
  unrescued cell"** (`t229-g8-site3/PREDICTION.md:183`); this cell **is** unrescued; `T271` never quotes the
  registration (**grep for `unrescued` across all 31 files + handoff: ZERO hits**); and the substitution is
  **circular** — P2's first two conjuncts *are* the EMI-plus-balloon assertion. **Driver verified the
  citation.** Left standing and now false as measured: `t229/PREDICTION.md:192-193`, *"the first two conjuncts
  STAND on every unrescued cell checked."*
- **`F-T290-1b` (MAJOR, BLOCKING, open under BOTH rules):** the **invisible route to green** (P-88). A
  **consistent two-file edit** — retro-edit the evidence **and** re-pin the register with its rows removed —
  is **GREEN on the live rule AND on `T286`'s rewrite**, because nothing is left to void. **Only a FLOOR on
  `disagreements` catches it, and no rule on any branch has one.**

**Attacks that FAILED, recorded as evidence of coverage:** same pairs at an unnamed path; a one-byte in-place
edit; a new fifth disagreement (`unack=5`, cannot be absorbed); a register aimed at another file — **all
refuse.** `T271-INDEP`'s independence **holds**, proven by audit hook and adversarial swap. Battery leg **G1
genuinely fails** when the count drops — broken deliberately, 5 of 12 legs red.

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first.** Zero tasks `in_progress`; **zero live workers.**

1. **`T292`** — the R-VPA retry. Read `P-91` before writing a line. **A sixth shape-patch will be rejected.**
   It also carries four defects `T291` measured that are *not* about the bracket: the battery passes with legs
   SKIPPED; duplicate predicate keys go green (JSON last-wins drops a recorded `false`); **`parse_constant`
   unset lets `NaN`/`Infinity` into a GREEN run AS FLOATS — a money non-negotiable**; and `read_text()` has no
   encoding, so **a Cyrillic payload exits 2 under `LC_ALL=C`, and Mongolian names are Cyrillic.**
2. **`T293`** — adjudicate the driver's **unreviewed** census-pin decision (see below). It is filed to be
   second-guessed, and a reviewer that disagrees should revert the row and repair the probe.
3. **`T269`** — **MUST NOT BE WIRED** until `F-T290-1b`'s floor on `disagreements` exists. Four hard
   preconditions are recorded in its `tasks.json` note: pin **all four** counters (not just `unacknowledged=0`),
   **anchor by content, not line 1569**, state which rule it installs, and note that **every approval this
   fire covers merging as a DECLARED ORPHAN and none covers wiring.**
4. **Promote `T287`'s captures** — the ledger corpus is still **6 vectors / 21 money cells**. Read `T289`'s
   date strategy first: **none of the four is promotable as a literal-date vector**; lift `businessDate` and
   `latestClosingDate` out of prose into the vector's `inputs` and **never re-fire the probe**. `T289` also
   named a cheaper untaken capture at `:810-816` needing no mutation and no clock.
5. **`T288`** — the wrapper detects the exit-protocol violation and does nothing. Then `T270`, `T272`, `T277`,
   `T279`, `T282`, `T284`, `T256`, `T257`, `T258`, `T226`, `T235`, `T145`, `T160`, `T174`, `T192`, `T195`,
   `T266`, `T267`.

## THE ONE UNREVIEWED JUDGEMENT THIS FIRE MADE, STATED PLAINLY

At close the bar went **exit 2, zero probe lines**. Not an oracle outage (`P-84` — read the **absence** of the
line; the oracle answered SQL seconds earlier), not a corpus defect: **`T273`'s brand-new guard had caught
`T271`'s brand-new probe, both merged in the same fire** — census 18 against a pin of 17.

The driver **PINNED the row rather than repairing the probe**, arguing `mktemp` is inapplicable by
construction because the probe exists to measure whether the bar depends on *one specific absolute path*, so
naming it **is** the measurement. **The reasoning is written into `conformance.sh` beside the pin**, not into
a commit message, because that is the file a reviewer reads. **This was not independently reviewed** and is
filed as **`T293`**. The bar returned to PASS **with the residue still absent**. See `P-93`.

## What is NOT true, and must not be inferred from the green bar

**The ledger is still graded on six captured cases and no more, and NO VECTOR WAS ADDED THIS FIRE** — T287's
captures are **raw observed** and promotion is a separate task by design. Accrual, account transfers (gl 17),
charge-off, multi-currency, opening balances/`GLClosure` and **slot resolution** remain **ungraded**; the
harness prints all eight rows every run. **Two of the 46 loanschedule vectors have `principal_amortizes_to_zero`
switched OFF**, legitimately and loudly. **`G-4`, `G-5`, `G-8`, `G-10`, `G-12` remain OPEN; `G-4` and `G-5`
are hard `user` gates.** **`G-8`'s region is a conservative superset only**, resting on the unproven
conjecture `δ ≤ 1`, and **options (b)/(c) must not be put to Buyan — unconditionally, with no expiry.**
**Nothing was cut over, and nothing here authorises it.** The gate register at the top of `gates.md` is
authoritative.

## Cite the rule, or the id AND its sentence — never the id alone (P-86)

Every worker prompt this fire wrote the **full rule text** beside each pattern id. Keep doing that: when the
ids were off by one two fires ago, materiality was LOW for exactly this reason — the sentence carried the
instruction and the number was decoration.
