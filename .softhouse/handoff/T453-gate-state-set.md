# T453 — the driver push gate's STATE set, and the gate nothing installed

**Branch** `softhouse/T453-gate-state-set` · **Filed by** T450's independent review of T412 ·
**Subject** `.softhouse/hooks/` (the gate), `.softhouse/bin/fire-program.sh` (the wiring only).

Everything below was **re-derived on this branch**, not inherited from T450. Every arm was driven
end to end through a real `git push` into a real bare remote with the gate really installed, in
throwaway universes under `$TMPDIR`. **The live `pre-push` on this host was never touched**: it
is gating the fire that dispatched this task, and an instrument that edited it would be changing
the control it is measuring.

---

## 0. The one-line summary

| item | before | after |
|---|---|---|
| **M-1** four STATE-confined deltas the gate allowed and the bar refused | 4/4 `ALLOWED`, `C3 PASS`, CHEAP attestation written | 4/4 `REFUSED`, 3/3 healthy controls still `ALLOWED` |
| **M-2** nothing installed the gate | 0 executable callers | installed + status-checked + reconciled by `fire-program.sh`, every fire; the block itself driven |
| **m-3** `--no-verify` drove a gitlink onto `main`, `bypass.log` had no reader | undetectable, unread | `reconcile-pushed-trees.sh` names it post hoc; bypass rows read every fire |
| **m-4** C3 named `bar-attest.sh`, which was not in the snapshot | installer checked 3, copied 2 | one `GATE_PARTS` list; refusal prints a path resolved **at the moment it is printed** |
| **m-5** enforcement changeable by an uncommitted edit | invisible | banner + the running gate's sha256 in every ledger row |
| **L-6 / L-7 / L-8** | tip-only C1; unreachable `case`; table omitted guards | range-wide C1; one `case`; all fifteen guards named |

Bar on the finished committed tree: **EXIT 0**, probe line **PRESENT ×1** reading `up`,
`VERDICT: PASS … 46 parity vectors … 7884 cells`, `deadOccurrences 108`, fail-open frontier
`11 == 11`. Transcript: `.softhouse/capture/t453-t450-conditions/transcripts/final-bar.txt`.

---

## 1. M-1 — the reasoning error, re-derived

T450 stated it as *"three guards resolve against the tree's INVENTORY, so an ADDITION is the same
hazard as the DELETION clause (j) already excludes."* That is right about two of the three arms
and **wrong about the money one**, and the difference decides the remedy. Re-derived from source:

* **B and C2 (and my new D) are INVENTORY hazards.** `guard_dead_path_frontier` resolves every
  quoted `.softhouse/` literal against `git ls-files` — the tracked universe, never the disk
  [`census_dead_paths.py`, `tracked_universe`] — and `guard_capture_namespace`'s entire population
  is `git ls-files` reduced to the first path component under `capture/` or `reviews/`
  [`check-capture-namespace.sh`, the `sed -n -E 's#^\.softhouse/(capture|reviews)/…'` line].
  **Neither guard opens the file you added.** Its presence in the index is the whole mechanism.

* **A (MONEY) is a READ hazard, and clause (h) was simply STALE.** The table said
  `guard_no_float_in_capture_requests` "takes every `*.json` whose DIRECT parent is `req`". That
  describes the guard **before T193**. Since T193 it has a **second arm** that opens every file a
  stored parity vector names in `provenance.capture_ref` and grades the numeric tokens inside its
  recorded-request blocks. Measured on this tree: **26 distinct `capture_ref` paths, all 26 under
  `.softhouse/capture/`, none with a `req/` segment** — so clause (h) excluded none of them.

**The deeper defect, which is what the remedy has to answer:** `state_path` is a
**hand-maintained model of fifteen other programs' corpora**. Clause (h) rotted the day T193
widened a guard, and nothing said so. Any fix that adds more rows to that table inherits the same
rot.

### The remedy, and the two alternatives rejected with numbers

Measured over the **last 400 non-merge first-parent commits on `main`** (the driver's own write
history; `git show --name-status` per commit, classified in Python):

| rule | cheap-path coverage | what it costs |
|---|---|---|
| T412 as shipped (`A`\|`M`, no capture/reviews exclusion) | **88 %** (353/400) | prints `PASS` over a money non-negotiable |
| *rejected* — **modifications only** | **71 %** (284/400) | blocks `A .softhouse/LOCK`, which the driver does **34 times** in those 400 commits, at fire start — the most latency-sensitive push there is |
| *rejected* — **exclude `.softhouse/capture/**` only** | ~87 % | does **not** close the frontier hazard outside `capture/` — arm D proves it |
| **chosen (T453)** | **84 %** (335/400) | 27 entries under `capture/`+`reviews/`; **0 of the 78 historical ADDITIONS blocked** |

The chosen rule is three parts:

1. **`.softhouse/capture/**` and `.softhouse/reviews/**` leave the STATE set** (clause h2).
   Structural, and it closes *two* guards at once: the money guard's second arm (all 26 cited
   records are there) and the namespace guard (its whole population is those two subtrees).
   Measured cost: 4 percentage points.
2. **Clause (k): an ADDITION is admitted only if it cannot move the dead-path frontier**, and
   that is decided by **measurement against the pushed tree's own pin** —
   `.softhouse/hooks/added-path-hazard.py` reads `.softhouse/guards/dead-path-frontier.pin` out of
   the pushed commit and asks whether any added path would make a pinned-dead literal resolve.
   **Not another row in the table**, deliberately: the table is what rotted, and this reads the
   guard's own pin, so if the pin moves the test moves with it.
3. **`state_path` rewritten as one `case`** (L-7), with a table naming **all fifteen** guards
   `run_guards` calls and saying explicitly why `guard_pnumber_citations` (it *is* the cheap
   subset), `guard_graded_root_is_this_tree` (reads an env var) and `guard_cost_census` (reads no
   path) need no exclusion (L-8).

**The predicate in (k) is a deliberate SUPERSET** — `L == P`, `P` under `L/`, `L` under `P/`, and
`L` starting with `P` (which catches the census's punctuation- and `:NN`-stripped spellings)
— because the fail-closed direction is *refuse a cheap re-grade that would have been safe and
send it to the full bar*. It **cannot** admit one that is not safe. It refuses on an unreadable
pin, an empty pin, an empty question, a missing helper, or a failed selftest; **exit 0 is the only
code that means "measured, no hazard"**.

### What clause (k) is NOT, stated so nobody over-reads it

It closes the `removed > 0` direction of the frontier, which is the only direction an addition can
move it (the census corpus is tracked `*.sh`/`*.py`, already excluded by clause (g), so an
addition cannot *add* a frontier row). It says nothing about guards nobody has enumerated. The
enumeration I did is in §6.

---

## 2. M-1 — all four arms, RED → GREEN

Three arms are T450's. **Arm D is mine**, and it is the one that shows this is not a `capture/`
problem: `.softhouse/uat.md` is untracked, is one of the 108 pinned dead literals, and adding it
is ordinary driver work nowhere near `capture/`.

### RED — the gate at `main` (cbc8733c) ALLOWED every one

`.softhouse/capture/t453-t450-conditions/transcripts/red-main/RESULTS.txt`

| arm | delta | push exit | verdict |
|---|---|---|---|
| A-MONEY-CAPTUREREF | `M .softhouse/capture/out/capture-prod3b-raw.json` | 0 | **ALLOWED** |
| B-FRONTIER-CAPTURE | `A .softhouse/capture/t290-second-rig/note.txt` | 0 | **ALLOWED** |
| C2-NAMESPACE-CAPTURE | `A .softhouse/capture/t305-second-directory/note.md` | 0 | **ALLOWED** |
| D-FRONTIER-UATMD | `A .softhouse/uat.md` | 0 | **ALLOWED** |
| CTRL-M-RESUME | `M .softhouse/RESUME.md` | 0 | ALLOWED (control) |
| CTRL-A-OBSERVATION | `A .softhouse/observations/…` | 0 | ALLOWED (control) |
| CTRL-A-LOCK | `A .softhouse/LOCK` from a base without it | 0 | ALLOWED (control) |

Each printed `C3 PASS -- cheap subset clean` and **wrote a CHEAP attestation**.

### RED — the FULL BAR on those exact trees

`.softhouse/capture/t453-t450-conditions/transcripts/red-main-bar/RESULTS.txt`

| arm | bar exit | `grep -c 'probe = '` | refusal |
|---|---|---|---|
| A-MONEY-CAPTUREREF | **2** | **0** | `the wire-float round-trip guard REFUSED: … the money the reference oracle was asked about is not the money the record says it was asked about` |
| B-FRONTIER-CAPTURE | **2** | **0** | `T316-DEADPATH-FRONTIER: REFUSED rows=106 pinned=108 added=0 removed=2` |
| C2-NAMESPACE-CAPTURE | **2** | **0** | `guard_capture_namespace FAILED (rc=1)` — `T305 needs 1 ownership record(s), has 0` |
| D-FRONTIER-UATMD | **2** | **0** | `T316-DEADPATH-FRONTIER: REFUSED rows=107 pinned=108 added=0 removed=1` |
| CTRL-M-RESUME | **0** | **1** | — |
| CTRL-A-OBSERVATION | **0** | **1** | — |
| CTRL-A-LOCK | **0** | **1** | — |

The three controls at **exit 0 with the probe printed** are what make the four refusals mean
something (P-98). They also settle a fixture question the hard way: **the first version of this
drive built its universe with `git archive` into a fresh `git init`, and the CONTROL came back
EXIT 2 as well** — `guard_reconciler_ownership` reads historical commits by sha and a squashed
single-commit fixture has none of them. A red control makes every red arm uninterpretable. The
drive now uses a real `git clone --local`, and the fixture defect is written into the instrument
rather than quietly fixed.

### GREEN — the gate on this branch (7bb43b5d)

`.softhouse/capture/t453-t450-conditions/transcripts/green-t453/RESULTS.txt`

| arm | push exit | verdict | refused by |
|---|---|---|---|
| A-MONEY-CAPTUREREF | 1 | **REFUSED** | STATE set — `[M] .softhouse/capture/out/capture-prod3b-raw.json` |
| B-FRONTIER-CAPTURE | 1 | **REFUSED** | STATE set — `[A] .softhouse/capture/t290-second-rig/note.txt` |
| C2-NAMESPACE-CAPTURE | 1 | **REFUSED** | STATE set — `[A] .softhouse/capture/t305-second-directory/note.md` |
| D-FRONTIER-UATMD | 1 | **REFUSED** | **clause (k), by measurement**: `ADDED-PATH-HAZARD: pin=… rows=108 literals=68 added=1 hazards=1` → `HAZARD .softhouse/uat.md would make the pinned dead literal .softhouse/uat.md RESOLVE` |
| CTRL-M-RESUME | 0 | **ALLOWED** | cheap subset clean |
| CTRL-A-OBSERVATION | 0 | **ALLOWED** | `hazards=0`, cheap subset clean |
| CTRL-A-LOCK | 0 | **ALLOWED** | `hazards=0`, cheap subset clean |

**Both calibrations pass in both phases** and are preconditions, not decorations: the drive
`ABORT`s at exit 92 if the installed gate cannot be seen to refuse a gitlink (**CALIBRATION+**, so
`ALLOWED` is distinguishable from a hook that never ran) or cannot be seen to allow an honest
driver state edit (**CALIBRATION−**, so `REFUSED` is distinguishable from a gate that refuses
everything). It `ABORT`s at 94 if the gate prints **nothing**: silence is never reported as a
verdict.

Instrument: `.softhouse/capture/t453-t450-conditions/instruments/drive-arms.sh`, one arm list,
two modes (`gate` and `bar`) — because two files would drift, and the finding *is* a disagreement
between the two instruments.

---

## 3. M-2 — the gate is now installed BY SOMETHING

**The census, re-run on this branch** (`git grep` over tracked `*.sh`/`*.py`/`*.json`, excluding
the gate's own directory, T450's review and `tasks.json`):

```
.softhouse/bin/fire-program.sh:1320  bash "$REPO/.softhouse/hooks/install-driver-push-gate.sh"      | log pushgate|
.softhouse/bin/fire-program.sh:1321  if bash "$REPO/.softhouse/hooks/install-driver-push-gate.sh" --status
.softhouse/bin/fire-program.sh:1329    bash "$REPO/.softhouse/hooks/install-driver-push-gate.sh" --status  | log pushgate|
.softhouse/bin/fire-program.sh:1342  bash "$REPO/.softhouse/hooks/reconcile-pushed-trees.sh"        | log reconcile|
```

Before this branch that census returned **zero executable callers** — only prose in a handoff, a
review and the task description. Placement is deliberately the **T312 precedent two lines above**:
the installer is idempotent, and a step that runs only when somebody types it is the defect being
closed.

**Wiring alone would still be a document, so the block was DRIVEN.**
`instruments/drive-fire-wiring.sh` **extracts the block from the tracked wrapper by its
sentinels** (nothing is retyped — a copy is not what runs; it REFUSES if a sentinel is missing)
and executes it under `zsh` against a **fresh clone**, which is exactly what the cloud fire and
any CI runner is. `transcripts/fire-wiring/`:

* **LEG A** — fresh clone, no hook. Block runs → `.git/hooks/pre-push` exists → log carries
  `pushgate| STATUS OK`.
* **LEG B** — the installer moved aside. Block runs → log carries
  `# THE DRIVER PUSH GATE IS NOT INSTALLED (or is incomplete).` The **absent arm has been seen to
  fire** (P-22); block exit stays 0, because a broken guard must not stop a fire.
* **LEG C** — `reconcile|` lines reach the log, and on a fresh clone the reconciler correctly
  **ABORTs(2)** — *"an absent ledger must never read as 'every push was graded'"*.

**And the absence is detectable by an exit code, which is the half that was missing.**
`instruments/drive-install-detect.sh`, `transcripts/install-detect/`:

| leg | at `main` (T412) | on this branch |
|---|---|---|
| A — `--status` on a fresh clone | **exit 0** ← *absence undetectable*; drive ABORTs 92 (`transcripts/install-detect-RED-at-main-RESULT.txt`) | **exit 1** |
| B — push to `main` from that clone | 0 gate output lines — measured, not asserted | same (it really is ungated until C) |
| C — after `install` | — | `--status` exit 0, push produces **18** gate lines |
| D — one part removed from the snapshot | — | `--status` **exit 1** (this is m-4's shape) |

> ⚠ **The mid-run caveat, said plainly.** `fire-program.sh` is the **running wrapper**. T301
> already recorded the wrapper editing itself mid-run as a defect. This change was **landed
> mid-run and is UNVERIFIED IN A LIVE FIRE**; it takes effect at the **next** fire. What is
> verified is that the block, extracted from the tracked file and executed, does what it says.

> ⚠ **The live host is RED right now, and correctly.**
> `bash .softhouse/hooks/install-driver-push-gate.sh --status` on this machine exits **1**:
> `snapshot MISSING bar-attest.sh` and `snapshot MISSING added-path-hazard.py`. That is the new
> check finding m-4 first-hand. **The driver must re-run the installer after merging this
> branch** — the next fire does it automatically, but any push before that still runs the old
> snapshot.

---

## 4. Per-item disposition

### m-3 — `--no-verify`, and `bypass.log` with no reader → **FU-T412-4 BUILT AND DRIVEN**

`.softhouse/hooks/reconcile-pushed-trees.sh`. `pre-push` is client-side; the answer to a
bypassable check is not a louder one, it is a **second reading taken afterwards from evidence the
bypasser did not choose** — what actually landed on the ref. Every tip in `origin/main`'s reflog
is reconciled against the ledger (**R1 attested?**) and scanned for gitlinks (**R2**, C1 taken
post hoc — the arm `--no-verify` cannot evade, because the mode is in the tree that landed). The
window is **derived from the ledger** (tips descending from the oldest commit it names), so
pre-gate history is reported as `pre-gate` and is not a finding — a census that cries wolf on its
first run gets pinned away.

`instruments/drive-reconciler.sh`, `transcripts/reconciler/`:

| leg | result |
|---|---|
| 1 — lawful gated push | ALLOWED, ledger row written, reconciler **exit 0** (the control; without it every RED below is unearned) |
| 2 — `--no-verify` push of a **gitlink** | push exit 0, **gate output lines = 0** — m-3 reproduced verbatim |
| 3 — reconciler afterwards | **exit 1**, `UNATTESTED 0b141357 tree bf4eb0c2…` **and** `GITLINK 0b141357 t453-nv-submodule` |
| 4 — a push under a recorded bypass | reconciler **reads 2 bypass rows** — `bypass.log`'s first reader |

**On the live host, now:** `T453-RECONCILE: ref=refs/remotes/origin/main window=15 pre-gate=65
unattested=0 gitlinks=0 bypasses=0` → `RECONCILED CLEAN`. (`window=15` is an independent
re-derivation of T450's *"15 pushes"*.)

**It cannot prevent anything, and does not claim to.** It makes the bypass **countable**, one
fire late. Server-side enforcement (a GitHub ruleset or a `pre-receive` hook) is the only thing
that would prevent it, and it is outside a worker's grant — see §7.

### m-4 — the refusal named a nonexistent remedy → **CLOSED TWO WAYS**

1. **One list.** `GATE_PARTS='driver-push-gate.sh cheap-subset.sh bar-attest.sh
   added-path-hazard.py'` is checked, copied and re-verified by the **same** loop. T412 wrote the
   list twice (checked 3, copied 2); P-80's prescription is not "fix the second list", it is "make
   the second site READ the first".
2. **The message resolves at the moment it is printed.** `beside_gate()` searches the directory
   beside the gate, then the main checkout, and prints an **absolute path that exists**; if
   neither has it, the gate says *`*** bar-attest.sh IS NOT ON THIS HOST ***`* and names both
   places it looked, instead of printing a command that does not resolve. Seen in
   `transcripts/green-t453/arm-D-FRONTIER-UATMD.txt`.
   The installer now also **runs `added-path-hazard.py --selftest` before installing anything** —
   installing a control that cannot fail is worse than installing none.

### m-5 — an uncommitted edit changes enforcement → **MADE LOUD AND RECONCILABLE, not fatal**

The gate computes the sha256 of the bytes that are running and of `HEAD:`'s blob, prints both on
every run (`gate bytes: running=… HEAD blob=…`), banners the divergence, and **writes the running
sha into every attestation row it appends** (`… gate=9360bd74 headblob=9360bd74`), so
`reconcile-pushed-trees.sh` can ask afterwards *"was this tree graded by a gate that was ever
committed?"*.

**Deliberately not fatal, and the reason is measured rather than aesthetic**: the legitimate
window is real — this file is edited on a branch before it merges, and refusing then would freeze
the driver mid-development. The severity is also bounded by m-3: anyone who can edit that file can
also type `--no-verify`, so refusing here buys silence, not safety. Recording is strictly
stronger. (Noted: this is the same disk-versus-blob gap T454 is closing in the harness.)

### L-6 — C1 inspected only the tip tree → **FIXED**

C1 now scans the tip tree **and every commit in the pushed range** with
`git diff-tree -r -m --root`. `-m` is required and is not decoration: without it `git diff-tree`
prints **nothing at all** for a merge commit, and a gate blind on merges would be blind on exactly
the commits C2 is already forced to exempt. The case this catches is instance 3 *with its revert
already applied* — 8c08f7d8 carried the gitlink, c31b0842 reverted it; a push of both has a clean
tip and a polluted history that every future clone still carries. Green output now reads
`C1 gitlinks: none in the pushed tree, and none in any of the N commit(s) of <range>.`

### L-7 — the unreachable second `case` → **DELETED, not repaired**

In bash `case`, `*` crosses `/`, so `.softhouse/*.md` already matched `.softhouse/a/b/c.md` and
the second block was unreachable code that read like a rule. Two blocks describing one predicate
is a second source of truth with no owner.

### L-8 — the table omitted guards → **ALL FIFTEEN NAMED**

Including the three that need no exclusion and why (`guard_pnumber_citations` **is** the cheap
subset; `guard_graded_root_is_this_tree` reads only `$CONFORMANCE_REPO_ROOT`; `guard_cost_census`
reads no path), plus `guard_no_narrow_catch_in_capture_rigs` (`*.java`, covered by the extension
clause) and `guard_no_float_in_harness`.

---

## 5. My own instruments, held to the bar they measure

* **Fail-open frontier `11 == 11`** — none of the six new `.sh`/`.py` files is on it. `sweeplib`'s
  *shape* is adopted rather than pinned: three facts, three exit codes; `ABORT(9x)` for a universe
  that could not be built; `die` on every unguarded `cd`; and no instrument prints a negative it
  did not measure. `drive-arms.sh` `ABORT`s at 94 when the gate prints nothing, rather than
  calling silence a refusal.
* **`deadOccurrences 108`, frontier `108 == 108`** — and the repair is on the record because it
  happened **twice**. The selftest fixture in `added-path-hazard.py` first spelled its dead
  literals directly (`108 → 116`); after assembling them from a variable, **one row survived —
  in my own comment explaining the repair, which quoted one of the spellings** (`→ 109`). T323's
  finding, third occurrence, now written into the file rather than quietly fixed. T323's test was
  applied both times: *can the instrument still do its job if the literal goes away?* Yes →
  **repair, do not pin.**
* **Namespace** — `capture/t453-t450-conditions` is the only `t453*` directory; guard PASS,
  `collidingIds=2 shortfallIds=0` unchanged.
* **No money code, no vectors, no `nexus/`, no floats** — this branch touches `.softhouse/hooks/`,
  `.softhouse/capture/t453-…/`, `.softhouse/handoff/` and 30 wiring lines in
  `.softhouse/bin/fire-program.sh`. `conformance.sh` (T454) and `ready-tasks.py` (T451) are
  untouched, as instructed.

---

## 6. The enumeration behind clause (k) — where I looked

For each of the fifteen guards `run_guards` calls, I asked what a **STATE-set-confined `M`, and
what an `A`,** can do to it. Read from `.softhouse/conformance.sh` and each guard's own source.

| guard | corpus | reachable by a STATE delta? |
|---|---|---|
| `guard_graded_root_is_this_tree` | `$CONFORMANCE_REPO_ROOT` (env) | no — no tree carries it |
| `guard_no_float_in_vectors`, `guard_accepting_side_gap_declared` | `.softhouse/vectors/**` | no — clause (b) |
| `guard_no_float_in_harness`, `guard_gofmt`, `guard_ledger_invariants` | harness + `nexus/` Go | no — clause (a)/(g) |
| `guard_no_float_in_capture_requests` | `req/` json + `*.req` + **every `provenance.capture_ref`** | **closed by (g)+(h)+(h2)**; all 26 cited records are under `capture/` |
| `guard_no_narrow_catch_in_capture_rigs` | `*.java` | no — clause (g) |
| `guard_no_fail_open_instruments`, `guard_no_host_state_in_lint_corpus`, `guard_dead_path_frontier` (corpus) | tracked `*.sh`/`*.py` | no — clause (g) |
| `guard_dead_path_frontier` (**resolution**) | the **tracked universe** | **yes, via an ADDITION** → **clause (k)** |
| `guard_pnumber_citations` | `git ls-files`, whole tree | **run by the cheap subset** |
| `guard_capture_namespace` | `git ls-files` → first component under `capture/`/`reviews/` | **closed by (h2)** |
| `guard_guards_dir_registration` | `.softhouse/guards/**` | no — clause (c) |
| `guard_reconciler_ownership` | `.softhouse/bin/ready-tasks.py` + **`tasks.json` at pinned historical shas** | no — clause (d); the historical corpus is immutable, so a working-tree `M .softhouse/tasks.json` cannot move it. *(Verified by the fixture defect in §2: the guard failed in a squashed clone with `could not read tasks.json at 5428c0a4`.)* |
| `guard_cost_census` | wall-clock of the others | no path |

**"Not found" is a statement about the search.** This is a reading of fifteen guard bodies in one
file plus five standalone guard scripts on **this tree**, at this commit. It does not close the
class for a guard added later — which is precisely why (k) measures against the pin instead of
listing paths.

---

## 7. What I could NOT close

1. **Server-side enforcement.** `reconcile-pushed-trees.sh` **detects** a `--no-verify` push one
   fire later; it cannot **prevent** one. Only a GitHub branch ruleset or a `pre-receive` hook on
   `origin` can, and both bind Gerege to a third-party configuration change on a live remote —
   outside a worker's grant, and arguably a `user` item. **Filed as a residual, not attempted.**
2. **The wiring has not run in a live fire.** Landed mid-run in the running wrapper; verified only
   by extraction-and-execution (§3). First real proof is the next fire's `pushgate|` and
   `reconcile|` log lines.
3. **The live host's snapshot is stale** (`--status` exits 1 today). Re-run the installer at
   merge.
4. **17 points of cheap-path coverage were NOT bought back surgically.** 88 % → 84 %. The 4-point
   loss is the `capture/`+`reviews/` exclusion, and it *could* be narrowed to just the 26
   `capture_ref`-cited records by deriving that set at gate time from the pushed tree (one
   `git grep` over `.softhouse/vectors`). I chose the blunt subtree exclusion because the money
   guard is the one that matters and 4 points is cheap; the derived version is a **stated
   follow-up**, with the measurement already in hand.
5. **Clause (k) covers the frontier's `removed` direction only**, which is the only direction an
   addition can move it *on this tree*. If a future guard resolves against the inventory in some
   other way, (k) will not see it. There is no detector for "a new guard's corpus now overlaps the
   STATE set"; the honest mitigation today is that the STATE set is small and the exclusions are
   subtree-shaped.
6. **`.softhouse/conformance.sh` was not touched** (T454 holds it). The cheap tier therefore still
   runs exactly one guard. The three inventory/read guards are handled by *excluding* their
   reachable deltas rather than by *running* them — sound, and less good than running them. Two of
   the three (`check-dead-path-frontier.sh`, `check-capture-namespace.sh`) are standalone and
   cheap (1–2 s each, per the cost census), so a future cheap tier could run them; the blocker is
   that `cheap-subset.sh` materialises its tree with `read-tree`+`checkout-index` and **not** as a
   real work tree, so `check-capture-namespace.sh`'s `git rev-parse --show-toplevel` would grade
   the caller's tree — the T165/T201 defect. Fixing that means giving the cheap subset a real
   scratch work tree, which is a design change, not a micro-fix. **Filed as FU-T453-1.**

---

## 8. Follow-ups

| id | what |
|---|---|
| **FU-T453-1** | Give `cheap-subset.sh` a real scratch work tree so the cheap tier can *run* `check-dead-path-frontier.sh` and `check-capture-namespace.sh` instead of excluding their inputs. Root readback is mandatory (T165/T201). |
| **FU-T453-2** | Derive the `provenance.capture_ref` set at gate time and narrow clause (h2) from "all of `capture/`" to "the cited records", recovering ~4 points of cheap-path coverage. |
| **FU-T453-3** | Server-side prevention of `--no-verify` (GitHub ruleset or `pre-receive`). Likely a `user` gate: it changes a live third-party configuration. |
| **FU-T453-4** | Re-run `install-driver-push-gate.sh` at merge; confirm `--status` exits 0 and the snapshot carries all four parts. |
