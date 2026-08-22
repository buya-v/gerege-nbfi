# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260822-060013`, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A slice **A2**, plus Tier-0 harness work.
- **SIX DISPATCHED IN TWO WAVES, SIX COMPLETED, SIX MERGED, ZERO LIVE AT EXIT.** Every branch
  scope-checked by the driver on the **three-dot** diff before merge; the BAR re-run by the driver on the
  **merge result** after every merge, never quoted from a worker.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL 18.3 only.

**Driver-verified on merged `main` at exit:**

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0)
  loanschedule  46 parity · 7884 graded cells
  LEDGER         4 parity · 2 oracle-refusal · 21 money cells
  ledger citations  12 PART-TWO resolutions: 1 ARTEFACT-BYTES · 8 HTTP-SIDECAR · 3 FILE-NAME-ONLY  <-- NEW
  refused 0 · inadmissible 0 · harness errors 0 · invariant violations 0 · 0 NOT RUN
  all 9 census pins == pinned
  vector store  13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d   (MOVED — see below)
  PIN-ledger.json  dec2_revision: 5   DELIBERATELY NOT BUMPED
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**THE STORE DIGEST MOVED AGAIN**, `8968c559…` → **`13b8342e…`**, when `T242` landed. **Every BAR quoting
`8968c559…` or `73c3ea7b…` is now stale.** The driver verified before accepting it that the move is
confined to `capabilities-ledger.json`: the `loanschedule`, `_selftest` and `ledger` subtrees are
byte-identical either side and all four PIN/capability/README blobs are unchanged. **No graded payload moved.**

---

# HEADLINE 1: DEC-2 REVISION 6 IS RATIFIED AND LANDED — G-13 CLOSED

`T244` PREPARED it and landed nothing. `T246` reviewed it **independently**, re-deriving against the live
oracle, and returned **ACCEPT** conditional on two corrections. **The driver applied both, ratified
`chosen_by: agent`, landed it, and re-ran the bar.** Buyan may reverse it.

The corrected evidential reason, re-derived by **both** workers: **8 reversed originals + 8 reversing legs
= 16 rows, 3 pairs, 6 transaction ids**, equal `amount` and flipped `type_enum` 8 of 8. **No obligation
moved** — the invariant statement, column 5's `Graded today? NO`, the `ErrNoDiscriminatingVector` refusal
and the rule paragraph are all untouched. Only the ground moved, from *"no reversal exists"* to *"no
reversal capture has been PROMOTED to a vector"*.

- **`T246` found a SECOND SITE `T244` had already found and the task had not named** (§9 item 13) — and
  demonstrated that the phrase matching site one does **not** match site two.
- **`F-2` stopped a fresh unsupported inference entering a ratified contract.** The draft cited *"all 16
  rows show `last_modified_on_utc > created_on_utc`"* with no denominator. **60 of 60** rows carry it,
  clustered at the G-12 recompute. **100 % of the subgroup AND 100 % of the population discriminates
  nothing.** The conclusion was right by a stronger route — a snapshot never observes a write at all — and
  the landed text says that instead.
- **`F-3`** required a re-measure stamp **at ratification**; `main` had moved five times since drafting.
  The landed text carries **both** stamps.
- **⚠ `PIN-ledger.json` STAYS AT 5.** `admit.go:49-52` compares vector-to-pin and never reads the ADR.
  `T246` drove it four ways including `pin6/vec6 → 0`, the direction `T244` did not drive — which shows the
  check is **relative**, so the argument against bumping both is **P-61**, not correctness.

# HEADLINE 2: G-14 RAISED — DEC-2's OPENING BANNER IS FALSE, AND IT NAMES THE INSTRUMENT THAT REFUTES IT

`T246`'s **F-1 (HIGH)**, found while reviewing a *different* correction to the same document — the argument
for independent review in one sentence.

DEC-2 opens, under *"read this before any other sentence in this document"*, with **"NOTHING GRADES THIS
CONTEXT'S MONEY. NOTHING GRADES THIS CONTEXT AT ALL."** The harness grades **LEDGER 4 parity / 2
oracle-refusal / 21 money cells** on every run. Its fact 1 cites **`ls .softhouse/vectors/`** as evidence
that no ledger vector exists; the driver re-ran that exact command and it lists `ledger/` holding **six**
`LDG-*` files. **Seven sites** (L3, L7, L10, L815, L819, L825, L2437) plus a third live falsehood at **L87**
(*"until then A2-15 stays blocked"* — `A2-15` is `done`).

Cause: **P-69 at maximum blast radius.** Revision 5 was written **2h13m before** `A2-15` promoted the ledger
vectors, and DEC-2 had not been touched since. Every sentence was true when written.

**`T247` PREPARES revision 7 and must not land it.** It is told explicitly that the banner's **warning
function is legitimate and must survive in corrected form** — the graded domain really is narrow, and a
green ledger section really is not a cutover argument. **Correct what is false; do not delete the caution.**

> **⚠ A QUESTION THE NEXT FIRE MUST SETTLE BEFORE IT DISPATCHES TIER-A GO WORK.**
> `ready-tasks.py` now prints G-14 as an **OPEN CONTRACT gate** and infers *"no task may write Go under
> `nexus/` … until it closes."* **The driver believes that inference is over-broad here and did NOT act on
> it.** That rule was written for G-11, where the contract was **UNRATIFIED**. DEC-2 is **ratified** (rev 5,
> then rev 6); G-14 is a **stale-evidence correction to a ratified document**, and blocking all Go writes on
> a false banner would park Tier A over a sentence that changes no obligation. **This is ENGINEERING and the
> next fire may decide it** — but decide it explicitly and record the reasoning; do not let the resolver's
> default quietly park the tier. Filed as a note here rather than silently overridden.

# HEADLINE 3: THE DRIVER DROVE T243's NEW GUARD AND IT DID NOT FIRE — P-76

`T243` wired three unwired guards and reported **RED 13/0**. True, and **narrower than it reads**. The
driver planted a fail-open instrument (P-22) and **the harness stayed green**. Calibrating the probe (P-72)
got the linter to **name the file** — and `conformance.sh` **still exited 0**.

```sh
# COVERED — the reassuring echo is an ARM of the failing construct
( cd "$WT" && git grep ... ) || echo "   (no hits)"
# NOT COVERED — UNCONDITIONAL, on the next line
cd /tmp/T138-merge 2>/dev/null && git grep ... 
echo "   (searched the MERGED tree)"
```

**`r11-hygiene.sh` is flagged ZERO times** — the site `T239` measured live **this fire**, and the site the
driver relayed to `T238` **as the reason for widening the brief**. Of two known live sites the boundary
splits them one and one.

**`P-76` filed, and it is NOT `P-45`.** Every prior P-45 is a guard that ran *nowhere*. This one runs, is
reached, passes its own red drive, and is blind in part — **because `T243` planted the shape the rule was
written from.** A red drive built from the same example as the rule is a tautology with a transcript.
**Duty: drive every guard red on a shape you did NOT design the rule around, and when a task was widened
because of a specific site, that site is a MANDATORY red-drive case.** Filed as **`T248`**.

# HEADLINE 4: P-75 — `grep` AND `rg` IN AN AGENT SHELL ARE NOT THE PROGRAMS YOU THINK

Found by `T242`, sharpened by `T244`, all of it re-derived by the driver — which had circulated the **wrong**
version to four workers earlier in the same fire and corrected them **mid-flight**.

`~/.claude/shell-snapshots/…` defines `grep` and `rg` as **shell functions**:
- **`grep`** execs bundled **ugrep 7.5.0** with `-G --ignore-files --hidden -I` and **six** `--exclude-dir`
  flags silently prepended. Measured on a purpose-built fixture: bare `grep -r` finds **1 of 3** needles,
  `/usr/bin/grep` finds **3 of 3**. **33 % recall, exit 0, hits printed, nothing saying anything was skipped.**
- **`rg` DOES NOT EXIST IN A SCRIPT** — no binary in any of the 13 PATH dirs. `rg P F` exits **127**;
  **`rg P F | head` exits 0.** The pipeline swallows it, and `pattern | head` is the shape of nearly every
  sweep script. Under `set -euo pipefail` it correctly dies 127. `T244`'s own sweep was killed by this and
  **saved only by its fail-closed calibration**.
- **`git grep -E` is broken BOTH ways** — it misses true hits **and FABRICATES** (`bmainb` matches
  `\bmain\b`). All prior lore called it recall-only. So **"I got hits, so my rig works" is not a valid
  calibration.**
- **`git grep -P` is sound and available**, and was never recorded — the lore only ever said
  `/usr/bin/grep -P` does not exist.
- It **reconciles two contradictory measurements that were both right**: `T239`'s *"ugrep is not
  installed"* (true — no such binary) and RESUME's *"ugrep honours `\b`"* (also true — it is what `grep`
  runs). **The NAME and the PROGRAM had come apart**, which is what P-33 exists to prevent.

**Consequence:** RESUME's exoneration of `T224` (*"it ran under ugrep where `\b` works"*) is **`[UNVERIFIED]`**.

---

## Corrections made against the DRIVER this fire — SEVEN

1. **The oracle PIN FILE did not name the database every ledger vector came from.** `reference-oracle.md`
   omitted `fineract_gerege` entirely, and the two tenants are in **different time zones** — tenant 1
   `default` is **`Asia/Kolkata` (+05:30)**, which CLAUDE.md permits nowhere. Corrected; **`T245` filed to
   re-derive it, because the driver found it and fixed it in one fire.**
2. **Two PENDING task BARs pinned a DEAD vector-store digest** (`T226`, `T235`). A worker handed an
   unmeetable BAR either reports red on a green repo or **mutates the money corpus to satisfy a stale
   sentence**. Corrected to read the digest live. The 22 `done` tasks quoting it are stamped historical
   records and were deliberately left alone.
3. **`P-73` was a numbering HOLE with a live pointer into it**; `P-71`'s heading still asserted a rule two
   fires had falsified in opposite directions.
4. **The engine roster in four worker briefings was wrong** (ugrep). Corrected mid-flight, not at merge.
5. **The driver's own `FINDINGS.md` mislabelled its engine as "BSD grep"** when it was the shadowing ugrep
   function. Result stands; the label did not. **P-33.**
6. **The GATE REGISTER was DESYNCED**: `G-13` was asserted RAISED in `program.json`, `RESUME.md` and
   `DRIVER.STATE.json` while `gates.md` — the file the program calls authoritative — contained the string
   **zero** times. **P-73**, second instance.
7. **`files_hint` under-specified THREE TIMES IN TWO FIRES** (`T219`, `T242`, `T243`). Always the same
   shape: **the task TEXT and the `files_hint` are written to different scopes, and only the hint is
   machine-checked.** `T242`'s and `T243`'s overruns were both unavoidable and both correct.

## STANDING INSTRUCTIONS

- **P-75: never bare `grep`, never `rg`, in a committed instrument.** Use `/usr/bin/grep`, `git grep`, or
  `python3 re`. **`set -euo pipefail` in every script.** `type grep` before you trust `grep`.
- **Calibrate on a known POSITIVE and a known NEGATIVE** — `git grep -E` fabricates.
- **P-76: drive every guard red on a shape you did NOT design the rule around.** A widened task's
  motivating site is a **mandatory** red-drive case.
- **P-71: the fork point is UNPREDICTABLE — MEASURE it.** Four fires, three distinct values, no rule
  survives. It is `origin/main` **at worktree creation**, and `main` moves during a wave.
- **NEVER `git commit -m` a message containing a backtick — use a heredoc + `git commit -F`** (P-74).
  **Never amend a commit whose sha you have circulated.** Verify with `git merge-base --is-ancestor`.
- **Report the sha you MERGED, never the one you LOOKED AT.** `main` is not quiescent during a wave.
- **Before recording that anything DOES NOT EXIST, state where you looked AND your scope** (P-66/P-70).
- **Before certifying a ratio, count BOTH terms and say where you counted** (P-67).
- **Prefer ENUMERATION over pattern-matching where the population is small enough to read** — `T246`
  settled "is there a third site?" by reading all 15 occurrences, which is stronger than any sweep.
- **A measured claim has a shelf life shorter than a busy fire (P-69).** Stamp claims with the commit.
- **Oracle-down is exit 2 AND a probe line actually PRINTED AND reading `down`** — test **presence** first.
- **The Go module root is `nexus/`**; `. .softhouse/bin/go-env.sh`. Invoke the harness with **`bash`**
  (exit 3 = wrong interpreter). **Never `gofmt -w` `contract.go`** (G-3).

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first.** At exit: **0 in progress, 15 READY, 0 blocked, 0
unresolved edges, G-14 the only open contract gate** (read the boxed note under HEADLINE 2 before letting
it park Tier A).

1. **`T247` — PREPARE DEC-2 revision 7 for the false banner (G-14).** Do not land it. Preserve the caution.
2. **`T248` — the P-76 gap.** Characterise C1's real matching rule **before** widening C2 — probe 1's
   `/nonexistent/...` path was not detected at all while probe 2's `.claude/worktrees/…` was, so if C1 is
   anchored to known roots then widening C2 alone fixes nothing.
3. **`T245` — independent check of the driver's own `reference-oracle.md` correction.** Claim (5), that the
   ledger vectors were captured against tenant `gerege`, was **INFERRED by the driver, not measured**.
4. **`T226`** (`v3`, the third P-45) and **`T235`** — both hold `conformance.sh`, as does `T248`.
   **Serialise all three.** Their BARs were corrected this fire and now read the digest live.
5. **`T241`** (gates.md; `T229`'s `site3.py` formula false on PARTIAL), **`T236`**, **`T237`**.
6. Then `T145` (denominator **438**), `T160`, `T164`, `T174`, `T192`, `T195`, `A2-23`.

**Carried forward, unfixed, with scope stated:** `r11-hygiene.sh`, both `t184` scripts, `T234`'s own
re-runner and `A2-32-evidence/sweep.sh` are **pinned, not repaired** — `T243`'s framing stands, **the pin
is a FRONTIER, NOT AN AMNESTY**, and `sweep-ORIGINAL.sh` must stay on it **permanently** because it is a
**specimen, not an instrument**. Also: `gate_exemption_census`'s missing retraction, the capture-rig gap
behind the three FILE-NAME-ONLY citations, and a 262-instrument advisory tail with its denominator stated.

## What is NOT true, and must not be inferred from the green bar

**The ledger is graded on six captured cases and no more.** Accrual, account transfers (gl 17), charge-off,
multi-currency, opening balances, `GLClosure` and **slot resolution** are all ungraded — and since `T242`
the harness **prints all eight** not-graded rows, derived from the registry rather than hand-written.
**Two of the 46 loanschedule vectors have `principal_amortizes_to_zero` switched OFF**, legitimately and
loudly. **G-4, G-5, G-8, G-10, G-12 and G-14 remain OPEN**; G-4 and G-5 are hard `user` gates. **G-8's
region is a conservative superset only**, resting on the unproven conjecture `δ ≤ 1`, and **options (b)/(c)
must not be put to Buyan — unconditionally, with no expiry.** **Nothing was cut over, and nothing here
authorises it.** The gate register at the top of `gates.md` is authoritative.
