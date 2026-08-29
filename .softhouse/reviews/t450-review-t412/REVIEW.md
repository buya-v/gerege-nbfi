# T450 — independent review of T412 (`softhouse/T412-driver-selfgrading`, tip `52d7e5e8`)

**Reviewer** T450, own worktree, branch `softhouse/T450-review-t412`.
**Subject** the driver push gate: `.softhouse/hooks/driver-push-gate.sh`, `cheap-subset.sh`,
`bar-attest.sh`, `install-driver-push-gate.sh`, plus the two committed drives.
**Diff measured three-dot.** `git merge-base main softhouse/T412-driver-selfgrading` =
`b102875c`; `git diff --stat main...softhouse/T412-driver-selfgrading` = 33 files, 3,263
insertions, 0 deletions. No file outside `.softhouse/hooks/`,
`.softhouse/capture/t412-driver-selfgrading/` and `.softhouse/handoff/` is touched. Scope clean.

---

## VERDICT: **APPROVED WITH CONDITIONS**

The gate is real, installed, and working. I reproduced eight of its refusal/allow arms
independently, and it has now gated **three** real driver pushes (the author claimed two — the
ledger carries a third). Every headline claim I could falsify, I could not: the fourth instance is
true by tree identity, the 15-pushes-in-121-minutes census is exact, the bar is ~80 s and not
~4 min, the oracle-dependency argument that killed option A is true in the source, the snapshot is
byte-identical to the tracked gate, `bypass.log` does not exist, and the dead-path pin was
**repaired rather than grown** — it still reads 108 and the fail-open frontier still reads 11.

It does not get a clean APPROVED because of one thing, and it is the thing the author told me to
attack.

> **YES — I found STATE-set-confined changes that pass the cheap subset and redden the full bar.
> Three of them, each driven end to end, and one is a MONEY non-negotiable.**

In all three the gate printed `C3 PASS -- cheap subset clean`, wrote a **CHEAP attestation** —
an affirmative record that the tree was graded — and **allowed the push**; and the full bar on
that exact tree then went **EXIT 2 with `grep -c 'probe = '` == 0**. A fail-open wearing a green
label is worse than no gate, because it is believed (P-22).

---

## 1. The claims, re-derived

Every number below is mine, taken with my own instrument, then compared to the author's.

| # | author's claim | my measurement | verdict |
|---|---|---|---|
| 1 | `tree(2a1dac46)=617c9a85…` ≠ `tree(b102875c)=729cd8a0…` | `git rev-parse 2a1dac46^{tree} b102875c^{tree}` → `617c9a853924c28a24d9fba59ca1f083acbd0a38` / `729cd8a07c986a0ebb3244ee2e6e3f47f8e18cb1` | **TRUE.** And `b102875c`'s own message says *"graded on 2a1dac46 — the tree that is actually on main"*, at 10:01:33, six minutes after the 09:55:37 commit it names. Instance 4 is a fact, not a story. |
| 4 | 15 pushes in 121 min, fire `20260829-080002` | `git reflog show origin/main --date=iso`: 08:00:40 → 10:01:39, I count **15** ref moves | **EXACT.** |
| 4 | full bar is 76–80 s, not ~4 min | my run on a clean tree: **88 s** wall, EXIT 0 (T445 was running its own bar concurrently on this host) | **SUBSTANTIATED.** The task's own "~4 min" premise was wrong and the author was right to correct it. |
| 4 | option A rejected because the full bar **requires the reference oracle** | `main_grade()` (`conformance.sh:4800-4838`): `run_guards` runs **before** `probe_oracle`; on `probe != up` it warns *"conformance reports EXIT 2, not a false PASS, and 2 never becomes 0"*; `bar-attest.sh:102-138` requires probe PRESENT **and** `up` **and** `VERDICT: PASS` **and** exit 0 | **TRUE, and load-bearing.** Under option A an oracle outage would freeze every `tasks.json` / `RESUME.md` / LOCK write on `main`. The program's stop conditions say an outage stops *vector* work while analysis continues. The design reason survives review. |
| 6c | the frontier moved to 109 once and was repaired **by rewording, not by growing the pin**; pin still 11 | my clean-tree bar: `frontier 11, pinned at 11` … `frontier == pinned (all 11 rows, by path)`; `T316-DEADPATH-CENSUS: … deadOccurrences=108`, `dead-path frontier: GREEN`. And I ran a **full bar on a tree that is `main` tip + all four T412 hook scripts** (`bar-attest.sh` on my clone base): EXIT 0, 84 s, probe ×1 `up`, VERDICT PASS | **TRUE.** The five new scripts join neither frontier. Evidence `evidence/00-attest-base.log`. |
| 7 | `bypass.log` does not exist — zero bypasses | `ls /Users/buv/gerege-nbfi/.git/softhouse-driver-gate/` → `attest.tsv`, `attested-729cd8a0….log`. **No `bypass.log`.** | **TRUE.** |
| 9 | the install-time snapshot is byte-identical to the tracked gate (`8fc9d676…`) | `shasum -a 256` of the snapshot vs `git show softhouse/T412-driver-selfgrading:…`: `8fc9d676e850e45c707a7bd75855756b9c379ab2a7384a9be27f78fe66f2c5bc` **both**; `cheap-subset.sh` `34954ee0…` **both** | **TRUE.** |
| 3c | two live driver pushes gated | `.git/softhouse-driver-gate/attest.tsv` carries CHEAP rows for `4e7d678a` (02:30:10Z), `4e48b7e8` (02:39:00Z) **and `8a08f8f9` (02:46:55Z)** | **UNDERSTATED — there are three.** The third is the push that dispatched this review. |

### The write-path allowlist derivation

I did not re-run the 400-commit census, but the live evidence corroborates it: `git ls-tree -r`
over `main` today finds no mode-`160000` entry, and my own C2 arm shows the gate examining
50 non-merge commits of real `main` history and reporting `clean` — i.e. the allowlist does not
refuse anything the driver has actually done.

---

## FINDINGS

### M-1 — MAJOR — the STATE set admits ADDED and MODIFIED paths that redden three HARD guards, one of them a money non-negotiable

**The reasoning error, in one sentence.** The STATE-set table asks *"which files does each guard
READ?"*. Three guards do not answer that question: they resolve against the **tree's file
inventory** — *does this tracked path exist?* — so their verdict changes when a file is
**added**, whatever its extension. The author saw this exactly once and drew the right conclusion
for the wrong half: clause (j) excludes `D` and `R` because *"deleting a file that some tracked
`*.sh` names by literal GROWS the dead-path frontier"*. **Addition is the same mechanism running
backwards**, and it is admitted.

Setup for all three arms (`instruments/setup-clone.sh`): throwaway clone in `/tmp`, the gate
installed by its own installer (`sha256 8fc9d676e850e45c`, the same file the live host runs), and
a genuine `FULL` attestation for the base tree produced by `bar-attest.sh` — EXIT 0, probe ×1
`up`, VERDICT PASS 46/7884, 84 s (`evidence/00-attest-base.log`). Base commit `0d38d884`,
base tree `f7dc5b04b0c21cd778d97bad972029507d2c3d3e`.

#### M-1a — MONEY. `guard_no_float_in_capture_requests` — a float on the wire, pushed with a green label

`check_wire_float_roundtrip.py`'s **second arm** opens every file a stored vector names in
`provenance.capture_ref`. All 26 of those paths are `.softhouse/capture/**/*.json` — no `req`
segment, not under `vectors/`, `guards/`, `bin/`, `toolchain/` — so **every one of them is inside
the STATE set**:

```
$ git grep -h -E '"capture_ref"' -- .softhouse/vectors | sed -E 's/.*"capture_ref"[^"]*"([^"]*)".*/\1/' | sort -u
.softhouse/capture/out/capture-prod3b-raw.json
… 26 paths, all .softhouse/capture/**/*.json
```

**Reproduction** (`instruments/drive-stateset.sh`, arm A; planter `instruments/plantA.py`):

1. In the clone, insert into a recorded-request block of a cited capture record a money token that
   does not survive a binary-double round trip:
   `"principalOnWire": 12345678901234567890.12` in `$.captures[0].inputs` of
   `.softhouse/capture/out/capture-prod3b-raw.json`.
2. Commit. Delta from the attested base is exactly `M .softhouse/capture/out/capture-prod3b-raw.json`.
3. `git push bare HEAD:refs/heads/main`.

**The gate's verdict** (`evidence/A-push.txt`):

```
driver-push-gate:   C3 delta from the graded ancestor is confined to the STATE set. Running the cheap subset
cheap-subset: PASS -- 0 fatal citation findings in the DIRECTIVE zone of tree 1b0b6a89…
driver-push-gate:   C3 PASS -- cheap subset clean; CHEAP attestation recorded for 1b0b6a89…
driver-push-gate: PUSH ALLOWED.
PUSH_RC=0
```

**The full bar on that same tree** (`evidence/A-fullbar.txt`, transcript `evidence/A-refused-bar.log`):

```
$ grep -c 'probe = ' A-refused-bar.log
0
conformance: the wire-float round-trip guard REFUSED:
REFUSED — a numeric token in a RECORDED REQUEST inside a cited capture record is NOT byte-preserved
under a binary-double round trip. This is the request that produced a promoted parity vector: the
money the reference oracle was asked about is not the money the record says it was asked about.
  .softhouse/capture/out/capture-prod3b-raw.json:82  $.captures[0].inputs.principalOnWire
  12345678901234567890.12  ->  1.2345678901234567e+19
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
BAR_ATTEST_RC=1 WALL=81
```

That is the first CLAUDE.md non-negotiable — *no floating point in any monetary path, including
intermediate calculation* — going red on a change this gate approved and recorded as graded.
The census line moved from `float-shaped PRESENT 0, ALTERED 0` to
`float-shaped PRESENT 1, ALTERED 1`.

The task asked specifically whether `guard_no_float_in_vectors` is reachable from a `.json` under
`.softhouse/`. **It is not** — its corpus is `find "$STORE_ROOT" -name '*.json'` with
`STORE_ROOT="$REPO_ROOT/.softhouse/vectors"` (`conformance.sh:400,842`), and `.softhouse/vectors/**`
is excluded. The author is right about that guard. The money hole is in its neighbour.

#### M-1b — `guard_dead_path_frontier` — one added `.txt` shrinks the frontier and the bar refuses

**9 of the 108 pinned dead-path literals are inside the STATE set** (`evidence/00-deadpath-pin-literals.txt`),
including `.softhouse/uat.md` — which is not an adversarial choice at all: `.claude/skills/softhouse-uat`
resolves the UAT definition from that exact path, so a driver creating it is ordinary work.

**Reproduction** (arm B): add `.softhouse/capture/t290-second-rig/note.txt`, a path two pinned
instruments name by literal. Delta: `A .softhouse/capture/t290-second-rig/note.txt`.

* gate (`evidence/B-push.txt`): `C3 PASS -- cheap subset clean` … `PUSH ALLOWED.` `PUSH_RC=0`
* full bar (`evidence/B-refused-bar.log`): `grep -c 'probe = '` → **0**

```
T316-DEADPATH-FRONTIER: REFUSED rows=106 pinned=108 added=0 removed=2
conformance: guard_dead_path_frontier FAILED. Full guard transcript above.
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
```

The guard is explicit that a *shrink* is a refusal — *"a frontier, not an amnesty"* — precisely so
the pin is folded in the same commit. A gate-approved push cannot do that.

#### M-1c — `guard_capture_namespace` — one added `.md` creates an undocumented namespace collision

The rule: *a task id that prefixes MORE THAN ONE directory must carry an `OWNER*.md` at the top
level of each*. `.softhouse/capture/t305-openingbalance-accepting-side/` exists; adding a second
`t305-` directory is a single `A` of a `.md` under `.softhouse/`.

**Honest negative first.** My first attempt at this arm used `t412-` and **passed** the bar
(`evidence/C-fullbar.txt`, `ATTESTED FULL`) — because `t412-driver-selfgrading` is not on `main`
yet, so there was no collision. My probe was wrong, not the guard. Recorded rather than deleted.

**Reproduction** (`instruments/drive-armC2.sh`): add `.softhouse/capture/t305-second-directory/note.md`.
Delta: `A .softhouse/capture/t305-second-directory/note.md`.

* gate (`evidence/C2-push.txt`): `C3 PASS -- cheap subset clean` … `PUSH ALLOWED.` `PUSH_RC=0`
* full bar (`evidence/C2-refused-bar.log`): `grep -c 'probe = '` → **0**

```
conformance: guard_capture_namespace FAILED (rc=1). Full transcript above.
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
bar-attest: probe lines PRINTED: 0
BAR_ATTEST_RC=1 WALL=65
```

This one is the least theoretical of the three: the driver writes `.softhouse/capture` in 27 of
its last 400 commits, and the guard exists *because a task was renumbered by an orchestrator*
(P-85/P-86) — a driver failure mode, guarded by a guard the driver's own push path skips.

#### The rest of the corpus — the census the author called reasoning, done as measurement

15 guards run in `run_guards`. The cheap tier runs **one**. For the other fourteen:

| guard | corpus / resolution | reachable from the STATE set? |
|---|---|---|
| `guard_graded_root_is_this_tree` | the run's own root | no |
| `guard_no_float_in_vectors` | `find $STORE_ROOT -name '*.json'`, `STORE_ROOT=.softhouse/vectors` | **no** — author correct |
| `guard_no_float_in_harness` | `nexus/**.go` | no (**omitted from the author's table**) |
| `guard_gofmt` | `nexus/` | no |
| **`guard_no_float_in_capture_requests`** | 2nd arm opens `provenance.capture_ref` targets: 26 × `.softhouse/capture/**/*.json` | **YES — MEASURED RED (M-1a). MONEY.** |
| `guard_no_narrow_catch_in_capture_rigs` | tracked `*.java` | no (**omitted from the author's table**) |
| `guard_ledger_invariants` | Go / SQL | no |
| `guard_no_fail_open_instruments` | classifies tracked `*.sh`/`*.py`, but **C1/C6 decide TIER by `os.path.exists` on a resolved literal** — the guard's own T273 commentary records the tier flipping on a file's presence with the tree unchanged | **plausibly yes; not driven by me.** Stated as reasoning, not measurement — the same status the author gave his whole table. |
| `guard_no_host_state_in_lint_corpus` | tracked `*.sh`/`*.py`, pinned by path+line | no |
| `guard_pnumber_citations` | this **is** the cheap tier | n/a |
| `guard_accepting_side_gap_declared` | `.softhouse/vectors/ledger`, `.softhouse/vectors/capabilities-ledger.json`, `git ls-files '.softhouse/capture/*/attest/*.disposable'` | **no** — author correct; `.disposable` is outside the extension set |
| **`guard_capture_namespace`** | `git ls-files`, directory-name collisions + `OWNER*.md` | **YES — MEASURED RED (M-1c)** |
| **`guard_dead_path_frontier`** | classifies `*.sh`/`*.py` literals, **resolves against the tracked universe** | **YES — MEASURED RED (M-1b)** |
| `guard_reconciler_ownership` | its own matrix over `.softhouse/bin/ready-tasks.py` | no |
| `guard_cost_census` | timings | no |

Beyond the guards, the cheap tier also skips **46 parity vectors, `go build`, `go test`,
`gate_exemption_census` and `gate_wrong_ledger_impls_die`** — none of them reachable from the
STATE set as written, so those exclusions hold.

#### On `patterns.md` — the attack the task suggested, and why it does not open a gap

`.softhouse/patterns.md` is `.md` under `.softhouse/`, so an `M` on it is inside the STATE set. But
the cheap subset **is** the P-number citation checker, and deleting a definition thousands of
sites cite makes those citations UNDEFINED. Where they sit in a DIRECTIVE file the cheap tier is
fatal — I drove exactly this (arm R6, an undefined `P-150` in `RESUME.md`) and the gate refused.
Where they sit in the evidence or orchestrator zones the checker is report-only — **in the full
bar too**, by its own tiering, so the cheap tier is not weaker than the bar there. A **deletion**
of `patterns.md` itself takes the full bar; I drove that too (arm R7, `git rm` of a state `.md`
→ `C3 REFUSED`). **This attack fails. The author's design holds on the case the task nominated.**

#### The fix, and why it is cheap

State it as the author stated clause (j), symmetrically: *an ADDITION changes the tree's
inventory, and three HARD guards resolve against the inventory.* Minimum sufficient narrowing:

1. **Exclude `.softhouse/capture/**` from the STATE set outright.** That closes M-1a and M-1c and
   most of M-1b in one clause. Cost: 27 of 400 driver commits move to the full bar.
2. **Admit `A` only for a named set** of driver bookkeeping paths (`tasks.json`, `LOCK`,
   `RESUME.md`, `program.json`, `gates.md`, `.softhouse/state/**`, `.softhouse/observations/**`,
   `.softhouse/reviews/**`), and treat every other `A` like a `D`.
3. Re-drive arms A, B and C2 as **refusals**. They are in `instruments/` and re-runnable.

---

### M-2 — MAJOR — nothing installs the gate, and nothing notices when it is missing

`.git/hooks/` is not tracked. The gate exists on this host because someone ran the installer once,
at 10:29:12. Where I looked, and what I found:

```
$ grep -rn 'install-driver-push-gate\|driver-push-gate\|softhouse-t412-gate' \
    --include='*.sh' --include='*.py' --include='*.md' --include='*.json' . \
  | grep -v '^./.softhouse/capture/t412' | grep -v '^./.softhouse/handoff/T412' \
  | grep -v '^./.softhouse/hooks/'
(no output)
```

That sweep covers `.softhouse/bin/fire-program.sh` (222 KB, 0 hits for `hooks` or `pre-push`),
`.claude/skills/softhouse-program/SKILL.md`, `docs/`, `patterns.md`, `conformance.sh` and every
tracked instrument. **Outside its own files, nothing in this repository knows the gate exists.**

Consequences, each of which is the P-45 shape one level up from the gate:

* a **fresh clone** — the cloud fire, CI, a rebuilt host — has no gate, and says nothing about it;
* a `git init`-fresh `.git/hooks`, a `core.hooksPath` set later, or a manual `rm` disables it
  silently (the installer refuses to install *under* `core.hooksPath`, but nothing re-checks);
* no bar guard asserts `pre-push` is present and is this gate, so a green bar is compatible with
  an ungated `main`.

The author's residual 4 frames this as *"origin cannot enforce this"*. That is a different and
weaker statement. The sharper one is: **this control is not installed by the program, it is
installed by hand, and its absence is silent.** Seven guards wired to nothing are already logged
in this program; this is the eighth shape, at the installation layer rather than the call layer.

**Fix:** call `install-driver-push-gate.sh --status` (and install on absence) from
`fire-program.sh` at fire start, beside the identity/sha256 banner it already prints; and add a
tracked instrument that fails when the hook is absent or is not this gate. The author deliberately
did not touch `fire-program.sh` mid-fire (T301) — correct at the time, and it is why this is a
condition on the next task rather than a rejection of this one.

---

### m-3 — MINOR — `--no-verify` walks past the one check that has no bypass, and nothing reconciles afterwards

Driven, not argued (`instruments/drive-refusals.sh` arm R9, `evidence/R9-no-verify.txt`):

```
$ git push --no-verify bare HEAD:refs/heads/main
 * [new branch]        HEAD -> main
PUSH_RC=0
--- gate output present? ---   0        <-- zero lines from the gate. It never ran.
--- does the pushed tree carry a gitlink? ---
160000 commit 0d38d884716a2c87f9c5f995bd4421eb0bea36c0	strayworktree
```

A **gitlink** — instance 3, the one check the author correctly gave no bypass — landed on
`refs/heads/main` with the gate silent.

**Judgement, since the task asked for it.** A client-side gate on an actor that is an LLM agent is
*necessary and not sufficient*, and the specific reason is in this program's own record: the
driver reproduced instance 1 *within minutes of reading a report describing it*. `--no-verify` is
a plausible next token for an agent whose push was refused and whose task says "keep the migration
advancing". The honour system is defensible for the **bypass** — it demands a 12-char reason,
prints a banner and appends to a ledger, and I confirmed both legs (arm R4 logged; arm R5 refused
a 2-char reason) — but an honour system with **no reader** is only half a control. Nothing today
reads `bypass.log`, and nothing detects a `--no-verify`.

So **FU-T412-4 (the reflog reconciler) should be built now, not filed.** It is the cheapest thing
in the whole design — walk `git reflog show origin/main`, report every pushed tree with no ledger
row — and it is what converts this gate from *trusted* to *auditable*. FU-T412-3 (a `pre-receive`
hook in `origin`) is the stronger answer and the author's reason for not building it blind is
sound.

---

### m-4 — MINOR — the gate's refusal names a command that does not exist on the host it prints on

Both C3 refusal paths tell the driver:

```
      bash .softhouse/hooks/bar-attest.sh <sha>
```

On the live host today, `/Users/buv/gerege-nbfi/.softhouse/hooks/` contains only `README.md` and
`push-before-spawn-audit.py`. `bar-attest.sh` is **not** in the install-time snapshot either — the
installer copies only `driver-push-gate.sh` and `cheap-subset.sh`
(`install-driver-push-gate.sh:111-113`), while checking for all three at `:102-104`. So a driver
refused right now is handed an instruction it cannot execute, from the shared hooks directory,
with no other path offered. The gate is fail-**closed**, which is right; but a refusal whose remedy
does not resolve is how a driver reaches for `--no-verify` (m-3).

**Fix:** snapshot `bar-attest.sh` too, and print the path the gate would actually run.

---

### m-5 — MINOR — post-merge the enforcing gate becomes an unversioned working-tree file

The shim prefers `/Users/buv/gerege-nbfi/.softhouse/hooks/driver-push-gate.sh` — the **main
checkout's working tree**, not a committed blob. Once T412 merges, enforcement is whatever is on
disk there: an uncommitted edit, a stale checkout, or a different branch checked out in the main
worktree all change what the gate does with no commit recording it. The shim prints the file's
`sha256` on every run, which is good discipline, but nothing **compares** that sha to anything, so
the print is evidence only for a human who happens to read a push transcript.

Editing the tracked `.softhouse/hooks/*.sh` and *pushing* it does take the full bar (`.sh` is
outside the STATE set — arm 11 of the author's drive and my arm R7's sibling), so the committed
form is protected. The uncommitted form is not.

**Fix:** have the shim (or a fire-start check) compare the resolved gate's sha256 against
`git show HEAD:.softhouse/hooks/driver-push-gate.sh | shasum -a 256` and refuse on divergence.

---

### L-6 — LOW — C1 inspects only the tip tree, not every commit in the pushed range

`git ls-tree -r "$LSHA"` is run once, on the ref tip. A gitlink introduced and removed **within a
single push range** is in the pushed history and in no C1 check. Instance 3 spanned two pushes
(`8c08f8f7` → `c31b0842`), so C1 would have caught it; C2 catches the historical case only when
the gitlink path is outside `.softhouse/`/`docs/`/`.claude/` — and C2 is bypassable. Low, because
the tip tree is what ships, but the check is narrower than its own banner implies.

### L-7 — LOW — `state_path`'s second `case` block is unreachable; the code does not mean what the comment says

In bash `case`, `*` crosses `/`. `.softhouse/*.md` at `driver-push-gate.sh:143` therefore already
matches `.softhouse/capture/out/x.md` at any depth, so the `.softhouse/*/*` fall-through at `:144`
and the second `case` at `:147-150` can only ever reach their `return 1` arm. Behaviour is correct;
the structure suggests a depth distinction that does not exist, and the next editor will believe it.

### L-8 — LOW — the STATE-set table is not a complete census

`guard_no_float_in_harness` and `guard_no_narrow_catch_in_capture_rigs` appear in no row of the
table that claims to name *"the guard each exclusion is there for"*. Both are in fact unreachable,
so nothing is wrong today — but a table that is missing two of fourteen entries cannot be used to
argue that the remaining twelve are complete, which is exactly the argument it is asked to carry.
FU-T412-2 (a guard asserting no guard's corpus selector reaches a STATE-set path) is the right
answer and should be scoped to *resolution*, not only *corpus*, or it will miss M-1b and M-1c.

---

## 2. What I drove, and what it proves

### 2a. The gate refuses what it claims — 8/8 arms, my clone, my harness

`instruments/drive-refusals.sh` (+ `drive-r5.sh`). Every arm asserts **both** the exit code **and**
a string the gate itself printed — the author's own run-1 lesson, and it earned its keep
immediately (below).

| arm | expectation | marker asserted | result |
|---|---|---|---|
| R1 gitlink in the tree | refuse | `C1 REFUSED -- THE PUSHED TREE CONTAINS A GITLINK` | PASS |
| R2 same push, 40-char bypass reason | still refuse | `THERE IS NO BYPASS FOR C1` | PASS |
| R3 `nexus/**.go` in a non-merge commit | refuse | `C2 REFUSED -- a NON-MERGE commit` | PASS |
| R4 same push, valid bypass | allow **and log** | `BYPASSED: C2 allowlist` | PASS |
| R5 same push, reason `"ok"` | refuse | `C2 REFUSED -- a NON-MERGE commit` | PASS |
| R6 `P-150` in `RESUME.md` (instance 1) | refuse | `C3 REFUSED -- THE CHEAP SUBSET FAILED ON THE PUSHED TREE` | PASS |
| R7 delete a state `.md` | refuse | `C3 REFUSED -- THE PUSHED TREE WAS NEVER GRADED` | PASS |
| **R8 an honest state-only edit** | **allow** | `C3 PASS -- cheap subset clean` | **PASS** |
| R9 gitlink with `--no-verify` | — | gate output lines: **0** | see m-3 |

**R8 is the arm that matters most after M-1.** A gate that refuses everything is as broken as one
that refuses nothing (P-98), and this one lets honest work through — R8 plus my three M-1 pushes
plus **three real driver pushes on the live host**, all allowed, all cheap-path, ~27 s each.

**My own harness reproduced the author's run-1 defect, and the marker caught it.** My first R5
returned `rc=0` — because R4's bypass had already advanced the bare ref, so git sent nothing and
the gate printed *"no update to refs/heads/main in this push"*. An exit code alone would have
recorded a false PASS; the missing marker recorded a `***FAIL***`. Both transcripts are kept
(`evidence/00-refusal-arms-summary.txt` shows the failing run; `evidence/R5-short-bypass-rerun.txt`
the correct one). The author's fix is not decorative — it is the only thing that separates
*allowed* from *never asked*.

`evidence/bypass.log` shows the recorded form: one reason, logged twice (C2 and C3) for one push,
with timestamp, check, sha and reason. Correct.

### 2b. The live installed hook

I did **not** touch `/Users/buv/gerege-nbfi/.git/hooks/pre-push`. All drives ran in throwaway
clones under `/tmp` with their own bare remotes; `origin` was never a push target. Read-only
inspection only:

* the shim is present, dated 10:29, and is this gate's (`softhouse-t412-driver-push-gate`);
* the snapshot matches the tracked branch files byte for byte;
* `attest.tsv` carries 1 FULL + 6 CHEAP rows, three of them real driver pushes;
* `bypass.log` is absent.

---

## 3. The bar, from a clean tree

`bash .softhouse/conformance.sh`, scratch in `/tmp` outside the repo,
`git status --porcelain` **empty** before the run.

**PRESENCE BEFORE VALUE**, in that order — four exit-2 paths run before the probe prints:

```
$ grep -c 'probe = ' bar.log
1                                    <-- PRINTED AT ALL. Absence is not `down` (P-84).

$ grep -n 'probe = ' bar.log
203:conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up

$ grep -n '^VERDICT' bar.log
818:VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.

EXIT=0
WALL_SECONDS=88
```

Frontiers, both unmoved:

```
T316-DEADPATH-CENSUS: corpus=1530 deadFiles=75 deadOccurrences=108 resolving=1445 indeterminate=117 prose=388
  dead-path frontier: GREEN, and the T323 reconciliation list is empty.
CENSUS fail-open instruments — … frontier 11, pinned at 11
  frontier == pinned (all 11 rows, by path).
GUARD-COST CENSUS: 15 guards timed, … ceiling breaches 0, unbudgeted guards 0.
```

`deadOccurrences` is **108**, unchanged; the fail-open frontier is **11**, unchanged. Full
transcript `evidence/00-BAR-on-clean-tree-run1.log`.

---

## 4. CONDITIONS

| id | severity | condition | evidence |
|---|---|---|---|
| **C-T450-1** | **MAJOR** | Narrow the STATE set so an `A` is treated like a `D` except for a named set of driver bookkeeping paths, and exclude `.softhouse/capture/**` outright. Re-drive arms A, B and C2 as **refusals**. | `evidence/A-*`, `evidence/B-*`, `evidence/C2-*`; `instruments/drive-stateset.sh`, `instruments/drive-armC2.sh` |
| **C-T450-2** | **MAJOR** | Make installation enforced, not manual: install/verify from `fire-program.sh` at fire start, and add a tracked instrument that fails when `pre-push` is absent or is not this gate. | §M-2 grep, `.softhouse/bin/fire-program.sh` (0 hits) |
| **C-T450-3** | MINOR | Build FU-T412-4 (reflog reconciler: every pushed tree with no ledger row is reported) now, and give `bypass.log` a reader. | `evidence/R9-no-verify.txt` |
| **C-T450-4** | MINOR | Snapshot `bar-attest.sh` with the other two, and make the C3 refusal name a path that resolves on the host it prints on. | `install-driver-push-gate.sh:102-113`; `ls /Users/buv/gerege-nbfi/.softhouse/hooks/` |
| **C-T450-5** | MINOR | Have the shim compare the resolved gate's sha256 against the committed blob and refuse on divergence. | §m-5 |
| **C-T450-6** | LOW | Scan every commit in the pushed range for gitlinks, not only the tip tree. | §L-6 |
| **C-T450-7** | LOW | Simplify `state_path` so its structure matches its comment; add the two missing guards to the STATE-set table. | `driver-push-gate.sh:136-151`; §L-8 |

**Not conditions, recorded as correct:** the merge exemption in C2 (a merge always leaves the
STATE set, so C3 forces a full bar on it anyway); the ledger living outside every tree; the
private-index materialisation instead of `git worktree add` inside a hook; the ≥100-file corpus
floor (P-35); `grep -c 'probe = '` before its value everywhere it is read; and the decision to run
the subset from `dirname $0` rather than the pushing worktree, which the clone drive structurally
could not have found.

---

## 5. Summary for the driver

The gate is worth having and is already earning its keep — three real driver pushes gated, the
instance-1 code path proven live, eight refusal shapes reproduced independently, honest work still
flowing at 27 s a push, and zero bypasses taken. Its cost argument is sound and its rejection of
option A rests on a true fact about the bar, which I checked in the source.

But **C3's cheap path issues a green verdict and a written attestation for trees the full bar
refuses outright**, including on the money non-negotiable, and it does so for changes the driver
plausibly makes — creating a capture directory, adding `.softhouse/uat.md`, touching a capture
record. Until C-T450-1 lands, `C3 PASS -- cheap subset clean` must not be read as *"this tree
would pass the bar"*, and nothing may cite this gate as the bar.

---

## 6. Bar re-run after committing this review

Run again on the committed, clean `softhouse/T450-review-t412` tree — because M-1b is a finding
about *added files moving a frontier*, and this review adds 45 of them.
`evidence/00-BAR-on-committed-tree-run2.log`:

```
$ grep -c 'probe = ' bar.log
1
$ grep -n 'probe = ' bar.log
203:conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
$ grep -n '^VERDICT' bar.log
818:VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
EXIT=0
WALL_SECONDS=55

T316-DEADPATH-CENSUS: corpus=1540 deadFiles=75 deadOccurrences=108 resolving=1446 indeterminate=117 prose=388
CENSUS fail-open instruments — … frontier 11, pinned at 11
  frontier == pinned (all 11 rows, by path).
```

`git status --porcelain` empty before and after. The corpus grew 1530 → 1540 (this review's ten
instruments); `deadOccurrences` is still **108** and the fail-open frontier is still **11**.

**Two bar timings, and the difference is informative:** 88 s while T445 was running its own bar on
this host, **55 s** with the host quiet. The author's 76–80 s sits between them. The task brief's
"~4 minutes" is wrong by a factor of three to four, and the author was right to correct it before
pricing the design against it.
