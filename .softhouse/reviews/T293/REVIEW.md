# T293 — ADJUDICATION of the driver's unreviewed census-pin decision

**Verdict: UPHELD-WITH-REPAIR.**
**Branch:** `softhouse/t293-census-pin-adjudication`
**Subject:** the row `.softhouse/capture/t271-b1-t219/probe_tmp_dependency_t271.sh | TARGET=/tmp/t234_matrix2.txt`
added to `HOSTSTATE_PIN_TEMP_ASSIGN_LIST` by the driver at the close of fire `20260823-080004`,
with no reviewer, to return the bar from `exit 2` to `exit 0`.

**The decision stands. Two of the reasons given for it were measured FALSE.** The row survives on
a ground the driver did not state, and the probe it protects carried a fail-open in its own
evidence line — the exact claim the pin was rested on.

Every number below was produced this fire on this host. Nothing is quoted from the driver's
paragraphs without re-deriving it.

---

## 0. How the bar was read

`bash .softhouse/conformance.sh` (bash, never `sh` — exit 3 is the wrong-interpreter refusal).

Baseline, `/tmp/t234_matrix2.txt` ABSENT:
`VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared`,
probe line PRESENT (`reference oracle (https://localhost:8443/...) probe = up`), frontier 11 == pinned 11,
census 18. The reference oracle (Fineract) was REACHABLE throughout.
[`evidence/00-baseline-bar.txt`]

**P-84 was applied at every red read** — *"exit 2 with no probe line printed at all is NOT an
oracle outage; four exit-2 paths run before the probe prints, one of them a failed HARD guard.
Read the line's PRESENCE first, then its value."* Both `exit 2` results in this review
(`evidence/40-red-drive.txt`, and the first param-evasion arm) were read that way: probe-line
count `0`, and the cause identified as `a HARD guard failed` on the line above, not as an outage.

---

## 1. Is the probe a MEASUREMENT or a DEPENDENCY? — **BOTH, and the guard is about the half the driver did not address.**

Driven, not reasoned. The fail-open linter was run against the identical tree, changing only
whether `/tmp/t234_matrix2.txt` existed.

| | residue ABSENT | residue PRESENT |
|---|---|---|
| probe's classification | **TIER 3**, `C1 :44 dead absolute path: /tmp/t234_matrix2.txt` | **unclassified** |
| TIER 3 totals | 7 files / 14 findings | 6 files / 13 findings |
| **frontier** | **11 rows** | **11 rows** (identical set) |
| **full bar** | **PASS exit 0** | **PASS exit 0** |

[`evidence/10-lint-residue-ABSENT.txt`, `evidence/11-lint-residue-PRESENT.txt`; the diff between
the two lint runs is exactly 4 lines — the TIER 3 count and the probe's 3-line entry.]

**Answer to the brief's question "can its fail-open TIER be decided by this host's `/tmp` along
any path?" — YES, measured.** The probe's tier is TIER 3 or nothing depending on a file in `/tmp`.

The driver's defence — *"the probe reads the path, records whether it was present, and RESTORES
THE STATE IT FOUND — it is a measurement, not a dependency"* — is a statement about the probe's
**runtime**. The guard's rule is about the **static** readability of the literal by a classifier
that calls `os.path.exists`. The probe could restore state perfectly and still have a
host-decided tier, because the linter never runs it. **The restoration argument is a non-sequitur
for this guard**, and it would have justified the row even if the row moved the frontier.

**But the row is nonetheless correctly pinned**, because the guard's own text already covers this
case and says so: *"THE PIN IS DELIBERATELY WIDER THAN THE DEFECT, AND SAYS SO … Refusing the
SHAPE rather than the currently-live subset is the choice."* The probe has the shape. TIER 3 is
not on the frontier, so the row moves no graded figure **today** — and the guard explicitly
declines to claim otherwise: *"It does not claim the seventeen rows below currently move a tier —
most do not."* The `t239-r11-rerun/50-red-drive.sh` row is pinned on identical grounds.

**Latent risk, stated because it is one line away.** The probe is TIER 3 only for want of a C2
finding. A single `|| echo` added to it would make it `C1+C2` = TIER 1 with the residue absent and
`C2` only = TIER 2 with it present — a **frontier tier-token flip driven by host state**, which is
`02-escape-matrix-fix.sh`'s original defect exactly, and `T254b` established the pin carries the
tier token. Nothing currently prevents that edit. This is an argument for keeping the row visible
in the census, not for removing it.

---

## 2. Would "take the path as a parameter" be a repair, or COSMETIC EVASION? — **Evasion, measured.**

A file was written that depends on the identical path in the two spellings an author would reach
for, tracked, and the bar run:

```
TARGET="${1:-/tmp/t234_matrix2.txt}"     # default-valued positional
TMPROOT=/tmp
TARGET2="$TMPROOT/t234_matrix2.txt"      # one concatenation
```

**Result: `conformance EXIT=0`. Host-state census `18` — unchanged. Fail-open frontier `11` —
unchanged.** The file is invisible to *both* instruments while depending on the same path on the
same host in the same way. [`evidence/20-param-evasion.txt`]

Mechanism, and it is worth naming precisely: the census ERE requires the value to *begin* with the
literal (`NAME=["']?/(tmp|private/tmp|var/tmp)/`), and C1's `RE_ABSPATH_LOC` requires an absolute
path of **two or more segments** in a location-reading position — so `TMPROOT=/tmp` is one segment
and misses, and `"${1:-...}"` and `"$TMPROOT/..."` do not begin with `/`.

An earlier arm of this drive carried an incidental `|| echo "(no hits)"` and *was* caught — at
TIER2, by C2, i.e. for a completely unrelated reason. Removing that one reassurance arm made it
vanish entirely. That is the honest form of the result: **nothing about the path evasion was
detected by anything.**

**So parameterising is strictly worse than pinning.** Pinning leaves the site enumerated in a list
a reviewer reads; parameterising blinds the census and the linter together and leaves the
dependency intact. `mktemp` remains inapplicable for the reason the driver gave — a fresh random
path measures nothing — though not for the *premise* the driver gave (§4).

---

## 3. Is this the move P-88 rejects? — **No, and it is provable rather than arguable.**

**P-88's rule:** *"an instrument's verdict must depend on nothing outside the repo … when a
guard's tier can be flipped by host state, the guard is not measuring the property; it is
measuring the host."* P-88's specimen: the bar was green **if and only if** the residue existed.

**Measured this fire: the bar is `PASS exit 0` with the residue PRESENT and `PASS exit 0` with it
ABSENT.** [§1 table; `evidence/00-baseline-bar.txt`, `evidence/11-lint-residue-PRESENT.txt`]

That is the whole answer. The pin manufactures no green out of host state — there is no host state
left for it to manufacture a green from, because T273 removed it. The driver's distinction
(*a census asking for a genuine site plus its justification, versus manufacturing a green*) **holds**,
and T271's own refusal to create the file or move `FAILOPEN_PIN_FILE_LIST` remains the correct
contrast case.

**The distinction holds, but the driver did not establish it.** The driver argued it from the
probe's restoration behaviour — which §5 shows was itself an unverified claim. The proof is the
two-arm bar measurement, and it was not taken. A correct conclusion resting on an unmeasured
premise is the shape this program keeps paying for; that is why this verdict is not a bare UPHELD.

---

## 4. FINDINGS

### F1 — HIGH — The pin's justification cites a hard-coding that the same fire deleted.

`conformance.sh` states, present tense:

> *"That probe's entire purpose is to measure whether the bar's colour depends on ONE SPECIFIC
> ABSOLUTE PATH that another instrument hard-codes (t234's 02-escape-matrix-fix.sh:6). Naming the
> path IS the measurement"*

**Measured.** `02-escape-matrix-fix.sh` line 6 is now:

```
# T273 — THE FIXTURE IS NOW SELF-OWNED SCRATCH, NOT A LITERAL PATH IN /tmp.
```

`C=/tmp/t234_matrix2.txt` was removed by T273 in commit `7e85a3e` — **merged in the same fire, hours
before the pin row was written.** The justification's central premise was already false when it was
recorded. `git grep -n t234_matrix2 -- '*.sh' '*.py'` returns no assignment in that file.

**Reproduction:** `sed -n 6p .softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh` ;
`git log --oneline -3 -- <that file>`.

**Consequence:** none for the *decision*, which survives on the ground in §6 — but the recorded
reasoning is what a future author will cite, and the driver chose to record it in `conformance.sh`
precisely so it would be cited. **Repaired** in this branch.

### F2 — HIGH — `restoredAsFound=1` was an ASSERTION, not a measurement — and it is the exact claim the pin rested on.

The probe printed, at both terminal lines:

```
T271-TMPDEP: REFUTED contingent=0 foundPresent=$WAS_PRESENT restoredAsFound=1
```

`restoredAsFound=1` was a **hard-coded literal**, emitted **before** `exit`, therefore **before the
`EXIT` trap that performs the restoration had run**. It was structurally incapable of being a
measurement.

**Red drive.** A copy with `trap restore_found_state EXIT` replaced by `:` was run with the file
found **PRESENT**:

```
BEFORE: /tmp/t234_matrix2.txt
exit=1
AFTER : ABSENT
T271-TMPDEP: REFUTED contingent=0 foundPresent=1 restoredAsFound=1
```

**It found the file present, left it deleted, and still claimed it had restored it.**
[`evidence/30-neutered-probe-red-drive.txt`, `red/t293-neutered-probe.sh.txt`]

This is a fail-open in the evidence line of a probe **written to expose fail-opens**, and it is the
sentence the driver quoted as the ground for pinning. **Repaired** — the claim is now emitted by
the trap itself, after restoring, from a fresh `[ -e ]`:
`T271-RESTORE: foundPresent=N nowPresent=M restored=0|1`.

### F3 — MEDIUM — Restoration is not universal: SIGKILL leaves the host changed.

The probe's header claimed restoration *"on every exit path including an error."*

**Driven by observation, not by reading the source** (brief, test 5). Each arm sets a known state,
runs the probe, and reads the state back; the signal is landed at t=9s, inside READING B, when the
probe holds the file **created** while it had found it **absent**:

```
ARM 1    found=ABSENT   probe exit=1  after=ABSENT    OK   T271-RESTORE: foundPresent=0 nowPresent=0 restored=1
ARM 2    found=PRESENT  probe exit=1  after=PRESENT   OK   T271-RESTORE: foundPresent=1 nowPresent=1 restored=1
ARM TERM found=ABSENT   signalled while PRESENT  exit=143  after=ABSENT    OK
ARM INT  found=ABSENT   signalled while PRESENT  exit=1    after=ABSENT    OK
ARM KILL found=ABSENT   signalled while PRESENT  exit=137  after=PRESENT   FAIL
```

[`evidence/50-restoration-by-observation.txt`, `instruments/50-restoration-by-observation.sh`]

`SIGKILL` cannot be trapped by any shell, so this is disclosed rather than fixed; `INT`/`TERM`/`HUP`
are now trapped **explicitly** so the intent is inspectable rather than inferred from bash's signal
semantics. The header no longer over-claims.

**Why this is not academic.** T271's own header records that an earlier draft deleted the file
unconditionally and *"would silently turn a CONCURRENT worker's conformance bar red for reasons
invisible to it."* Today that harm is gone — but only because the bar is green in **both** arms
(§1), which is a property of **T273's repair**, not of the probe. If the probe ever regains a C2
finding (§1, latent risk), residue left by a SIGKILL becomes visible to other workers again.

**Note on my own rig, because it nearly reported a vacuous pass.** The first run of this instrument
signalled at t=1.6s and reported `ARM KILL OK` — the signal had landed **before** the probe inverted
the state, so the arm measured nothing and scored as a success. The instrument now **checks the
window first and reports INCONCLUSIVE (counted as a failure) when the signal misses**, per P-91's
corollary: *"a test rig is inside the trust boundary of the thing it grades; check that it cannot
pass vacuously before quoting its counts."* Both readings are in the evidence.

### F4 — MEDIUM — The probe's verdict silently INVERTED, and nothing runs it, so nobody noticed.

The probe now exits **1** in both arms: `T271-TMPDEP: REFUTED contingent=0`. Its own legend read:

> *"1 = REFUTED: the classification did not move with the file, so T271's explanation of the red
> bar is WRONG and must not be quoted"*

**That reading is now false, and it repudiates the evidence P-88 rests on.** The hypothesis was
true when written and was **repaired** by T273. The probe cannot distinguish *"never true"* from
*"true, then fixed"* — both produce `A == B == C`.

This is **P-45** — *"a test-only guard is not a guard … verify the path that actually executes in
CI/conformance calls it, not merely that a test does"* — in its purest form: nothing invokes the
probe, so its conclusion inverted across a fire and no one saw it. This program has now recorded
that lesson **six** times (P-89 counts five: `manifest.py verify`, `t44_float_roundtrip_v3`, T173's
float guard, `guard_ledger_invariants`, T238's linter).

**Repaired in text, not in wiring.** The exit legend now reads `exit 1 = T273's repair HOLDS` /
`exit 0 = the repair has REGRESSED`, and the conclusion prints both readings and tells the reader
which line of the tree decides between them. **Wiring is deliberately NOT done** — per T261's
sharpening of P-89, *"an orphan may not acquire a caller until the fail-opens in it are repaired,
because wiring a liar is strictly worse than leaving it unwired"* — the fail-open (F2) is now
repaired, but wiring costs ~19s per bar run and crosses this task's file partition. **Filed, not
written down** (see §7): *prose does not fire on the next fire.*

### F5 — MEDIUM — The guard's own printed evidence line contradicts the pin it enforces. **NOT REPAIRED — outside partition.**

The guard prints, every run:

```
conformance:   literal /tmp, /private/tmp or /var/tmp path to a name: 18, pinned at 17.
conformance:   census == pinned (all 18 site(s), by path and source line).
```

`17` is a **hard-coded literal** in the `say` in the guard body; the pin has **18** rows. The two
lines contradict each other on screen, and during the red drive it printed `19, pinned at 17`. The
guard's stated reason for printing every run is *"A guard that speaks only when it fires cannot be
told from one that never ran"* — a hard-coded count in that line is the rot **P-86** names:
*"THE PATTERN IDS THEMSELVES ROTTED, IN THE FILE THAT NAMES THE ROT."*

**Not repaired here.** That line is in the guard body, outside T293's declared partition
(`HOSTSTATE_PIN_TEMP_ASSIGN_LIST` and its surrounding reasoning comment, and nothing else in that
file). A reviewer that reaches outside its partition costs two tasks a clean merge. The correction
is bracketed in the comment block, and the one-line patch is in §7.

**Exact patch:** in `guard_no_host_state_in_lint_corpus`, replace
`… path to a name: $m, pinned at 17."` with a count derived from `$want` —
`p="$(LC_ALL=C grep -ac '' "$want" || true)"; [ -n "$p" ] || p=0` then `… pinned at $p."`
A derived figure cannot rot; a literal one already has.

### F6 — MEDIUM — The census's guarantee is narrower than its stated purpose: **four of the five sites carrying this exact literal are NOT censused — and one of the four is a file this review created.**

The guard states its claim as: *"no NEW literal shared-temp assignment can enter the fail-open
linter's corpus without a source edit to this file that a reviewer reads."* That claim is TRUE as
written. But the driver's paraphrase in the pin justification — *"a CENSUS … whose stated purpose is
that no new site enters unseen"* — is **wider than what the instrument delivers**, and the gap is
measurable.

The population is the fail-open linter's corpus: files matching a **repo-wide-search** idiom. Sites
carrying `/tmp/t234_matrix2.txt` as a line-initial assignment, measured with the guard's own ERE:

| site | censused? | why |
|---|---|---|
| `capture/t271-b1-t219/probe_tmp_dependency_t271.sh:44` `TARGET=` | **yes** (pinned) | only because **line 30 is a COMMENT** quoting P-81's ``*`git grep`/`grep` exits 1 on NO MATCH*``. The probe performs no repo-wide search at all. |
| `capture/t253-portability/instruments/50-t234-residue-probe.sh:22` `RESIDUE=` | no | no repo-wide-search idiom |
| `reviews/t254-harness-portability/instruments/70-t234-residue-adjudicate.sh:30` `RESIDUE=` | no | no repo-wide-search idiom |
| `reviews/t285-review-t273/instruments/90-residue-watch.sh:10` `P=` | no | no repo-wide-search idiom |
| `reviews/T293/instruments/50-restoration-by-observation.sh:13` `T=` | no | no repo-wide-search idiom — **this review's own instrument** |

`git grep -l -E '<selector>' -- <the non-censused ones>` exits **1** — none of them match. The list
is the guard's own ERE, narrowed to this literal, over the tracked corpus with every T293 artefact
already committed:
`git grep -n -E '^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*=["'"'"']?/(tmp|private/tmp|var/tmp)/t234_matrix2' -- '*.sh' '*.py'`

**The last row is the finding demonstrating itself.** T293 wrote a new instrument this fire that
assigns the identical literal absolute path to a name, committed it, and **the census did not gain a
row** — 18 before, 18 after, `census == pinned`, bar `exit 0`. A site entered, and it entered unseen.
That is the guarantee gap in one observation, produced accidentally while testing the guarantee.

**Two consequences worth stating plainly.** The pinned row is censused for an *incidental* reason:
rewording one comment would drop the T271 probe out of both the census and the linter's corpus, with
no change whatever to its behaviour — a third evasion route, alongside §2's two. And a new
host-state site added to a non-search script enters **completely unseen**.

This is not a new hole — it follows from the population the guard already declares, and the guard
explicitly disclaims completeness (*"It does not claim to have found every way a graded run can read
state outside the repo"*). It is recorded because the **justification for the pin leans on the wider
reading**, and the wider reading is not what the guard enforces.

**Where I looked:** `git grep -n t234_matrix2 -- '*.sh' '*.py'` — **40 hits across 12 files**
(the remainder are narration in `t273-residue`, `t285-review-t273`, `t254-harness-portability` and
`t271/run.sh`, plus `conformance.sh`'s own comment block, none of them line-initial assignments);
the census ERE over the full tracked `*.sh`/`*.py` corpus (18 rows, all pinned); the linter's output
for any frontier row absent from `FAILOPEN_PIN_FILE_LIST` (none).
*Correction against my own first pass: I initially recorded "10 hits" from a `head`-truncated read.
The figure above is the untruncated count.*

---

## 5. Does the census still EXCUSE anything it should not? — **No. Driven RED.**

A genuinely new accidental site was written the way an unwary author would write one — a repo-wide
search instrument parking its scratch at a literal absolute path — and **tracked** (`git add`, since
the census reads `git grep`):

```
SCRATCH=/tmp/t293-accidental-scratch
mkdir -p "$SCRATCH"
git grep -n -E 'MoneyHelper' -- '*.java' >"$SCRATCH/hits.txt" || echo "(no hits)"
```

**Result — `conformance EXIT=2`, probe-line count `0`** (read as the guard firing, per P-84 — the
line above it is `a HARD guard failed`, and the oracle answered seconds earlier):

```
conformance: THE HOST-STATE CENSUS IS NOT THE PINNED CENSUS (- pinned, + measured):
+.softhouse/reviews/T293/red/t293-new-accidental-site.sh | SCRATCH=/tmp/t293-accidental-scratch
conformance: EXIT 2 — no verdict is available. This is NOT a pass.
```

Census read `19, pinned at 17`. Removing the site returned the bar to `exit 0`, census `18`.
[`evidence/40-red-drive.txt`, `evidence/41-green-restored.txt`]

**The census fires.** Both red-drive files are preserved as `red/*.sh.txt` — the `.txt` suffix keeps
them out of the census population (`git grep -- '*.sh' '*.py'`) and out of the linter's corpus
(`f.endswith((".sh",".py"))`) while keeping the artefact readable and re-runnable: `cp` to `.sh`,
`git add`, run the bar.

---

## 6. WHY THE ROW SURVIVES — the ground the driver did not state

The probe's subject path must stay a literal **not** because another instrument still hard-codes it
(F1: it does not), but because the probe is now a **regression test that T273's repair holds**:

- `exit 1` = the classification does not move with the file = **the repair holds**;
- `exit 0` = a literal path is back in the linter's corpus and the bar's colour is host-decided again.

Naming the path is still the measurement — of the *opposite proposition*. A `mktemp` path would
measure nothing, then as now. And §2 shows the only other candidate "repair" is evasion. So:
**pin, with the row visible, and the reasoning corrected.**

---

## 7. REQUIRED FOLLOW-UPS — to be FILED as dispatchable tasks, not left as prose (P-89)

1. **F5 — derive the printed pin count.** One line in `guard_no_host_state_in_lint_corpus`; patch in
   §F5. Currently prints `pinned at 17` against an 18-row pin on every run. Owner must hold
   `conformance.sh`. *Red-drive requirement:* change the pin's length and show the printed figure
   follows it.
2. **F4 — do NOT wire the probe. Decided here, against my own first recommendation, on a measurement.**
   Before recommending wiring I checked whether the regression is already covered, and **it is —
   by this very census.** `02-escape-matrix-fix.sh` **is** in the census population
   (`git grep -l -E '<selector>' -- <it>` exits 0). Driven: appending `C=/tmp/t234_matrix2.txt` to
   that file makes the census ERE match it at the new line, which is a `+` row, which is `exit 2`;
   the file was then restored and the restore verified by an empty `git diff --stat`.
   **So reintroducing T273's exact defect already turns the bar red every run, through a wired
   guard.** Wiring the T271 probe as well would add ~19s per bar for a redundant check — and P-45's
   lesson is *"verify the path that actually executes calls it"*, which is satisfied by the census,
   not by a second instrument. The probe's remaining value is diagnostic and archival: it explains
   *why* the row is red in a way a census row does not. **Recorded as a deliberate decision not to
   wire, which is what P-89 asks for — "a declared orphan is acceptable; a silent one is not."**
3. **F6 — decide whether the census population should be the SEARCH-INSTRUMENT corpus or ALL tracked
   shell/python.** Demonstrated live: T293 committed a new instrument assigning the identical
   literal and **the census did not gain a row**. Widening the population is not obviously right —
   the guard's tie to the linter's corpus is what makes "can move a TIER" true of every row, and a
   repo-wide population would pin many sites that no classifier reads. But the gap should be a
   *decision on record*, not a side effect of the selector. *Red-drive requirement:* whatever is
   chosen, add a non-search script with a literal temp assignment and show the guard's behaviour
   matches the decision.
4. **Latent, §1.** Consider whether a probe pinned in the host-state census should be prevented from
   acquiring a C2 finding, since that alone converts it from an off-frontier TIER 3 into a
   host-decided frontier tier flip. Analysis task; no red drive implied.

---

## 8. Non-negotiables

No monetary code path was touched. Money remains integer minor units, MNT (ISO 4217 numeric 496,
minor unit 2); no float was introduced or altered — the bar's own wire-float census reports
`float-shaped tokens … ALTERED by a binary-double round trip 0` and
`float-shaped PRESENT 0, ALTERED 0` on the recorded-request arm, unchanged from baseline.
No database, driver, payment rail, vendor or deposit surface is involved. "Oracle" throughout this
review means the **reference oracle (Fineract)** at `https://localhost:8443`, never Oracle Database.

## 9. Final bar

```
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
frontier == pinned (all 11 rows, by path)
census == pinned (all 18 site(s), by path and source line)
reference oracle probe = up
```
with `/tmp/t234_matrix2.txt` **ABSENT**, which is the state this review found and the state it left.
[`evidence/70-bar-after-repair.txt`]
