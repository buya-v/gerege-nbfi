<!-- T288-WRAPPER-BANNER — written by fire-program.sh, not by a driver -->
> ## STALE — this manifest was NOT rewritten by fire `20260901-140002`, which ended 2026-09-01T06:02:13Z.
>
> Everything below predates that fire, so its task table, its "next action" and its
> pause reason are all claims about a world that has moved. The driver did not reach
> STEP 5.5, which is why a shell script is writing this.
>
> - driver outcome: rc=`1` — **THE DRIVER PRODUCED 0 MODEL TURNS** and no quota rejection was recorded — cause UNKNOWN, read /Users/buv/Library/Logs/gerege-nbfi/fire-20260901-140002.jsonl before blaming the driver's logic.
> - tasks.json reconcile: ran clean (see the reconcile| lines in /Users/buv/Library/Logs/gerege-nbfi/fire-20260901-140002.log)
> - a task shown below as `in_progress` is a DEAD dispatch unless the reconcile line
>   above says it was refused; read `tasks.json` notes, not this table.
> - fire log: `/Users/buv/Library/Logs/gerege-nbfi/fire-20260901-140002.log`
>
> This banner is not maintained by anyone. It disappears when a driver rewrites
> RESUME.md per STEP 5.5.4, and it comes back on any fire that fails to.
<!-- /T288-WRAPPER-BANNER -->
















# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260829-080002` ITERATION 6 — **WAVE 2 IN FLIGHT. FIVE WORKERS LIVE.**

**WAVE 1 IS COMPLETE AND MERGED: FIVE REVIEWED PAIRS, TEN BRANCHES, EVERY MERGE ATTESTED BY TREE SHA.**
`T458+T468` (373bf176) · `T465+T471` (dbfbae4f) · `T462+T469` (8f3136cb) · `T466+T477+T479` (4cb2103c) · `T467+T476+T481` (44966ad8).
TWO STACKS WERE HELD UNMERGED ON THEIR REVIEWER MAJORS AND REPAIRED BEFORE LANDING -- T466 opened a fourth forgery route while closing three; T467 regressed two spellings its predecessor caught. Neither was merged on its first delivery.
**THE FIRE EXIT NO LONGER REDDENS THE BAR** (T465): a lock-released tree now grades exit 0 probe 1 PASS, where the base tree gave exit 2 probe 0.
**ORACLE SIGTERMed TWICE** (`Exited (143)`), the second time taking the Docker daemon with it; both recovered, both recorded in `.softhouse/reference-oracle.md`.

Oracle **REACHABLE** (`https://localhost:8443/fineract-provider/actuator/health`), PostgreSQL `localhost:5432`,
pinned Fineract `/Users/buv/fineract @ 426a23544`.

**IF YOU ARE READING THIS AND THE FIRE IS NOT RUNNING, THE WORKERS WERE KILLED.** Each was dispatched to an
isolated worktree on the branch named below. Check `git log --oneline main..<branch>` for each; a branch with
no commit means that worker died before committing and its task must be set `needs_retry`, never left
`in_progress`.

## WAVE 1 — DISPATCHED, LIVE

| Task | Branch | Subject |
|---|---|---|
| `T465` | `softhouse/T465-lock-frontier` | C-T461-1 MAJOR — the dead-path frontier is a function of whether the fire LOCK is tracked; releasing it reddens the bar |
| `T466` | `softhouse/T466-skipwt-smudge` | T459's two MAJORs on T454 — SKIPWT and SMUDGE reach PASS with a CLEAN `git status`; the two-deletion cost claim is false |
| `T462` | `softhouse/T462-wallclock-refusal` | T456's MAJOR on T451 — a safety refusal bounded by wall clock demotes on a slow host what it refuses on a fast one |
| `T458` | `softhouse/T458-fixture-literal-pattern` | Six workers refused in one fire by the same reflex — record the pattern, make the refusal teach the fix |
| `T467` | `softhouse/T467-t464-conditions` | T464's conditions on T455 — abuse B re-opens through `printf`; the F-6 fail-closed branch is reachable only by a crash |

Wave 2 is the paired INDEPENDENT reviewers, one per landed worker branch, dispatched only after wave 1 lands.

## BAR ON `main` AT ITERATION START
`bash .softhouse/conformance.sh` was re-run on the iteration-5 tip `9f341a2b` at iteration 6 start; result
recorded in the iteration-6 close block. Iteration 5 attested EXIT 0, probe PRESENT x1 `up`, PASS 46 vectors /
7884 cells, frontier 11 == 11, deadOccurrences 108, 16 guards timed.

## ⚠ WHAT A WORKER OR THE NEXT FIRE MOST NEEDS TO KNOW

**1. THE DRIVER PUSH GATE IS LIVE AND IT REFUSES THE DRIVER.** A transcript is bytes and nothing binds it to
the tree it claims to have graded. The remedy is `bash .softhouse/hooks/bar-attest.sh HEAD`, which checks the
tree out itself. **Never bypass; attest.** `bypass.log` does not exist and should stay that way.

**2. PUSH EVERYTHING BEFORE THE LOCK RELEASE.** `D .softhouse/LOCK` leaves the STATE set, so the release push
takes the full-bar path, and the full bar on a lock-released tree is `EXIT 2` with **no probe line**. Nothing
should depend on the exit push landing. `T465` is the task that fixes this and it is live above.

**3. THE WITNESS-FORGERY CHAIN IS AT EIGHT LINKS AND STILL OPEN.**
`T404→T407→T431→T444→T445→T446→T454→T459`. Open and driven: `LONGSTRIP`, `LONGNOP`, `SKIPWT`, `SMUDGE` — the
last two reach `PASS` with the guard fully intact **and `git status --porcelain` EMPTY**. `T466` is live on
SKIPWT/SMUDGE; `T460` (the external verifier) follows and **is amended** — bare `git hash-object` is defeated
by SMUDGE, use `--no-filters`.

**4. RUN THE BAR ON YOUR OWN INSTRUMENTS BEFORE YOU COMMIT.** Seven workers last iteration had a first bar
refused, six for the same reflex: **spelling a real `.softhouse/...` path as a literal in a fixture**. Assemble
paths from a variable (`S='.softhouse'`) or at run time. `T458` is live writing this into `patterns.md`.

## QUEUE AFTER THIS WAVE
`T463` → `T460` (**after** reading the amendment) → `T403` → `T443`, `T441` → `T419` → `T437` →
`T434`/`T435`/`T436` → `T399`, `T425`, `T394`, `T395`.

## OPEN GATES — none blocks anything, no CONTRACT gate open
`G-4`, `G-5`, `G-8`, `G-10`, `G-12`, `G-19`, `G-20`, `G-21`, `G-22`.

**For Buyan:** server-side prevention of `--no-verify` is partly a `user` item — designing and driving it
against a throwaway bare remote is ENGINEERING and needs no gate; applying it to live `origin` needs repo-admin
rights the agent does not hold. Note `pre-receive` is **not available on github.com** (Enterprise Server only),
so the realistic instrument is a branch ruleset.

## Pause reason
Not paused — iteration 6 wave 1 in flight at dispatch time.
