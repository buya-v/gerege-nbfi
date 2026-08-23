# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260824-000016` — **IN FLIGHT.** Written BEFORE the first worker was spawned (P-85).

If you are reading this and no fire is running, the holder died. Every task listed below as `dispatched`
is **`needs_retry`, not `in_progress`** — a killed worker is dead, not paused. Check
`git branch --list 'softhouse/*'` for rescued WIP before re-dispatching anything.

### Baseline measured at fire open, by the driver, first-hand

```
bash .softhouse/conformance.sh  ->  PASS exit 0
                                    probe line PRESENT, reads `up`
                                    46 parity vectors / 7884 cells
                                    LEDGER: 4 parity + 2 oracle-refusal, 21 money cells, 6 wrong impls killed
```

Oracle REACHABLE (https://localhost:8443), PostgreSQL up on 5432, pinned Fineract `426a23544`.
`ready-tasks.py`: **0 in progress, 0 live workers, 23 READY, 0 edges resolving nowhere, 0 open contract gates.**

### What this fire is spending itself on, and why

The oracle is up, so the fire is weighted to **work only an oracle-reaching fire can do**. The ledger corpus
has been frozen at **6 vectors / 21 money cells** for many fires while the registry itself prints rows saying
the captures are cheap and untaken. `T287` finally took two and `T289` found **all four probes in that rig
ARMED** — so promotion is now a delicate job, not a clerical one, and it is this fire's headline.

### Dispatched this fire

| task | role | what it is |
|---|---|---|
| `T294` | test_writer | **ORACLE-ONLY.** Take the `:810-816` opening-balance refusal T289 named as the cheapest untaken capture — no mutation, no clock — **and promote it** in the same task. |
| `T292` | coder | R-VPA retry, **fourth in the lineage**. A sixth shape-patch will be rejected; find a fail-closed-by-construction formulation or a measured argument that none exists. |
| `T293` | reviewer | Adjudicate the driver's **unreviewed** census-pin decision from the last fire. Filed to be second-guessed. |
| `T284` | coder | T274 broke three FROZEN verify call sites; nobody owns the repair. |
| `T288` | coder | The wrapper **detects** the exit-protocol violation and does nothing about it. |
| `T256` | coder | The Mac toolchain path is hardcoded in 30 instruments and `reference-oracle.md` **prescribes** it. |

Filed but **NOT dispatched in wave 1**, by dependency:
`T295` (adjudicate/promote T287's four armed captures — depends on T294),
`T296` (independent review of T294), `T297` (independent review of T295).

### FILE PARTITION declared by the driver, because two in-flight tasks share `conformance.sh`

- `T294` owns `EXEMPTION_PIN_LEDGER_*` (:524, :551-553) and `EXEMPTION_PIN_LEDGER_WRONGIMPLS` (:2062).
- `T293` owns `HOSTSTATE_PIN_TEMP_ASSIGN_LIST` and its reasoning comment.
- Neither reflows, reformats or re-sorts anything else in that file.

### THE STANDING HAZARD ANY FIRE MUST READ BEFORE TOUCHING THE T287 RIG

All four probes in `.softhouse/capture/t287-closure-refusals/req/` are **valid, balanced, postable journal
entries**. Only an oracle-side precondition refuses them, and **when it lapses the request becomes a write —
and a posted journal entry cannot be deleted.**

| probe | date | armed |
|---|---|---|
| `a2-01` / `a2-02` | 2026-01-31 / 2026-01-15 | **NOW** — T287 deleted the closure that refused them |
| `a1-02` | **2026-08-24** | **tomorrow** |
| `a1-01` | 2026-12-31 | 2027-01-01 |

`guard-probe-expiry.sh` is merged and driver-verified RED (exit 1). Run it. Do not fire these probes.

### Carried forward, unchanged, from fire `20260823-080004`

- `T269` **MUST NOT BE WIRED** until `F-T290-1b`'s floor on `disagreements` exists — the invisible route to
  green (P-88) is open under **both** the live rule and T286's rewrite.
- **`G-4`, `G-5`, `G-8`, `G-10`, `G-12` remain OPEN**; `G-4` and `G-5` are hard `user` gates. `G-8`'s region is
  a conservative superset resting on the unproven conjecture `δ ≤ 1`, and **options (b)/(c) must not be put to
  Buyan — unconditionally, with no expiry.**
- Ledger accrual, account transfers (gl 17), charge-off, multi-currency and **slot resolution** remain
  **ungraded**; the harness prints all eight rows every run.
- Two of the 46 loanschedule vectors have `principal_amortizes_to_zero` switched OFF, legitimately and loudly.
- **Nothing has been cut over, and nothing here authorises it.**
- **P-86:** cite the rule text, or the id AND its sentence — never the id alone.
