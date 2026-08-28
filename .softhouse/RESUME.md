# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-140005`, chain iteration 3 — **IN FLIGHT. SIX LIVE WORKERS.**

**If you are reading this and no driver session is running, six workers were killed mid-flight.**
Mark each `needs_retry` with the WIP evidence from its branch. `in_progress` never means "work is
happening"; it means "a driver said so, once".

### Why this iteration exists
Iteration 2 ended at ~10:35Z on a `five_hour` rate limit (`resetsAt=1787914200`), not on a stop
condition. The wrapper reconciled state at `cefd8f6c`. The limit had reset by the time this iteration
started (11:15Z), the tree was clean, `origin/main` tip was 47 s old, and **zero workers were live**.

### Pre-flight, measured — not assumed
| Check | Result |
|---|---|
| Lock arm taken | own fire (`20260828-140005`), wrapper-held |
| `origin/main` tip age | 0.01 h |
| `git status --porcelain` | empty |
| `bash .softhouse/conformance.sh` on `main` | **EXIT 0**, probe line **PRESENT** at line 162 reading `up` |
| loanschedule | parity **PASS 46 FAIL 0**, contract-refusal 4, inadmissible 0, 7,884 cells |
| ledger | parity **PASS 7 FAIL 0**, oracle-refusal 6, inadmissible 0, 142 cells (39 money) |
| 13 `ledger-wrong-*` drives | all **KILLED** |
| Pre-fire attestation snapshot | `/tmp/attest-before-iter3.json` (7-term, T318 shape) |

Reference oracle **REACHABLE**: `https://localhost:8443/fineract-provider/actuator/health`.
PostgreSQL up on `:5432`. No prohibited-engine port open.

## WAVE 1 — IN FLIGHT. Five workers. Grants are pairwise DISJOINT.

| Task | Branch | Model | Exclusive grant |
|---|---|---|---|
| `T382` review T374 | `softhouse/T382-review-t374` | opus | `.softhouse/reviews/t382-review-t374/` |
| `T375` T364's conditions on T358 | `softhouse/T375-t364-conditions` | opus | **`.softhouse/conformance.sh`**, `.softhouse/capture/t375-t364-conditions/` |
| `T383` F-T380-1 tail -1 fail-open | `softhouse/T383-t380-conditions` | opus | **`.softhouse/bin/fire-program.sh`**, `.softhouse/capture/t383-t380-conditions/` |
| `T381` T379's R2 anti-calibration | `softhouse/T381-t379-conditions` | opus | `.softhouse/capture/t363-oracle-baseline/instruments/`, `.softhouse/capture/t381-t379-conditions/` |
| `T360` divergence vector class | `softhouse/T360-divergence-class` | opus | `.softhouse/vectors/`, `.softhouse/capture/t360-divergence-class/`, `nexus/internal/apps/ledger/conformance/` |

`T375` is a **RESUME of a killed worker**, from its own 8-commit branch head `2422adc9` — not a restart,
and **not** a consumed retry: it was killed by a rate limit, not rejected.

### Plan gate, checked AT dispatch rather than after
Four of the five are `code` tasks, so check 1 needs a paired reviewer for each. **`T384` (reviews
T375), `T385` (T383), `T386` (T381), `T387` (T360) were filed in the SAME commit as the dispatch**,
before any worker spawned. Iteration 2 found three code tasks dispatched with no reviewer at all; this
closes that shape by construction rather than by inspection.

### Deliberately NOT dispatched, with reasons
- **`T372`** (install the PreToolUse push-before-spawn gate) — its own brief forbids dispatch while any
  worker is live, because it installs a `deny` hook on the **Agent** tool. Reserved for a wave with
  **zero** live workers. This is the only mechanism that would give the push-before-spawn obligation any
  mechanical backing; it currently has none (P-45).
- **`T366`** — the previous manifest records it as touching `conformance.sh`, which `T375` holds.
- **`T373`, `T378`** — blocked on `T370`, which is **parked** (rejected by `T376`, and already T351's one
  retry). `T378` is the landing task that unblocks them.

## Worker roster — READ THE ID BACK OFF THIS TABLE BEFORE SENDING A MESSAGE

A previous iteration misrouted two coordinator messages by typing the wrong id. Every worker in this wave
was instructed to **name its task in the first line of any message**, so a misroute is self-identifying to
whoever receives it.

| Task | Agent id | Role | State |
|---|---|---|---|
| `T382` review T374 | `a5c55c8ed65c59f4b` | reviewer | running |
| `T375` registration-guard fail-opens | `abfb64ef9a5d23f1a` | code (RESUME of a killed worker) | running |
| `T383` fire-wrapper `tail -1` fail-open | `af72b6ec837e41331` | code | running |
| `T381` anti-calibration fail-open | `aab1c4d016f417758` | code | running |
| `T360` divergence vector class | `ad3a06a761a0fd26d` | code | **done** @ `d6979763` |
| `T387` review T360 | `a33a413de77ef1024` | reviewer | running |
| `T388` FIRST accrual capture | `a8fa18aedf7a9db13` | test_writer (ORACLE-ONLY) | **done** @ `977e37af` |
| `T389` review T388 | `a049874f964182c77` | reviewer | running |

## WAVE 1b — `T388`, dispatched second, under the G-20 decision

`G-20` was raised this iteration and says: **a port-or-capture task goes out before any further harness
repair.** `T388` is that task, dispatched in the same fire that raised the gate rather than recommended for
the next one. It took the **first accrual observations in this program**.

**TENSE MATTERS HERE AND THIS DRIVER GOT IT WRONG ONCE.** At `T388`'s DISPATCH, `ledger.accrual.entry` was
ENTIRELY UNGRADED and **not one journal entry in this tenant had ever arrived through a RECEIVABLE slot**.
`T388` made that false an hour later, which was its purpose. The sentence sat here in the PRESENT tense
until `T389` caught it — a falsehood written by the driver, in the manifest, *after* dispatching the task
that would falsify it. Not `T388`'s defect. Recorded rather than quietly fixed, because it is the same
correct-conclusion / stale-support shape as `G-21`.

`T388`'s grant is `.softhouse/capture/t388-accrual-capture/` **only**: raw observed capture, **no promotion**,
because `T360` holds `.softhouse/vectors/` this wave. Promotion is a separate follow-on. Its paired reviewer
`T389` was filed in the same commit as its dispatch.

### `T388` RESULT — the first accrual observations in this program

**9 journal entries through 3 receivable slots**: 3 x `INTEREST_RECEIVABLE` (slot 7, gl 41), 3 x
`FEES_RECEIVABLE` (slot 8, gl 42), 3 x `PENALTIES_RECEIVABLE` (slot 9, gl 43) -- JEs 78/81/83, 84/87/89,
90/93/95, all DEBIT, all MNT, all non-manual. The bar's every-run assertion *"NOT ONE JOURNAL ENTRY IN THIS
TENANT ARRIVED THROUGH A RECEIVABLE SLOT"* **is now false**, which was the point.

**P0 HELD -- no promoted GL account moved.** T388 did not trust the forbidden set the driver gave it: it
DERIVED the set from all 67 store files and found **two members the brief had missed** -- gl 22 (from
`capabilities-ledger.json`'s `unposted_slots`) and gl 15 (a `contra_gl_account_id`) -- then red-drove its own
disjointness checker. Bar exit 0 with the probe line PRINTED; ledger 7/6/0/142/39 and loanschedule 46/7884
unmoved; dead-path pin 109 unmoved. Created 13 GL accounts (35-47), `ACCRUAL_PERIODIC` product 63, client 3,
loan 8; accrual fired via `POST /runaccruals tillDate 15 April 2026`, and T388 states plainly that this is
the same method job 16 calls and therefore **not** evidence about the scheduler. **AWAITING `T389`.**

### A FINDING THE DRIVER MEASURED WHILE TRIAGING T388 -- P-45, the fourth live instance

**`oracle-state-baseline.sh` is invoked by NOTHING THAT RUNS.** Its only references outside its own directory
are inside `t367-review-t363`'s own drives, and T367 asked the question explicitly (*"X9 is
oracle-state-baseline.sh referenced by anything that RUNS?"*). **The instrument built to detect unattributed
oracle-state movement would not have fired had T388 contaminated a promoted account.** It is not T388's
defect and T389 was told not to reject on it -- but it is why T389 owes this capture more independent
verification than usual: the automated safety net was not armed. Filed as `T390` item 3, beside the still-
pending `T311`, `T303`, `T313` and `T333`, which are all the same shape.

**`T388` moved shared oracle state permanently and knew it.** It was told to take the expensive route T352
named as correct — a NEW `ACCRUAL_PERIODIC` product on CLEAN GL accounts — because the cheap route (a loan on
product 28) posts into **gl 16, a promoted leg of LDG-01/02/03**, through a mapping A2-314/403 hold
inadmissible. Its P0 acceptance test was that **no promoted GL account moved**, and `T389` is re-deriving that against
the live database rather than reading T388's notes -- including deriving the forbidden set independently,
because T388 already found two members the driver's own brief had missed.

`T390` (append `PROBES.tsv`, correct `CASUALTIES.md:40,44` whose `m_loan` claim T388 made half false, and
wire the unwired baseline) and `T391` (promote the observations, and rewrite the four sentences in
`capabilities-ledger.json` the harness now prints falsely every run) are FILED and sequenced behind their
holders.

### `T360` RESULT — and it refused its own reviewer's measured remedy

T360 concluded **(c) BOTH** and then **declined the one change T359 had measured for it**. T359's remedy was
`impl.go:276-279` returning `(*Refusal, nil)` instead of a Go `error`. T360's objections: that return produces
a **fabricated HTTP 422** no oracle, port or wire ever produced, and it changes the meaning of the return for
**every** class — a residue arriving on a *parity* vector would grade as "the port refused" when the truth is
a broken corpus. It routed in `gradeOne` on the class instead, and gave `PortRefusal` **no HTTP status field
at all**. `T387` was dispatched to **adjudicate that specific disagreement from source**, not to prefer either
side. A worker refusing a reviewer's specific remedy, with a reason, is the pipeline working.

**The money constraint was the hard part and it held.** Money cells are **ABSENT, not empty** — `admit`
refuses `expect.legs`, `total_*_minor`, `expect.refusal` and `expect.http_status` on the new class — so no
author is ever put in T352's position of inventing `10013` for a value no `int64` can hold. The oracle's
`100.125` is **characters**, byte-checked verbatim on both sides, with representability decided by a pure byte
scan of the fraction digits: no `strconv`, no arithmetic, no exponent. **The amount is never a number in this
program.**

`LDG-DIV-01` is built from T352's committed capture, re-read live read-only this fire and byte-identical.
T360 posted nothing and moved no oracle state. The 14th wrong implementation is KILLED and load-bearing
**measured both ways**. ledger parity 7/6 and 39 money cells **unmoved**; cells 142 → 144; divergence
**PASS 1 FAIL 0**.

### ⚠ SECOND MERGE HAZARD — `T360` CANNOT MERGE BEFORE `T375`

`T360` needs `EXEMPTION_PIN_LEDGER_WRONGIMPLS` **13 → 14** at `.softhouse/conformance.sh:3923` — a file
`T375` holds, so T360 correctly did not touch it and filed
`.softhouse/capture/t360-divergence-class/CONFORMANCE-SH-PATCH-REQUEST.md` instead.

**Its branch is `exit 2` and that is CORRECT.** The probe line is **PRINTED** and reads `up`, and the sole
refusal is `WRONG-IMPLEMENTATION POPULATION 14, PINNED 13`. Under **P-84** that is **the pin working** — not
an oracle outage, not a corpus defect. **Do not park anything over it.** The driver applies the one integer
on the **merge result** after `T375` lands (P-83).

## MERGE HAZARD carried forward from iteration 2 — read before merging anything
`T374` ships the dead-path pin at **108**; `main` is at **109**; `T375` is at **109**.
**Re-run `.softhouse/capture/t326-frontier-host-state/instruments/10-regen-pin.py` ON THE MERGE RESULT.
Never pick a side between two pins** (P-83: two independent movements of one pinned number reconcile by
running, never by arithmetic).

`T360` may move the parity counts. If it does, the summary and **every pinned census that restates them**
move in ONE commit, and the bar is re-run on the merge result.

## UNMERGED AND COMPLETE ON BRANCHES
| Task | Branch | Head | Waiting on |
|---|---|---|---|
| `T374` | `softhouse/T374-t362-conditions` | `f4157d42` | `T382` (dispatched) |
| `T376` | `softhouse/T376-review-t370` | `9255d1af` | nothing — it is a review, verdict **REJECTED** |
| `T370` | `softhouse/T370-t351-retry` | `4925bbef` | **parked**; substance verified good, lands via `T378` |
| `T351` | `softhouse/T351-progress-accounting` | `a0139c5d` | superseded by `T370`/`T378` |
| `T369` | `softhouse/T369-review-t351` | `e10e3f07` | `T373` |

## THE PROGRAM-LEVEL FACT THIS DRIVER IS SURFACING TO BUYAN
`T352` found it and it is still true, measured again this iteration: **the READY queue contains 31 tasks
and not one of them ports Fineract code.** Every one repairs the harness. Program progress stands at
**1 of 17 contexts done, 182 LOC of ~544,000**. The harness work is not waste — the bar has caught a
false PASS in nearly every fire — but a driver that only ever dispatches harness repair will never
finish the migration. Raised as `G-20` in `.softhouse/gates.md`; it blocks nothing and needs no answer
to keep working.

## Open gates
`G-19` (oracle accepts a sub-minor-unit residue the port refuses) — OPEN for Buyan, blocks nothing.
`G-20` (the READY queue has no porting work in it) — OPEN for Buyan, blocks nothing.

## Pause reason
**Not paused.** Six workers dispatched and being awaited by chain iteration 3.
