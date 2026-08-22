# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260822-140002`, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A slice **A2**.
- **FIVE DISPATCHED, FIVE COMPLETED, FIVE MERGED, ZERO LIVE AT EXIT.** Every branch scope-checked by the
  driver on the **three-dot** diff before merge; the BAR re-run by the driver on the **merge result** after
  every merge, **never quoted from a worker**.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL 18.3 only. No prohibited engine.

**Driver-verified on merged `main` at exit:**

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0)
  loanschedule  46 parity · 7884 graded cells
  LEDGER         4 parity · 2 oracle-refusal · 21 money cells
  refused 0 · inadmissible 0 · harness errors 0 · invariant violations 0 · 0 NOT RUN
  all 9 census pins == pinned
  fail-open frontier  10 == pinned 10      (moved 9 -> 10 by T248)
  vector store  13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d   UNMOVED ALL FIRE
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**The store digest did not move this fire.** No task touched the money corpus. Any BAR pinning
`8968c559…` or `73c3ea7b…` is still stale; `13b8342e…` is current. **Read it live** —
`git rev-parse HEAD:.softhouse/vectors` (P-61: the git tree hash IS the canonical recipe).

---

# HEADLINE 1: THE DRIVER DECIDED A GATE'S SCOPE, FIXED THE INSTRUMENT THAT DISAGREED — AND SHIPPED A FAIL-OPEN DOING IT

The previous fire left a boxed note refusing to act on `ready-tasks.py`'s printed inference that G-14
forbids all Go under `nexus/`, and asked the next fire to settle it explicitly. **Settled, and the suspicion
was justified.**

That sentence was **hardcoded** and printed for *every* open CONTRACT gate, reading **no per-gate field** —
so it could not have been about G-14 at all. It encodes **G-11**, where DEC-2 was UNRATIFIED and its
*shape* was under negotiation. G-14 is a stale-evidence correction to a **ratified** document and moves no
obligation, field, rounding rule or graded cell. `gates.md`'s authoritative register had said *"Blocks
nothing today"* from the moment G-14 was raised. **The machine copy and the authoritative copy disagreed,
and the machine one was wrong.** Filed as **`P-77`**.

**Then the driver's own fix was FAIL-OPEN, and `T249` — the reviewer the driver filed against itself —
caught it.** The patch read `str(g.get("blocks", "")).strip()`, so the **five most likely encodings of "no
value"** (`None`, `False`, `0`, `[]`, `{}`) all stringify **truthy** and printed under
`=> SCOPE RECORDED ON THIS GATE`. A gate with `blocks: null` rendered as *"SCOPE RECORDED … None"*, **which
reads as "nothing is blocked."** **The pre-patch code was fail-CLOSED; the patch made it fail-OPEN** — a
fresh **P-45** instance created *in the very commit that filed P-77 about unenforced permission surfaces*.
Fixed at `925fdfc`, red-driven nine ways.

`T249` also found the **selector** failed open independently: `g.get("class") == "CONTRACT"` **silently
drops any gate with no `class` key** — and **`G-13` is exactly that shape** [VERIFIED at HEAD:
`class=None`]. An unclassified OPEN gate would have been invisible to the section that exists to catch it.

**`T249` CONFIRMED the DECISION itself correct**, by a route the driver never stated: **the banner errs
PESSIMISTICALLY.** It says nothing is graded when 4 ledger parity + 2 oracle-refusal + 21 money cells are —
**no direction of that error licenses Go that a corrected banner would forbid.** The harm is *epistemic*,
not *normative*; the remedy is a briefing, not a prohibition. It explicitly did **not** find the driver
rationalised past a gate.

# HEADLINE 2: ONE STALE-EVIDENCE SHAPE, THREE INSTANCES, ALL IN THE GATE REGISTER, ALL FOUND THIS FIRE

**P-69 is not an incident, it is the register's default failure mode.** Every one was true when written.

| Site | Found by | State |
|---|---|---|
| DEC-2's opening banner (G-14) | `T246`, last fire | rev 7 **PREPARED** by `T247`; **awaiting `T251`** |
| `G-12`'s `blocks` field | `T249` | **ground corrected** this fire, obligation untouched |
| `gates.md:98`, inside **G-11's own ratification block** | `T247` (FU-T247-2) | **corrected** at `cb337d7` |

`G-12` had read *"No ledger vector exists yet (G-11), so no vector grades the column."* Six exist. The
conclusion survives by a **stronger** route: the gate blocks nothing because **no vector grades the
running-balance COLUMNS**, not because nothing grades the ledger. `gates.md:98` was **struck through, not
deleted** — it was true when written and that record is the evidence for how this happens.

# HEADLINE 3: T245 — THE DRIVER FIXED THE INVENTORY AND LEFT THE INSTRUCTION (HIGH)

The pin file's **"Connection facts for vector capture"** table still prescribed **`tenantIdentifier=default`
and `psql -d fineract_default`** — about **sixty lines below** the warning describing exactly that hazard,
in the same file, unchanged by the same commit. Of **5,129** tracked files, **10** carry a copyable
`default` instruction, **9 are deliberate negative controls**, and **the pin file was the only prescriptive
one.** Fixed by `T245`; both tenant selection forms verified HTTP 200 live.

**Claim (5) — the one the driver INFERRED — is now MEASURED three ways, and the decisive leg trusts no
document:** every entity the six ledger vectors name exists in `fineract_gerege` and is **absent** from
`fineract_default`, which holds **0 GL accounts, 0 journal entries, 0 loans**. **No HIGH finding of a vector
captured against the `Asia/Kolkata` tenant.** Claim (1) was **overstated**; claim (4) was true at `c0be92b`
(74/71) and **already stale** at `9b6c596` (88/78).

# HEADLINE 4: T248 — THE GUARD WAS BLIND IN ITS SELECTOR, NOT ITS CONDITIONS

Sent to widen a guard's *conditions*, `T248` measured first and found the defect one level up:
**`RE_REPOWIDE`, the corpus SELECTOR, was itself blind.** Shape **R4 satisfied BOTH conditions and was never
inspected**, because the selector never put it in front of them.

C1's real rule was a **four-root allow-list** (`/Users`, `/home`, `/opt`, `/var`) — `/tmp`, `/nonexistent`,
`/srv`, `/data`, `/mnt`, `/private`, `/scratch` all invisible. The driver's hypothesis about
`r11-hygiene.sh` was right, but **the precise version mattered: widening C2 alone would have put r11 on the
frontier at TIER 2, whose printed meaning is "corpus reachable today" — a FALSE claim about a directory gone
for days.** The fix would have *created* a false claim while closing a true one.

Widening **proved STRICTLY ADDITIVE** (20 → 22 detections, **LOST = none**). Frontier **9 → 10**, the new row
**NEWLY VISIBLE, not newly introduced**. **THREE of the five red-drive shapes CHANGED THE RULE when first
driven** — that, not the transcript, is what makes it P-76 rather than a re-enactment. **P-76 addendum
adopted**: *a rule's blind spots live in its POPULATION SELECTOR as much as in its conditions.*

# HEADLINE 5: T247 PREPARED REV 7, LANDED NOTHING, AND FOUND 26 SITES BEYOND T246's 8

Verified by the driver on the three-dot diff: `docs/adr/`, `gates.md`, `program.json`, `vectors/`,
`PIN-ledger.json`, `nexus/`, `conformance.sh` — **touched zero times.**

Worst misses: **L820**, the row directly beneath a named site reading only *"NO. Same reason."*, carrying
**no keyword any wording-sweep could hit**; and **§8.1 at L2345-2409**, restating all four banner facts in
full **2,300 lines below**, where §8 tells a ratifier to read **last**. **Two live banner falsehoods nobody
had named:** L76 (*ratification "would buy no grading whatsoever"* — DEC-2 **is** ratified), and fact 3's
**ordinal** (*"seven guards … the seventh"* — it is **eight**, and the guard is **sixth**, since `T243`
wired one after `A2-28`'s stamp). **An ordinal used as an identifier goes wrong silently.**

It **refused to certify §5.3's adequacy** after measuring it, and reported **P-5 is named nowhere in the
ledger package**. The caution survives **with a denominator**: 6 of 14 declared capabilities graded, 8
declared out by name — **both terms counted**.

---

## Corrections made against the DRIVER this fire — FIVE

1. **The driver's `ready-tasks.py` patch was FAIL-OPEN** (`T249`). Pre-patch was fail-CLOSED. The driver
   made a guard worse while fixing it, in the commit that filed the pattern about exactly this.
2. **The driver's `reference-oracle.md` correction fixed the inventory and left the instruction** (`T245`,
   HIGH). The only prescriptive wrong-tenant instruction in 5,129 files was in the pin file itself.
3. **Two of the driver's own verification probes were BROKEN** (`P-72`), each producing a false reading it
   nearly acted on: grepping `SCOPE RECORDED` also matched the fallback **`NO SCOPE RECORDED`** as a
   substring, reporting every arm permissive; and lowercase `` no `class` KEY `` missed uppercase output,
   reporting a working guard as vacuous. **Both were the probe, not the code.**
4. **The driver's `:125` citation was unstamped** — true at `9b6c596^`, but a reader at HEAD finds different
   code there. Stamped in both `patterns.md` and `gates.md`.
5. **`gates.md` said G-14 blocks "NOTHING" flat at two sites** while the decision names a real residual
   DEC-2 prohibition — permissive in the wrong direction. Both corrected.

## STANDING INSTRUCTIONS

- **P-75: never bare `grep`, never `rg`, in a committed instrument.** `grep` is bundled **ugrep 7.5.0** with
  six `--exclude-dir` flags silently prepended (**33 % recall** measured); **`rg` has no binary** and
  `rg P F | head` exits **0**; **`git grep -E` misses AND fabricates** (`bmainb` matches `\bmain\b`).
  Use `/usr/bin/grep`, `git grep -P` (sound, available), or `python3 re`. `set -euo pipefail` everywhere.
- **Calibrate on a known POSITIVE and a known NEGATIVE — and make the probe DISCRIMINATE.** A negative
  string that is a **substring** of the positive one matches both. This bit the driver twice in one fire.
- **P-76: drive every guard red on a shape you did NOT design the rule around — and on a TYPE you did not
  either.** The driver drove both its arms as *strings*; the defect was in the *types*.
- **P-76 addendum: check your SELECTOR before you trust your CONDITIONS.**
- **P-77: a gate's scope belongs to the gate, not its class.** Record it in
  `program.json gates_pending[].blocks`. A tool that answers a question the authoritative record already
  answers is a **second source of truth**.
- **P-69 is the register's default failure mode. STAMP every measured claim with its commit**, and
  re-measure when you finish — `main` moved **four merges** under `T247` alone.
- **P-71: the fork point is UNPREDICTABLE — MEASURE it.** `T249` reported P-77 "exists nowhere" — **true at
  its fork, stale against main.** Not an error; read fork points before calling a finding a miss.
- **P-67: count BOTH terms.** **P-66/P-70: state where you looked before recording a non-existence.**
- **NEVER `git commit -m` with a backtick — heredoc + `git commit -F`** (P-74). **Report the sha you
  MERGED, not the one you looked at.**
- **Prefer ENUMERATION over sweeping** where the population is readable.
- **The Go module root is `nexus/`**; `. .softhouse/bin/go-env.sh`. Invoke the harness with **`bash`**
  (exit 3 = wrong interpreter). **Never `gofmt -w` `contract.go`** (G-3).

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first.** At exit: **0 in progress, 14 READY, 0 blocked, 0
unresolved edges, G-14 the only open contract gate — and it now carries its OWN recorded scope**, so the
resolver no longer asserts a blanket prohibition it never measured.

1. **`T251` — INDEPENDENT review of DEC-2 revision 7.** **Highest value in the queue**: the last thing
   between G-14 and closure. `T247` prepared it and landed nothing; **the driver has committed not to
   ratify without this review.** T251 may not land it either.
2. **`T252`** — `T248`'s two unfixed findings: a probable **third live fail-open site whose false claims are
   printed COUNTS, not sentences** (so no reassurance vocabulary reaches it), and **TIER 3's label asserting
   "fails closed" while the classifier verifies that for no file** — P-45 at the taxonomy level.
3. **`T250`** — `T245`'s F-2: `cap.sh`/`cap8.sh`/`cap9.sh` send `-H "$T"` but write the sidecar's tenant
   line as a **hard-coded literal**. A sidecar that cannot disagree with its run is decoration, not
   evidence. **Do not retro-edit historical sidecars.**
4. **SERIALISE `T226`, `T235`, `T250`, `T252`** — all hold `conformance.sh` or the capture lib.
5. **`T241`** (gates.md), **`T236`**, then `T145` (denominator **438**), `T160`, `T164`, `T174`, `T192`,
   `T195`, `A2-23`.

**Carried forward, unfixed, with scope stated:** `r11-hygiene.sh` is now **on the frontier at TIER 1** but
**still not repaired** — `T243`'s framing stands and **the pin is a FRONTIER, NOT AN AMNESTY**;
`sweep-ORIGINAL.sh` stays on it **permanently** because it is a **specimen, not an instrument**. Also: both
`t184` scripts, `T234`'s re-runner, `A2-32-evidence/sweep.sh`, `gate_exemption_census`'s missing retraction,
the capture-rig gap behind the three FILE-NAME-ONLY citations, and `a2-31`/`t185` instruments that hardcode
dead worktree paths and cannot rerun without a source edit. **DEC-2 still calls itself "DRAFT (revision 5),
NOT RATIFIED" while being a ratified revision 6** — revision 6 landed with no §10 entry and no status-block
update; rev 7 addresses it, pending `T251`.

## What is NOT true, and must not be inferred from the green bar

**The ledger is graded on six captured cases and no more.** Accrual, account transfers (gl 17), charge-off,
multi-currency, opening balances, `GLClosure` and **slot resolution** are all ungraded — the harness prints
all eight not-graded rows from the registry. **Two of the 46 loanschedule vectors have
`principal_amortizes_to_zero` switched OFF**, legitimately and loudly. **G-4, G-5, G-8, G-10, G-12 and G-14
remain OPEN**; **G-4 and G-5 are hard `user` gates**. **G-8's region is a conservative superset only**,
resting on the unproven conjecture `δ ≤ 1`, and **options (b)/(c) must not be put to Buyan — unconditionally,
with no expiry.** **Nothing was cut over, and nothing here authorises it.** The gate register at the top of
`gates.md` is authoritative.
