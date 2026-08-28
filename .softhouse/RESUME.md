# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-140005`, chain iteration 4 — **TEN WORKERS IN FLIGHT.** Written and pushed BEFORE the first `git worktree add`.

If you are reading this after a kill, **ten tasks were live**. Each was told to commit incrementally, so each
branch should carry partial work. Verify with `git log --oneline main..softhouse/<branch>` per row below;
a branch with no commit means that worker died before its first checkpoint and the task is `needs_retry`,
**not** `in_progress`.

### Why iteration 4 exists
Iteration 3 closed clean at `c4d89c1a` (16:54Z) with zero live workers and a green bar. The wrapper chained.
Nothing was interrupted.

## BAR ON `main` AT ITERATION-4 DISPATCH — re-measured by this driver, not inherited

```
bash .softhouse/conformance.sh   →  VERDICT: PASS (exit 0)
probe line PRESENT (grep -c 'probe = ' == 1), reads `up`     ← presence tested BEFORE value, P-84
46 parity vectors / 7884 cells · contract-refusal 4/0 · self-test 1/0
all 14 wrong ledger implementations KILLED · EXEMPTION_PIN_LEDGER_WRONGIMPLS=14 == population 14
dead-path frontier GREEN · namespace census PASS (dirs=189 collidingIds=2 declared=2)
```

Reference oracle REACHABLE: `https://localhost:8443/fineract-provider/actuator/health`. PostgreSQL on `:5432`.
No prohibited-engine port open. **The iteration-3 merge hazard is genuinely closed** — the pin reads 14 at
`conformance.sh:4476` and the wrong-implementation population is 14.

## IN FLIGHT — ten workers, all `isolation: worktree`

| Task | Branch | Model | What it is |
|---|---|---|---|
| `T391` | `softhouse/T391-accrual-promotion` | opus | **Promote T388's accrual observations into vectors.** Oracle-only work. Grades the SLOT, not the account (T242's lesson). |
| `T390` | `softhouse/T390-baseline-attribution` | opus | Oracle-state baseline cannot attribute L28-L31 / T388's 20 command keys. Oracle-only. |
| `T402` | `softhouse/T402-t386-conditions` | opus | **Blocks `T399`.** A `2>` redirect that cannot be opened returns 1 *without running the command*. |
| `T404` | `softhouse/T404-t384-conditions` | opus | The FIFTH registration fail-open, REACHED by T384 via an ambiguous-glob symlink. **Holds `conformance.sh`.** |
| `T400` | `softhouse/T400-t385-conditions` | opus | Two `fire-program.sh` offsets that "cannot drift apart" and do. **P-97 applies — land through git, never `cp`.** |
| `T401` | `softhouse/T401-zsh-census-gap` | opus | 110 tracked `.zsh` files invisible to the fail-open/dead-path census. |
| `T393` | `softhouse/T393-t382-conditions` | opus | T382's four conditions on T374. **The task iteration 3 recorded as dispatched and never spawned.** |
| `T397` | `softhouse/T397-t387-conditions` | opus | `verbatimInCapture` is `bytes.Contains`, so a numeric PREFIX satisfies it. **No float, no parse — the amount is never a number.** |
| `T396` | `softhouse/T396-t389-conditions` | opus | T389's three citation defects; m-3 hides three real port traps. |
| ~~`T392`~~ | **MERGED** at iter4 | sonnet | Took **P-98**. Driver verified it free independently before merge (zero hits repo-wide, highest was P-97). Bar green on the merge result; main's tree hash is identical to it. |
| `T398` | `softhouse/T398-measured-but-backwards` | opus | Dispatched after T392 landed. **Must take the next free cardinal ABOVE P-98 — `P-99` is a permanent negative control, so `P-100`.** |

## ⚠ `conformance.sh` IS CONTENDED BY TWO OF THESE — MERGE SERIALLY

`T404` holds the registration-guard regions. `T391` may move **pinned counts only**, and **BY NAME**. Merge
into a scratch worktree, run the bar on the **merge result**, only then touch `main`, then re-run on `main`.
**Never apply a pin bump by line number** — iteration 3 measured a **546-line** shift between two branches on
`EXEMPTION_PIN_LEDGER_WRONGIMPLS`.

`T390` and `T401` were both told they may NOT edit `conformance.sh` this wave: if wiring is the right answer
they ship the exact patch as a **request** in their handoff (the `T360` pattern) and drive it RED in their own
worktree to prove it.

## DRIVER STATE REPAIRS MADE INLINE THIS ITERATION (no worker; `.softhouse/` is the driver's own)

1. **`ready-tasks.py` CRASHED, and the crash read as noise.** `program.json.gates_pending` held `G-20` and
   `G-21` as **bare strings**, so `g.get("class")` raised `AttributeError` — *after* READY and BLOCKED had
   printed. Every driver running the resolver since got a full, plausible task list and **no gate section at
   all**. That is the P-77 failure the block exists to prevent, arriving through a shape P-77 did not
   anticipate: not a gate missing `class`, but an entry that is not a gate object. Resolver now surfaces
   non-dict entries under `MALFORMED` and reads them as **OPEN**, never closed.
2. **`G-20` and `G-21` normalised into gate objects** in `program.json`, from their `gates.md` text.
   Both `state: OPEN`, both `blocks: nothing`. Resolver now reports **0 open CONTRACT gates** — so nothing in
   this wave is forbidden on permission grounds, as opposed to merely dependency-ready.

## QUEUE AFTER THIS WAVE, IN ORDER
`T394` (reviews `T393`) → `T398` (needs `T392`'s P-number) → `T399` (needs `T402`) → `T395` (G-21, DEC-2
**evidential correction only**) → then the reviewer pairings for whatever lands here.

## OPEN GATES — none blocks anything
`G-4`, `G-5`, `G-8`, `G-10`, `G-12`, `G-19`, `G-20` (effort ratio: 60% instrument, 39% port), `G-21` (a
ratified DEC-2 carries a cardinal the oracle moved out from under; `T395` prepares the correction citing it).
**No CONTRACT gate is open.**
