# T339 — independent review of T270 (`softhouse/T270-superseded-trap`, head `512040fc`)

**Reviewer:** T339, fire `20260828-140005`. I did not plan T270 and I am not its author.
**Branch:** `softhouse/T339-review-t270`.
**Method:** every number below was re-derived by running something, on scratch copies of
`main` and of T270's tree exported with `git archive` into `/tmp/t339/`. No committed file
outside my own review directory was written. `run-all.sh` overwrites
`TRANSCRIPT-A2-11.txt` (T270's own F-5); that is why every run-all execution in this
review happened in a throwaway export and never in a worktree.

---

## VERDICT: **ACCEPT-WITH-CONDITIONS**

T270 did the thing it was sent to do, and did it the hard way: the frozen bytes are
untouched, the execution is stopped, the stop is fail-closed, and the three things it
reported past its brief are — with one correction — **true**, including the two that
contradict earlier tasks. Its own two self-disclosed defects are real, complete, and
mechanised into assertions rather than described.

It is not APPROVED because of two defects I found that T270 did not, one of which is in
the direction of a false green:

* **`F-T339-1` [HIGH]** the census's headline `54` is **`55`**. Its shell grammar cannot
  see an invocation used as an `if` condition, and — unlike the Python selector — the
  shell half of the instrument, which produces 53 of the 54 published findings, **has no
  self-test at all**. The miss is a live in-place invocation of the superseded capture
  transport `cap9.sh`.
* **`F-T339-2` [MEDIUM]** `resolve-supersession.py`, T270's own new instrument, accepts a
  `..`-escaping replacement path and hands it to `run-all.sh` to execute — the exact
  defect T270 closed, in the same task, in `guard-parse-float-ast.py`. **P-80: an
  instrument that breaks the rule it was written to enforce.**

Neither touches a money value, the ledger, a vector, or a schema. `bash
.softhouse/conformance.sh` is **PASS (exit 0)** both on my branch and on a fully-tracked
copy of T270's tree.

**Conditions for merge** (all mechanical, none of them a money number):
1. `F-T339-1` — restore `if|elif|while|until|!` to `_CMD_START` and add a shell-side
   self-test; republish the cardinal as `55`. Or, if the successor task owns it, record
   `55` and the blind spot in the census's own MISSES block, which today does not
   contain it.
2. `F-T339-2` — refuse absolute and root-escaping `->` targets in
   `resolve-supersession.py`, the same three lines `check_reproduction` already carries.
3. `F-T339-5(b)` — correct the handoff's `16 assertions string absent` and `.py 699`.

`F-T339-3`, `-4`, `-6`, `-7` are recorded findings, not merge blockers; `-3` refutes the
driver's brief and T270 together and should be carried into the successor task.

---

## 0. What the brief asserted, and whether it held

| brief's premise | verdict | how I know |
|---|---|---|
| T270 must honour BOTH halves: bytes preserved AND execution stopped | **HELD** | §1 |
| census moves `4 -> 5` | **HELD, exactly** | §2 |
| no OTHER superseded artefact is still invoked from a `run-all.sh` | **HELD** | §3 |
| T270's claim 1 — `run-all.sh` §§2,4,5,6,7 abort; committed transcript records §§3-8 at exit=0; "exactly ONE section was producing a real verdict" | **TWO-THIRDS TRUE — the last clause is FALSE** | §4 / `F-T339-3` |
| T270's claim 2 — 54 live in-place invocations | **UNDERSTATED. It is 55** | §5 / `F-T339-1` |
| T270's claim 3 — T263's F-5 premise is FALSE, 3 of 6 not 6 | **HELD, re-derived independently** | §6 |
| T270's two self-disclosures are complete | **complete as far as they go; they are not the whole list** | §7 |

---

## 1. The trap: both halves of T114, verified separately

**Bytes.** `sha256(prove-mkreq7-guard-red.py)` =
`6aba7e14963ed81c814f82490703f15c7ff7a98712263bd5e91afc8e60818a35` on `main` and on
T270's tree — computed by me on both exports, not read from T270's transcript. The
`MANIFEST.sha256` line moves from `:1095` to `:1096` (one line inserted above it) and
pins the **same digest**. The file is absent from `git diff --name-status
main...softhouse/T270-superseded-trap`.
[VERIFIED: shasum on both exports; `git diff --name-status`.]

**Execution.** I wrote my own sweep rather than reading T270's census —
`probe/t339-runall-supersession-sweep.py`. It walks for registers (`basename =~
/supersed/i`), parses `A -> B` including the markdown spellings, walks for every
`run-all*.sh` in the tree, and classifies each occurrence as INVOCATION / ECHO-PROSE /
COMMENT / MENTIONED. It **self-tests on every run** against a synthetic `run-all.sh`
carrying one invocation, one echo and one comment, and exits 2 if it cannot discriminate
all three.

```
RUN-ALL SCRIPTS FOUND BY WALKING: 4
   .softhouse/capture/pathb/t99/run-all.sh
   .softhouse/capture/t305-openingbalance-accepting-side/throwaway/run-all.sh
   .softhouse/capture/t327-closure-accepting-side/throwaway/run-all.sh
   .softhouse/reviews/A2-11/run-all.sh
OCCURRENCES OF A SUPERSEDED BASENAME IN A run-all*.sh: 7
VERDICT: 0 INVOCATION(s) of a superseded artefact from a run-all*.sh
SELF-TEST ... ok  the sweep discriminates all three
```

All 7 occurrences are in `A2-11/run-all.sh`: six `echo` prose lines (`:43,52,59,72,80,82`)
and one at `:71` where the basename is an **argument** to `resolve-supersession.py`, not
an interpreter operand. `out/41-runall-supersession-sweep-t270.txt`.

**Fail-closed, re-driven by me.** `evidence` for ARM 9 regenerated:
`out/80-rerun-prove-t270-red.txt`, **29 assertions, 0 failed**. Deleting the register line
makes §8 refuse; pointing it at a missing replacement also refuses; neither falls back.
I did not accept T270's transcript — I ran the prover in a fresh export.

**I also ran the thing end to end, both sides.** `out/10-` (main) and `out/20-` (T270).
My `main` run is byte-identical to T270's committed `evidence/10-run-all-BEFORE.txt`
except for the worktree path inside seven traceback lines
(`out/11-my-BEFORE-vs-t270-committed-BEFORE.diff`, 28 lines, all path). T270's committed
BEFORE evidence is genuine.

---

## 2. The published number `4 -> 5`, re-derived from the census's own output

I ran `census-json-float-siblings.py` on each export and diffed the two stdouts. Not read
from T270 — produced:

```
163c163
< SUPERSESSION REGISTER (SUPERSEDED.txt) — 4 entr(ies)
> SUPERSESSION REGISTER (SUPERSEDED.txt) — 5 entr(ies)
165a166
>   prove-mkreq7-guard-red.py      -> guard-parse-float-ast.py   CLEAN (AST-verified, 0 R1)
172c173
<           4 redirect(s) verified
>           5 redirect(s) verified
```

Exit `1 -> 1`. `FAILURES: 1 -> 1`, the same pre-existing
`EVERY MECHANICAL CANDIDATE IS CLASSIFIED`. The redirect is **accepted**, and accepted as
a redirect (the replacement is graded `CLEAN`), not as an allowlist entry.
T263's `4 -> 5` is right; **T270's refinement is also right** — one cardinal, rendered at
two print sites, plus a third changed line. A reader diffing transcripts meets three
changed lines. `out/30-`, `out/31-`, `out/32-census-diff-4-to-5.txt`.

---

## 3. Every `SUPERSEDED.txt` entry against every `run-all.sh`

Asked for by the brief, answered in §1: **0** invocations, over 5 registers, 5 declared
originals (`cap.sh`, `cap9.sh`, `prove-mkreq7-guard-red.py`, `resolve7.py`,
`run-220-a2-7-runtime.sh`) and 4 `run-all*.sh`. On the `main` export the same sweep also
returns 0 — because on `main` the trap file **is not declared superseded at all**, which
is precisely the T263 defect. A register-scoped sweep cannot find an undeclared
retirement; that hole is the census's declared miss M6 and remains open.

---

## 4. `F-T339-3` — "exactly ONE section was producing a real verdict" is FALSE. §1 also does, and it is RED.

**Severity: MEDIUM.** This refutes the driver's brief and T270's §6.5 together.

Measured on the `main` export today (`out/10-runall-BEFORE-rerun-by-t339.txt`):

| § | today | committed `TRANSCRIPT-A2-11.txt` |
|---|---|---|
| 1 | **exit=1, `FAILURES: 3`, a full verdict** | exit=1, `FAILURES: 3` (`:70-74`) |
| 2 | traceback, exit=1 | exit=1, `FAILURES: 3` |
| 3 | exit=0, a full verdict | exit=0 |
| 4,5,6,7 | traceback, exit=1 | exit=0 |
| 8 | exit=0 (the trap) | exit=0 |

So the sharp half of T270's claim is **confirmed by execution**: five sections abort with
`FileNotFoundError` / `CalledProcessError` against
`/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3ac3d56d665ff7da`, which
`ls` reports does not exist, hard-coded at `enumerate-corpus.py:22`,
`verify-manifest-independently.py:21`, `audit-float.py:18`,
`prove-resolve7-float-red.py:33`, `prove-a2-7-guards-are-falsifiable.py:19` — I read all
five lines. The committed transcript does record §§3-8 at exit=0. It is already not
re-derivable.

**Where the claim breaks.** §1 is not dead. `check-shape.py` imports exactly
`json, sys, decimal.Decimal, pathlib.Path` (`:7-10`) — no `urllib`, no `requests`, no
`socket`, no `subprocess` — and loads committed bytes out of `A2-11/obs/`. It is a fully
offline, deterministic replay and it reproduces the committed §1 **exactly**, three named
FAILURES and all. So of eight sections, **two** produce a real verdict, and the one nobody
has been reading is **red**:

```
FAILURES: 3
  -   paymentChannelToFundSourceMappings present and null
  -   feeToIncomeAccountMappings present and null
  -   penaltyToIncomeAccountMappings present and null
```

Consequences:
* T270's `[UNVERIFIED] #4` ("whether §1 would pass against a live oracle … not
  investigated") is answerable from four import lines: §1 never contacts an oracle.
  T270's "Oracle: not contacted" header is **true**; the caveat is over-cautious, not wrong.
* `run-all.sh:28` still labels §1 `[ORACLE]` and "A2-11's OWN **live** re-observation".
  T270 rewrote the header block directly above it and left that mislabel standing, which
  is what makes an offline, reproducible RED read like an unavailable oracle.
* The proposed `patterns.md` corollary in T270's F-10 — "a lone green among reds is a
  reason to distrust the green" — survives intact; that sentence is about §8 vs §§2,4-7
  and is correct. Only the "exactly ONE" count is wrong.

---

## 5. `F-T339-1` [HIGH] — the census's `54` is `55`, and the shell half of it is never self-tested

**Re-derivation, step 1 — a different instrument.** `probe/t339-recount-54.py` is a
line-oriented exact-basename matcher, deliberately not the census's AST method. It
reproduces **every one of the census's 52 `cap.sh` in-place sites**, the single
`resolve7.py` site (`run-220-a2-7-runtime.sh:27`) and the single `cap9.sh` site
(`run-463-a2-29-recompute-org-after-reversal.sh:8`), plus 17 extras. I read every extra:
6 in `prove-cap-transport-red.py` and 5 in `poison-d2-transport-modes.py` are
`tempfile.mkdtemp` sandbox copies, 1 in `prove-manifest-blind-red.py` is a sandbox write,
and 3 are docstring usage lines or a `grep` argument. **My instrument over-reports; the
census is right about all 54 it published.** `out/50-independent-recount-of-54.txt`.

**Re-derivation, step 2 — the one it misses.** `census-superseded-invocations.py:142`:

```python
_CMD_START = r"(?:^|[;&|(`{]|\$\(|&&|\|\||\bthen\b|\bdo\b|\belse\b|\btime\b)\s*(?:exec\s+)?"
```

It admits `then`, `do`, `else` and `time` as command introducers. It does **not** admit
`if`, `elif`, `while`, `until` or `!`. So this line, in the rig, is graded MENTIONED:

```
.softhouse/capture/tierA-a2/prove-a2-26-guards-red.sh:100
  if sh "$DIR/cap9.sh" A2-999-should-not-exist POST /journalentries req/a2-26-manual-je-idem.json 2>"$TMP/g3.err"; then
```

`$DIR` is the rig, not a sandbox; `sandboxes()` (`:340`) returns False for it because
nothing `cp`s `cap9.sh` anywhere. It is structurally identical to the site the census
*does* catch at `run-463-…:8`. The census lists `prove-a2-26-guards-red.sh` under
cap9.sh's `mentioned in:` list.

**Proof, not inference.** `probe/t339-if-condition-blindspot.py`
(`out/60-if-condition-blindspot.txt`):
* ARM 1, against the SHIPPED regex copied verbatim from `:141-147`: the `if` form is
  MISSED; the same call without `if` is EXECUTED (**the control hits**, so the probe is
  measuring the right thing); with the four introducers restored it is EXECUTED.
* ARM 2, over 644 shell callers: exactly **1** real site differs — the one above.
* ARM 3, end to end: the shipped census over a scratch tree whose only caller invokes
  `cap9.sh` as an `if` condition.

**And end to end on the real tree.** I patched *one line* of a scratch copy of the census
(`_CMD_START` + `if|elif|while|until|!`), dropped it into a pristine export at its own
path, and ran it. `out/61-census-with-if-restored-55.txt`:

```
cap9.sh
      status: *** STILL EXECUTED IN PLACE -- TRAP ***
      2 executed-in-place, 0 executed-as-copy, 45 mentioned, across 16 caller file(s)
      EXECUTED  capture/tierA-a2/prove-a2-26-guards-red.sh:100
      EXECUTED  capture/tierA-a2/run-463-a2-29-recompute-org-after-reversal.sh:8
...
  TOTALS: 55 EXECUTED-IN-PLACE, 6 EXECUTED-AS-COPY, 319 MENTIONED, over 12 artefact(s)
```

`prove-mkreq7-guard-red.py` stays at **0 executed-in-place** under the widened grammar
too — T270's actual fix survives the stronger instrument, which is the most important
thing in this section.

**Root cause, and why this is HIGH rather than LOW.** `selector_selftest()` (`:317`)
exercises `py_exec_lines` — the **Python** selector — against 3 synthetic spawns and 4
decoys, and refuses if blinded. There is **no equivalent for `SH_EXEC` / `SH_DIRECT`**,
and 53 of the 54 published findings come out of the shell path. That is P-22 —
*"a guard, a canary, or a control that cannot fail is worse than none — because it is
believed"* (`patterns.md:473`) — applied to one half of an instrument and not the other.
The error direction is **under-report**, i.e. a false green, and the blind spot is **not**
among the seven misses M1-M7 the census declares at `:71-99` and restates at its verdict
(`:601-608`); I read that whole block. The published `54` is the number the successor task
(T270 F-1, `[HIGH]`) will size its work from.

---

## 6. T263's F-5 premise — refuted independently

T263 recommended requiring "the exempted file's name to occur in the evidence file",
saying it holds "for **all six** live records today". Re-derived by `grep -c` of each
record's own `produced:` target for its own producer's basename, on T270's export:

| record(s) | evidence | names its producer? |
|---|---|---|
| `prove-mkreq7-guard-red.py:70,119,126` | `RED-GREEN-A2-7-guards.txt` | **yes** (1 occurrence) |
| `resolve7.py:24,25` | `req/a2-7-loan-220-resolved.json` | **no** — it is a JSON request body (`{"clientId":1,"productId":46,"principal":1200000,…}`); there is nowhere in it to name a producer |
| `verify-provenance-a2-15.py:24` | `PROVENANCE-A2-15.txt` | **no** — a case_id/leg/money-cell table |

**3 of 6.** T270 is right, and right about the consequence: enforcing F-5 as written would
have turned the guard permanently red on the two records the register itself grades
**MATERIAL** (`resolve7.py`, 11 + 12 JSON-float leaves). Implementing it as a printed
GRADE is the correct call. I confirmed the grade **discriminates** on the live rig rather
than being a constant — `out/82-`: three records print `evidence NAMES its producer`,
three print `ASSERTED ONLY`. A grade that said the same thing about every record would
have been P-22 again.

---

## 7. `F-T339-2` [MEDIUM] — P-80: `resolve-supersession.py` reintroduces the defect T270 closed one directory away

T270 closed T263's `(d)` in `guard-parse-float-ast.py:379-390` (`check_reproduction`,
`:365`): an absolute
`reproduces:` target is refused outright, and `..` is refused with it after `realpath`,
"because it reaches the same place by a different spelling". Correct, and I verified it
including a spelling T270 did not drive — a **symlink** (`out/70-` ARM G: absolute,
dot-dot and symlink all rc=2).

The **new** instrument shipped in the same commit does not carry that check.
`resolve-supersession.py:73-79`:

```python
    repl = entries[frozen]
    rdir = os.path.dirname(os.path.abspath(register))
    if not os.path.exists(os.path.join(rdir, repl)):
```

`os.path.join` with an absolute `repl` returns the absolute path; with `../` it walks out
of the rig. Measured (`out/70-attacks-on-t270.txt`):

* **ARM A** — register entry `prove-mkreq7-guard-red.py -> ../OUTSIDE-THE-RIG.py`:
  **rc=0**, stdout `../OUTSIDE-THE-RIG.py`. `run-all.sh:74` then does
  `python3 "$RIG/$REPL"`, which resolves and **runs the out-of-rig file**.
* **ARM B** — an absolute out-of-tree replacement: also **rc=0**. Here the shell's
  `"$RIG/$REPL"` concatenation happens to produce a broken path and dies loudly, so the
  absolute form is saved by an accident of string joining, not by a check.
* **ARM C** — the resolver accepts a replacement that is **not a guard at all**
  (`NOT-A-GUARD.py`, prints a sentence and exits 1). Driving `run-all.sh`'s §8 logic
  verbatim: it resolves it, runs it, prints `exit=1`, and the section **still ends rc=0**.
  `run-all.sh` never propagates any section's exit code.

The register is a committed, reviewable file, so this is not a live compromise — it is the
same *shape* T270 itself graded as the one "a reviewer cannot audit", left in its own new
code. **P-80** — *"a corrected cardinal rots in every place it was restated … the fix is
never the new number — it is to make the second site READ the first"* (`patterns.md:2775`)
— is cited by T270 as the reason `run-all.sh` READS the register; the corollary it missed
is that reading an untrusted register is only safe if you constrain what it can say.

**Remedy (mechanical, 3 lines):** in `resolve-supersession.py`, refuse
`os.path.isabs(repl)` and refuse `realpath(join(rdir, repl))` that is not under
`realpath(rdir)`.

---

## 8. `F-T339-4` [MEDIUM] — T263 F-4(a) is closed only for records that opt in, and the disclosure stops one step short

T270's headline exemption fix is real and I reproduced it against the pre-T270 guard.
I rebuilt T270's authoring state exactly — a git repo whose **HEAD carries `main`'s**
`guard-parse-float-ast.py` / `PARSE-FLOAT-EXEMPT.txt` / `MANIFEST.sha256` and whose
working tree carries T270's — so `prove-t270-exempt-red.py`'s `git show HEAD:` arms
actually compare the two guards. **23 assertions, 0 failed**
(`out/81-rerun-prove-t270-exempt-red.txt`), including:

```
ok  REPRODUCE step 2: regenerate MANIFEST.sha256 -> PRE-T270 guard exits 0 again.
    THE EXEMPTION CAME BACK TO LIFE with the edit still in place.
ok  FIXED step 2: regenerate MANIFEST.sha256 -> IT STAYS DEAD, exit 2
```

My own independent version (`out/70-` ARM D) agrees: edit → rc 2 → `manifest.py write`
(rc 0) → still rc 2, and the refusal names `THIS REGISTER pins …`, not the manifest.

**What is not said.** Field 7 is **optional**; six fields are still accepted, on purpose,
so T164's T114-frozen red-driver keeps working. T270 discloses that and says such a
record is "printed `MANIFEST-ONLY -- WEAK`, not treated as equivalent". Printed is not
enforced. `out/70-` ARM E drives it end to end:

```
ok  a 6-field record is still ALLOWED, graded MANIFEST-ONLY -- WEAK
ok  edit the file -> guard refuses                                   rc=2
ok  `manifest.py write` REVIVES the exemption                        rc=0
```

So **T263's exact attack is fully live for any 6-field record**, and downgrading a
7-field record to 6 is a one-field deletion. The mitigation is genuine (both the
downgrade and the revival appear in `git diff` on the register) and the trade-off with
T114 is legitimate; what is missing is the sentence that says the attack reproduces. A
reader of the handoff would conclude `(a)` is closed. It is closed **for records that
opted in**.

For completeness I also measured the two T270 declares still open, rather than relaying
them: `(c)` swapping `produced:` for another MANIFEST-pinned file still ALLOWS
(`out/70-` ARM F, exit 0, `produced CAPTURE-PLAN.md`); `(b)` a brand-new unguarded
`json.load`, git-tracked, with a correct pinned source line and a correct field-7 digest,
citing evidence it never produced, is ALLOWED (ARM H). Both match T270's statements
exactly. ARM H also surfaced a control T270 did not claim credit for: field 4 pins the
**source line verbatim**, so a minting attempt that gets it wrong is caught as DRIFT.

---

## 9. `F-T339-5` [LOW] — two published cardinals in the handoff disagree with T270's own transcripts

**(a)** Handoff §4.1: "caller files inspected **1,345** (`.py` 699, `.sh` 584, `.zsh` 60,
`+ .softhouse/bin/`)". `CENSUS-T270-STILL-EXECUTED.txt:43-46` prints `.py **701**`, `.sh
584`, `.zsh 60` — which sums to 1345 exactly, with no separate `bin` bucket (the census
folds `.softhouse/bin/` into those extensions at `:475`). The handoff's breakdown sums to
1343 and misstates a measured number.

**(b)** Handoff §2 table, the AFTER column: "`16 assertions` string **absent**". It is not.
It occurs three times in T270's **own committed** `evidence/20-run-all-AFTER.txt` — at
`:176` (section 7's title), `:194` and `:278` (the explanatory prose T270 added) — and
three times in my independent re-run. What is absent is the **start-of-line verdict**
`16 assertions, 0 failed`. This matters more than a typo because it is **the same shape
as T270's own self-disclosed defect #9**: a whole-output text claim satisfied by prose.
T270 caught it in `prove-t270-red.py` ARM 0, anchored the assertion to start-of-line, and
left the lesson as a comment at `:87-91` — and then restated the unanchored version in
the handoff. The shipped prover is correct; the prose is not.

---

## 10. `F-T339-6` [LOW, process] — T270 applied to itself the remedy shape it forbade for the other five

`run-all.sh` produced committed evidence (`TRANSCRIPT-A2-11.txt`). `SUPERSEDED.txt:6-10`,
T270's own register, states T114 "forbids editing them in place: the committed artefacts
must stay re-derivable from the scripts that actually made them", and T270's F-4
prescribes, for the five dead sections, "successors + redirects, **not** in-place edits".
T270 nevertheless edited `run-all.sh` in place, justifying it as "already void for 6 of
its 8 sections, measured".

Measured cost, which the handoff does not state: §8 of the committed transcript **was**
still byte-reproducible from `main`'s `run-all.sh`. I diffed my re-run's lines 176-198
against the committed transcript's lines 354-376 — **identical, rc=0**
(`out/12-committed-transcript-section8.txt`). So of the three sections that still
reproduced (§1, §3, §8), T270's edit removes one.

I do not treat this as a rejection. The trap was live, removing it loudly was the point,
the change is recorded in the diff, and the script now prints a staleness notice a reader
meets before any exit code. But the handoff's justification should say "6 of 8 were
already void, and this change makes §8 the seventh" rather than implying the edit cost
nothing.

---

## 11. `F-T339-7` [MEDIUM, inherited, still open] — P-45: nothing automatic runs any of this

*"A guard that only runs when someone remembers to run it enforces nothing."* Establishing
this by grep, as the role requires:

`grep -n "guard-parse-float-ast\|census-superseded\|run-all.sh\|A2-11\|tierA-a2"
.softhouse/conformance.sh` over all **4132** lines returns **nothing**. I also grepped for
`capture/`, `.softhouse/reviews`, `source ` and `. "$` to rule out an indirect include;
the hits are comments, the `capture/lib/` guard runner, and `FAILOPEN_PIN_FILE_LIST`, none
of which names T270's directory or the rig. **Where I looked: the whole of
`.softhouse/conformance.sh`, by tool name and by directory.**

So the delivered state is: the repaired guard runs from `run-all.sh`, which is hand-run,
and which exits 0 whatever §8 prints (§7 ARM C). T270 discloses this honestly as F-2/F-3,
notes `conformance.sh` is held by T323, supplies exact patches, and warns that wiring the
census today would fail on its own 54 (now 55) pre-existing findings. That is the right
call for a task that may not edit the file. It is still, by T270's own count, the
**seventh** recorded P-45 fire for `guard-parse-float-ast.py`, and the successor task
should treat the wiring as the deliverable rather than the follow-up.

---

## 12. What I checked and found CLEAN — so silence is distinguishable from not looking

* **Self-disclosures #9 and #10 are complete and mechanised**, not merely present. #9's
  comment is at `prove-t270-red.py:87-91` and the assertion is anchored
  (`not any(l.startswith("PASS --") …)`). #10's two over-report shapes are live
  assertions: ARM 3 (`:118-129`, name-in-argument-position is not execution — the exact
  shape T270's own fix uses) and ARM 8 (blinded selector must abort). Both re-ran green
  for me.
* **`[VERIFIED: measured]` #6.7 traces exactly.** I re-ran `prove-parse-float-guard-red.py`
  and diffed ARM 13 against the committed `RED-GREEN-T164-parse-float-ast.txt:198`:
  precisely one line differs, `manifest pins` → `THIS REGISTER pins …`. Same digests,
  same `41 assertions, 0 failed`, exit 0 (`out/83-`).
* **`[VERIFIED]` #6.12's citation resolves.** `patterns.md:3238` row 13 records
  `.softhouse/tasks.json:3149` citing `P-79` for a gloss that is `P-80`. T270 inherited a
  documented off-by-one and said so. Correct.
* **`manifest.py verify`**: `OK: 1139 files match MANIFEST.sha256`. The `1138 -> 1139`
  delta is `ORACLE-STATE-MOVED-BY-T276.md`, a pre-existing untracked-in-manifest file that
  T270 flagged rather than absorbing silently.
* **T164's frozen prover, after the change**: `41 assertions, 0 failed`, exit 0.
* **`guard-parse-float-ast.py` population unchanged**: `PASS -- 21 call site(s) across 35
  file(s): 15 carry parse_float=, 6 are declared … 0 violations` — identical before and
  after. The git-tracked control returns `git: tracked` inside a real work tree and states
  `DID NOT RUN here` outside one, rather than passing silently (`out/82-`).
* **Money non-negotiables**: the diff introduces no arithmetic, no `float(`, no `double`,
  no schema and no API field. Every `float` token in the added lines is transcript text or
  register prose. `git rev-parse main:.softhouse/vectors` ==
  `git rev-parse softhouse/T270-superseded-trap:.softhouse/vectors` ==
  `3b0713620556edbdac1b93942c83a81b5844e5a5` — **the vector store did not move.**
  No PostgreSQL/driver/dialect change. No deposit-taking string.
* **Scope**: `git diff --name-status main...softhouse/T270-superseded-trap` is 15 files,
  every one under `.softhouse/capture/tierA-a2/`, `.softhouse/reviews/A2-11/`,
  `.softhouse/capture/t270-superseded-trap/` — the declared `files_hint` — plus the
  handoff. `.softhouse/conformance.sh`, `patterns.md` and `.softhouse/vectors/**` are
  untouched, as claimed.
* **`bash .softhouse/conformance.sh`** (bash, never sh): **PASS, exit 0**, "46 parity
  vectors match the pinned reference oracle, 7884 cells compared" — on my branch
  (`out/90-`) and, separately, on a fully git-tracked copy of T270's own tree
  (`out/91-`). On the T270 tree the guards most likely to be perturbed by its additions
  all passed: the T299 namespace guard (151 evidence directories, T270's new
  `t270-superseded-trap` prefix collides with nothing), the T316 dead-path frontier
  (GREEN), the fail-open instrument census (`frontier == pinned (all 11 rows, by path)` —
  T270's new scripts add no fail-open instrument), and the P-number citation guard
  (VERDICT PASS). Both runs printed a verdict line, so neither is a HARD-guard exit-2
  masquerading as an outage (P-83/P-84).

---

## 13. Findings, indexed

| id | severity | one line |
|---|---|---|
| `F-T339-1` | **HIGH** | census publishes 54; it is 55. `_CMD_START` (`census-superseded-invocations.py:142`) is blind to an `if`-condition invocation, and the shell half of the instrument — 53 of 54 findings — has no self-test. Under-report = false green. Not in the declared misses. |
| `F-T339-2` | MEDIUM | `resolve-supersession.py:73-79` accepts a `..`-escaping (and absolute) replacement path and `run-all.sh:74` executes it — the defect T270 closed in `check_reproduction` (`guard-parse-float-ast.py:379-390`) in the same commit. P-80. |
| `F-T339-3` | MEDIUM | "exactly ONE section produced a real verdict" is false in the brief and in T270 §6.5. §1 is offline, deterministic, reproduces the committed transcript, and is **RED with 3 failures**; `run-all.sh:28` still mislabels it `[ORACLE] live`. |
| `F-T339-4` | MEDIUM | T263 F-4(a) is closed only for records carrying field 7. Strip the field and the revival attack reproduces end to end (measured). T270 disclosed the WEAK grade, not the reproduction. |
| `F-T339-5` | LOW | Handoff cardinals disagree with T270's own transcripts: `.py 699` vs 701; "`16 assertions` string absent" when it occurs 3× in T270's own AFTER evidence — the same prose-satisfies-a-text-match shape T270 fixed in its own ARM 0. |
| `F-T339-6` | LOW | `run-all.sh` is an evidence producer edited in place, the remedy shape T270's own register and F-4 forbid; the measured cost (§8 was still byte-reproducible; now it is not) is not stated. |
| `F-T339-7` | MEDIUM (inherited) | P-45: `conformance.sh` (4132 lines, grepped whole) invokes neither the guard nor the census. The only path is a hand-run `run-all.sh` that exits 0 regardless. |

---

## 14. Artefacts

**Probes** (`probe/`), each self-testing, each written for this review and independent of
T270's instruments:
* `t339-runall-supersession-sweep.py` — registers × `run-all*.sh`, with a
  three-way discrimination self-test that exits 2 if blind.
* `t339-recount-54.py` — a different-method recount of the EXECUTED-IN-PLACE population.
* `t339-if-condition-blindspot.py` — the `F-T339-1` red drive: synthetic, real-tree
  census, and an end-to-end run of the shipped census over a tree it must fail on. Its
  ARM 1 asserts its own control hits before reading the negative.
* `t339-attack-t270.py` — 19 arms against both new instruments and all four exemption
  fixes, including a symlink spelling T270 did not drive. **19 ok, 0 FAILED.**

**Evidence** (`out/`): 18 files, listed in the sections above. `10-`/`20-` are my own
regenerated run-all transcripts; `11-` proves T270's committed BEFORE evidence is genuine;
`32-` is the re-derived `4 -> 5`; `61-` is the 55; `70-` is the attack matrix; `80-`/`81-`
are T270's own red drives regenerated by me rather than read; `90-`/`91-` are the two
conformance runs.
