# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-080001` — **IN FLIGHT. BATCH 1 = 6 WORKERS DISPATCHED. NOT CLOSED.**

Written and pushed **BEFORE the first worker was spawned** (STEP 0 standing obligation, P-85). If you are
reading this and no `claude` process owns this repo, **these six workers are DEAD** and their worktrees may
hold uncommitted work. Demote each to `needs_retry`, not `in_progress`, and check
`git log --oneline main..softhouse/<TASKID>-*` for rescued WIP. Branches are **uppercase** `softhouse/T326-…`.

### What this fire found on arrival

- **Oracle UP**, confirmed by running the bar rather than by trusting the fire args:
  `bash .softhouse/conformance.sh` → **exit 0**, `probe = up` (line PRESENT, checked for presence first per
  P-84), **46 parity vectors / 7884 cells**, 11/11 wrong ledger implementations DIED. Main is GREEN.
- **T324 was mis-reconciled.** The wrapper demoted it to `needs_retry` because its branch "does not exist in
  this repo" — it did not exist because it had **already been merged and deleted** (`a08a64e2` + merge
  `d36863ad`, 14 files / 2338 insertions). Corrected to `done`. **Branch-absence is not work-absence**;
  filed as `FU-RECONCILE-1` against the wrapper's reconcile step.
- Five of the previous fire's seven workers left **real rescued WIP** on their branches (T326: 20 commits,
  T272: 6, T306: 4, T277: 4, T282: 1). The fire died on a `five_hour` rate limit, not on a defect. **This
  batch resumes those branches; it does not rebuild them.**

### Batch 1 — sole-writer table (edit sets disjoint by construction)

| Task | Branch | Owns (sole writer this batch) | WIP resumed |
|---|---|---|---|
| **T326** | `softhouse/T326-frontier-host-state` | `.softhouse/conformance.sh`, `guards/dead-path-frontier.*` | 20 commits |
| **T306** | `softhouse/T306-admit-gate-adjudication` | `nexus/…/conformance/admit.go`, `openingbalance_test.go`, `.softhouse/reviews/T306/` | 4 commits |
| **T272** | `softhouse/T272-goenv-graft` | `.softhouse/bin/go-env.sh` | 6 commits |
| **T277** | `softhouse/T277-shapelaw-salvage` | `.softhouse/gates.md` | 4 commits |
| **T282** | `softhouse/T282-pnumber-drift` | `.softhouse/patterns.md` | 1 commit |
| **T329** | `softhouse/T329-date-zone-disagreement` | `.softhouse/capture/t329-audit-date-zone-disagreement/` | new (docs) |

Held back deliberately so a single owner exists per file: `T301`/`T279` (also name `fire-program.sh`),
`T310`/`T311`/`T313`/`T303`/`T267` (also name `conformance.sh`), `T322`/`T307` (also name `admit.go`, and both
are formally `dependencies: [T306]`).

### Batch 2 — the point of the fire, gated on batch 1

**`T328` — promote T327's two ACCEPTANCES and kill `ledger-wrong-date-rules-always-refusing`.**
`dependencies: [T327 done, T326, T306]`. T327 banked every byte last fire, so **no oracle contact is required
or permitted**. The hole it closes is live right now: the store pins only the **refusing** side of both date
rules, so **a port that refuses every dated entry passes LDG-REFUSE-04 and -05 and survives the entire
corpus** — the identical mutant shape T305 killed for opening balances. The deliverable is a dead mutant, not
two files.

Also unblocked by batch 1: `T325` (T324 now `done`), `T307`, `T322`.

## Pause reason

**None — work is in flight.**

---

## BATCH 2 — dispatched after T306/T272/T329 merged. **LIVE.**

| Task | Branch | Owns (sole writer) |
|---|---|---|
| **T325** | `softhouse/T325-adopt-attestation` | `.softhouse/guards/repo-state-attest.sh`, **`.softhouse/bin/fire-program.sh`** |
| **T330** | `softhouse/T330-reconcile-merged-work` | `.softhouse/bin/ready-tasks.py` |

Still live from batch 1: **T326** (`conformance.sh`, frontier pin), **T277** (`gates.md`), **T282** (`patterns.md`).

**T325 owns `fire-program.sh` while a fire is running from it, and that is SAFE, measured not assumed.**
T309's probes [`fire-program.sh:67-79`]: zsh 5.9 does not slurp a script, so an **in-place** rewrite (same
inode) mid-run executes the rewritten tail — but **every git operation that lands a change writes a NEW inode
and renames over the path**, which cannot reach the running shell's open fd. Landing through git is safe;
`sed -i ''` / `cat >` / python `open(path,"w")` against the live checkout is not.

**Merged this fire so far:** T306 (`3da08fbb`), T272 (`16c59715`), T329 (`61c0f382`).

---

## BATCH 3 — **T328 DISPATCHED. LIVE.** This is the task the fire exists for.

`softhouse/T328-date-rule-promotion`. All three dependencies merged: T327 `done`, T326 `6c3d0787`,
T306 `3da08fbb`. **No oracle contact required or permitted** — T327 banked every byte with sidecars and a
99-entry manifest precisely so this task needs none.

**The hole:** the store pins only the REFUSING side of both date rules, so **a port that refuses every dated
entry passes `LDG-REFUSE-04` and `LDG-REFUSE-05` and survives the entire corpus.** The deliverable is a
**dead mutant**, not two files.

Sole writer of `.softhouse/vectors/`, `.softhouse/conformance.sh`, `dead-path-frontier.pin`,
`nexus/internal/apps/ledger/conformance/`.

**Merged this fire:** T306 `3da08fbb` · T272 `16c59715` · T329 `61c0f382` · T277 `e8374743` · T326 `6c3d0787`.
**Still live:** T282 (`patterns.md`), T325 (`fire-program.sh`, `repo-state-attest.sh`), T330 (`ready-tasks.py`), T328.

**Bar on `main` right now:** exit 0, probe PRESENT and `up`, 46 parity vectors / 7884 cells, LEDGER 5/5/29,
11/11 wrong impls dead, dead-path frontier 109 == pinned, corpus 1214.
