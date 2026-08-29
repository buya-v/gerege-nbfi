# T412 — the driver pushes to `main` without ever running the bar on its own commits

**Branch** `softhouse/T412-driver-selfgrading`
**Verdict** a `pre-push` gate is **built, INSTALLED, and has already graded a real driver push in the wild.**

---

## 0. The four instances, and the fourth verified rather than believed

The brief listed three recorded instances and asserted a fourth from this fire. I verified the
fourth myself, by tree identity, because that is the only form of the claim that cannot be argued
with:

```
tree(2a1dac46, the commit the driver GRADED)   = 617c9a853924c28a24d9fba59ca1f083acbd0a38
tree(b102875c, the commit the driver PUSHED)   = 729cd8a07c986a0ebb3244ee2e6e3f47f8e18cb1
                                                  DIFFERENT
```

`b102875c`'s own commit message says *"Bar on main at dispatch: EXIT 0 … graded on 2a1dac46 — the
tree that is actually on main."* That sentence stopped being true at the instant it was written.
The bar ran at 09:55-ish on `617c9a85`; the commit landed at 10:01:33 with tree `729cd8a0` and was
pushed at 10:01:39. Nothing measured the difference.

I also checked instance 3's fingerprint across history:
`git ls-tree -r` over the last 400 non-merge first-parent commits on `main` finds a mode-`160000`
entry exactly once — `160000 commit af397c6bec0bbd490c9d270a1520fad9b523aa75  main`, at `8c08f7d8`,
removed at `c31b0842`. Current `main` is clean.

---

## 1. The design, and the two options I rejected with numbers

### The measurement the decision rests on

Fire `20260829-080002`, **08:00:40 → 10:01:39 = 121 minutes**, from
`git reflog show origin/main` (the remote-tracking ref moves once per successful push, which is a
better census than grepping the driver's transcript for `git push` — the transcript only carried
one of them):

| quantity | measured |
|---|---|
| pushes to `origin/main` | **15** (one every ~8 min) |
| push *ranges* classified | 14 |
| ranges carrying a merge | **6** |
| state-only ranges (no merge) | **8** |
| ranges with a gitlink anywhere in the tree | 0 |
| ranges whose **merge** commits touch `nexus/` Go source | **3 of 6** |
| non-merge commits in those ranges touching anything outside `.softhouse/` | **0 of 19** |
| full bar, this host, this tree, warm | **76 s** wall (guard budget 65 s of it); the `main` attestation run measured ~90 s |
| citation checker, standalone, on the real 9,730-file tree | **24.98 s** (5.12 materialise + 0.24 selftest + 19.62 graded) |
| cheap path end-to-end, **through the installed hook, live** | **27 s** |

### Option A — full bar before every push. REJECTED — **and not primarily on cost.**

The cost is real but survivable, and I want to be straight about that rather than inflate it. The
brief priced the bar at "~4 minutes"; **measured on this host on this tree it is 76 s wall** (65 s
of that the guard budget), and the `main` attestation run took ~90 s. So option A costs
15 × 76 s ≈ **19 minutes of a 121-minute fire — about 16 %.** Expensive, not prohibitive. If cost
were the only objection I would have taken option A.

**The decisive objection is that the full bar REQUIRES THE REFERENCE ORACLE, and the driver's
ability to record state must not.** The bar's verdict line is
`46 parity vectors match the pinned reference oracle`, and it will not reach `EXIT 0` with
`probe = up` when Fineract is unreachable — `bar-attest.sh` refuses to attest in exactly that case,
by design. Wiring the full bar into every driver push would therefore make an oracle outage freeze
`main` **completely**: no `tasks.json` update, no `RESUME.md` checkpoint, no `gates.md` entry, no
LOCK release. That directly contradicts the program's own stop conditions, which say an unreachable
oracle stops *vector work* while "analysis/spec tasks continue" — and it would take the driver's
crash-recovery record down with it, which is the one thing that must survive an outage.

The cheap subset has **no oracle dependency at all**: it is `/usr/bin/python3` over a materialised
tree. Under the adopted design an outage degrades exactly as it should — state pushes keep flowing
on the cheap path, and merge pushes correctly wait for a bar that cannot honestly pass yet.

Two lesser objections, recorded because they also hold: the driver commits state many times per fire
while nine workers hold the very files a bar reads, so a bar over the driver's **working tree**
would be grading other agents' scratch (the gate closes that separately — §2, "the pushed tree");
and 8 of this fire's 14 push-ranges differ from an already-graded tree by one or two `.json`/`.md`
files, where a 46-vector oracle comparison cannot change its answer.

### Option B — run only the guards whose INPUTS the commit touched. REJECTED AS BUILT, ADOPTED AS SHAPE.

The brief's example — *`RESUME.md` and `patterns.md` changed ⇒ run `guard_pnumber_citations`* — is
the right instinct and unbuildable this wave, for a reason I could not engineer around:

* `run_guards` is a **function inside `.softhouse/conformance.sh`**. There is no `--guards-only`
  entry point, and sourcing the file executes the whole bar. `conformance.sh` is held by T445 this
  wave and I may not edit it, so I cannot add one.
* Reimplementing fifteen guard bodies in a second file is a second copy of a rule that will
  diverge from the first the moment either is edited, and nothing would report the divergence —
  fifteen times over.

So I adopted the **shape** and bounded it honestly: the cheap tier is exactly the guards that
already exist as standalone invocable programs, which today is **one** — the P-number citation
checker — and I state the residual rather than dressing it up (§4).

### Option C — ADOPTED. A `pre-push` gate with three checks and an anchored cheap path.

```
C1  GITLINK REFUSAL            no mode-160000 entry anywhere in the pushed tree.   NO BYPASS.
C2  DRIVER WRITE-PATH ALLOWLIST every path of every NON-MERGE commit in the pushed
                               range must be under .softhouse/, docs/ or .claude/.
C3  GRADE IDENTITY             the tree BEING PUSHED must be attested, or differ from
                               an attested ancestor only inside the STATE set — in which
                               case the cheap subset is run on the PUSHED tree.
```

Engages **only** for remote ref `refs/heads/main`; stands aside, loudly, for everything else.

**Measured cost of C on this fire, had it been installed at 08:00:**
8 state-only pushes × 27 s = **216 s ≈ 3.6 minutes across the whole fire**, plus 6 merge pushes
needing a FULL attestation — of which the driver already ran a bar for roughly 4, so ≈ 2 extra bar
runs ≈ 152 s. Total ≈ **6 minutes, or 5 % of the fire**, against option A's 19 minutes — and,
unlike option A, it keeps working when the reference oracle does not.

### Why the allowlist exempts merges — and why that is not a hole

Derived, not chosen. Over the **last 400 non-merge first-parent commits on `main`** the driver's
entire write set is:

```
231 .softhouse/tasks.json   122 .softhouse/LOCK     88 .softhouse/RESUME.md   43 .softhouse/reviews
 31 .softhouse/program.json  27 .softhouse/capture   21 .softhouse/patterns.md 19 .softhouse/observations
 17 .softhouse/state         15 .softhouse/gates.md   4 .softhouse/bin          3 .softhouse/conformance.sh
  2 .softhouse/reference-oracle.md   2 .softhouse/handoff   1 docs/adr   1 .claude/skills
  2 main            <-- INSTANCE 3. The gitlink, added at 8c08f7d8 and removed at c31b0842.
```

**The only top-level entry in 400 commits that is not `.softhouse/`, `docs/` or `.claude/` is the
defect itself.** So the allowlist refuses exactly what has gone wrong and nothing that has ever
gone right.

Merge commits are a different animal: 3 of this fire's 6 merge ranges carry
`nexus/internal/apps/ledger/conformance/*.go` and similar, lawfully — a merge brings a worker's
whole branch, and *that branch ran the full bar before handoff*. Applying the allowlist to merges
would have refused half this fire's merges. C2 is therefore scoped to single-parent commits, which
is precisely "the driver's own writing".

---

## 2. What the gate actually checks, and the trap in each

### C1 — gitlink, no bypass

`git ls-tree -r <pushed-sha>` into a **file** (P-57: no pipeline, so a `git` failure cannot be
laundered into "no gitlinks"), a zero-line listing REFUSES rather than passing, then `awk` for mode
`160000`. This is the only check with no escape hatch, and the argument is measured: one occurrence
in 400 commits, and it was the defect. False-positive cost zero.

### C2 — write-path allowlist

Every changed path of every non-merge commit in `<remote>..<local>`. If the remote has no readable
tip the range degrades to the last 50 commits of the pushed sha — **never to "no commits"**, which
would pass everything.

### C3 — grade identity, and **the pushed tree, never the working tree**

This is instance 2's mechanical closure. The gate resolves `<local-sha>^{tree}` and:

1. **tree attested FULL** → allow. (`bar-attest.sh` put it there.)
2. **tree carries a CHEAP row already** → allow; the subset is deterministic over a tree.
3. otherwise walk up to 400 ancestors for the newest FULL-attested tree.
   * none → **REFUSE**, naming the command.
   * found → `git diff --name-status <base> <local>`; if every entry is `A` or `M` **and** every
     path is in the STATE set → run the cheap subset **on the materialised pushed tree**, and on
     PASS record a CHEAP row.
   * otherwise → **REFUSE**, naming the command.

The subset materialises the tree with `git read-tree` + `git checkout-index` into a **private
index** under `$TMPDIR` — not `git worktree add`, because this runs inside a hook that fires while
nine workers hold worktrees off the same common dir, and a hook has no business mutating the shared
worktree registry. It then refuses if the materialised index lists fewer than 100 files, because an
empty corpus passes everything (P-35).

### The STATE set, and the guard each exclusion is there for

A path is STATE only if the **fourteen guards the cheap subset does not run cannot read it**:

| clause | there for |
|---|---|
| `.softhouse/` only | `guard_gofmt`, `guard_ledger_invariants`, every parity vector |
| never `.softhouse/vectors/**` | `guard_no_float_in_vectors`, `guard_accepting_side_gap_declared` |
| never `.softhouse/guards/**` | `guard_guards_dir_registration`, the dead-path pin |
| never `.softhouse/bin/**` | `guard_reconciler_ownership` (it runs a matrix over `ready-tasks.py`) |
| never `.softhouse/toolchain/**` | untracked build root — T326's recorded frontier trap |
| never `.softhouse/conformance.sh` | changing the grader is never a state edit |
| extension ∈ `md txt json log` only | `guard_no_fail_open_instruments`, `guard_dead_path_frontier` and `guard_no_host_state_in_lint_corpus` **all** select over tracked `*.sh` / `*.py`; excluding those two extensions removes three corpora at once |
| no path segment `req` | `guard_no_float_in_capture_requests` takes every `*.json` whose **direct parent** is `req`, plus every `*.req` |
| `.softhouse/LOCK` by name | it has no extension |
| **`A` and `M` only — never `D` or `R`** | a DELETION reddens guards whose corpus it never appears in: removing a file some tracked `*.sh` names by literal **grows the dead-path frontier**; removing a `req/` json **lowers a derived float floor**; removing one of the two calibration directories makes `guard_capture_namespace`'s P-72 calibration lapse into a pass |

That last row is the one I would defend hardest. It is the difference between a delta-based subset
that is sound and one that only looks sound.

### The bypass, and why C1 is outside it

`SOFTHOUSE_DRIVER_GATE_BYPASS="<reason, ≥12 chars>"` is honoured for **C2 and C3 only**. It prints a
banner and appends `timestamp / check / sha / reason` to `$(git rev-parse --git-common-dir)/softhouse-driver-gate/bypass.log`, so
*"how often did the driver bypass this"* is a countable fact for the next reviewer rather than an
impression. A gate with no exit is a gate somebody deletes; a gate whose exit leaves no trace is a
hole. Driven both ways — arm 9 (bypass honoured and logged) and arm 10 (a 2-character reason is not
a bypass).

### Why the ledger is not a tracked file

An attestation says *"tree T was graded"*. If the ledger were tracked, writing the row would change
the tree, so the recorded tree could never be the tree that ships — **instance 2 rebuilt as a data
structure**. It lives under the git common dir, in no commit, deliberately host state: a record of
what *this machine* ran. A fresh clone that has graded nothing is told so rather than inheriting a
claim.

---

## 3. The drives — RED first, then GREEN, both committed

### 3a. Gate logic, throwaway clone: **13/13 arms**
`.softhouse/capture/t412-driver-selfgrading/bin/drive-gate.sh` →
`out/clone-drive/` (`99-SUMMARY-run2-all-13-arms.txt`)

| arm | expectation | result |
|---|---|---|
| 1 non-`main` ref | STANDS ASIDE, push allowed | PASS |
| 2 state-only, empty ledger | `C3 REFUSED — NO GRADED ANCESTOR` | PASS |
| 3 same commit, base attested | cheap subset runs, push allowed | PASS |
| **4 `P-150` in `RESUME.md`** | **`C3 REFUSED — THE CHEAP SUBSET FAILED`** | **PASS** |
| 5 citation repaired in place | same gate allows | PASS |
| 6 gitlink at `main` | `C1 REFUSED … CONTAINS A GITLINK` | PASS |
| 7 same push **with a bypass reason** | still refused — `THERE IS NO BYPASS FOR C1` | PASS |
| 8 `.go` file in a non-merge commit | `C2 REFUSED` | PASS |
| 9 same push with a 43-char reason | allowed **and logged** to `bypass.log` | PASS |
| 10 same push with reason `"ok"` | refused — too short to be a reason | PASS |
| 11 edit `.softhouse/guards/*.sh`, unattested | `C3 REFUSED … leaves the STATE set` | PASS |
| 12 **delete** a state file | `C3 REFUSED` — deletions take the full bar | PASS |
| 13 pushed tree itself attested | fast path, allowed | PASS |

Arm 4's refusal, verbatim:

```
PNUMBER-CITATIONS: FATAL UNDEFINED .softhouse/RESUME.md:75 P-150 -- P-150 is defined in neither register
driver-push-gate: C3 REFUSED -- THE CHEAP SUBSET FAILED ON THE PUSHED TREE (exit 1).
driver-push-gate: PUSH REFUSED. Nothing was sent.
```

**Run 1 of this drive is committed too** (`98-SUMMARY-run1-harness-false-pass.txt`), because it is
the more useful transcript. It reported `ARM nonmain-stands-aside  EXPECT rc=0 GOT rc=0  PASS`
**while the hook was not installed at all** — the installer had exited 127. A push no gate examined
exits 0 for the same reason a push a gate approved does, so an exit code alone cannot tell *allowed*
from *never asked*. Every arm now also asserts a string the gate itself prints; an arm whose marker
is missing FAILS however its rc came out.

### 3b. The **installed** hook, this repository, real git: **5/5 arms**
`.softhouse/capture/t412-driver-selfgrading/bin/drive-installed.sh` → `out/installed-drive/`

Pushes go to a bare remote under `$TMPDIR` with refspec `…:refs/heads/main` — the gate keys on the
**remote** ref name, so it engages fully — and `origin` is never touched.

| arm | expectation | result |
|---|---|---|
| I1 this branch → `softhouse/T412-installed-probe` | STANDS ASIDE | PASS |
| I2 this branch → `main` (delta is `*.sh`) | `C3 REFUSED` — even T412's own branch takes the full bar | PASS |
| I3 the attested commit → `main` | `C3 the pushed tree is ATTESTED FULL`, 0 s | PASS |
| I4 `P-150` in `RESUME.md` → `main` | `C3 REFUSED`, **27 s** | PASS |
| I5 healthy note → `main` | `C3 PASS — cheap subset clean`, **27 s** | PASS |

### 3c. **The live driver pushed through the gate, 58 seconds after install.** Not an arm.

`out/installed-drive/90-LIVE-DRIVER-PUSH-GATED.md`

```
10:29:12  pre-push installed into the shared hooks dir
10:29:36  the driver commits 4e7d678a  "softhouse iter5: T350 complete (bar EXIT 0, scope clean);
                                        dispatch T449 to review it"   [.softhouse/tasks.json, +19]
10:30:10  THE GATE RUNS ON IT and writes  CHEAP  ed1b2ee1…  4e7d678a…
10:30:11  origin/main advances to 4e7d678a
```

One second between the gate's verdict and the ref moving. The driver did not know it was there.
The delta from the attested ancestor was `.softhouse/tasks.json` alone, so the gate took the cheap
path, graded the **pushed tree** `ed1b2ee1`, found no fatal citation, and allowed it. Correct on
both counts.

**A second live driver push at 10:39:00** — `4e48b7e8`, *"softhouse iter5: T442 complete (bar
EXIT 0, scope clean); dispatch T447 to review it"*, again `.softhouse/tasks.json` alone — went
through the same cheap path one second before the ref moved. Two consecutive real driver pushes
gated, and `bypass.log` **does not exist on this host**: zero bypasses taken.

This also killed an arm and improved it: run 3's arm I3 pushed *the name* `main` and failed its
marker, because `main` had moved underneath it — the same race that is instance 2. The arm now
pushes the attested **sha**, and the race is recorded rather than papered over.

### 3d. Two defects the drives found in the gate itself

Both are committed with the fix, because a drive that never fails is worth nothing.

1. **`ad778020` — the subset was resolved from the pushing worktree.** The gate ran from the
   install-time snapshot in the shared hooks dir while the pushing worktree sat at a commit without
   these files, and refused every push with *"the cheap subset is ABSENT"*. Fail-**closed**, but for
   the wrong reason, and it would have blocked the live driver until this branch merged. The gate
   now resolves the subset **beside itself** (`dirname $0`), with the worktree path as a secondary.
   **The clone drive could not have found this** — there the repo copy is always present. Only the
   installed drive could.
2. **`f0f0bb9f` / `df8440c5` — the installed drive dirtied the tree it then switched branches
   inside**, aborting itself after three PASS lines and no failures, which reads like a short clean
   run. Transcripts now go to scratch and are copied in at the end, and the drive refuses outright
   on a dirty tree. Separately, the healthy arm hit the gate's own CHEAP cache (identical edit →
   identical tree → 2 s short-circuit) and now carries a nonce.

---

## 4. What I deliberately did NOT close — stated so nobody cites this as the bar

1. **The cheap tier is ONE guard.** It does not run the other fourteen, the 46 golden parity
   vectors, or `go build` / `go test`. It is licensed only when the delta from an attested tree is
   inside the STATE set, and §2 names the guard each exclusion is there for — but that mapping is
   **reasoning over corpora I read, not a measurement of every guard against every state path.**
   A reviewer who wants to break this should attack that table, not the code.
   → **FU-T412-1:** when `conformance.sh` is free, add a `--guards-only` entry point (measured
   guard budget 71 s vs the full bar) and make the cheap tier all fifteen guards. That converts the
   whole of this residual into a measurement.
2. **The cheap subset is fatal only in the checker's DIRECTIVE zone**, which is the checker's own
   tiering and not something I widened or narrowed. Measured from
   `check-pnumber-citations.py:108-135`: `.softhouse/RESUME.md` is DIRECTIVE (fatal — it is
   instance 1's exact site), and so are `patterns.md`, `conformance.sh`, `obligations.md`,
   `reference-oracle.md`, `CLAUDE.md`, `.claude/skills/`, `.softhouse/bin/`, `.softhouse/guards/`
   and `docs/`. But **`.softhouse/tasks.json` and `.softhouse/program.json` are ORCHESTRATOR-owned
   and report-only** — a drifted citation the driver writes into `tasks.json` is counted and
   printed, never refused. That is deliberate upstream (P-31: never snapshot a file the
   orchestrator is actively editing) and I did not override it, but it means the gate's cheap tier
   protects the driver's *standing instructions* and not its *task records*.
   My own files live under `.softhouse/hooks/`, which is evidence zone — also report-only.
3. **The STATE-set mapping rots** the moment a guard widens its corpus. Nothing detects that today.
   → **FU-T412-2:** a guard that asserts no guard's corpus selector reaches a STATE-set path.
4. **`origin` cannot enforce this.** A `pre-push` hook is client-side; `SOFTHOUSE_DRIVER_GATE_BYPASS`,
   `--no-verify`, or a machine without the hook all get through. This gate raises the cost of the
   defect on the machine where the fire runs; it is not a server-side branch protection. On a
   single-host launchd program that is the available control, and it is the honest limit of it.
   → **FU-T412-3:** a `pre-receive` hook in the `origin` bare repo would be unbypassable. Not built:
   I did not confirm `origin`'s layout is a bare repo I may write to, and guessing at it is how a
   hook gets installed somewhere it does nothing.
5. **`--no-verify` is not detected after the fact.** The ledger records what the gate saw, not what
   it missed. A push whose tree has neither a FULL nor a CHEAP row is evidence of a skip, and
   nothing checks for that yet.
   → **FU-T412-4:** a reconciler that walks `origin/main`'s reflog and reports every pushed tree
   with no ledger row. This is the detector that makes the gate auditable rather than trusted.
6. **`fire-program.sh` is untouched, deliberately.** A fire is running, and T301 already recorded
   the wrapper editing itself mid-run as a defect. The gate needs no wrapper change — it is a git
   hook, not a driver code path — so there is no deferred graft and no patch file to apply.
7. **`git add -A` is not removed from the driver.** C1 and C2 refuse its *consequences*; they do not
   change its *behaviour*. Making the driver stage explicitly is a change to
   `.claude/skills/softhouse-program/SKILL.md`, which is a directive file I did not have in scope.
   → **FU-T412-5:** replace the driver's blanket `git add -A` with explicit pathspecs.
8. **Instances 2 and 3 have not recurred since install**, so their refusals are driven on fixtures
   only. Instance 1's refusal is driven on a fixture *and* the same code path is proven live by the
   driver's own 10:30:10 push. A refusal observed in the wild is stronger than one driven on a
   fixture, and the difference is stated rather than blurred.

---

## 5. Installation — where it is, and how to check

**INSTALLED** at `$(git rev-parse --git-common-dir)/hooks/pre-push`, i.e.
`/Users/buv/gerege-nbfi/.git/hooks/pre-push` on this host, at **2026-08-29 10:29:12**.

```
bash .softhouse/hooks/install-driver-push-gate.sh            # install / re-install
bash .softhouse/hooks/install-driver-push-gate.sh --status   # is it there, and is it ours
bash .softhouse/hooks/install-driver-push-gate.sh --uninstall # removes only OUR shim
```

The installed file is a **shim** that prefers the tracked
`<main checkout>/.softhouse/hooks/driver-push-gate.sh` and falls back to an install-time snapshot in
`hooks/softhouse-t412-gate/`. A copy would rot; a symlink could not work before this branch merges
(`main` has no such file yet). The shim prints which one it used and that file's sha256 **on every
run**, the same identity discipline `fire-program.sh` already prints for itself at fire start.
The installer **refuses** if `core.hooksPath` is set (it would install a hook git will not run) or
if a `pre-push` exists that is not ours.

**Why a git hook works here at all,** given T336 measured that the agent harness suppresses hooks at
worktree spawn: that measurement is about the *spawn*. The same T336 evidence records both hooks
firing for an agent's **own git commands**, and `git push` is the driver's own git command. The
`reference-transaction` hook installed by `branch_sweep.py` (T312) is the standing precedent for a
hook in this repository's shared hooks directory that demonstrably refuses. The 10:30:10 live push
is the confirmation.

**The hooks directory is shared by every worktree**, so this hook fires for worker pushes too — which
is why the gate's first act is to stand aside for any ref that is not `refs/heads/main`. 35
`softhouse/*` heads exist on `origin` and must keep pushing; arm I1 drives that.

## 6. Files

| path | what |
|---|---|
| `.softhouse/hooks/driver-push-gate.sh` | the gate: C1 / C2 / C3, the STATE set, the bypass |
| `.softhouse/hooks/cheap-subset.sh` | materialises a named tree and runs the citation checker on it |
| `.softhouse/hooks/bar-attest.sh` | runs the full bar on a named commit's tree and writes the ledger row |
| `.softhouse/hooks/install-driver-push-gate.sh` | installs / status / uninstalls the shim |
| `.softhouse/capture/t412-driver-selfgrading/bin/drive-gate.sh` | 13-arm logic drive, throwaway clone |
| `.softhouse/capture/t412-driver-selfgrading/bin/drive-installed.sh` | 5-arm drive of the installed hook |
| `.softhouse/capture/t412-driver-selfgrading/out/clone-drive/` | 13 transcripts + both run summaries |
| `.softhouse/capture/t412-driver-selfgrading/out/installed-drive/` | 5 transcripts + the live-push record |

Host state, in no commit and named here so it is findable:
`$(git rev-parse --git-common-dir)/softhouse-driver-gate/{attest.tsv, bypass.log, attested-<tree>.log}`
and `$(git rev-parse --git-common-dir)/hooks/{pre-push, softhouse-t412-gate/}`.

## 7. This branch's own bar

`bash .softhouse/conformance.sh` on the committed, clean `softhouse/T412-driver-selfgrading` tree.
Scratch in `/tmp`, outside the repo. Transcript: `.softhouse/capture/t412-driver-selfgrading/out/BAR-on-this-branch.log`.

**PRESENCE BEFORE VALUE**, in that order, because four exit-2 paths run before the probe prints:

```
$ grep -c 'probe = ' bar.log
1                                   <-- PRINTED AT ALL. Absence would not be `down`.

$ grep -n 'probe = ' bar.log
203:conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up

$ grep -n '^VERDICT' bar.log
818:VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.

EXIT=0
WALL_SECONDS=80
```

`git status --porcelain` empty before and after. Guard census 15/15 timed, 0 ceiling breaches,
0 unbudgeted. The dead-path frontier reads `108 == 108` — it moved to 109 once, on a quoted
literal in `driver-push-gate.sh` that ended in an escaped backtick, and was repaired by rewording
rather than by growing the pin. The fail-open frontier is unchanged at 11 rows; none of the five
new scripts joins it.

