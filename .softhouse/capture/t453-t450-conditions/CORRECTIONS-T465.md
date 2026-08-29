# Corrections to T453's record — filed by T465

T465 held the conditions from `T461`'s independent review of `T453`. Three of them are
corrections to statements T453 recorded. Each is re-derived here rather than inherited from
T461, with the drive that produced it named. `.softhouse/handoff/T453-gate-state-set.md` is
outside T465's edit grant, so the corrections are recorded HERE, beside T453's own evidence,
rather than by rewriting the handoff.

---

## 1. FU-T453-1's stated blocker DOES NOT REPRODUCE  (C-T461-3)

**What T453 recorded** (handoff §6, and the FU table): extending the cheap tier to *run*
`check-capture-namespace.sh` is blocked because *"`cheap-subset.sh` materialises its tree with
`read-tree`+`checkout-index` and **not** as a real work tree, so `check-capture-namespace.sh`'s
`git rev-parse --show-toplevel` would grade the caller's tree — the T165/T201 defect. Fixing
that means giving the cheap subset a real scratch work tree, **which is a design change, not a
micro-fix**."*

**Re-derived by T465**, with a control, at
`.softhouse/capture/t465-lock-frontier/instruments/40-cheap-tier-blocker.sh`:

| arm | tree | `NAMESPACE-CENSUS` |
|---|---|---|
| CONTROL | the caller's own work tree | `dirs=237` |
| ARM | the materialised tree of `HEAD~40`, under `cheap-subset.sh`'s exact environment | `dirs=219` |

and `git rev-parse --show-toplevel` under that environment returns the **materialised**
directory, not the caller's.

**The figures differ, so the two trees are distinguishable and the guard graded the materialised
one.** The three exports `cheap-subset.sh` already makes — `GIT_DIR`, `GIT_INDEX_FILE`,
`GIT_WORK_TREE` — are what redirect `--show-toplevel`; a `read-tree`+`checkout-index`
materialisation is not invisible to git, it is a work tree declared by environment rather than
by `.git`. **The blocker as stated is not there. It is a small change, not a design change.**

The instrument REFUSES rather than concluding when the two arms agree — the first run, against
`HEAD`, came back `distinguishable=NO` (both `dirs=237`) and said so instead of claiming a
result. That is the arm that makes the reported `YES` mean something.

**What survives from T453, unchanged:** the *obligation*, not the blocker. T165/T201 require the
graded root to be **READ BACK and asserted**, not assumed. A cheap tier that runs this guard must
still assert which root it graded; what it does not need is a redesign of the materialisation.

**Scope note:** T465 did not extend the cheap tier. That is FU-T461-3's work and it needs the
root readback designed with it.

---

## 2. The rejected "exclude `capture/**` only" alternative is 84.0 %, not ~87 %  (C-T461-5a)

Re-derived from the same window by
`.softhouse/capture/t465-lock-frontier/instruments/50-coverage-remeasure.py`, which CHECKS the
shipped `state_path()` case block before computing anything and refuses if it has moved:

```
T465-COVERAGE: window=400 entries=630 cheap_shipped=335 cheap_captureonly=336
               captureEntries=27 reviewsEntries=43
```

* rule as shipped (h2 excludes `capture/` **and** `reviews/`): **335/400 = 83.8 %**
* rejected alternative (exclude `capture/` **only**): **336/400 = 84.0 %**
* **difference: ONE commit**, not the three points "~87 %" implies.

Both figures are **upper bounds**: clause (k) is not modelled, and that limit applies equally to
both rules, which is what makes the *difference* sound even though each absolute figure is a
ceiling. The decision T453 made does not change — it gets **cheaper to defend**.

**A declared discrepancy, not argued shut:** T461 reports 629 name-status entries and
`RESUME.md=90`; T465's selector reports **630** and **92**. The three load-bearing figures
(335, 336, 27+43=70) agree exactly. The difference is in the entry enumeration, not in the
verdict, and T465 did not chase it down.

## 2b. The `(h2)` comment priced its own exclusion at half  (C-T461-5b)

The gate comment said *"27 entries"*. Measured: `capture/` = 27, `reviews/` = 43, and clause
(h2) excludes **both** — **70 entries**. Corrected in `.softhouse/hooks/driver-push-gate.sh`,
with the note that the entry count and the commit count are different denominators and only the
second one decides which path a push takes (the ~4-point coverage cost stands).

---

## 3. `CTRL-A-LOCK` rested on a seeded row for a tree that could not be attested  (C-T461-7)

`drive-arms.sh`'s `CTRL-A-LOCK` models the fire-lock cycle: the PREP commit **deletes** the
tracked lock, `seed_full` writes a `FULL` row for that prep tree, and the measured push then
**adds** the lock back.

C-T461-7's objection is exact, and it is a corollary of C-T461-1: **before T465's repair, a real
`FULL` attestation for that prep tree could not exist.** A full bar on a lock-deleted tree took
`check-dead-path-frontier.sh` to `REFUSED rows=125 pinned=108 added=17`, which the wiring turns
into a failed HARD guard — exit 2 with no probe line. The arm's control was therefore standing in
for something the program could not produce.

**T465's repair removes the objection rather than answering it.** With the 17 sites repaired, the
lock-released tree is no longer red on the frontier, so a `FULL` row for the prep tree is now
achievable in principle. Measured, both arms, at
`.softhouse/capture/t465-lock-frontier/out/RESULTS.txt`.

**What is still true and is recorded in `drive-arms.sh` itself:** `seed_full` is a *seed*. It
writes a row without running a bar, so the arm measures the GATE's behaviour on an addition and
never the bar's on the prep tree. That was always the arm's purpose, and it is now stated in the
file rather than left to be re-derived.
