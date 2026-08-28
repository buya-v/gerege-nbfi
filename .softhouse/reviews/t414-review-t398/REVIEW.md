# T414 — INDEPENDENT REVIEW OF T398 (`P-100`, `P-101`, and the out-of-grant guard change)

**VERDICT: `APPROVED WITH CONDITIONS`.**

Three conditions, each drivable, none of them touching the change that mattered. **The out-of-grant
guard edit stays.** I reproduced the latent fatal on pre-T398 `main` with a paired control, and I proved
the fix is load-bearing and narrow by driving it in both directions in a throwaway copy. T398's central
claim — *the pattern register was frozen at 98 forever, silently, by a guard* — is **TRUE**, and I
re-derived it rather than accepting it.

- Reviewer branch: `softhouse/T414-review-t398`, based on `main` at `daf8e6fb`.
- Under review: `softhouse/T398-measured-but-backwards` at `c81278e3`.
- Instruments and transcripts: `.softhouse/reviews/t414-review-t398/drives/`, `…/out/`.
- Engine: `Python 3.9.6`, `git version 2.50.1 (Apple Git-155)`, `bash`.
- Nothing in this review edits `.softhouse/patterns.md`, `.softhouse/conformance.sh`, or any file
  outside `.softhouse/reviews/t414-review-t398/`.

---

## SUMMARY OF FINDINGS

| id | severity | subject | disposition |
|---|---|---|---|
| `F-T414-1` | CONFIRMED | the latent fatal is real; reproduced on pre-T398 `main` with a paired control | the change stays |
| `F-T414-2` | CONFIRMED | the fix is **not** a widening — load-bearing (ARM C) and narrow (ARM B) | the change stays |
| `F-T414-3` | MINOR | `NEGATIVE_CONTROL_IDS` has **no staleness check**, unlike the file's two other declaration mechanisms | FOLLOW-UP (fold into `T415`) |
| `F-T414-4` | CONFIRMED | `P-100` and `P-101` were genuinely free; no third collision minted | — |
| `F-T414-5` | CONFIRMED / SHARPENED | `P-101`'s cardinals re-measured; **T398's own table is already stale at T398's own branch tip** | strengthens `P-101` |
| `F-T414-6` | MINOR | `P-101` breaches its **own duty 1**: it demands "its exact invocation" and gives neither the instrument path nor the invocation | **CONDITION C1** |
| `F-T414-7` | MINOR | `P-100` argues "why this is not `P-98`"; `P-101` gives no "why this is not `P-7`", though its rule sentence leans on `P-7` | **CONDITION C2** |
| `F-T414-8` | MEDIUM | T398's follow-up on `T386`'s lying instrument exists **only in a handoff** — no task is filed. That is `P-45`, over `P-101`'s own duty 4 | FOLLOW-UP (file the task) |
| `F-T414-9` | MEDIUM | the `DO-NOT-APPLY` marking is correct, but `T359`'s **committed, applyable `.patch`** carries no pointer to it | **CONDITION C3** (driver, not T398) |
| `F-T414-10` | INFO | agreed: `range(1, max(...))` is a **class**; one second instance named | `T415` owns the sweep |
| `F-T414-11` | CONFIRMED | "`main` was already red" independently confirmed at `4cf77a42` | — |

**No money defect, and no float.** The diff is 709 added lines of markdown, one Python predicate line and
one bash drive. The only `float` tokens in the added lines are the three sentences *asserting* there is no
float. No `ojdbc` / `oracle.jdbc` / MySQL / MariaDB / `:1521`, no US payment vendor. "Oracle" appears four
times in added lines and every one is the reference oracle (Fineract) or a transcript quotation.
I separately re-derived the no-float claim `P-100` makes about its own subject matter:
`nexus/internal/apps/ledger/conformance/admit.go:1199-1215` — `strings.IndexByte(text, '.')`, then a byte
walk comparing against `'0'`. No `strconv`, no division, no exponent. **`10013` never becomes a number.**

---

## 1. `F-T414-1` — THE LATENT FATAL IS REAL. REPRODUCED, WITH A CONTROL.

*Instrument: `drives/t414-drive-gap-guard.sh` (written from the brief and from reading the checker, **not**
by editing T398's drive). Transcript: `out/T414-gap-guard-drive.txt`.*

T398's claim rests on `check-pnumber-citations.py:860` as `main` carries it:

```
gaps = [n for n in range(1, max(reg) + 1) if n not in reg]
```

Confirming the *shape* proves nothing — the question is whether it detonates. So I built a **pair** whose
only difference is a pattern filed above the reserved id, and ran `main`'s checker, unmodified, on both.

| arm | tree | result | rc |
|---|---|---|---|
| **0-CTL** | `main` @ `daf8e6fb`, `patterns.md` **untouched** | `ids=98 gaps=none`, `VERDICT PASS` | **0** |
| **0-FAT** | the same tree + **one** appended `DEFN_BOLD` line at 100, nothing else | `ids=99 gaps=[99]`, **`FATAL REGISTER GAP P-99: cited ids may resolve to nothing`**, `VERDICT FAIL -- 1 fatal (register 1, directive-file 0)` | **1** |

**That is the whole defect, in one controlled pair.** The reserved id `P-99` sits *beyond* `max(reg)=98`
and is never scanned; the instant any pattern is filed at 100, it becomes an *interior* gap and the guard
kills the run. Note what 0-FAT reports: **`register 1, directive-file 0`** — the gap is the *only* fatal.
Nothing else about filing a pattern above 99 is unlawful. **The guard, alone, is what froze the register.**

Two details that make it worse than "a guard that fires early":

1. **The reason printed is the inverse of the truth.** `cited ids may resolve to nothing` is exactly
   backwards: `P-99` resolves to nothing **by construction**, declared 650 lines above in the same file
   (`:61`, and the `NEGATIVE_CONTROL_IDS` dict at `:203`), with a committed instrument named as depending
   on it (`.softhouse/capture/t255-dec2-rev8/instruments/15-p5-probe.py:59,73`). A worker hitting this
   would have read a message telling them to go **define** the one id the file forbids defining.
2. **`P-4` is the right classification, and I verified the citation resolves** —
   `patterns.md:1239`, *"Latent harness defects detonate on first real use — the first promotion is a
   test of the rig."* Armed at `T282` (`fbdada27`, when the register's high-water mark was 96 — which is
   why the in-source comment's "written when `max(reg)` was 96" is **correct** and not in conflict with
   the handoff's "98 at detonation"). It waited through 16 further patterns.

**The fix is motivated. It does not come out.**

## 2. `F-T414-2` — THE FIX IS NOT A WIDENING. DRIVEN IN BOTH DIRECTIONS.

The change is:

```
gaps = [n for n in range(1, max(reg) + 1)
        if n not in reg and n not in NEGATIVE_CONTROL_IDS]
```

I drove the counter-case the brief asked for, plus the control on the exemption itself, plus the selftest.
All against T398's branch tree materialised into a throwaway root; the repo tree was never mutated.

| arm | input | result | rc | want |
|---|---|---|---|---|
| **A** | T398's branch as landed | `ids=100 gaps=none`, `VERDICT PASS` | **0** | 0 |
| **B** | **UNDECLARED** hole — `P-97`'s definition line deleted, every citation left | `ids=99 gaps=[97]`, **`FATAL REGISTER GAP P-97`** + 5 directive `UNDEFINED`, `VERDICT FAIL -- 6 fatal` | **1** | 1 |
| **C** | ARM A's input, exemption **neutralised in a throwaway copy of the checker** | `ids=100 gaps=[99]`, **`FATAL REGISTER GAP P-99`**, `VERDICT FAIL -- 1 fatal` | **1** | 1 |
| selftest | branch checker `--selftest` | `SELFTEST: PASS` | **0** | 0 |

`rc 0 / 1 / 1`, matching T398's report exactly. **ARM C is the one that decides the question**: with the
exemption removed and *nothing else changed*, ARM A's own input goes red on the reserved id. The exemption
is therefore **load-bearing** — ARM A is green *because of* it, not for some unrelated reason. ARM B is the
other half: an id that is **not** declared is still fatal, and it drags five directive-file fatals with it.

**I accept T398's argument, and I checked its premise rather than its wording.** The exemption is bound to
`NEGATIVE_CONTROL_IDS`, the *same* dict the citation scan already consults at `:563`. So an id can be
excused from the gap scan only if the same declaration already excuses it from the citation scan. There is
no second, looser predicate. It is the narrowest possible expression of "this absence is deliberate", and
it is symmetric with the file's own treatment of declared collisions and declared dangling ids.

### `F-T414-3` (MINOR, FOLLOW-UP) — but the narrowness rests on a comment, not on a check

This is the one thing T398's argument understates, and it is worth writing down because T398's own
reasoning is what exposes it. T398 says `NEGATIVE_CONTROL_IDS` *"already requires every entry to name the
instrument that relies on it."* **It requires that in a comment.** Nothing verifies it. Compare the file's
two sibling mechanisms, both of which self-invalidate and both of which are FATAL when stale:

- `DECLARED_MARKER` — *"A declaration for an id that is NOT actually colliding is itself rot… Fatal."*
  Enforced at `:880-886`.
- `DANGLING_MARKER` — *"A DANGLING declaration must be TRUE on both counts, or it is a silencer."*
  Enforced at `:890+`.
- `NEGATIVE_CONTROL_IDS` — **no check at all.** Its three uses are the definition (`:203`), the citation
  exemption (`:563`) and the JSON dump (`:947`).

Today the dict has exactly one entry, it is correct, and adding another requires a source edit that a
reviewer would see. So this is **not** a defect in T398's change and **not** a condition. But T398 has just
made that dict load-bearing in a *second* place, and the guarantee it now carries — "an undeclared hole is
still fatal" — degrades the moment an entry names an instrument that no longer cites the id. Then the
register acquires a permanent, silent hole, which is the same failure class T398 just closed.

**Drive for the follow-up:** for each `n` in `NEGATIVE_CONTROL_IDS`, assert (a) `n not in reg`, and (b) the
named `path:line` exists and the id is actually cited there; fatal otherwise. RED drive: repoint an entry
at a nonexistent instrument and show the checker refuse. GREEN control: the real dict, untouched, passes.
Fold into `T415` — it is the same file and the same reviewer will be in it.

## 3. `F-T414-11` — "`main` WAS ALREADY RED" IS TRUE, AND I RAN IT

T398's §3 justifies the whole excursion partly on `main` being red before it started. Confirmed, by
materialising `main` at the dispatch commit and running the checker of that era:

```
4cf77a42$  python3 .../check-pnumber-citations.py
PNUMBER-CITATIONS: register=.softhouse/patterns.md ids=98 gaps=none in-file-collisions=2 …
PNUMBER-CITATIONS: FATAL UNDEFINED .softhouse/RESUME.md:42 P-100 -- P-100 is defined in neither register
PNUMBER-CITATIONS: VERDICT FAIL -- 1 fatal (register 0, directive-file 1)      rc=1
```

`.softhouse/RESUME.md` is in `DIRECTIVE_EXACT` (`:110`), and the driver's own dispatch row wrote the literal
token `P-100` while naming the id T398 should take. Worth recording precisely: **current `main` is green
because the driver later removed the token from `RESUME.md`, not because the id got defined.** So the fatal
was cleared by deleting the citation, and T398's branch is what actually resolves it.

## 4. `F-T414-4` — THE P-NUMBERS. VERIFIED FREE, THREE WAYS, INDEPENDENTLY.

The brief is right to insist: this repo has shipped a P-number collision before. I did not reuse T398's
greps.

1. **Whole-tree token enumeration on `main`**, using the checker's own `CITE` semantics
   (`(?<![A-Za-z0-9_])P-([1-9][0-9]*)(?![0-9])`, so `HTTP-404` and `STEP-578` do not count — a loose
   `grep -oE 'P-[0-9]+'` reports spurious `P-404` and `P-578`, and I checked that both are substrings and
   **not** citations). Every occurrence of `P-100` / `P-101` on `main`:
   - `.softhouse/handoff/T392-vacuous-pass-pattern.md:31-32` — `T392`'s note about its own near-miss;
   - `.softhouse/tasks.json:5837` — the driver's status note on T398;
   - `.softhouse/tasks.json:6077`, `:6110` — the `T412` and `T414` dispatch descriptions.
   **All four are prose about taking the id. No definition anywhere.** (`tasks.json` is in neither
   `DIRECTIVE_EXACT` nor `DIRECTIVE_PREFIX`, which is why these are report-only and `main` stays green.)
2. **Mechanically, from the register itself**, which does not depend on my greps: my ARM 0-CTL ran the
   checker on unmodified `main` and got `ids=98 gaps=none`. `max(reg) = 98`. **There is no definition at
   99, 100 or 101 on `main`.**
3. **After the change**, ARM A reports `ids=100 gaps=none in-file-collisions=2` — 98 + two new, with the
   reserved id correctly excluded and **no new collision**. `in-file-collisions` stayed at **2**, the
   declared pair. T398 minted no third collision.

`P-99` re-read at both sites and confirmed permanently reserved: `patterns.md:3253` (*"`P-99` is NOT in
that list and must never be"*) and the dict at `check-pnumber-citations.py:203`, which names its dependent
instrument. **T398 did not use it.** `P-131` and `P-261` are in the `PNUMBER-DANGLING-CITED-IDS: 131, 261`
marker and are citations, not definitions — confirmed.

**Citation integrity of the two new entries.** I resolved the load-bearing ids by hand rather than trusting
the checker's aggregate: `P-4` `:1239` ✓, `P-7` `:1284` ✓, `P-35` `:803` ✓, `P-84` `:2813` ✓,
`P-86` `:2854` ✓, `P-98` `:3411` ✓. Each says what the new entries claim it says.

## 5. `F-T414-5` — `P-101`'s CARDINALS, RE-MEASURED. THE ROT IS WORSE THAN T398 RECORDED.

*`T386`'s `t386-r3-measure.sh` run **unmodified**, scope `-- .softhouse`, `git grep -c` summed. Transcripts:
`out/T414-r3-remeasure-MAIN-PRECOMMIT.txt` (main `daf8e6fb`) and `out/T414-r3-remeasure-T398BRANCH.txt`
(T398's branch tip, materialised).*

| term | `T234` | `T386` @ `9eedfe4d` | T398 @ `4cf77a42` | T398 after-commit @ `f1e2d670` | **T414 @ `main` `daf8e6fb`** | **T414 @ T398 branch tip** |
|---|---|---|---|---|---|---|
| `-E '\bmain\b'` | 0 | 114 | 138 | 147 | **139** | **155** |
| `-E 'bmainb'` | 0 | 114 | 138 | 147 | **139** | **155** |
| `-F 'bmainb'` | not run | 114 | 138 | 147 | **139** | **155** |
| `-E 'ma(in\|ni)'` | not run | 33,751 | 35,633 | 35,653 | **35,934** | **35,674** |
| `-F 'ma(in\|ni)'` — control | not run | **0** | 7 | 11 | **7** | **13** |
| `-P '\bmain\b'` | 17,646 repo-wide | 22,524 | 23,111 | 23,113 | **23,178** | **23,119** |
| `-E 'bzzqabsenttermb'` — negative control | not run | **0** | 3 | 5 | **3** | **7** |

Everything the brief said would have moved has moved, and I confirm every one of T398's corrections:

- **the brief's `114` and `22,524` are stale.** They were stale when T398 measured them and they are more
  stale now.
- **the ERE degradation is byte-exact, not approximate.** All three forms produce one output with a single
  sha256 — `ba031fbdd5b417bbb0df854806458b4522491f62de9c89bd312c5f13327e0f49` on `main` today, a *different*
  sha from T398's `f4f1f7…` because the bytes changed, which is itself the point. `-E '\bmain\b'` **is**
  `-F 'bmainb'` on this engine.
- **`T386`'s two controls are contaminated, live, right now.** ARM E on `main` prints
  `-E '\bzzqabsentterm\b' = 3` and `-E 'bzzqabsenttermb' = 3` and then narrates
  **`>>> both 0, they AGREE`**. On T398's branch it reads 7 and 7 and prints the same sentence. **I watched
  the instrument lie.** T398's follow-up 1 is confirmed by observation, not by report.

**The finding T398 did not make, because it could not: the count is a function of `(branch, commit)`, not
of time.** `main` reads **139** and T398's branch reads **155** *on the same clock*, differing by exactly
the documents T398 wrote. And **T398's own published table is already stale at T398's own branch tip**:
147 → **155**, 11 → **13**, 5 → **7**, with no work in between beyond T398 finishing its handoff. The rule
outran its author twice inside one branch.

### Judgment: **does `P-101` survive its own evidence rotting? Yes — with one gap, which is `C1`.**

The test I applied: *can a reader who finds every number in this entry falsified still act correctly?*

- **Yes, on structure.** The table's columns are keyed to **head shas**, not to "today". Read as
  `(sha, scope, term) -> count`, the rows are not invalidated by movement; they are a *time series*, and
  the series is the evidence. My two new columns extend it rather than contradicting it — which is only
  possible because the earlier columns were labelled.
- **Yes, on self-awareness.** The `THIS ENTRY IS ITSELF AN INSTANCE` paragraph shows `138 → 147` measured
  one commit apart and states plainly that recording the rule invalidated the numbers the rule cites. It
  closes with the correct instruction — *"so the next reader re-runs it instead of quoting it"* — and
  points at `P-84`, read the absence not the value.
- **Yes, on the rule.** The rule sentence and duties 1–4 contain **no cardinal at all**. Nothing a reader
  must *obey* depends on 138 or 147. The numbers are exhibits; the rule is stated as a property. That is
  precisely the form `P-7` demands, applied to itself.
- **No, on one thing — and it is `P-101` failing its own duty 1.** See `F-T414-6`.

### `F-T414-6` (MINOR) → **CONDITION C1**

`P-101` duty 1: *"Never state a self-referential count as a standing fact. State it with its head sha, its
scope, its exact invocation, and the date."* The entry gives the **head sha** (`4cf77a42`), the **scope**
(`-- .softhouse`), the **date** (via the fire id) and a **transcript path** — but it does **not** give the
**exact invocation**, and it does not give the **instrument's path**. It says only *"`T386`'s own
instrument, unmodified"*. A reader who takes the entry's own advice and tries to re-run it must first go
find `.softhouse/reviews/t386-review-t381/instruments/t386-r3-measure.sh`, which is in a *different task's*
review directory. That is a small friction guarding the one behaviour the whole entry exists to produce.

**Drive:** add to `P-101`, inside T398's own grant:

```
bash .softhouse/reviews/t386-review-t381/instruments/t386-r3-measure.sh <repo-root>
```

and name the instrument path in prose. **Verify by:** a reader who has only `patterns.md` open can
re-derive the table without opening any other file first. (And note in one clause that the count is a
function of the *branch* as well as the commit — `main` 139 vs T398 branch 155, measured above.)

### `F-T414-7` (MINOR) → **CONDITION C2**

`P-100` carries an explicit **"Why this is not `P-98`"** section, and it is the best paragraph in the
diff — it distinguishes *polarity* from *vacuity* and shows that a `P-98`-compliant control would have
failed to catch `T359`'s remedy. `P-101` has no counterpart, yet its own rule sentence hands the
load-bearing half to another id: *"Such a count is **a fact about today's corpus, not a property**
(`P-7`)"*. `P-7` (`:1284`) reads *"A proof that asserts a FACT ABOUT TODAY'S CORPUS goes stale on the next
promotion — assert the property."* A sceptical later reader can reasonably ask whether `P-101` is `P-7`
with a worked example attached, and the entry does not answer.

I judge that it is **not**, and the entry should say why in two sentences: `P-7` says a corpus count is
dated. `P-101` says something `P-7` does not — that the count moves **in a specific, self-confirming
direction**, toward the program's own commentary, so the drift manufactures *false positives that look
exactly like confirmations*; and that **a negative control built from a literal term is destroyed by the
act of publishing the control**, which is duty 4 and has no analogue in `P-7`.

**Drive:** add the two sentences. **Verify by:** the same test `P-100` passes — state a case `P-7` would
wave through and `P-101` would catch. (`T386`'s absent-term control is that case: `P-7` has nothing to say
about it; `P-101` predicts it dies, and it did, `0 → 3 → 5 → 7`.)

### `F-T414-8` (MEDIUM, FOLLOW-UP) — the follow-up on the lying instrument is filed nowhere executable

T398's handoff §7.1 says `t386-r3-measure.sh` should grow a **computed** expectation so it goes red when it
rots. That is exactly right and it is `P-101` duty 4 applied to the artefact that taught it. **But it lives
in a handoff.** I searched `.softhouse/tasks.json`: `t386-r3-measure` appears **zero** times, and the only
occurrence of `both 0, they AGREE` is inside my *own* dispatch description at `:6109`. `T415` is properly
filed for the `range(1, max(...))` class; **nothing is filed for this.**

That is `P-45` — *a fix whose only enforcement is that someone remembers it* — sitting directly on top of
the duty `P-101` exists to impose, in the same fire that filed it. The instrument is committed evidence, so
the repair is forward: a **new** wrapper or a **new** instrument that computes the expectation, not an edit
to `T386`'s bytes.

**Drive:** file the task. Its RED drive is free and already exists: run `t386-r3-measure.sh` on `main`
today and show ARM E printing `both 0, they AGREE` over `3` and `3`. GREEN: the replacement asserts the
absent-term count against a **derived** expectation (a nonce generated at run time, or the count of the
program's own documents partitioned out) and **exits non-zero** on today's tree, forcing the number to be
re-read rather than narrated.

## 6. `F-T414-9` — THE `DO-NOT-APPLY` MARKING. CORRECT WHERE IT IS; THE WRONG ARTEFACT IS UNMARKED.

**What T398 did is right, and I checked it clause by clause.** The marking is inside `P-100` under the
heading **`T359`'S REMEDY IS `DO-NOT-APPLY`**, so it travels with the rule instead of sitting in a note
that rots separately. It:

- **names the exact patch** — `impl.go:276-279`, returning `(*Refusal, nil)` with HTTP `422` instead of a
  Go `error`;
- **names four consequences**, (a) a fabricated wire status and globalisation code that no observed refusal
  carries, against nine existing `&Refusal{…}` sites that all carry an observed `403`; (b) the grading
  inversion; (c) an invented `amount_minor` admitted to the money-cell census; (d) the kill criterion made
  vacuous;
- **is explicit that only the patch is condemned** — *"`T359`'s **diagnosis** stands and `T360` built on it
  correctly; only the patch is condemned"*, plus *"`T360` was right to refuse it"*;
- **is correct-forward** — it does not rewrite `T359`'s committed review, which `T316` established may not
  be done.

I also verified the evidence the marking rests on, against the **transcripts** rather than the prose, and
found T398's §2a table exact line for line:
`DRIVE-A2-…-FULL.log:273` `FAIL 1 cells (0 money)`, `:276` `PASS 7 FAIL 1`, `:281` `143 graded … 39 MONEY`;
`DRIVE-B2-…-FULL.log:246` the wrong-implementation banner, `:276` `PASS 11 cells (4 money)`,
`:277` `debits 10013 == credits 10013 (minor units), over 2 legs`, `:279` `PASS 8 FAIL 0`,
`:284` `153 graded … 43 MONEY`, `:479` `VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells`.
**The deliberately wrong port greens the bar and the correct port reds it. That is the finding, and it
reproduces.**

**The gap is where the marking is *not*.** The brief's test is: *a later reader finding `T359`'s review
alone must not find a confident, measured, wrong recommendation with nothing marking it.* The most
actionable artefact in that directory is not the review — it is
`.softhouse/reviews/t359-review-t352/PROPOSED-impl-refusal-routing.patch`, **78 lines of committed,
applyable diff.** I grepped the whole `t359-review-t352/` directory for `do-not-apply`, `do not apply`,
`superseded`, `withdrawn`: **nothing relevant.**

The patch header is honest and cautious — *"NOT a fix to be merged on my say-so… this patch lands only if
(a) is chosen"* — which materially reduces the risk, and I credit `T359` for it. **But that framing is the
hazard, not the mitigation:** it conditions application on a *decision* (`G-19` option (a)), and `P-100`'s
finding is that the patch is wrong **under every decision**, because it inverts the grading regardless of
which way the refusal question is settled. A future reader who resolves `G-19` as (a) will read that header
as a green light.

**Drive → CONDITION C3, discharged by the DRIVER, not by T398** — `T398`'s grant does not reach
`.softhouse/reviews/t359-review-t352/`, and it must not be widened again. Add a **new sibling file**
`.softhouse/reviews/t359-review-t352/DO-NOT-APPLY.md` (a new file, so committed bytes stay unedited),
naming the patch file, stating that `P-100` in `.softhouse/patterns.md` condemns it, that it inverts
grading under both `G-19` options, and that the diagnosis stands. **Verify by:** `ls` of that directory
shows the warning before the patch is opened, and a `grep -ril 'do-not-apply'` over the directory returns
a hit.

## 7. `F-T414-10` — IS `range(1, max(...))` A CLASS? **YES.** ONE SECOND INSTANCE NAMED.

**I agree it is a class**, and T398 was right to say it checked only one file. The class is not the literal
call — it is *any reasoning that treats an integer series derived from `max(...)` as dense, over a series
that carries a declared, deliberate absence.* The two halves are independent: a hole-scan gets it wrong by
**refusing**, an allocator gets it wrong by **minting**.

**Second instance, named, not swept —** `.softhouse/capture/t334-writer-guidance/append-p97.py:83-86`:

```
top = max(ids)
if top != 96:
    print("NOTE: register high-water mark is P-%d, not P-96. The id below may collide." % top)
```

Same reasoning on the **allocation** side. It derives the high-water mark from definition lines and knows
**nothing about the reserved id**, so its notion of "the next id" cannot exclude 99; and its guard is a
hardcoded `!= 96` that only **prints** — it never refuses. It is a one-shot capture script in the evidence
zone and is not currently wired to anything, so it is **not** a live defect. It is a clean exemplar of the
second half of the class, and `T415` should take it.

A third hit I checked and am **excluding**, so `T415` does not waste a pass on it:
`.softhouse/reviews/T84-evidence/src/classify.py:49` — `if ks != list(range(1, max(ks)+1))` — is the same
*code shape* but runs over a principal-amount sweep grid with no reserved absence in it. Shape yes, hazard
no. Its presence does support the "class, not instance" call: this idiom is habitual in the repo.

**I did not run `T415`'s sweep.** `.softhouse/bin/`, `.softhouse/guards/` and `conformance.sh` are its
scope, and `conformance.sh` is held by `T404`.

## 8. ONE PATTERN OR TWO — I JUDGED IT RATHER THAN ACCEPTING IT

**T398 is right: two.** I tried to break the decision three ways and it held.

- **Is `P-101` a corollary of `P-100`?** No. The mechanisms are different in kind. `P-100` is *polarity
  invisible from one side* — the observation "my patch made the stuck vector red" and "my patch made every
  conforming port red" are the same bytes. `P-101` is *the observer's output entering the observed
  population*. Neither derives from the other, and the decisive test is the remedies: adding a deliberately
  wrong implementation does **nothing** for a self-referential grep count, and excluding the program's own
  record does **nothing** for an inverted comparator. A corollary must inherit its parent's remedy. These
  do not.
- **Would merging restate `P-98`?** Yes, and T398 named the right reason. The only honest merged headline
  is *"a control can be wrong in a way one vantage point cannot see"*, which is `P-98`'s altitude — and
  `P-98` was merged **four days ago**, which is precisely when a near-duplicate does the most damage.
  `P-100`'s "Why this is not `P-98`" paragraph already does the harder work of distinguishing them at the
  correct altitude; a merge would throw that away.
- **The citation argument is the strongest one and it is verified.** A merged entry would be **cited** for
  its grading half and **read** for its census half, and `P-86` (`:2854`, *"the pattern ids themselves
  rotted, in the file that names the rot"*) is exactly that failure. I resolved the id: the citation is
  accurate.

Where I'd push back mildly: `P-101` is the weaker entry, not because the rule is weaker but because it is
carrying `P-7`'s water without saying so (`C2`), and because its own duty 4 is currently enforced nowhere
(`F-T414-8`). Neither is a reason to merge them.

## 9. THE OUT-OF-GRANT CHANGE — DISPOSITION

**It stays, and it was correctly handled.** Grading a worker on an out-of-grant edit, my test is: was it
*forced*, was it *minimal*, was it *declared*, and was it *driven*?

- **Forced** — `F-T414-1`. Without it, the register is frozen at 98 and no pattern can ever be filed again.
  T398's own deliverable was unlandable. There was no in-grant route.
- **Minimal** — one predicate clause. Everything else added is comment. The file is in `SELF_SOURCE_EXACT`
  (`:171`), so editing it cannot move any citation count, and I confirmed `in-file-collisions` and the
  register figures are unchanged in ARM A but for the two new ids.
- **Declared** — prominently, in the handoff's own opening, with the reasoning inline in the source.
- **Driven** — three ways, and I reproduced all three plus a fourth arm (`0-CTL`/`0-FAT`) that T398 did not
  run. **T398 applied `P-100`'s discipline to `P-100`'s own landing**, which is the right instinct and the
  reason this is approvable at all.

T398's own suggestion — that the checker's real home is `.softhouse/guards/` — is sound and should be a
follow-up, not a condition. `T415` will be in this file next; that is the moment to move it, along with
`F-T414-3`.

---

## CONDITIONS

| id | owner | condition | drive |
|---|---|---|---|
| **C1** | T398 (in grant: `patterns.md`) | `P-101` must carry the **exact invocation** and the **instrument path** it demands of everyone else, plus one clause noting the count varies by **branch** (`main` 139 vs branch 155) | a reader with only `patterns.md` open can re-derive the table without opening another file first |
| **C2** | T398 (in grant: `patterns.md`) | `P-101` must say **why it is not `P-7`**, as `P-100` says why it is not `P-98` | name a case `P-7` waves through and `P-101` catches — `T386`'s absent-term control, `0 → 3 → 5 → 7` |
| **C3** | **DRIVER** (outside T398's grant — do not widen it again) | a **new** `.softhouse/reviews/t359-review-t352/DO-NOT-APPLY.md` pointing the committed `.patch` at `P-100` | `grep -ril 'do-not-apply'` over that directory returns a hit; the warning is visible from `ls` before the patch is opened |

## FOLLOW-UPS (not blocking)

1. **`F-T414-3`** — give `NEGATIVE_CONTROL_IDS` the staleness check its two sibling declaration mechanisms
   already have. Fold into `T415`.
2. **`F-T414-8`** — **file a task** for `t386-r3-measure.sh`'s computed expectation. It exists only in a
   handoff today, which is `P-45` over `P-101`'s own duty 4.
3. Lift `check-pnumber-citations.py` from `capture/t282-pnumber-drift/bin/` into `.softhouse/guards/`.
   T398 proposed it; `T415` is the natural moment.
4. `report.go:592` — the correct-port drive prints `VERDICT: FAIL (exit 1) — 0 mismatched vector(s)`.
   Already `F-T387-1`; T398's sighting is the same defect from the other side. `T416` is in flight on the
   money-facing half of it.

---

## 10. BAR

`bash .softhouse/conformance.sh` — **`bash`, never `sh`** — from a **clean tree** after commit.
Transcript: `out/T414-BAR.txt`.

<!-- BAR-RESULT -->
