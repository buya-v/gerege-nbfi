# T449 — INDEPENDENT REVIEW of T350 (`softhouse/T350-reconcile-content`)

**Reviewer** T449, own worktree, branch `softhouse/T449-review-t350`.
**Under review** `.softhouse/bin/ready-tasks.py` — the file the entire program reads to
decide what to work on.
**Method** every number below was re-derived with an instrument written from the
predicate, in `bin/`, with the raw transcript in `out/`. T350's own capture scripts were
read only *after* the corresponding measurement had been taken independently, and only to
explain a difference. Both modules are loaded **by path**: RED is
`git show main:.softhouse/bin/ready-tasks.py`, **sha256 `3d7fef805a55bf21…`, byte-identical
to `.softhouse/bin/ready-tasks.py` in this checkout** [`out/31-drive.txt` line 1]; GREEN is
`git show softhouse/T350-reconcile-content:…`, sha256 `e80196813ea210a0…`.

---

## VERDICT: **APPROVED WITH CONDITIONS**

The change is correct in its main claims and it is a real improvement: the four real cases
re-drive as claimed, the must-block controls still block, the verdict lattice **partitions**
(256 states, 0 with no verdict, 0 with two), the wiring is exact, and the calibration
arithmetic reconciles to the commit. **Two MAJOR conditions**, both of them the same defect
the task was filed to fix, surviving in the two places the change did not look: the new
`stillborn` arm never asks the ref store at all, and the ref-side content test applies the
strict OWNING anchor that its own comment argues against. Both are *constructible*, both are
driven RED here, and neither has a live instance in this checkout today.

---

## CONDITIONS

### C-T449-1 — MAJOR — the `stillborn` arm never consults ref evidence, and prints "it is UNSTARTED" while a live ref carries the work

`_branch_wip_core`'s ancestor-of-main leg (rt_t350.py:1437–1497) calls `landed_evidence(tid)`
and **nothing else**. `refs_carrying_content` is called from exactly one site in the whole
module — `_absent_verdict:1306` [grep, `out/` not needed: `grep -n 'refs_carrying_content('`
returns 1188 (def) and 1306 (only call)]. So the moment `git rev-parse` resolves the recorded
branch, the ref store is out of the picture.

**Enumerated, not argued.** PASS 4 of `bin/21-partition-passes34.py` runs the predicate over
all 8 ref states for each branch state and prints the verdict set:

```
exists-0ahead-ancestor  main=none  verdicts over ALL 8 ref states: [('stillborn', 'demote')]
absent                  main=none  verdicts over ALL 8 ref states: [('indeterminate','demote'),
                                    ('name-only-refs','demote'), ('relocated','REFUSE'),
                                    ('unstarted','demote')]
```
[`out/21-partition-passes34.txt`]

**Driven RED on a constructed repo.** `bin/30-fixture.sh` case **G**: the recorded branch
`softhouse/T900-work` sits at the dispatch commit (0 ahead, ancestor of main) *and*
`softhouse/rescued-t900-base-20260829` carries a real commit adding
`.softhouse/capture/t900-work/out/wip.txt`. Case **G2** is byte-for-byte the same evidence
with the recorded branch deleted:

```
G/ATTACK   rescue ref CARRIES real t900 content, recorded branch STILL EXISTS
                                                 RED merged    REFUSE  ->  GREEN stillborn DEMOTE
G2/CONTROL identical rescue ref, recorded branch DELETED
                                                 RED relocated REFUSE  ->  GREEN relocated REFUSE
```
[`out/31-drive.txt`]

Identical content evidence, opposite polarity, decided by whether the recorded branch was
deleted. §3 of the handoff says polarity is chosen "per kind of evidence"; here it is not.

**The emitted text is false in this state**, verbatim from `out/31-drive.txt`:

> "the branch was cut from the driver's own dispatch commit and **never moved**. It reads as
> MERGED to `merge-base --is-ancestor` and **it is UNSTARTED**."

`softhouse/rescued-t900-base-20260829` exists and carries the work. "Not found" has been
written down as a fact about the world in the one arm that did not search. That is the
P-66/P-70 defect inside the change filed to remove it, and it is what a human reads before
deciding.

**Reachability is not hypothetical — it is what the shipped sweep produces.**
`fire-program.sh:3127` is `git -C "$W" checkout -q -b "$WB"`: it creates the rescue branch and
**does not delete the worker's task branch**. The sweep fires precisely when the worker left
uncommitted WIP, i.e. commonly with zero commits, i.e. with the task branch parked at the
dispatch commit. And `reconcile()` does not repair this from the pairing: `rescue_map.get(branch)`
at rt_t350.py:1597 only *appends a sentence to the note*; the verdict came from
`branch_wip(branch, id)` one line above and is unaffected. A later fire has no `rescue_map` at
all — which is the T339 situation exactly.

**Measured live instances today: 0.** `bin/40-realrepo-attack-census.py` tests every id
nameable from a local head: two `stillborn` branches exist (`softhouse/T447-review-t442`,
`softhouse/T449-review-t350`) and neither has a carrier ref [`out/40-realrepo-attack.txt`].
So this is latent, not burning.

**Reproduce:** `bash bin/30-fixture.sh && python3 bin/31-drive.py` → rows G and G2.

**Suggested repair:** the ancestor leg must ask `refs_carrying_content` before returning
`stillborn`, and when a carrier exists must name it and withhold (or emit a distinct kind), the
same way `_absent_verdict` does. At minimum the `stillborn` text must stop asserting
"it is UNSTARTED" when refs were never probed.

---

### C-T449-2 — MAJOR — `ref_content_evidence` applies the OWNING anchor to the ref's own diff, contradicting the comment three lines above it, and demotes a rescue ref that carries the task's real work

`ref_content_evidence` (rt_t350.py:1139–1187) reasons **explicitly** that the ref side must be
generous:

> "Generous on purpose: this is the ref side, where the destructive error is demoting a line
> that still exists, and a commit message is written by the worker doing the work rather than
> by a sweep naming a directory."

…and then applies `leading.match` — the strict OWNING anchor — to the paths in the same ref's
diff, justified as "same rule as main". The two halves of one function carry opposite stated
polarities, and the strict half governs the case that matters, because **the sweep's rescue
commit subject is boilerplate that names no id**, so the subject test can never fire on a
rescue ref.

**Driven RED.** `bin/32-case-k.sh` builds case **K**: T945's genuine work
(`.softhouse/capture/t944-t945-conditions/out/work.txt` — this program's condition-bundle
convention) rescued by the sweep, recorded branch deleted:

```
K/  T945's genuine work under T944's condition dir, sweep-rescued, branch DELETED
      RED  relocated       REFUSE
      GREEN name-only-refs DEMOTE      <== CHANGED
```
and the GREEN text says, verbatim:
> "1 live ref(s) carry id T945 IN THEIR NAME … and **NOT ONE of them carries any content
> belonging to it**. … **no path in its diff vs main has a component naming T945**."

Both sentences are false: `t944-t945-conditions` names T945. [`out/33-case-k.txt`]

**The on-main analogue of this shape is instantiated twice in the real repo.** Of the 354 ids
nameable from a tracked path component on main, exactly **5** have zero OWNING paths, and two
of them — **T405** and **T408**, both `done` — are real tasks whose landed work lives entirely
under *another* task's directory (`t416-t405-conditions/`, `T424-t408-conditions.md`) with no
`<id>:` subject on main either. `landed_evidence` finds **nothing** for both.
[`out/50-owning-mentioning.txt`; corroborated by
`git ls-tree -r --name-only main | grep -i t405` and `git log main --format=%s | grep -i t405`.]
Neither is currently reachable by the code (both terminal), but they prove the shape is real.

**The repair is one word, and I verified it does not reintroduce the defect the task was
filed for.** `bin/34-proposed-fix-probe.py` re-runs `ref_content_evidence` with the ref-diff
path test relaxed from `leading` to `anywhere`:

```
case                                                    SHIPPED(leading)  RELAXED(anywhere)
T339  the incident ref -- MUST STAY name-only           name-only         name-only
T945  case K -- genuine work under T944's dir           name-only         CARRIES
T900  case G's rescue ref                               CARRIES           CARRIES
T351  control -- real content, owning path              CARRIES           CARRIES
```
[`out/34-proposed-fix.txt`]

The T339 rescue ref stays `name-only` because its paths
(`.softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt`, `.t347-postcheckout-marker`) name no t339
**anywhere**, not merely not-at-the-front. The OWNING anchor was never what saved T339; it is
buying nothing on the ref side and costing case K.

**Reproduce:** `bash bin/30-fixture.sh && bash bin/32-case-k.sh && python3 bin/33-drive-k.py
&& python3 bin/34-proposed-fix-probe.py`.

---

### C-T449-3 — MINOR — the "313 handoffs" cardinal is wrong by 3×, and it shipped **inside `ready-tasks.py`**

Handoff §5 and the code comment at `landed_index()` (rt_t350.py:916–926) both state:

> "Measured on main at b102875c: **542** handoff paths are tracked, **229** are bare `T###.md`
> and **313** are the convention this program has used all month."

Re-measured **at b102875c**, the commit cited:

| | author | measured |
|---|---|---|
| handoff paths tracked | 542 | **542** ✓ |
| of those, ending `.md` | (implied 542) | **337** |
| bare `T###.md` | 229 | **229** ✓ |
| other `.md` (the inert population) | **313** | **108** |

`313` is `542 − 229`, which silently counts the **205 non-`.md`** files under
`.softhouse/handoff/` (114 `.txt`, 30 `.py`, 26 `.out`, 18 `.sh`, 11 `.zsh`, 2 `.go`, and a
`.patch`, `.mod`, `.json`, `.gitkeep`) as handoffs "using the `<id>-<slug>.md` convention".
Source 2 `continue`s on every one of them (`if not base.endswith(".md")`). Of the remaining
108, a further **29** are `A2-<n>.md`, which *do* key correctly for A2 ids — so the genuinely
inert population is ~79, not 313.

**The change's own instrument disagrees with its own prose, in the same file.** The runtime
note it now prints reads:
`337 handoff .md path(s) tracked on main (EXACT `<id>.md` only -- see source 3 for the rest)`
[`out/60-readylist-t350.txt`, line 15].

The finding (P-22: source 2 was near-inert) stands and is correct in kind. Only the cardinal is
wrong — which is P-80 precisely: it is now restated in the shipped module, in the handoff and
in the capture, and the file it is restated in is the one the whole program reads.

**Reproduce:**
`git ls-tree -r --name-only b102875c -- .softhouse/handoff | awk -F/ '{print $NF}' | grep -c '\.md$'` → 337;
`… | grep -cE '^[Tt][0-9]+\.md$'` → 229; the difference is 108. [`out/ho-b102.txt`]

---

### C-T449-4 — LOW — "24 paths, **every one** under `.softhouse/capture/t286-t268-retry/`" is 23 + 1

The measurement that the handoff §2(b) and the `id_pattern` docstring both cite as *forcing*
the leading anchor. Re-measured: **24** paths on main name t268 — **23** under
`.softhouse/capture/t286-t268-retry/` and **1** under
`.softhouse/reviews/t291-review-t286/out/rerun-t268-battery.txt`, which is **T291's** review
directory, not T286's. [`out/50-owning-mentioning.txt`; `git ls-tree -r --name-only main |
grep -i t268 | grep -v t286-t268-retry`]

The count 24 is right, OWNING=0 / MENTIONING=24 is right, and the conclusion is right. The word
"every one" is not, and it is restated in the shipped docstring.

---

### C-T449-5 — LOW — `MAX_REFS_PROBED = 8` converts REFUSE → DEMOTE when the carrier sorts past position 8

`refs_carrying_content` probes `refs[:8]` of a `sorted()` list and pushes the remainder into
`unprobed`, which forces `indeterminate` → **demote**. If a real carrier sorts after position 8
and none of the first 8 carries content, the demotion fires and the carrier is never named.

**Driven RED.** Fixture case **H**: 9 name-matching refs for T950, the only carrier
(`softhouse/zz-t950-real`) last in sort order —
`RED relocated REFUSE → GREEN indeterminate DEMOTE` [`out/31-drive.txt`].

**Not live.** Census of every id nameable from a local head: **max fan-out today is 3**, and
**0 ids are at or over the cap** [`out/40-realrepo-attack.txt`]. The `indeterminate` text does
say the signals did not all run, and it does print `"%d further name-matching ref(s) were NOT
probed (cap %d)"`, so it is declared rather than silent. Rated LOW on that basis, but it is a
fail-open shape and the cap should probe by *cheapest-first* or raise with the population.

---

### C-T449-6 — LOW — `main_tree()`'s cost is stated as two different numbers in two places

Code comment (rt_t350.py:1010–1012): *"0.070s for 9,730 paths … net +0.029s once"*.
Handoff §6: *"`main_tree()` … **0.083 s**, once per process"* and *"net: +0.083 s once"*.
Measured here: `main_tree()` **0.0967 s** cold, raw `git ls-tree -r main` **0.0856 s**, raw
handoff-only listing **0.0446 s**, net additional **0.0410 s** [`out/70-cost.txt`]. All three
figures are the same measurement to within host noise; the defect is that the change carries
two of them. P-80 again — derive the second site from the first.

---

### C-T449-7 — LOW — a live worker that has not yet made its first commit loses an accidental protection

Observed live, on this reviewer's own branch, at the moment of dispatch:

```
RED   T449  WIP: MERGED    … The work LANDED …          RECONCILE WOULD: REFUSE to demote
GREEN T449  WIP: STILLBORN … it is UNSTARTED. DEMOTED.  RECONCILE WOULD: demote to needs_retry
```
[`diff out/62-readylist-main.txt out/60-readylist-t350.txt`]

GREEN is *correct* — nothing had been committed. It is recorded only so the driver knows the
change removes a protection that used to exist by accident: a worker doing long analysis before
its first commit is now demotable. `wrapper` mode only reconciles when
`foreign_live_session_in_repo()` says no session is live, so this is guarded — but the guard is
now the only thing standing there.

---

## CLAIMS RE-DERIVED AND CONFIRMED

**Claim 1 — the predicate.** Read from the shipped bytes and exercised in every arm by
`bin/21-partition-passes34.py`. Accurately described, with the two gaps at C-T449-1/2.

**Claim 2 — OWNING vs MENTIONING.** Confirmed in substance, and stronger than the author
claimed. `T268`: OWNING=0, MENTIONING=24, `landed_evidence` → **not flagged**. `T286`:
OWNING=27 → flagged. Sweeping **all 354** ids nameable from a tracked path component on main,
the anchor drops exactly **5** (T268, T269, T405, T408, T900) and **none of them is a case the
code would act on** — T268/T269 are genuinely unfinished, T405/T408 are `done`, T900 is a
filename inside a probe prompt. **The fix loses no real case on main.** [`out/50-owning-mentioning.txt`]
Cardinal corrected at C-T449-4; the ref-side analogue of the same rule *does* lose a case, at
C-T449-2.

**Claim 3 — non-uniform polarity. IT PARTITIONS.** 256 states enumerated —
{6 branch states + 2 instrument-failure states} × {found, found-but-incomplete, none, unrun}
× {8 ref-store outcomes} — by *running* `_branch_wip_core` and `reconcile_action` with the two
leaf probes stubbed:

```
states enumerated: 256 ; states with NO usable verdict: 0
absent 32 demote · commits 32 demote · indeterminate 8 demote · merged 32 REFUSE ·
merged-unverified 8 REFUSE · name-only-refs 1 demote · relocated 6 REFUSE ·
stillborn 8 demote · unstarted 1 demote · unverified 128 demote
```
[`out/21-partition-passes34.txt`]

**No state with no verdict. No state with two verdicts. Every kind maps to exactly one of
REFUSE / demote.** This is not the seven-arm-lock situation and the author's design is sound in
that respect. (The 7 `AttributeError` states my first pass reported were **my artifact** — the
module copy had no `branch_sweep.py` beside it, which forces `carriers is None` in the real code
and makes those combinations unreachable. Recorded here so the first transcript
`out/20-partition-t350.txt` is not misread.)

What does *not* hold is that the polarity is a function of the evidence: **4 of 4** evidence
groups contain both polarities once branch state varies (PASS 3). Two of those splits are the
author's declared design (`unrun` probe → withhold on the ancestor leg, demote on the absent
leg — implemented exactly as §3 states). The other two are C-T449-1.

**Claim 4 — the calibration. CONFIRMED, and the arithmetic reconciles to the commit.**
Re-run today with T350's own population definition: **174** heads are 0-ahead-and-ancestor with
a parseable id, **173 keep `merged`**, **1 flips**. The author's 175/173/2 differs by exactly
the movement the brief predicted: `softhouse/T350-reconcile-content` (+2 commits) and
`softhouse/T412-driver-selfgrading` (+7) have both left the population, and
`softhouse/T449-review-t350` — this reviewer's own branch, cut at the dispatch commit — has
entered it. 175 − 2 + 1 = **174**. **The `173` is reproduced exactly.**
[`out/11-explain-175.txt`]

With my own narrower id regex (`T<digits>` only, 201 of 689 heads exercised) the population is
157, keep 156, flip 1 — same conclusion, different denominator, and the denominator difference
is entirely T350's regex admitting `A2-<n>` ids. **Zero real merges flip, in both populations.**
[`out/10-calibration.txt`] Every flip is listed, not counted.

**Claim 5 — the four real cases. RE-DRIVEN, all four.** On my own synthetic fixture (built from
`git init`, not a clone of the repo), against RED loaded by path and sha256-verified equal to
`main`'s bytes:

```
A/T339  name-only rescue ref            relocated REFUSE  ->  name-only-refs DEMOTE   CHANGED
B/T431  branch AT the dispatch commit   merged    REFUSE  ->  stillborn      DEMOTE   CHANGED
C/T421  branch gone, files ON MAIN      merged    REFUSE  ->  merged         REFUSE
D/T428  branch gone, review ON MAIN     merged    REFUSE  ->  merged         REFUSE
```
[`out/31-drive.txt`] The RED is main's bytes: `sha256 3d7fef805a55bf21…` for both
`/tmp/t449/mods/rt_main.py` (from `git show main:…`) and the working-tree file.
The supporting counts are exact: **70** paths on main name t421, **33** under
`.softhouse/capture/t421-t406-conditions/`; **36** name t428, **35** under
`.softhouse/reviews/t428-review-t421/`.

**Claim 6 — the must-block controls. E and F BLOCK BEFORE AND AFTER.**
`E/T351` and `F/T442` — a live ref carrying real content for the id, recorded branch gone —
are `relocated`/REFUSE under **both** RED and GREEN [`out/31-drive.txt`]. The refusal was not
silently dropped. I then spent the bulk of this review trying to construct a ref that *should*
block and no longer does, and found **three**: C-T449-1 (G), C-T449-2 (K), C-T449-5 (H).

**Claim 7 — the structural finding. CONFIRMED by grep on the shipped bytes.**
`branch_wip(` appears at exactly three lines in each module: the definition, `reconcile():1596`,
`main():1790`. `reconcile()`'s subject list is `live = [t for t in tasks if t.get("status") ==
"in_progress"]` (:1540); `main()`'s is built by `if t.get("status") == "in_progress":
live.append(...); continue` (:1761–1762), and every other non-terminal status `continue`s past
it into `ready`/`blocked`. So for `needs_review` (T421) and `needs_retry` (T428) **the
reconciler was never asked** — the old code's silence was not a defect in the predicate. The
READY path is therefore the right site, and `_landed_flag` is wired into **both** the READY
listing (:1886) and the BLOCKED listing (:1890), which between them carry every non-terminal
non-`in_progress` task. `--json` does not carry the flag; I looked for `--json` consumers in
`.softhouse/bin/`, `.claude/skills/` and `docs/` and found **none** other than the usage line
in `ready-tasks.py` itself, so nothing is missing it today.

**Claim 8(a) — Source 2 was near-inert.** Confirmed in kind; cardinal wrong, see C-T449-3.
**Claim 8(b) — T286 is live-partially-landed. CONFIRMED exactly.** 27 tracked paths on main
whose component begins with `t286`; `softhouse/t286-t268-retry` is **2** commits ahead of main
(`73483f58`, `b6f0a770`) and `merge-base --is-ancestor` returns **1** — not an ancestor. It is
the only `!! WORK BEARING id … IS ALREADY ON MAIN` flag raised on the live tasks.json, over
46 READY + 8 BLOCKED tasks [`out/60-readylist-t350.txt`].

**Claim 9 — cost. CONFIRMED to within host noise.** 9,730 paths ✓ (printed by the tool itself).
`landed_evidence` per task **0.00382 s** (author 0.0034). Ref probe, 2 git calls, **0.092 s**
(author ~0.16). READY listing, 54 tasks, **0.130 s** (author ~0.18 for 53). `MAX_REFS_PROBED`
**= 8** ✓, and unprobed ⇒ `indeterminate` ⇒ demote ✓ (verified by enumeration, not by reading).
The `main_tree()` figure is the one with two spellings — C-T449-6. [`out/70-cost.txt`]

**Claim 10 — wiring (P-45). CONFIRMED, every citation exact, by grep on the real files.**
`mn.gerege.nbfi.softhouse-program.plist:14` → `/Users/buv/gerege-nbfi/.softhouse/bin/fire-program.sh`
under `ProgramArguments` on a `StartCalendarInterval`;
`fire-program.sh:2732` → `/usr/bin/python3 "$SCRIPT_DIR/ready-tasks.py" "${args[@]}"` with
`args=(--reconcile --fire … --repo … --no-live-session-established-out-of-band)` (:2723), inside
`reconcile_tasks_json()` (defined :2692), called from the normal tail **:3242** and the signal
path **:2151**; `.claude/skills/softhouse-program/SKILL.md:183` → *"Use `python3
.softhouse/bin/ready-tasks.py`"*, which reaches `main()` and therefore `_landed_flag`.
**The changed code is on the unattended path.**

**Scope. CLEAN.** `git diff --name-only main...softhouse/T350-reconcile-content` is 19 paths:
`.softhouse/bin/ready-tasks.py`, `.softhouse/capture/t350-reconcile-content/**`,
`.softhouse/handoff/T350-reconcile-content.md`. Nothing else — `conformance.sh` and
`fire-program.sh` untouched, as claimed.

---

## THE BAR, AND THE TOOL

**`bash .softhouse/conformance.sh` on a clean tree — EXIT 0.**
`grep -c 'probe = '` → **1**, tested for PRESENCE before its value was read (P-84: absence is
not `down`). Probe line **verbatim**:

```
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
```
```
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
conformance:   reconciler ownership: GREEN 13/13 cells correct / RED 8/13 cells correct
conformance:   all 16 wrong ledger implementations DIED through this harness, not by hand.
```
[`out/90-bar-clean-tree-BEFORE-commit.txt`, `out/91-bar-clean-tree-AFTER-commit.txt`]

**The bar's own reconciler guard, re-run directly against T350's bytes.** `conformance.sh`
grades `ready-tasks.py` through `guard_reconciler_ownership` → `run-ownership-matrix.py
--selftest` (:2969). Run independently against T350's file:

```
GREEN LEG (shipped tool): 13/13 cells correct
RED LEG (planted T309 defect): 8/13 cells correct
SELFTEST OK: the planted T309 defect drives cell B' RED, and the shipped tool keeps it GREEN.
```
[`out/80-ownership-matrix-t350.txt`] — identical to the bar's result on main's file, so T350's
change does not weaken the one guard standing between this predicate and destroyed work.

**`python3 ready-tasks.py` on T350's bytes against the live `tasks.json` — sane and correct.**
`IN PROGRESS (5)` / `READY (46)` / `BLOCKED (8)`, exit 0. The only two differences from main's
bytes are both improvements: T449 `MERGED/REFUSE` → `STILLBORN/demote` (correct — no commits),
and the single `!! WORK BEARING id T286 IS ALREADY ON MAIN` flag (correct — 27 paths, branch
2 ahead, not an ancestor). One flag over 54 non-terminal tasks; no noise.
[`out/60-readylist-t350.txt`, `out/62-readylist-main.txt`]

**`--json` still parses.** `json.load` succeeds; keys `blocked`, `in_progress`, `ready`,
`unresolved_edges`; counts **46 / 5 / 8 / 0**, agreeing with the text output.
[`out/61-json-t350.txt`]

---

## INSTRUMENTS

| file | what it establishes |
|---|---|
| `bin/10-calibrate.py` | calibration over all 689 local heads, my own id regex |
| `bin/11-explain-175.py` | the same with T350's population definition — reconciles 175 → 174 |
| `bin/20-partition.py`, `bin/21-partition-passes34.py` | the 256-state enumeration, passes 1–4 |
| `bin/30-fixture.sh`, `bin/31-drive.py` | synthetic repo; cases A–J RED vs GREEN |
| `bin/32-case-k.sh`, `bin/33-drive-k.py` | case K — work under another task's directory |
| `bin/34-proposed-fix-probe.py` | the C-T449-2 repair, verified not to reintroduce T339 |
| `bin/40-realrepo-attack-census.py` | are G and H live on the real repo? (0 and 0) |
| `bin/50-owning-mentioning.py` | the anchor over all 354 ids on main |
| `bin/70-cost.py` | independent cost re-measurement |

**Where I looked, for every "not found" above:** `.softhouse/bin/` (all `*.py`, `*.sh`),
`.softhouse/launchd/*.plist`, `.claude/skills/softhouse-program/SKILL.md`,
`.claude/skills/softhouse/SKILL.md`, `docs/`, `.softhouse/conformance.sh`, and the full
`git ls-tree -r --name-only main` (9,730 paths). No invoker outside those was searched for.
