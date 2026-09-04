# Incident — five completed commits on one laptop, and a `main` that said they were done

**Recorded by** fire `cloud-20260904-1200` (cloud routine, 20:00 Asia/Ulaanbaatar, oracle unreachable
by design), 2026-09-04.
**Status of this document:** every finding below is a measurement taken in a clone that contains
nothing but `origin`. Each command is named so the next fire can re-run it rather than trust it.

---

## 1. The headline

**Five completed worker commits exist on exactly one machine, and the record on `main` asserts they
are done.**

The 2026-09-03 local fire dispatched eight workers and closed clean. Its bookkeeping reached
`origin/main`. **Its work did not.** A cloud fire the next evening — which knows only what is
published — found that the commits `tasks.json` names as landed cannot be resolved at all.

This is not a new failure mode. It is **P-85** — *"two orchestrators held the lock at once, and the
cause was an unpushed in-flight state"* — one level up. P-85 cost a lock decision. The same root
cause has now cost the **reviewability of five completed tasks**, one of them the program's declared
critical path.

## 2. The measurement

Run in `/home/user/gerege-nbfi`, a clone whose only remote is `origin`:

```
$ for sha in 1abd3a11 857dd4d8 5c4233fc 8ff5ff15 84dc208e; do
    git rev-parse --verify -q "$sha^{commit}" || echo "ABSENT $sha"; done
ABSENT 1abd3a11
ABSENT 857dd4d8
ABSENT 5c4233fc
ABSENT 8ff5ff15
ABSENT 84dc208e

$ git ls-remote --heads origin 'refs/heads/softhouse/*' \
    | grep -oE 'T[0-9]+' | sort -tT -k2 -n | tail -1
T497
```

**Nothing numbered above T497 was ever pushed.** Against that, `.softhouse/tasks.json` **on `main`**
records:

| Task | Status on `main` | Claimed in its own `note` | Reality on `origin` |
|---|---|---|---|
| **T509** | `done` | landed `857dd4d8` on `softhouse/T509-ledgerguard-blindspot` | **absent** |
| **T508** | `done` | landed `1abd3a11` on `softhouse/T508-journalentry-insert-schema` | **absent** |
| **T515** | `done` | landed `84dc208e` on `softhouse/T515-savings-classification-rework` | **absent** |
| T510 | `needs_retry` | `5c4233fc` | **absent** |
| T512 | `needs_conditions` | `8ff5ff15` | **absent** |

T509 is the task the previous fire itself named **THE CRITICAL PATH** — the repair of
`guard_ledger_invariants`, a money non-negotiable.

## 3. What separated the work that survived from the work that did not

Four tasks from the same fire **did** survive: T502 (`0b5e8b81`), T511 (`fc35f4eb`), T516
(`709e51c3`), T519 (`d355d422`). All four are ancestors of `origin/main`.

The difference is not merit and not review status. It is mechanical:

> **Work reached `origin` if and only if it was MERGED to `main` during the fire.** A merge commit
> pushed to `main` drags its second parent's content along with it. A task that was marked `done` and
> left on its branch *pending review next fire* had nothing to drag it, and no step ever pushed the
> branch itself.

The rule that saved work was *"merge and push"*. The rule that lost it was *"mark `done`, leave it on
a branch, review it next fire"*. The pipeline prescribes the second for every task — review is
supposed to happen on the branch, before the merge — so **the losing path is the normal path**, and
the surviving four survived by being further along, not by being handled better.

The three bookkeeping commits that did reach `origin/main` make the divergence exact:

```
$ git show --stat --format=%s a6f88805 f78ed058 a4b5ebac
softhouse: T508 done + T520/T521 …   → .softhouse/{LOCK, reference-oracle.md, tasks.json}
softhouse: T515 done + T522 filed …  → .softhouse/{LOCK, tasks.json}
softhouse: T509 CLEARS THE CRITICAL PATH … → .softhouse/{LOCK, tasks.json}
```

Not one line of code, guard, handoff or review among them. **`main` received the claim and none of
the evidence.**

## 4. The second-order damage: three independent reviews cannot run

T520, T522 and T523 are the paired independent reviewers for T508, T515 and T509. Each is briefed to
*re-derive* its subject from the diff — deliberately, so the reviewer never depends on the author's
prose. With the branch absent, that is impossible: what remains readable is exactly the author's own
summary, which is the one input the design forbids.

They are therefore parked with reason **`branch_unpushed`** — and deliberately **not**
`oracle_unreachable`, even though this fire genuinely cannot reach the oracle and parking them under
that reason would have been easier and would have looked identical in the summary. Misfiling a
publishing failure as an outage is precisely the reclassification `/softhouse-program` STEP 4 exists
to prevent: *a refusal mistaken for an outage, parking work that nothing is blocking*. Here it would
also have been self-concealing — an oracle park invites "retry next fire", and no number of retries
pushes a branch.

## 5. Why the bar is red, and why nothing about it is the oracle's fault

`bash .softhouse/conformance.sh` exits **2 with no probe line printed** — a HARD guard failure. Two
distinct failures, both downstream of T509 being absent:

1. **The guard fails its own selftest.** `check-ledger-invariants.sh --selftest` reports
   `FAIL (n) the REAL Go tree at /home/user/gerege-nbfi/nexus — must PASS: expected exit 0, got 1`.
   T509's recorded fix was to *replace* case (n) with a committed fixture at
   `ledgerguard/testdata/cleantree/`. That directory **does not exist on `main`**, and
   `main.go:1206` still runs case (n) against the real tree.
2. **The guard refuses with 9 `I-3` findings** — four in `loanproduct`, three `savings` field writes,
   two `savings` SQL balance writes. T509's repair and T515's savings rework are both unpushed.

Per STEP 4 this is *not* an oracle outage and **nothing may be parked for it**. The distinction
matters more than usual here, because this fire could not reach the oracle either — so an inattentive
driver had a ready-made, wrong explanation sitting in front of it for every red thing it saw.

## 6. Why no instrument caught it

`ready-tasks.py` already carries an arm for the **opposite** direction — it warns when work bearing a
task id is *already on `main`* while the task sits non-terminal (the T286 arm, added after T421 and
T428 sat non-terminal with their deliverables merged). There is **no arm at all** for *"this task
claims a branch and a commit that `origin` has never heard of."*

`conformance.sh` grades the **tree**, and the tree is internally fine. The defect is not in the tree;
it is in what the tree **asserts about work that is not in it**. No guard in this program reads
`tasks.json` as a set of falsifiable claims about `origin`.

That gap is now filed as **T527** (build `.softhouse/bin/check-branch-published.py`, fail closed when
`origin` is unreachable, wire it into `ready-tasks.py`) with paired independent reviewer **T528**.
The fail-closed arm is the whole of it: a guard that passes when it cannot reach `origin` would have
scored this incident **GREEN**, which is **P-45** — *a guard that only works when someone remembers
to run it enforces nothing* — in its network-partition form.

## 7. What only Buyan can do

```
cd ~/gerege-nbfi && git push origin --all
```

Until that runs, T509's repair of a money non-negotiable exists on one laptop, three independent
reviews cannot start, and the bar cannot go green. No agent on any other machine can recover this
work; it is not a matter of retrying.

## 8. Pattern to record — number deliberately not assigned here

The lesson belongs in `.softhouse/patterns.md`:

> **A task is not done when its author says so; it is done when `origin` can show you.** Status in
> `tasks.json` is a *claim about the world*, and this program had no instrument that checked it
> against the world. Work that is merged is published as a side effect; work that is merely finished
> is published only if someone remembers — and P-45 is the standing finding that "someone remembers"
> enforces nothing.

**No `P-` number is claimed by this document, on purpose.** The five unpushed commits may already
have added pattern entries, and inventing a number here would collide with them invisibly — the same
class of unverifiable claim this incident is about. Assign the number in the fire that lands the
unpushed branches, when the real maximum is readable.

---

*Recorded by the cloud fire that could see the gap precisely because it could see nothing but
`origin`. The local fire was not able to detect this: on the machine that holds the commits, every
one of them resolves.*
