# RESUME manifest — gerege-nbfi Fineract→Go migration

## ⚠ IN FLIGHT — local fire `20260823-080004` HAS FIVE LIVE WORKERS AS OF THIS COMMIT

**Do not read this HEAD as a closed fire.** Written and pushed BEFORE the first worker was spawned (P-85).

| task | role | branch | what |
|---|---|---|---|
| T287 | test_writer | softhouse/t287-* | **ORACLE-ONLY, NEW** — the two closure/opening-balance refusals the registry calls CHEAP and records nobody has taken |
| T285 | reviewer | softhouse/t285-* | independent review of T273 (the `/tmp` residue guard, +222 lines into the file that grades everything) |
| T283 | reviewer | softhouse/t283-* | independent review of T274's attestation root repair — forge a sidecar the re-derivation accepts |
| T286 | coder | softhouse/t286-* | T268 RETRY — repair the fail-open T281 measured *inside T268's own fix* |
| T271 | coder | softhouse/t271-* | B-1 in `t219-g8-residual`; blocks T269 on a MEASURED red bar |

**Lock**: held by this fire (`pid 93922`), taken by the wrapper. Freshness read via push-recency on
`origin/main`, per STEP 0 — `started_at` is not a freshness signal (P-85).

**Oracle**: REACHABLE, `https://localhost:8443`. Bar re-run by the driver at fire open, before any dispatch:
**PASS exit 0, probe line PRESENT and reads `up`, 46 parity vectors / 7884 cells.** `/tmp/t234_matrix2.txt`
is present (mtime 22 Aug 22:50) and this host has **5 days 13 h uptime**, so that green is still resting on
the residue T273 exists to remove — it has not yet been tested by a reboot.

---

# HEADLINE 1: THE 14:00 FIRE EXITED WITH FOUR LIVE WORKERS, AND THE 23:00 FIRE DID NOT NOTICE

**The single most important fact for reading this repo's recent history.** Fire `20260822-140002` dispatched
`T271`, `T283`, `T285`, `T286` and then **ended its turn**, killing all four (STEP 5.5: *"NEVER exit with live
workers — they die with you"*). It left them `in_progress` in `tasks.json`, which told every later reader that
work was happening when nothing was.

Fire `20260822-230001` then opened and released the lock **with zero commits between them** — a whole
oracle-reaching window spent on nothing, and the stale claim went uncorrected for a second time.

**So `RESUME.md` described fire `20260822-060013b` while four fires' worth of history sat on `main` above it.**
This is `P-69` (*acting on a stale measurement*) at manifest scale, and it is the second time the exit protocol
has been the thing that failed rather than the work.

**Corrected this fire:** all four are `needs_retry` with their rescue branch named in the note, per STEP 5.4
(*"A task whose worker you killed is not `in_progress`"*). **WIP was NOT lost** — the wrapper's sweep caught
six `softhouse/rescued-agent-*-20260822-140002` branches, and they are substantial:

| rescued branch | task | size |
|---|---|---|
| `a4668dbf` | T286 | 6,639 insertions / 58 files (incl. `t281-review-t268` probe fixtures) |
| `ad426472` | T285 | 8,100 insertions / 40 files (incl. `80-host-state-bracket.py`, "the hazard is a RACE, not a reboot") |
| `a157842e` | T273 base | 7,514 insertions / 42 files |
| `a2dfa827` | T268 base | 4,047 insertions / 34 files |
| `a533818f` | T271 | 1,992 insertions / 22 files |
| `af19d6f1` | T283 | 303 insertions / 2 files — **thin; this one barely started** |

**Completeness is UNVERIFIED for every one of them.** A rescue branch is where a worker happened to be standing
when it died, not a handoff it chose to write. Each re-dispatch this fire is told to treat its own rescued WIP
as *evidence*, never as *a conclusion*.

# HEADLINE 2: THE ORACLE WINDOW IS BEING SPENT ON CAPTURE AGAIN — `T287`

The queue is **20 READY tasks and every one is harness self-repair.** That is the same signal that raised
`T275` last fire, and `T275` merged and was worth it (it **refuted** CAPTURE-PLAN §5's own framing: the
oracle reconciles mappings **by key**, it does not delete-then-recreate).

The ledger corpus is still **6 vectors / 21 money cells** against loanschedule's **46 / 7884**, with **8 of 14
declared capabilities out of the graded domain.** The driver read all eight rows and picked the one that
**names its own capture and says nobody took it**:

> `ledger.opening.balance.and.closure` — *"validateBusinessRulesForJournalEntries refuses both shapes
> [VERIFIED: …:626-640] and NEITHER refusal is observed. **Both are CHEAP captures and both belong in a refusal
> vector; nobody has taken them.**"*

`T287` takes them. **Arm 1** (future-dated entry) has zero side effects — a refused write writes nothing — and
is committed before arm 2 is touched. **Arm 2** (entry before the latest `GLClosure`) needs a closure to
*exist*, and creating one is a **tenant-wide, hard-to-reverse mutation**: after a closure at date D, every
future capture that back-dates at or before D is refused *forever*, and the existing 46-vector corpus lives in
this tenant. So arm 2 must **measure the blast radius in SQL first** and is explicitly permitted — and graded
as a success — to **decline on the record**. Refusing an unsafe mutation of the reference oracle is the right
answer, not a failed task.

Why the other seven were not chosen: accrual needs a new product **plus** a job run; charge-off is unmapped on
both admissible products; gl 17's accounting path needs account transfers; multi-currency has no observation to
take; slot resolution needs a **contract-shaped** request naming one slot (forbidden as capture work);
running balance is **permanently refused while G-12 is open**.

# HEADLINE 3: WHAT THE FIVE WORKERS UNBLOCK

`T269` — wire all four unwired artefacts — is the drain everything runs into, and it is blocked on
**`T268` (via `T286`)**, **`T274` (via `T283`)** and **`T271`**. All three are dispatched this fire. `T285`
closes the last HIGH defect (`T273`, the `/tmp` residue, four independent confirmations).

**`P-89` still governs the lot: three artefacts have already shipped wired to nothing, each inside an artefact
written to remove `P-45`.** `T262`'s sentence is the standing test — **"PROSE DOES NOT FIRE ON THE NEXT FIRE."**

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first**, and **check `git branch --list 'softhouse/rescued-*'`**
before concluding any work was lost.

1. Merge/adjudicate whatever the five workers above landed. Their branches are the record; `tasks.json` notes
   say what each was told.
2. **`T269`** once `T286`/`T283`/`T271` clear — wiring a liar is worse than leaving it unwired.
3. **Promote `T287`'s raw captures into refusal vectors** — a separate task by design, because `conformance.sh`
   was contended this fire. This is how the ledger corpus finally grows past 6.
4. Then `T270`, `T272`, `T277`, `T279`, `T282`, `T256`, `T257`, `T258`, `T226`, `T235`, `T145`, `T160`, `T174`,
   `T192`, `T195`, `T266`, `T267`.

**CONTENTION MAP** — `conformance.sh` → T273/T285, T257, T258, T226, T235, T160, T192, T195, T266, T267, T269.
`capture/lib/` → T274/T283, T195. `capture/tierA-a2/` → T270, T174. `.softhouse/capture/` (whole) → T145.

## What is NOT true, and must not be inferred from the green bar

**The ledger is graded on six captured cases and no more.** Accrual, account transfers (gl 17), charge-off,
multi-currency, opening balances/`GLClosure` and **slot resolution** are all **ungraded**, and the harness
prints all eight rows from the registry every run. **Two of the 46 loanschedule vectors have
`principal_amortizes_to_zero` switched OFF**, legitimately and loudly. **`G-4`, `G-5`, `G-8`, `G-10`, `G-12`
remain OPEN; `G-4` and `G-5` are hard `user` gates.** **`G-8`'s region is a conservative superset only**,
resting on the unproven conjecture `δ ≤ 1`, and **options (b)/(c) must not be put to Buyan — unconditionally,
with no expiry.** **Nothing was cut over, and nothing here authorises it.** The gate register at the top of
`gates.md` is authoritative.

## Cite the rule, or the id AND its sentence — never the id alone (P-86)

The previous manifest's pattern-id block was off by one for `P-78`…`P-83` and propagated into ten worker
prompts. **Materiality was LOW for one reason: every prompt wrote the FULL RULE TEXT beside the id**, so the
number was decoration and the sentence carried the instruction. Keep doing that.
