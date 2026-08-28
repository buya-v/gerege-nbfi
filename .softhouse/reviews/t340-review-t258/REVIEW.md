# T340 — INDEPENDENT review of T258 (`softhouse/T258-frontier-rot-residuals`, head `0928fa16`)

Reviewer: T340, fire `20260828-140005`. Branch `softhouse/T340-review-t258`.
Subject read **from the branch**, never from disk:
`git show softhouse/T258-frontier-rot-residuals:.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T258.md`.
Diff read with three dots: `git diff main...softhouse/T258-frontier-rot-residuals` — **19 files, +3955 / −3**.

Everything below was **RE-RUN**, not read off T258's transcripts (P-22). Two scratch worktrees at
T258's exact head were used: `/private/tmp/t340-t258` (end-to-end red drive) and
`/private/tmp/t340-probe` (perturbations). Both detached at `0928fa161fc1092c198d1df375e4083f3737315a`.

---

## VERDICT: **ACCEPT-WITH-CONDITIONS**

The repair is real. T258 did **not** type a fresher number — it made the second site READ the
first, and I proved the coupling by perturbing the pin rather than by reading the diff. Its
refutation of the brief is **correct**. Its money arithmetic is integer-only. Its scope is clean.
Six of its seven `[VERIFIED]` citations plus its manifest no-hit claim resolve exactly.

But two of its own refusal paths have never fired, and I fired one of them and found it blind:

* the fail-closed diagnostic it documents at length is **unreachable dead code** (`F-T340-1`);
* the class-level census **does not refuse a brand-new typed cardinal added to a file already on
  its pin** — the single most likely place for the next restatement to appear (`F-T340-2`), and
  `FU-6`'s proposed wiring inherits that hole verbatim.

Neither produces a false green in the graded bar, which is why this is not a REJECT. Both must be
closed before `FU-6` is wired, because a guard wired with a known hole is worse than no guard
(P-22 — *"a guard, a canary, or a control that cannot fail is worse than none — because it is
believed"*).

**Conditions C1–C4 are at the bottom and are binding on whoever lands `FU-1`…`FU-6`.**

---

## 0. THE BRIEF IS FALSE, AND T258 WAS RIGHT TO SAY SO

`F-T340-6` **[INFORMATIONAL — against the DRIVER, not against T258]**

My own dispatch, and `.softhouse/tasks.json`'s `T340` record, both say the fail-open frontier
"is now **109**". `.softhouse/RESUME.md:24` says the same ("`all 9 rows` vs a frontier of 109").

**MEASURED by me, on a bar I ran myself at T258's delivered head:**

```
:94   conformance:   /tmp/t340-t258 (git ls-files, whole repository); frontier 11, pinned at 11
:99   conformance:   frontier == pinned (all 11 rows, by path).
:139  conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
```
[VERIFIED: `out/20-BAR-T258-0928fa16.txt:94,99,139`, `bash .softhouse/conformance.sh`, exit 0.]
[VERIFIED, independently of any bar: `FAILOPEN_PIN_FILE_LIST` in `.softhouse/conformance.sh`
`:1627`–`:1637` holds **11** `TIER*` rows — counted, not read.]

**The fail-open frontier is 11. 109 is the DEAD-PATH frontier (T316/T323), a different pin
reported by a different guard on a different line.** T258's opening refutation is correct on the
world, correct on `RESUME.md:24`, and it is the *nastiest* variant of the class, exactly as it
says: the number is not stale, it is the right number for the wrong frontier, so it survives every
check that asks "is this count current?".

**One correction to the refutation itself, and it is small.** T258 writes "My dispatch text says
the frontier *is 109*". The **committed** `T258` record in `.softhouse/tasks.json` does *not*: it
says *"became 10 at T248, and is 11 since T252 [VERIFIED by the driver at 2674f7c…]"*. The 109
therefore came from the spawn prompt and/or `RESUME.md:24`, not from the task record. The
refutation is right; its attribution is one source off, and the committed record is the one a
later reader will find. **This is a refutation made to get the work right, not to escape it** —
T258 then did strictly more work than the brief asked for, which is the good case.

---

## 1. THE LIVE DEFECT — repaired, and the repair is COUPLED, not retyped

`main`'s instrument asserted the literal at two sites:

```
:74   want_line control0 control0 "frontier == pinned (all 9 rows, by path)."
:152  want_line green1   GREEN    "frontier == pinned (all 9 rows, by path)."
```
[VERIFIED: `git show main:.softhouse/capture/t243-wiring/instruments/20-failopen-red-drive.sh`.]

**BEFORE result re-derived rather than accepted** (P-22; I did not spend three more graded bars
to reproduce a deterministic string match): that needle occurs **0 times** in a real graded bar,
while the derived needle occurs **1 time**.
[VERIFIED: `/usr/bin/grep -c -aF` over `out/20-BAR-T258-0928fa16.txt` → `0` and `1`.]
Two `want_line` calls × one absent needle = the **2 failed** in T258's `10-BEFORE-red-drive.txt`.
The transcript is honest.

**AFTER — I regenerated the whole drive end to end**, three graded bars, on T258's tree, with the
new `T243_RED_DRIVE_LOG` override so committed evidence was not clobbered (T114):

```
  OK   [control0] found (1): frontier == pinned (all 11 rows, by path).
  OK   [control0] pin agreement: harness published 'pinned at 11'; FAILOPEN_PIN_FILE_LIST counts 11
  OK   [RED] exit 2 … OK [RED] no verdict line at all on the refused run
  OK   [GREEN] pin agreement: harness published 'pinned at 11'; FAILOPEN_PIN_FILE_LIST counts 11
RED DRIVE 2: 15 passed, 0 failed
```
[VERIFIED: `out/40-failopen-red-drive-RERUN.txt`, exit 0, 15 `OK` / 0 `***` counted mechanically.]
Identical to T258's claim. The RED arm still goes EXIT 2 on the planted fail-open sweep and the
instrument correctly reads the **absence** of the verdict line rather than its value (P-84 —
*"'exit 2 with no probe line' is the guard working. Read the absence, not the value."*).

**Is the count actually coupled, or is it a fresher 11?** Perturbed, not read:

| probe | perturbation | result |
|---|---|---|
| 1 (control) | none | pin block 11 lines; instrument rule counts 11; harness rule counts 11 |
| 2 | rename `FAILOPEN_PIN_FILE_LIST` → `…_RENAMED_BY_T340` | **exit 1**, `frontier == pinned` asserted **0** times, graded bars run **0** |
| 3 | insert a pin row that is not a `TIER` line | harness counts **12**, instrument counts **11** — the two-source agreement can genuinely disagree |
[VERIFIED: `out/30-adversarial-probes.txt`, script `probe/20-adversarial-derivation.sh`.]

Probe 3 matters: T258's argument for keeping the cardinal (rather than asserting the bare
`frontier == pinned`) rests on the claim that `want_pin_agreement` is a *two-source* check that
can fail. It can. The argument holds.

---

## 2. `F-T340-1` — THE FAIL-CLOSED MESSAGE IS UNREACHABLE DEAD CODE **[MAJOR / P2]**

**The claim.** Handoff, §(1): *"**Fail-closed.** If the pin block cannot be read the derivation
yields no digits and the instrument **dies with a distinct message** rather than falling back to 0
and reporting a frontier mismatch. A derivation failure and a real frontier movement are different
events."* The same claim is written into the file at `:99`–`:105`.
**It carries no `[VERIFIED]` and no `[UNVERIFIED]` marker.** (The handoff uses `[VERIFIED]` 7
times and `[UNVERIFIED]` 0 times, so the convention was in use and this claim was left unmarked.)

**MEASURED (probe 2 above): the instrument produced ZERO BYTES of output and exited 1.**
`wc -c /tmp/t340-probe2.txt` → `0`.

**Re-derivation from source.** In the delivered file:

```
 23  set -euo pipefail
109  PINNED_ROWS="$(LC_ALL=C /usr/bin/grep -c -aE '^(FAILOPEN_PIN_FILE_LIST=")?TIER[0-9]' "$PINBLOCK")"
110  case "${PINNED_ROWS:-}" in ''|*[!0-9]*) PINNED_ROWS=0 ;; esac
111  if [ "$PINNED_ROWS" -lt 1 ]; then
112–116    echo "  ***  [pin] COULD NOT DERIVE the pinned frontier cardinal …"   (5 lines)
117    exit 1
118  fi
```

`grep -c` **exits 1 when the count is zero**. A variable assignment from a command substitution
takes the substitution's exit status, and `set -e` is in force from `:23`, so the script dies **at
`:109`** — before `:110` can normalise the value and before `:111` can test it. **Lines 111–118
can never execute.** Isolated and reproduced outside the instrument:

```
$ bash -c 'set -euo pipefail; X="$(printf "" | /usr/bin/grep -c -aE "^TIER[0-9]")"; echo "REACHED, X=$X"'
$ echo $?
1                       # "REACHED" never printed
```

**Why it matters, in T258's own words.** The comment at `:103`–`:105` says a derivation failure and
a frontier movement *"are different events and reporting one as the other is the whole class this
rig exists to refuse."* As shipped the instrument reports **neither**: a bare exit 1 with no
output. And exit 1 is **also** the ordinary failure exit of this script — the last line is
`[ "$FAIL" -eq 0 ]`. So the operator cannot distinguish "the pin moved", "an assertion failed",
"the derivation broke" or "the script was killed". The distinction the whole block was written to
preserve is destroyed by the mechanism that was supposed to enforce it.

**Severity is MAJOR, not CRITICAL, and here is the honest boundary:** the behaviour is still
fail-**closed**. It does not fall back to 0, does not print a frontier, does not run a bar, does
not manufacture a green. `out/30-adversarial-probes.txt` measures all three zeroes. This is a dead
diagnostic and a false claim, not a fail-open.

**This is the P-22 shape one layer in** — a refusal path written with great care, documented at
length, and never once executed. Precisely what T258 itself argues about `sweep-ORIGINAL.sh`.

---

## 3. `F-T340-2` — THE CENSUS DOES NOT REFUSE A NEW RESTATEMENT IN AN ALREADY-PINNED FILE **[MAJOR / P2]**

This is the finding that answers the question the brief actually asked — **"can this rot recur?"**

**Source.** `.softhouse/capture/t255-frontier-rot/instruments/20-cardinal-restatement-census.py:379`

```python
got = sorted({"%s %s" % (tag, rel) for tag, rel, _n, _t in hits})
```

The pin is a **set keyed on (rule, file)**. The line number is present in the printed report and
then thrown away before the comparison. So growth is invisible whenever the new restatement lands
in a file already pinned under the same rule.

**DRIVEN, not reasoned** (`probe/30-census-duplicate-in-pinned-file.sh`, output
`out/51-census-DUPLICATE-IN-PINNED-FILE-NOT-REFUSED.txt`):

```
== PERTURB — append a NEW typed cardinal to .softhouse/reviews/t262-verdict-predicate/bar_check_t262.sh,
             which is ALREADY on the pin under R2 ==
  perturbation landed (want 1): 1
== MEASURE — does the census refuse? ==
  exit=0   <-- 0 means IT DID NOT REFUSE
  the planted line IS reported (hits): 2
    |   frontier == pinned (all 11 rows, by rule and path)
    | T258 CARDINAL-RESTATEMENT CENSUS: PIN MATCHED
```

The planted cardinal is *listed* in the report and the census still says **PIN MATCHED, exit 0**.

**Why T258 never saw it.** Its own red drive plants only into a file that is *not* on the pin:
`50-census-red-drive.sh:39-42` — `PNAME="planted-restatement"`, `PLANT="$R/$PDIR/$PNAME.sh"`,
`git add -f -- "$PLANT"`. The `+`-row arm therefore exercises only the easy input. P-22 again:
the arm that would have caught this was never written.

**Why it is not academic.** The six files on the pin today are `50-conformance-red-drive.py`,
`bar_check_t262.sh`, `95-frontier-delta.sh`, `42-bar-extract.py` and the two `t300` specimens —
i.e. **the frontier-checking instruments themselves**, which is where the next author will add the
next assertion, and where T258's own `FU-2`/`FU-3`/`FU-4` will be applied. A worker who "fixes"
`FU-3` by adding a derived line while leaving the typed one, or who adds a second typed check
alongside, gets a clean census.

**And `FU-6` inherits it.** The proposed guard body is
`if [ "$rc" -ne 0 ]; then warn "…A FRONTIER CARDINAL IS TYPED WHERE IT SHOULD BE DERIVED…"`.
It gates entirely on the census exit code. Wiring it as written installs a control that is
believed and is blind to the most likely input — P-22's definition of *worse than none*.

**Tension acknowledged, because the fix is not free.** Pinning by `(rule, file, line)` would rot on
every unrelated edit above the line — which is P-80's *other* currency and the thing T253 was
filed to fix. The right key is `(rule, file, COUNT)`: stable under reordering, sensitive to
growth. That is condition **C2**.

---

## 4. `F-T340-8` — P-45: NOTHING T258 DELIVERED IS REACHED BY `conformance.sh` **[MEDIUM]**

*P-45 — "A test-only guard is not a guard… when hardening a check, verify the path that actually
executes in CI/conformance calls it, not merely that a test does."*

**BY GREP, cited by file and line.** `LC_ALL=C grep -n` over `.softhouse/conformance.sh`
(read-only — T323 holds it exclusively this batch):

| symbol | hits in `conformance.sh` |
|---|---|
| `20-failopen-red-drive` | `:1518`, `:1621`, `:1694` — **all three are `#` comment lines**. No invocation. |
| `cardinal-restatement-census` | **0** |
| `t255-frontier-rot` | **0** |
| `rederive-provenance-T258` | **0** |
| `rederive-provenance.sh` (the original) | `:1594`, `:1601`, `:1630` — `:1630` is the `TIER1B` **pin row**, i.e. it is *linted*, never *run* |

So: the repaired red drive is a manual instrument (that is its correct role — it exists to prove
the *wired* `guard_failopen_frontier` fires, and `out/40-…-RERUN.txt` shows it doing exactly that);
the census is inert; the successor is inert.

**T258 declares this for the census, loudly and in the right place** — module docstring
`20-cardinal-restatement-census.py:101-107`, heading `STATUS — READ THIS BEFORE CITING IT (P-45)`,
and again in `FU-6`: *"It is **UNWIRED** and nobody may cite it as an enforced control until it
is."* That is the honest disclosure the pattern demands and I credit it.

**What I will not credit is the framing.** The census's own title line calls it *"the half of P-80
that does not have to be remembered"*, and the handoff sells it as the remedy for the mechanism.
Today it is a script somebody must remember to run — which is the definition of the thing it
claims to replace. **The accurate statement of the delivered state is: the rot can still recur.**
It can recur because nothing runs the census (`F-T340-8`), and it will *still* be able to recur
after `FU-6` lands, for the shape in `F-T340-2`.

---

## 5. Citation rot in the fix for citation rot

`F-T340-3` **[MEDIUM] — a `[VERIFIED]`-adjacent citation that does not resolve.**
`FU-3` says: *"Same file, `:99`: `if [ "$total" -ne 9 ]` hard-codes the exemption-census cardinal."*
`.softhouse/reviews/t262-verdict-predicate/bar_check_t262.sh` is **93 lines long**. There is no
`:99`. The line described is **`:75`**:
```
75  if [ "$total" -ne 9 ]; then echo "  EXPECTED 9 exemption census pins, got $total"; fail=1; fi
```
[VERIFIED: `wc -l` = 93; `sed -n '75p'` on both the T258 branch and `main`.]
The content of the follow-up is right — that `-ne 9` is a typed cardinal of the same class, and the
bar prints exactly 9 exemption-census rows today (`out/20-BAR-T258-0928fa16.txt:567-575`, counted).
But a follow-up written to cure P-80's *line-number* currency ships a line number that resolves to
nothing. P-80: *"the count is the same defect as the line number… bind citations by CONTENT with
the line number a non-normative hint."*

`F-T340-4` **[LOW] — off-by-one, and internally inconsistent within the same commit.**
`20-failopen-red-drive.sh:125` cites
`.softhouse/capture/t252-tier3/instruments/50-conformance-red-drive.py:122` as one of the two
trailing-period sites. The `"pinned at 11." in out2` assertion is at **`:121`**; `:122` is a
comment. The census file *in the same commit* cites `:120,121` correctly
(`20-cardinal-restatement-census.py:184`). Two artefacts of one task disagree about one line
number, in the task about restatements disagreeing.

`F-T340-5` **[LOW] — P-80 turned on the deliverable, as the brief requires.**
`20-cardinal-restatement-census.py:79` asserts, in the present tense, **"THE FAIL-OPEN FRONTIER IS
11."** It is true today and it is a typed cardinal in a second place. The census exempts it under
its own rule *"COMMENT LINES ARE NOT ASSERTIONS"* (`:50-52`) — but that carve-out is argued for
**quotations of history** (*"a `#` line quoting the rotted sentence is documentation"*), and this is
not a quotation of history, it is a live claim. Same shape as P-86 (*"the pattern ids themselves
rotted, in the file that names the rot"*). Not worth a code change on its own; worth one word —
make it "was 11 at `0928fa16`", the commit-qualified form T258 itself accepts as correct handling
in its adjudication of `42-bar-extract.py`.

---

## 6. What I checked and found CLEAN — so silence is distinguishable from not looking

**Graded bar, run by me, on T258's delivered head `0928fa16`** (not on `8e7f0652`, which is what
T258's own `72-BAR` graded, and not on a transcript):
`bash .softhouse/conformance.sh` → **exit 0, `VERDICT: PASS`** (`:563`), 46 parity vectors / 7884
cells, `frontier 11 == pinned 11` (`:94`,`:99`), dead-path frontier GREEN with an empty T323
reconciliation list (`:139`), all 9 exemption-census rows `== pinned` (`:567-575`).
**P-83/P-84 discipline observed: the probe line's PRESENCE was tested before its value** — line
`:144` exists and reads `probe = up`, `:153` `oracle probe UP`. The oracle was reachable this fire,
so no exit-2/no-probe adjudication was needed. [`out/20-BAR-T258-0928fa16.txt`.]

**Every deliverable re-run from source, none accepted from a transcript:**

| artefact | T258 claimed | T340 MEASURED |
|---|---|---|
| `20-failopen-red-drive.sh` (repaired) | 15 passed / 0 failed | **15 / 0, exit 0** |
| `20-cardinal-restatement-census.py` | exit 0, PIN MATCHED | **exit 0, PIN MATCHED**, WIDE 17 / NARROW 13 / dropped 4 |
| `50-census-red-drive.sh` | 24 passed / 0 failed | **24 / 0, exit 0** |
| `60-rederive-successor-red-drive.sh` | 17 passed / 0 failed | **17 / 0, exit 0** (ARM3 exit 2 with `PROMOTED CELLS SWEPT` **absent**; ARM4 exit 128, no count) |
| `rederive-provenance-T258.sh` | 13 files, 122 cells, 0 fail | **13 files, 122 cells, 0 fail, exit 0** |
| `rederive-provenance.sh` (original) | exit 0, 0 cells — still fail-open | **exit 0, `PROMOTED CELLS SWEPT: 0`**, `cd: /Users/buv/gerege-nbfi/.claude/worktrees/agent-ac008956278f2d6ea: No such file or directory`; that root confirmed absent by `ls` |

**The detector is not on its own frontier.** `20-cardinal-restatement-census.py:254`
(`CAL_POSITIVE = …`) is matched by WIDE `R4` and dropped by NARROW `R4`, and it does **not** appear
in the MEASURED list. Verified in `out/50-census-clean.txt`, not taken from the comment.

**Independent restatement sweep, my rules, my corpus** (`probe/10-independent-cardinal-sweep.sh`,
`out/10-sweep-T258tree.txt`): 1285 tracked `.softhouse` `.sh`/`.py`, 2421 `.md`/`.json`, four arms
including two aimed at blind spots T258 *declared* (word-form cardinals; numeric comparisons such
as `-ne 9`, which R1–R4 cannot see). **I found no live typed frontier cardinal that T258's site
table omits.** Arm A reproduces exactly T258's adjudicated set. Arm B surfaced only
`bar_check_t262.sh:75` (`-ne 9`), which T258 *did* name in `FU-3` (at the wrong line — `F-T340-3`).
Everything else in arm B is unrelated (`productId == 46`, `len(lp_posts) == 11`, transcript
counts). Arm C found the one word-form cardinal T258 declared. Where I looked is the script; what
I did not look at is untracked files and `.txt` transcripts, deliberately and for T258's stated
reason (retro-editing committed evidence is forbidden, T114/T176).

> **P-72 on my own instrument, recorded because it is the same defect this review is about.** My
> first draft used GNU `xargs -a`, which BSD/macOS xargs rejects; my second wrote
> `xargs … LC_ALL=C grep`, which makes xargs exec `LC_ALL=C` as the command. **Both printed every
> arm EMPTY**, which reads exactly like "no restatements exist". A fatal known-positive
> calibration was added and it caught both. The committed script refuses to report a zero until
> it has found `pinned at <N>` in at least one file (measured: 7).

**Honesty rule.** 7 `[VERIFIED]` markers in T258's handoff, all traced:
`evidence/00-graded-run.txt:94,99` ✓ ; `evidence/70-BAR-delivered.txt:563` ✓, `:144`,`:153` ✓ ;
`evidence/72-BAR-at-delivered-commit-8e7f0652.txt` VERDICT PASS at `:563` ✓ ;
`transcripts/10-BEFORE` (11/2) ✓ ; `transcripts/20-AFTER` (15/0) ✓ ;
`transcripts/30-t262-barcheck-rotted-today.txt:8` `MISMATCH frontier count expected: frontier 11,
pinned at 11.` ✓ ; `capture/bar-baseline-20260822-060013.log:87` — the trailing period **was** real
✓. The manifest no-hit claim re-run by me over **169** `*MANIFEST*`/`*.sha256` files with a
calibration positive: **0 hits** for `20-failopen-red-drive` / `a2-34-review-a2-15` /
`t255-frontier-rot`, CAL+ 1. The `## Unverified` section is substantive and accurate; the one gap
in the convention is the unmarked fail-closed claim, which is `F-T340-1`.

**Money non-negotiables — re-derived, not skimmed.** No Go file, no vector, no schema, no
`nexus/` path is in the diff (19-file list checked). The only arithmetic is
`rederive-provenance-T258.sh:124-135`, `minor_from_major_text`: `partition(".")`, right-pad the
fraction to 2, string-concatenate, `int()`. **No `float(` anywhere in the file.** It **raises**
rather than rounds when more than two decimal places are significant
(`"minor-unit conversion would lose money"`), and correctly accepts non-significant trailing zeros
(`1.2300` → `123`). Totals are `sum(int(leg["amount_minor"]))` over integer minor units, compared
as strings. Integer minor units throughout; nothing touches the append-only ledger; no database
work; PostgreSQL-only unaffected. **CLEAN.**

**Scope — CLEAN.** All 19 files fall inside `files_hint`
(`.softhouse/capture/t243-wiring/`, `.softhouse/capture/t255-frontier-rot/`,
`.softhouse/reviews/a2-34-review-a2-15/`) plus the handoff. **`.softhouse/conformance.sh` is
untouched**, so T323's exclusive hold is respected — and T258's `STOP-AND-REPORT` (it refused to
repair `rederive-provenance.sh` in place because the `−` row would have to leave
`FAILOPEN_PIN_FILE_LIST` in the same commit) is the correct call, correctly argued, with the exact
patch supplied as `FU-1`. The new namespace `capture/t255-frontier-rot` is DECLARED to T299's
namespace guard by `OWNER-IS-T258-NOT-T255.md` and the bar reads it (`out/20-BAR…:132`).

`F-T340-7` **[INFORMATIONAL, process, against the DRIVER].** The `T340` dispatch note states the
task *"Never started in fire 20260828-080001 (all three T330 signals empty)"*. Two git worktrees,
`/private/tmp/t340-probe` and `/private/tmp/t340-scratch`, exist right now, both detached at
T258's exact head `0928fa16`, both mtime `Aug 28 12:13`, both clean and containing no T340 review
directory. A prior T340 attempt got as far as creating scratch worktrees. *"Never started"* is a
statement about the three signals, not about the world — the same P-66/P-70 error the note itself
is trying to avoid. (No impact on this review; I reused the clean worktrees.)

---

## 7. CONDITIONS — binding on whoever lands `FU-1`…`FU-6`

**C1 — close `F-T340-1` and DRIVE the repaired path.** In
`.softhouse/capture/t243-wiring/instruments/20-failopen-red-drive.sh`, make lines 111–118
reachable. Do **not** write `|| true` alone: that collapses `grep` exit 1 (no match) and exit 2
(grep itself broke) onto one number, which is P-81 verbatim (*"`grep -c || echo 0`, putting 'zero
matches' and 'I broke' onto one printed zero"*). Capture the status:
```bash
set +e
PINNED_ROWS="$(LC_ALL=C /usr/bin/grep -c -aE '^(FAILOPEN_PIN_FILE_LIST=")?TIER[0-9]' "$PINBLOCK")"
grc=$?
set -e
if [ "$grc" -gt 1 ]; then
  echo "  ***  [pin] grep FAILED (exit $grc) reading the pin block — this is a TOOL failure,"
  echo "  ***        not an empty pin and not a frontier movement. RED DRIVE 2 ABORTED."
  exit 1
fi
```
then leave `:110`–`:118` as they stand. **The fix is not accepted until `probe/20-adversarial-derivation.sh`
(probe 2) is re-run and the five `***` lines are seen in the transcript.** I have deliberately not
applied this myself: this program's recorded history is `T259 → T268 → T286`, three consecutive
fail-opens introduced by repairs in this area, and an unreviewed reviewer edit to a refusal path
is how the fourth arrives.

**C2 — close `F-T340-2` BEFORE `FU-6` is wired.** Change the census pin key from `(rule, file)` to
`(rule, file, count)` — line numbers stay out of the pin, growth does not. Add a fifth red arm to
`50-census-red-drive.sh` that plants into a file **already on the pin under the same rule** and
requires exit 1. `probe/30-census-duplicate-in-pinned-file.sh` in this review is a ready-made
starting point and currently prints `exit=0 <-- 0 means IT DID NOT REFUSE`.

**C3 — fix the two citations (`F-T340-3`, `F-T340-4`).** `FU-3`'s `:99` → `:75`;
`20-failopen-red-drive.sh:125`'s `:122` → `:121`. Bind by content, line number as a hint (P-80).
Mechanical, no number of any pin changes, no money logic. Safe as a micro-fix.

**C4 — `FU-6` may not be cited as an enforced control, by anyone, until C2 *and* the wiring both
land.** Until then the correct sentence about this work is: *the mechanism is built, driven and
inert.* T258 says this itself; it must not be softened on merge.

**Non-blocking (`F-T340-5`):** commit-qualify the present-tense cardinal at
`20-cardinal-restatement-census.py:79`.

**Endorsed unchanged:** `FU-1` (the `TIER1B` pin row must leave `FAILOPEN_PIN_FILE_LIST` in the
same commit that repairs or deletes `rederive-provenance.sh`, never alone — I reproduced the
fail-open, it is real, and it is correctly pinned rather than silently repaired), `FU-2`, `FU-4`,
`FU-5`, `FU-7`.

---

## Reproduce this review

```
bash .softhouse/reviews/t340-review-t258/probe/10-independent-cardinal-sweep.sh <tree>
bash .softhouse/reviews/t340-review-t258/probe/20-adversarial-derivation.sh      <scratch-tree>
bash .softhouse/reviews/t340-review-t258/probe/30-census-duplicate-in-pinned-file.sh <scratch-tree>
```
Evidence under `out/`: `10-sweep-T258tree.txt`, `20-BAR-T258-0928fa16.txt`,
`30-adversarial-probes.txt`, `40-failopen-red-drive-RERUN.txt`, `50-census-clean.txt`,
`51-census-DUPLICATE-IN-PINNED-FILE-NOT-REFUSED.txt`, `52-census-red-drive-RERUN.txt`,
`60-successor-RERUN.txt`, `61-successor-red-drive-RERUN.txt`, `62-original-failopen-REPRODUCED.txt`.
