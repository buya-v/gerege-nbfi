# T461 — independent review of T453 (`softhouse/T453-gate-state-set`, tip `141e3ae5`)

**Reviewer** T461 · **Branch** `softhouse/T461-review-t453` · **Subject** the driver push gate's
STATE set (M-1), the gate nothing installed (M-2), and m-3/m-4/m-5/L-6/L-7/L-8.

Every number below was **re-derived on this branch from the source**, with my own instruments, in
throwaway universes under `$TMPDIR`. Nothing was taken from T453's handoff. The live `pre-push`
on this host was **never touched**: it is gating the fire that dispatched this task, and the
review's own arm drives install a gate into a throwaway `git clone --local` with its own bare
remote. `.softhouse/hooks/`, `.softhouse/conformance.sh`, `.softhouse/bin/ready-tasks.py` and
`.softhouse/bin/fire-program.sh` are untouched by this branch.

---

## VERDICT: **APPROVED WITH CONDITIONS**

T453's diagnosis is right where it corrects T450, its remedy closes all four arms, its numbers
all reproduce to the digit, and M-2 is genuinely wired into the fire's linear control flow. The
conditions below are five findings — one MAJOR, three MINOR, three LOW — none of which is a
reason to hold the branch, and one of which (C-T461-1) is a **live, recurring freeze that this
branch adds one occurrence to and does not measure**.

| id | finding | rating | evidence |
|---|---|---|---|
| **C-T461-1** | The dead-path frontier is a function of whether the fire lock is TRACKED: `108 → 125` the instant `.softhouse/LOCK` leaves the index, which the driver does **34 times in 400 commits**. `D` leaves the STATE set (clause j) → full bar → **EXIT 2, no probe line**. T453 grows the latent set from 16 to 17 occurrences and its §5 says only that its files are not on the frontier *as measured with the lock held*. | **MAJOR** | `evidence/30-lock-frontier-coupling.txt` |
| **C-T461-2** | m-5 writes `gate=…  headblob=…` into every CHEAP attestation row and **nothing anywhere reads it**. The handoff justifies not making the divergence fatal on the ground that `reconcile-pushed-trees.sh` "can ask afterwards". It cannot. One writer, zero readers — P-45 (`patterns.md:1503`) one level down, and the same shape as m-3's own finding about `bypass.log`. `bar-attest.sh`'s FULL rows carry no grader identity at all. | **MINOR** | `git grep -n headblob softhouse/T453-gate-state-set` → 1 writer, 0 readers |
| **C-T461-3** | FU-T453-1's stated blocker **does not reproduce**. T453 says `cheap-subset.sh`'s `read-tree`+`checkout-index` would make `check-capture-namespace.sh` "grade the caller's tree". Measured: the subset exports `GIT_WORK_TREE`/`GIT_INDEX_FILE`, so `git rev-parse --show-toplevel` returns the **materialised tree** and the guard reports `dirs=228` (the pushed tree) against `dirs=227` in the caller's. The follow-up is a small change, not a design change. | **MINOR** | `evidence/40-cheapsubset-root-readback.txt` |
| **C-T461-4** | FU-T453-3 (server-side prevention of `--no-verify`) is correctly classified as a `user` item and is then left as a **residual bullet in a handoff** instead of being filed in `.softhouse/gates.md`. CLAUDE.md's rule is that a pending `user` gate parks in `gates.md`; a `user` item that only a handoff knows about is not surfaced. | **MINOR** | `.softhouse/handoff/T453-gate-state-set.md` §7.1 / §8 FU-T453-3 |
| **C-T461-5** | Two mis-stated cardinals. (a) The rejected "exclude `capture/**` only" alternative is stated at **~87 %**; measured **84.0 %** (336/400) — it is worth 0.25 points, not 3. (b) The `(h2)` comment in the gate prices the exclusion at "**27 entries**"; 27 is the `capture/` figure alone, `reviews/` adds **43** more, so the exclusion covers **70** entries. Neither changes the decision. | **LOW** | `evidence/10-coverage-rederivation.txt` |
| **C-T461-6** | The new `fire-program.sh` block calls bare `mktemp` for `RECON_TMP`. That file resolves `$FIRE_MKTEMP` absolutely at the top precisely because a `PATH` `mktemp` (busybox) was once "a fire that could not start" (T377). Fails safe (`|| RECON_TMP=''` and the else-arm logs), but it is the one line in the block that departs from the file's own declared discipline. | **LOW** | `.softhouse/bin/fire-program.sh`, the `T453-PUSHGATE-BLOCK` |
| **C-T461-7** | The `CTRL-A-LOCK` control passes only because `drive-arms.sh` **seeds** a FULL row for a lock-absent base tree. On this repository that tree could not actually have been bar-attested — see C-T461-1. The control demonstrates the gate's arithmetic, not a reproducible driver workflow. | **LOW** | `evidence/30-lock-frontier-coupling.txt` + `drive-arms.sh`, `seed_full` |

Nothing in this branch touches money code, vectors, `nexus/`, or a float. Arm A **is** the money
arm and the fix does close it — see the adjudication below and `evidence/20-…`.

---

## 1. The headline — the money arm is a READ hazard, and T453 is RIGHT to correct T450

**ADJUDICATED IN T453's FAVOUR, from source, with the numbers re-measured.**

T450's one-sentence diagnosis — *"three guards resolve against the tree's INVENTORY, so an
ADDITION is the same hazard as the DELETION already excluded"* — is correct for arms B, C2 and D
and **wrong for arm A**, and the difference is not bookkeeping: it decides whether the remedy is
an addition rule or an exclusion.

Re-derived here:

* `guard_no_float_in_capture_requests` has had a **second arm since T193**. It is stated in
  `.softhouse/conformance.sh:1224-1238` and implemented in
  `.softhouse/capture/lib/check_wire_float_roundtrip.py` (its own header, line 85: *"the
  referenced file is **opened**"*). The guard **opens** every file a stored vector names in
  `provenance.capture_ref` and grades the numeric tokens in its recorded-request blocks. Opening
  a file is a READ, not an inventory lookup. Arm A's delta is an `M` of a capture record's
  **content**; nothing about the tree's inventory changes.
* T412's clause (h) — *"no path segment named `req`"* — describes the FIRST arm only, i.e. the
  guard **as it stood before T193**. The table was stale, exactly as T453 says.
* **Measured on this tree, independently of T453:** `26` distinct non-empty `capture_ref`
  citations, **26/26 under `.softhouse/capture/`**, **0 with a `/req/` segment** — so clause (h)
  excluded none of them, and T412's `state_path` returned 0 (admit) for
  `.softhouse/capture/out/capture-prod3b-raw.json` because `*` crosses `/` in a bash `case`.
  Reproduction: `git grep -h -E '"capture_ref"[[:space:]]*:' -- .softhouse/vectors | sed -E
  's/.*"capture_ref"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/' | grep -v '^$' | sort -u | wc -l`.

**The deeper claim is sound, and it is the most important sentence in the task.** `state_path` is
a hand-maintained model of fifteen other programs' corpora. It rotted the day T193 widened one of
them, and nothing said so. Adding rows to that table buys the next rot. Clause (k) reading the
**guard's own pin out of the pushed tree** is the right shape for the frontier specifically,
because the pin moves when the guard moves. It is *not* a general answer — nothing measures "a
new guard's corpus now overlaps the STATE set" — and T453 says so itself (residual 5). C-T461-1
is that residual arriving early, in the fail-CLOSED direction, on the driver's most common write.

---

## 2. The numbers — every one reproduces

Independent classifier, `git rev-list --first-parent --no-merges --max-count=400`, `git show
--name-status` per commit, bash-`case` semantics re-implemented with `fnmatch` (`*` crosses `/`).
Measured at T453's own merge base `cbc8733c`. Transcript:
`evidence/10-coverage-rederivation.txt`.

| rule | T453 claims | T461 measures | agree? |
|---|---|---|---|
| T412 as shipped | 88 % | **353/400 = 88.2 %** | yes |
| chosen (h2 + k) | 84 % | **335/400 = 83.8 %** | yes |
| modifications only | 71 % | **284/400 = 71.0 %** | yes |
| exclude `capture/**` only | ~87 % | **336/400 = 84.0 %** | **no** — C-T461-5(a) |
| historical ADDITION entries | 78 | **78** | yes |
| `A .softhouse/LOCK` | 34 | **34** | yes |
| `capture/`+`reviews/` entries | "27" | **27 + 43 = 70** | **no** — C-T461-5(b) |

Also measured, and worth putting on the record because it is what the exclusion actually costs:
of the 629 name-status entries in those 400 commits, **235 are the task graph**, 122 the fire
lock, 90 `RESUME.md`, 43 `reviews/`, 30 `program.json`, 27 `capture/`. The status histogram is
`M 473 / A 78 / D 78`. Clause (h2) removes `reviews/` (43) and `capture/` (27) and costs 18
commits of coverage; the 4-point figure is right for the reason T453 gives.

The **`0 of 78 additions blocked`** claim is confirmed the same way: 53 of the 78 additions fall
inside commits the T453 rule already admits, and none of them appears in the pin — `hazards=0` on
every one, driven live at `evidence/20-green-gate-drive-T461.txt` (`CTRL-A-OBSERVATION` and
`CTRL-A-LOCK` both ALLOWED, both cheap).

---

## 3. The arms — re-driven, both polarities, with the controls

`drive-arms.sh` in `gate` mode, run twice from this worktree into throwaway bare remotes under
`$TMPDIR`. Both calibrations are abort-preconditions and both fired.

**RED, at TODAY's `main` (`71c9f19c` — not T453's base; the defect is live right now):**
`evidence/21-red-gate-drive-at-main-T461.txt`

    A-MONEY-CAPTUREREF     push-exit 0  ALLOWED
    B-FRONTIER-CAPTURE     push-exit 0  ALLOWED
    C2-NAMESPACE-CAPTURE   push-exit 0  ALLOWED
    D-FRONTIER-UATMD       push-exit 0  ALLOWED
    CTRL-M-RESUME / CTRL-A-OBSERVATION / CTRL-A-LOCK   ALLOWED (controls)

**GREEN, at `141e3ae5`:** `evidence/20-green-gate-drive-T461.txt`

    CALIBRATION+  the installed gate REFUSES a gitlink
    A-MONEY-CAPTUREREF     push-exit 1  REFUSED   (23 gate lines)
    B-FRONTIER-CAPTURE     push-exit 1  REFUSED   (23 gate lines)
    C2-NAMESPACE-CAPTURE   push-exit 1  REFUSED   (23 gate lines)
    D-FRONTIER-UATMD       push-exit 1  REFUSED   (23 gate lines)
    CALIBRATION-  the installed gate ALLOWS an honest driver state edit
    CTRL-M-RESUME          push-exit 0  ALLOWED   (13 gate lines)
    CTRL-A-OBSERVATION     push-exit 0  ALLOWED   (12 gate lines)
    CTRL-A-LOCK            push-exit 0  ALLOWED   (12 gate lines)

4/4 refused, **3/3 controls still allowed and still cheap** — P-98 (`patterns.md:3411`) satisfied
in both directions, which is the half that matters. The gate-output-line counts (23 vs 12/13) are
themselves a discriminator: silence would have aborted the drive at 94, and it did not.

**The fixture defect T453 disclosed is genuinely gone.** The instrument builds its universe with
`git clone --local` and asserts `NTRACK >= 100` and `BASE == SRCSHA`; the squash-and-`git archive`
form that reddened the control on `guard_reconciler_ownership` (historical shas unreachable) is
written into the file as a comment rather than quietly removed. Both my drives report `base tree
10142/10143 tracked path(s)`, and the controls came back exit 0.

**Arm D was worth adding.** `.softhouse/uat.md` is untracked, is one of the 108 pinned dead
literals, is a `*.md` directly under `.softhouse/`, and is nowhere near `capture/`. A
`capture/`-only fix looks sufficient and is not; arm D is the proof, and C-T461-5(a) shows the
capture-only alternative buys 0.25 points, not the 3 the handoff credits it with.

---

## 4. Did I find a FOURTH STATE-set-confined bypass? — **No fail-open; yes a fail-closed**

**The search, stated, because "not found" is a statement about the search.** I read all fifteen
guards `run_guards` calls plus the five standalone instruments they delegate to; I enumerated
every `$REPO_ROOT/.softhouse/…` read in `.softhouse/conformance.sh` (14 distinct paths, all under
`vectors/`, `guards/`, `bin/`, `capture/` or `conformance.sh` itself — every one excluded); I
enumerated every quoted `.softhouse/` literal in that file (three, all excluded); and I **drove**
four probes rather than reasoning about them.

Driven, not read:

* **Clause (d) — the task graph.** 235 of 629 entries in the last 400 commits are
  `.softhouse/tasks.json`, so if `guard_reconciler_ownership` read the working-tree copy this
  would be the biggest hole in the set. It does not: with the file replaced by
  `not json at all { [ ,,,` and committed, the rig still returns `GREEN 13/13 · RED 8/13 ·
  SELFTEST OK`, identical to the untouched control. `evidence/50-clause-d-taskgraph.txt`.
* **`guard_no_fail_open_instruments`.** Its C1/C6 dead-path rules match **absolute** paths only
  (`RE_ABSPATH`, `RE_ABSPATH_LOC`, `RE_ASSIGN_ABS` — all anchored on `/`), so no relative
  `.softhouse/…` addition can flip a tier token. Frontier `11 == 11` reproduced here.
* **`guard_capture_namespace`.** Its whole population is the first path component under
  `capture/`/`reviews/`, both now excluded; my GREEN drive confirms arms B and C2 refused.
* **The frontier's `added` direction.** An addition can only ever *grow* the tracked universe and
  the set of directory prefixes, so it can only make a dead literal RESOLVE, never the reverse.
  Clause (k)'s predicate is a deliberate superset of `census_dead_paths.resolves()` (`L == P`,
  `P` under `L/`, `L` under `P/`, `L` prefixed by `P`) and refuses on an unreadable/empty pin, an
  empty question, an absent helper and a failed selftest. I could not construct an addition it
  admits that the frontier guard then rejects.

**Conclusion: within the fifteen guards on this tree I could not construct a fourth
STATE-set-confined FAIL-OPEN.** That is a statement about a one-reviewer search over one tree at
one commit, and it does not close the class — which is exactly why (k) measures instead of
tabulating, and exactly why C-T461-1 matters.

### C-T461-1 — the fourth arm I did find, in the opposite direction

`.softhouse/LOCK` is a tracked file that **tracked `.softhouse/*.sh` and `*.py` instruments name
as a bare quoted literal**. While a fire holds the lock those literals RESOLVE; the moment the
lock leaves the index they are DEAD. Driven, with a control:

    CONTROL  lock held      exit 0   T316-DEADPATH-FRONTIER: GREEN    rows=108 pinned=108 added=0  removed=0
    ARM      lock released  exit 1   T316-DEADPATH-FRONTIER: REFUSED  rows=125 pinned=108 added=17 removed=0

and the census the guard reads:

    lock held      deadFiles=75  deadOccurrences=108
    lock released  deadFiles=91  deadOccurrences=125          (at `main`: 90 / 124)

Consequences, in order:

1. **`D .softhouse/LOCK` is not in the STATE set** (clause j), so the gate sends the end-of-fire
   release to the full bar; the full bar on that exact tree goes **EXIT 2 with NO PROBE LINE**
   — which reads like a money non-negotiable and is not one, the same misreading arm D exists to
   prevent. The driver does this **34 times per 400 commits**. Its only exits are
   `SOFTHOUSE_DRIVER_GATE_BYPASS` or never releasing the lock from the index.
2. **T453 grows it.** `main` carries 16 such occurrences; this branch carries 17 —
   `drive-arms.sh` adds one. §5's claim ("none of the six new `.sh`/`.py` files is on the
   frontier, `11 == 11`, `108 == 108`") is true **as measured with the lock held**, and the
   branch's own control arm is the fire-lock cycle, so this was the one condition its instrument
   was in the best position to measure and did not.
3. **It is the mirror of the freeze the branch rejected `modifications only` to avoid.** The
   argument against that alternative was "it blocks `A .softhouse/LOCK` 34×, trading a fail-open
   for a freeze". The `D` half of the same 34 cycles is already frozen, by clause (j) plus the
   frontier, and nobody has said so.
4. **It is pre-existing** — T412's clause (j) and 16 of the 17 occurrences predate this branch,
   and no bypass has been recorded on the live host yet (`bypass.log` does not exist; the fire
   still holds its lock). It is rated MAJOR because it is measured, live, recurring and
   undisclosed, not because T453 caused it.

**Recommended remedy** (small, and it is the repair T323's test prescribes rather than a pin): the
four instruments that spell the lock path as a bare literal should assemble it from a variable, as
`drive-arms.sh` already does for `capture/` and `toolchain`. Can each still do its job if the
literal goes away? Yes → repair, do not pin. Filed as **FU-T461-1**.

---

## 5. M-2 — is the gate installed by something, and is the block REACHABLE?

**Yes to both, and the second one is the half the author's drive could not prove.**

* **The wiring exists and is driven.** `drive-fire-wiring.sh` clones the repo at a named rev,
  greps the **tracked** wrapper in that clone for `T453-PUSHGATE-BLOCK-BEGIN/END`, `sed`s the
  interior out, refuses on a missing/mis-ordered sentinel or a block under 5 lines, and executes
  the extracted bytes under `zsh` with only `log()` and `REPO` supplied. Nothing is retyped.
  **The extraction is honest**: it is the tracked bytes of the file under review, not a copy
  typed into the instrument. What it supplies beyond the block (a stub `log`, `REPO`) is declared
  in the file.
* **Reachability, verified by me, statically, because the extraction drive cannot see it.** The
  block sits at top level in `fire-program.sh` between `log "reference oracle (Fineract): …"` and
  the T325 pre-flight baseline, immediately after the T312 `branch_sweep.py` pair it cites as
  precedent. The last function body closes at `:1234` (`attest_exit_protocol`); every `exit`
  before the block (`:616 :635 :681 :803 :960`) is inside an `if [[ "${1:-}" == "--flag" ]]`
  query-mode block (`--lock-decide`, `--lock-signals`, `--self-test-lock-readers`) or an argument
  error; `PROBE_ONLY` is parsed at `:966` and not consumed before `:1290`. `REPO` is set at `:19`
  and `log()` defined at `:1065`. **The block is on the linear pre-flight path of every ordinary
  fire.**
* **The T301 objection is answered by the file itself, and better than the handoff says.**
  `fire-program.sh:1039-1051` snapshots `${0:A}` into `$TMPDIR` and `exec`s the copy at fire
  start, so a mid-fire edit to the tracked file cannot change the running fire — it takes effect
  at the next one, which is exactly the disclosure T453 makes. **Editing the running wrapper was
  acceptable here**: M-2 could not be closed anywhere else (the skill's steps are prose a driver
  retypes, which is the defect), the change is 30 lines of `|| true` wiring inside sentinels, the
  block is extraction-driven, and the wrapper is excluded from the STATE set (clause d) so the
  merge itself takes the full bar. The residual — "unproven in a live fire" — is correctly stated.
* **`--status` really does exit non-zero now**, and I confirmed the live host is RED for the
  reason stated: the installed snapshot predates `added-path-hazard.py`. The ledger on this host
  shows the **old** gate still running (its CHEAP rows carry no `gate=` field), which corroborates
  it.

---

## 6. The minors — checked

* **m-3 `reconcile-pushed-trees.sh`** — sound, and fail-closed in every direction that matters:
  it refuses on an absent ledger, an empty ledger, an empty reflog, a window of zero tips, and a
  `git ls-tree` that returns nothing. The window is derived from the ledger's oldest resolvable
  commit, so pre-gate history reports as `pre-gate` and is not a finding. It reads `bypass.log`,
  and states the absence of that file as a **measured** zero (the gate creates the directory on
  every run) rather than as silence. It cannot prevent anything and does not claim to.
  **Its one gap is C-T461-2**: it never reads the `gate=`/`headblob=` column m-5 writes.
* **m-4 `GATE_PARTS`** — one list, checked, copied and re-verified by the same loop, plus a
  post-copy readback. `beside_gate()` resolves at print time and names both places it looked.
  Correct application of P-80 (`patterns.md`) — make the second site read the first.
* **m-5** — the banner and the row field are right; the reader is missing (C-T461-2). The
  argument for not making divergence fatal is sound and is bounded by m-3 as stated.
* **L-6** — `-m` on `git diff-tree` is load-bearing and correctly argued: without it a merge
  prints nothing and the gate would be blind on precisely the commits C2 already exempts.
  `--root` handles the first commit. `RANGE_N` is printed on the green path.
* **L-7** — the second `case` really was unreachable (`*` crosses `/` in bash `case`); deleting
  it rather than repairing it is right, and I verified the single `case` still classifies
  `.softhouse/capture/out/capture-prod3b-raw.json` as non-STATE and `.softhouse/RESUME.md` as
  STATE.
* **L-8** — all fifteen named, including the three that need no exclusion and why.
* **`added-path-hazard.py`** — selftest drives both polarities *and* the ABORT arm (an empty pin
  clears a known-dead literal, which is why `main()` refuses before calling `hazards()`); exit 2
  is reserved for "could not answer". The fixture is assembled from `SOFT = ".softhouse"` with no
  trailing slash, so it stays out of the census's selector; the twice-repaired-and-recorded
  history of that fixture (`108 → 116 → 109 → 108`) is written into the file, which is T323's
  test applied rather than quoted.

---

## 7. The residuals — each confirmed, and my rating

1. **The live host is RED and correctly.** Confirmed independently: the installed shim is still
   T412's (its CHEAP ledger rows carry no `gate=` field), and `--status` must exit 1 because the
   snapshot predates two of the four `GATE_PARTS`. Real, correctly rated. **FU-T453-4 must run at
   merge.**
2. **Server-side prevention of `--no-verify`** — see C-T461-4. **I partly agree.** The *design and
   a drive against a throwaway bare remote* are ENGINEERING and need no gate; the *application to
   the live `origin`* needs repo-admin rights the agent does not hold and can lock the user out of
   his own `main`, so it is a `user` item under CLAUDE.md's RESERVED clause. Worth adding: a
   `pre-receive` hook is **not available on github.com** (GitHub Enterprise Server only), so the
   realistic instrument is a branch ruleset / required status check, and the gate should say so.
   The classification is right; leaving it in a handoff instead of `.softhouse/gates.md` is not.
3. **4 points recoverable by deriving the `capture_ref` set at gate time (FU-T453-2)** — real, and
   my measurement makes it *smaller* than stated: the whole `capture/` exclusion is worth 0.25
   points of commit coverage (336 vs 335), because `reviews/` does most of the work. FU-T453-2 is
   therefore lower value than the handoff implies. Correctly rated as a follow-up; the number in
   it is not.
4. **`conformance.sh` untouched, so the cheap tier still runs ONE guard** — real, and correctly
   rated as the largest structural residual. **The last clause is wrong** — see C-T461-3.
5. **Clause (k) covers the `removed` direction only, and nothing detects a future guard's corpus
   overlapping the STATE set** — real, correctly rated, and **already realised**: C-T461-1 is that
   very failure, live, in the fail-closed direction, on the driver's most common write.

---

## 8. Reproduction recipes

All four instruments run from a checkout of this repository, write only under `$TMPDIR`, and never
touch the live hook. They are shipped as fenced blocks in `INSTRUMENTS.md` rather than as tracked
`*.sh` **deliberately**: a tracked `.softhouse/**/*.sh` joins the dead-path census corpus, the
fail-open lint corpus and the host-state lint corpus, and this review is not the place to move
three pins. Paths inside them are assembled from variables, T238-style; `SH='.softhouse'` carries
no trailing slash, which is what keeps it out of the census's selector.

| finding | recipe |
|---|---|
| coverage 88/84/71, 78, 34, 27+43 | `INSTRUMENTS.md` §1 `coverage.py`, §2 `entries.py`, §3 `lockhist.py` — run against `cbc8733c` |
| C-T461-1 | `INSTRUMENTS.md` §4 `lockguard.sh <repo> softhouse/T453-gate-state-set` |
| C-T461-3 | `INSTRUMENTS.md` §5 `cheapenv.sh <repo> softhouse/T453-gate-state-set`, then the same guard plainly |
| clause (d) | `INSTRUMENTS.md` §6 `tasksprobe.sh <repo> softhouse/T453-gate-state-set` |
| RED / GREEN arms | `bash .softhouse/capture/t453-t450-conditions/instruments/drive-arms.sh main T461-RED <out> gate` and the same with `softhouse/T453-gate-state-set` |
| C-T461-2 | `git grep -n headblob softhouse/T453-gate-state-set` → one writer, zero readers |
| M-2 reachability | `sed -n '1234,1300p' .softhouse/bin/fire-program.sh`; `grep -n '^}' …` (last at 1234); `grep -n 'exit ' …` (all pre-1290 exits inside `--flag` blocks) |

---

## 9. The bar, on this review's own committed tree

`bash .softhouse/conformance.sh`, from a clean scratch `git worktree` under `/tmp`, **outside this
repository**, on the tree carrying every deliverable above. Probe **PRESENCE** read before its
value. Transcript: `evidence/60-final-bar.txt`.

    EXIT 0
    grep -c 'probe = '  ->  1        (PRESENT, read before its value; it reads `up`)
    conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
    VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
    conformance:   T316-DEADPATH-CENSUS: … deadOccurrences=108 …
    conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
    conformance:   frontier == pinned (all 11 rows, by path).      [fail-open frontier 11 == 11]

The bar prints the raw `T316-DEADPATH-FRONTIER: … rows=108 pinned=108 …` line only on its
REFUSAL path; on green it forwards the census line instead. `rows=108 pinned=108 added=0
removed=0` was therefore taken separately, from the standalone guard, as the CONTROL arm of
`evidence/30-lock-frontier-coupling.txt`.

**On the tree that was actually graded.** Committing this transcript changes the tree the bar just
graded, so one run always attests a tree that is not the one that ships. The bar was run twice —
on the tree carrying every deliverable, and on the tree that additionally carries this transcript.
Both **EXIT 0, probe PRESENT ×1 reading `up`, `deadOccurrences 108`, frontier `11 == 11`**. Only
the first is committed, because committing the second is what makes the regress non-terminating.

---

## 10. Follow-ups filed by this review

| id | what |
|---|---|
| **FU-T461-1** | Assemble `.softhouse/LOCK` from a variable in the four tracked `*.sh`/`*.py` that spell it as a bare literal, so the dead-path frontier stops being a function of whether a fire holds the lock (C-T461-1). Re-pin only after the repair, and drive both halves of the lock cycle. |
| **FU-T461-2** | Give `reconcile-pushed-trees.sh` a reader for the `gate=` / `headblob=` column, and record the grader's identity on `bar-attest.sh`'s FULL rows too (C-T461-2). |
| **FU-T461-3** | Re-scope FU-T453-1: measured, `cheap-subset.sh`'s materialisation already resolves to the pushed tree, so running the two standalone inventory guards in the cheap tier is a small change (C-T461-3). Root readback stays mandatory (T165/T201). |
| **FU-T461-4** | File FU-T453-3 in `.softhouse/gates.md` as a `user` item, noting that `pre-receive` is not available on github.com (C-T461-4). |
