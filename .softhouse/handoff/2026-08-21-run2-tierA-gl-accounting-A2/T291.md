# T291 — independent review of T286: the fifth fail-open is real, and it is one bracket wide

**Branch** `softhouse/t291-review-t286` · **subject** T286 @ `73483f5` on `softhouse/t286-t268-retry`
(2 commits vs `main`: `b6f0a77` adopts T268's tree verbatim, `73483f5` is the repair — 39 files,
+5822/−55 in the repair commit, 72 files vs `main` including the adopted base) ·
**evidence** `.softhouse/reviews/t291-review-t286/`

---

## 0. VERDICT

# REJECTED

**F-T291-1 (HIGH, BLOCKING).** T286's repair rests on one sentence — **"A RECORD IS A ROW REACHED
THROUGH A LIST"** — and it chose that phrasing *specifically because* "the document root does not
count" loses to a one-line evasion. **The structural phrasing loses to the same evasion, one
bracket further.** Take T286's own R1b fixture and wrap the header dict in `[ ]`. Two characters.
Measured, four arms, pinned by blob sha:

```
H1  {"meta": {"verdict":"AS PREDICTED"},               "cells": []}   PRE=1  T268=0  WIP=0  NEW=1
X2  {"meta": {"summary": [{"verdict":"AS PREDICTED"}]}, "cells": []}  PRE=1  T268=0  WIP=0  NEW=0
                            ^^                       ^^
```

`NEW` = T286's shipped rule (blob `4f844ed`). `X2` is an affirmative verdict over nothing at all
exiting **0 GREEN** where the **pre-T268 rule exits 1 REFUSED**. That is a **LOST REFUSAL** — the
exact measurement T281 used to REJECT T268, in the exact direction, applied to the exact fixture
family T286 built.

**And it reproduces inside T286's own instrument, unmodified.** T286's no-lost-refusal sweep
reports "38 fixtures, 0 lost refusals". Drop four fixtures into its corpus, change not one line of
its code, and the same sweep says:

```
SWEEP: 42 fixtures, 4 lost refusals, 1 exit-code repairs (crash-1 -> error-2) -- FAIL
T286 BATTERY: 31 passed, 1 failed, 0 SKIPPED          [driver exit 1]
```

[`out/t286-own-sweep-with-t291-fixtures.txt`, reproducible with
`probe/reproduce-in-t286s-own-sweep.sh` once T286's branch state is in the tree]

**This is the fourth link in a chain of fixes for fail-opens, and it fails the same way as the
first three: the fix was TRADED, not CLOSED.** T286 diagnosed the pattern correctly and then
repeated it.

**What the rejection is NOT.** T286 is a strict improvement on T268 — it closes N6, H1, R2 and R3,
its 53-case error invariant holds (0 violations, independently re-enumerated), every count it
claims reproduces exactly, and its scope discipline is clean. The rejection is on the **residual**
lost refusals, not on a regression T286 introduced.

**Not safe to wire.** T269 must not install the wrapper against this rule (§8).

---

## 1. HOW HARD I LOOKED FOR THE FIFTH FAIL-OPEN, AND WHAT I TRIED

The brief said an approval must be earned by saying what was attempted. It was not an approval, so
here is the same account for the rejection: the finding above came out of a systematic sweep, not
a lucky guess, and most of what I tried **failed**. The failures are the evidence that the search
had coverage.

### 1a. The exit-0 enumeration — 53 cases, INDEPENDENTLY WRITTEN, 0 invariant violations

`probe/enumerate-exit0-t291.py`, driven against the `NEW` arm's **pinned blob**, never
`HEAD:<path>` and never the working tree [`out/enumerate-exit0-t291.txt`]. Every case the brief
named, plus what I could add. **This part of T286 HOLDS and holds well.**

| route | cases | measured outcome |
|---|---|---|
| missing input | `target/missing`, `register/missing` | **2**, probe ABSENT |
| unreadable file | `chmod 000`, `is-a-directory` | **2**, ABSENT |
| empty file | `zero-bytes`, `whitespace-only` | **2**, ABSENT |
| zero rows | `json-null`, `-empty-array`, `-empty-object`, `-bare-int`, `-bare-string`, `-bare-true` | **1**, probe PRESENT/REFUSED |
| malformed JSON | `malformed-json`, `trailing-garbage` | **2**, ABSENT |
| a row that is a scalar | `list-of-scalars`, `list-of-nulls` | **1**, REFUSED |
| a row that is a list of scalars | `list-of-lists-of-scalars` | **1**, REFUSED |
| an affirmative STRING (not a dict) in the list | `affirmative-STRING-in-list-no-dict` | **1**, REFUSED |
| deeply nested `verdict` — **via mapping keys** | `verdict-40-deep-via-MAPPING` | **1**, REFUSED |
| deeply nested `verdict` — **via lists** | `verdict-40-deep-via-LISTS` | **0 GREEN** ← **F-T291-1** |
| duplicate keys — verdict | `duplicate-VERDICT-keys` | **1**, REFUSED |
| duplicate keys — predicate | `duplicate-PREDICATE-keys-false-then-true` | **0 GREEN** ← **F-T291-4** |
| unicode / encoding failure | `invalid-utf8-bytes`, `utf8-BOM` | **2**, ABSENT |
| locale-dependent decode | `CYRILLIC-payload-under-LC_ALL=C` | **2** ← **F-T291-6** |
| a `verdict` under a key that is a list index | `X4` top-level JSON array | **0 GREEN** ← **F-T291-1** |
| a tool that isn't installed | wrapper probe, `PY=…does-not-exist` | wrapper returns **1** (§8) |
| a subprocess that dies | SIGTERM / SIGKILL / SIGINT mid-run | **−15 / −9 / −2**, never 0 |
| an exception swallowed anywhere | register/ack as array, string, null; no-pattern; block without `file` | **2**, ABSENT |
| `SystemExit` from any path but `--help` | `-h`, unknown flag, missing option value, `""`, `--`, `-` | **2**, ABSENT |
| **`--help` itself (T286's fourth)** | `argv/--help` | **2**, ABSENT — **CLOSED, confirmed** |
| recursion limits | 3000-bracket bomb, 2000-deep dict bomb | **2**, ABSENT |
| symlinks | to `/dev/null`, to a directory, broken, self-loop | **2**, ABSENT |
| no `.git` ancestor | rule copied outside any repo | **2**, ABSENT |
| stdout closed before the probe line | broken pipe | **120**, ABSENT |
| a named pipe as target | FIFO | **HUNG — no exit code in 20 s** ← **F-T291-7** |
| optimised interpreter | `PYTHONOPTIMIZE=2` | **0 GREEN**, correct |
| ack sha mismatch | `block-file-mismatch` | **1**, REFUSED (`voidAcks`) — R3 works |

**INVARIANT VIOLATIONS: 0** across all 53. `exit 0 ⇒ probe PRESENT/GREEN`, `exit 1 ⇒
PRESENT/REFUSED`, `exit 2 ⇒ ABSENT` holds without exception. **The six exit-0 rows** are
`verdict-40-deep-via-LISTS`, `duplicate-PREDICATE-keys-false-then-true`,
`real-evidence-under-LC_ALL=C`, `JSON-NaN-and-Infinity-literals-in-a-GREEN-run`, `JSON-1e400`,
`argv/same-file-twice`.

> `argv/no-targets-uses-built-in-default` measures **2** here where T286's matrix records **0**.
> Not a discrepancy in the rule: the built-in default is `HERE/../t229-g8-site3/out/…`, and `HERE`
> is the *unpacked blob's* directory. T286 flagged this hazard itself. Stated so nobody reconciles
> the two numbers by arithmetic (P-83) — I reconciled them by running both.

### 1b. Evasions I attempted against the structural rephrasing — INCLUDING THE FAILURES

`probe/drive-t291.py`, four arms, 11 legs [`out/drive-t291-output.txt`, `out/t291-legs.json`].

**Succeeded (= the rule fails open):**

| fixture | shape | PRE | T268 | WIP | **NEW** |
|---|---|---|---|---|---|
| `X2` | header in a list **one level down** | 1 | 0 | 0 | **0** |
| `X3` | header in a **list of lists** | 1 | 0 | 0 | **0** |
| `X4` | **top-level JSON array** holding only the header | 1 | 0 | 0 | **0** |
| `X7` | header in a list **four levels down** | 1 | 0 | 0 | **0** |
| `X2` **batched with `classify-t229.json`** | F-1's own hiding shape | 0 | 0 | 0 | **0** |
| `X5` | affirmation **in a list** over a genuinely REFUTED record | 0 | 0 | 0 | **0** ← F-T291-2 |

**Failed (= the rule holds). These are the coverage evidence:**

* `X5b` — the **same** document as `X5` with the header as a mapping key → **NEW REFUSES**
  (`containerAffirmations=1`). Guard #10 is real; its scope is one bracket wide.
* `X8` — a non-inspectable dict `{"note":"x"}` inside the list, header at root → **NEW REFUSES**
  `rows=0`. The root header cannot borrow coverage from a dict that carries no evidence.
* `verdict-40-deep-via-MAPPING` — 40 levels of mapping keys → **REFUSED**. Every mapping-key
  phrasing of the evasion is closed; only the list phrasing walks past.
* `X1` — header in a **top-level** list → NEW greens, **but so does PRE**. **NOT a lost refusal**,
  and I record it as a PASS so the finding is not overstated: `X1` is the pre-existing decoy class
  T286 discloses as item **a2**. `X2/X3/X4/X7` are **not** that class — PRE refuses all four.
* Every degenerate document (`{}`, `[]`, `null`, bare scalars, lists of scalars, lists of nulls) →
  refused with a probe line.
* Every malformed register/acknowledgement edit → 2 with no probe.
* Every argparse path → 2 with no probe.
* Both recursion bombs → 2 with no probe.
* All four symlink shapes → 2.

### 1c. Why `X2` is not "just a2", and why it is not exotic

T286's disclosed limit **a2** is *"a DELIBERATELY PLANTED DECOY RECORD… put one dict with one
registered boolean inside a list"*. Three measured reasons that does not cover this:

1. **It costs less than a2 says.** No registered boolean is needed and no register edit is
   involved. `{"verdict": "AS PREDICTED"}` alone is inspectable (the verdict-key signal) and in a
   list it is a RECORD.
2. **It is a lost refusal, which a2 is not.** a2 describes a shape PRE also greens. PRE **refuses**
   `X2`, `X3`, `X4` and `X7`. T286's own sweep classifies all four as `LOST REFUSAL` when they are
   put in front of it.
3. **`X4` is the shape this program's own evidence files use.** `t286-legs.json` and
   `red-green-legs.json` are top-level JSON arrays of dicts. I ran the rule on `t286-legs.json`:
   `rows=32`, i.e. every leg dict censused as a record. An array that came out holding only a
   summary or skipped entry with an affirmative word is `X4` verbatim. **Not exotic — the house
   format.**

T286 argues H1 (`{"meta": {...}}`) is a fail-open the WIP repair left open because `meta` is "an
ordinary nested row". `X2` is H1 plus two characters. **The argument that condemns the root
phrasing condemns the list phrasing.**

### 1d. Where I looked and found nothing

Stated because "not found" is a statement about the search. I did **not** find: any exit-0 path
without a probe line; any uncaught exception; any counter incremented and ungated; any drift
between `Report.COUNTERS`, the gate and the probe line; any edit to `conformance.sh`; any
floating-point in a monetary path (there is no monetary computation here at all); any movement of
the vector store; any edit to T259's or T268's batteries.

---

## 2. FINDINGS

### F-T291-1 — HIGH, BLOCKING. The coverage predicate is defeated by one pair of brackets

**Defect.** `walk_rows` reports `via_list=True` for a dict reached as an element of **any** list at
**any depth**; `check_file` counts exactly those as `seen_records`; `seen_records == 0` is the only
thing that fires guard #3. So wrapping a metadata dict in `[ ]` manufactures coverage.

**Reproduction** (`probe/drive-t291.py`, or by hand):

```
$ printf '%s\n' '{"meta": {"summary": [{"verdict": "AS PREDICTED"}]}, "cells": []}' > X2.json
$ python3 <blob 86f4285 = PRE-T268> --register … --acknowledgements … X2.json ; echo $?
T259-VPA: REFUSED files=1 rows=0 … nilCoverage=1
1
$ python3 <blob 4f844ed = T286>     --register … --acknowledgements … X2.json ; echo $?
T259-VPA: GREEN files=1 rows=1 predicates=0 … nilCoverage=0 … containerRows=0 containerAffirmations=0
0
```

and batched with the real evidence (`X2.json classify-t229.json`) it is still **exit 0**, which is
F-1's own hiding shape restored.

**Why it matters more than an over-refusal.** `predicates=0` on that green. The rule reported that
it measured a population and found nothing wrong, having read **zero predicate booleans**. Nothing
in the gate notices.

**Repair direction — MEASURED VIABLE, not prescribed.** The natural statement of what guard #3 is
actually for is *"did this file present something GRADEABLE"*, i.e. a record must be reached
through a list **and carry at least one PREDICATE-classed key**. Measured on the real corpus
[`out/drive-t291-output.txt`]:

```
classify-t229.json   records=11  containers=0  records carrying a PREDICATE=8
classify-t219.json   records=11  containers=0  records carrying a PREDICATE=9
```

so both real files stay green. It also refuses `X1`–`X7` and reduces the decoy to *fabricating a
predicate*, which is a2's forgery class and honestly out of reach. **I am not installing it.** It
changes the central predicate, it must be re-driven against 32 + 23 + 14 legs and the sweep, and
every previous quick trade in this lineage introduced a new hole. It needs its own task and its own
battery. The acceptance criterion for that task should be stated as a **measurement, not a
sentence**: *no shape the PRE-T268 rule refused may exit 0 on the new rule*, swept over a corpus
that contains list-wrapped headers at depths 1..n and a top-level array.

### F-T291-2 — HIGH. Guard #10 loses to the same bracket, and its claim is false as measured

Guard #10's own text says it *"closes the evasion of moving the affirmative word out of the records
and into a header."* It closes the **mapping-key** phrasing only.

```
X5   {"summary": [{"verdict":"AS PREDICTED"}],
      "cells":   [{"id":"c1","P2_totalInterestEqualsNEplusB":false,"verdict":"REFUTED"}]}
     NEW -> exit 0 GREEN   rows=2 predicates=1 disagreements=0 containerAffirmations=0

X5b  the same with "summary": {…}          NEW -> exit 1 REFUSED containerAffirmations=1
```

A document-level "AS PREDICTED" standing beside a record that recorded its own predicate **false**,
with `disagreements=0`. That is the rule's founding defect, printed green. `X5b` is the control
that shows the guard is real and the gap is exactly one bracket.

### F-T291-3 — MED. T286's battery exits 0 with legs silently dropped

`drive_red_t286.py:486` is `return 1 if b.failed else 0`. Skipped legs do not reach the exit code.
Driven, by pointing the `WIP` arm at a bogus blob [`out/t286-battery-with-one-arm-absent.txt`]:

```
T286 BATTERY: 23 passed, 0 failed, 9 SKIPPED          driver exit 0
```

The printed report is loud, exactly as T286 claims. **The exit code is not.** A caller reading only
the code cannot distinguish 32/0/0 from 23/0/9. This is live, not hypothetical: T286's §9 records
that the `WIP` blob lives on a local rescued branch — if it is deleted and GC'd, all eight `FO3`
legs and the WIP control vanish and the battery still returns 0. **A battery that silently skips is
a fail-open in the test rig** — the brief's own words, and it is present. One line:
`return 1 if (b.failed or b.skipped) else 0`. My own `drive-t291.py` does that.

**`0 SKIPPED` in T286's headline is nonetheless TRUE and I verified the arm was present** — the
blob resolves on this host and the count reproduces.

### F-T291-4 — MED. Duplicate predicate keys green, and the case is undisclosed

```
{"cells":[{"P9_x":false,"P9_x":true,"verdict":"AS PREDICTED"}]}   ->  exit 0 GREEN
```

`json.loads` keeps the **last** duplicate, so a recorded `false` predicate is dropped without a
word and the affirmative verdict stands. The brief named duplicate keys explicitly; it is not in
T286's 37-case matrix and not in `WHAT IS STILL OUT OF REACH`. A duplicate key is an ordinary
hand-edit accident in a committed evidence file — which is T286's own argument for why the
register-as-array case mattered. `json.loads(..., object_pairs_hook=…)` that refuses a repeated key
is the fail-closed repair.

(`duplicate-VERDICT-keys` refuses, for an unrelated reason — the surviving verdict disagrees with a
false predicate. The predicate case is the one that greens.)

### F-T291-5 — LOW/MED. `parse_constant` is unset, so floats DO enter, in a GREEN run

The rule's docstring: *"NO FLOATING POINT. `json.load(..., parse_float=Decimal)` on every read."*
`parse_float` does not cover the JSON constants:

```
$ python3 -c "import json;from decimal import Decimal;
              print({k:type(v).__name__ for k,v in json.loads('{\"v\":NaN,\"w\":Infinity,\"x\":1.5}',
                                                             parse_float=Decimal).items()})"
{'v': 'float', 'w': 'float', 'x': 'Decimal'}
```

and a target carrying `NaN`/`Infinity` exits **0 GREEN** with those floats in the graded document
[`enumerate-exit0-t291.txt`, `target/JSON-NaN-and-Infinity-literals-in-a-GREEN-run`]. **Blast
radius nil** — nothing monetary is computed here, no value the rule inspects is used numerically,
and the project's integer-minor-units rule is not violated. But the file's own claim is false as
written, and `load_json` is the helper the next instrument will copy. One argument:
`parse_constant=lambda s: (_ for _ in ()).throw(RuleError(...))`, or simply state the limit.

### F-T291-6 — LOW/MED. `read_text()` carries no encoding, so the guard reads the host's locale

```
target/CYRILLIC-payload-under-LC_ALL=C   ->  exit 2, no probe   (UnicodeDecodeError)
target/real-evidence-under-LC_ALL=C      ->  exit 0 GREEN       (that file is pure ASCII)
```

Fail-**closed**, so not a fail-open — but a guard whose verdict depends on `LC_ALL` is measuring the
host, which is the T273 class, raised inside the task that documents T273 for the sixth time. This
program's evidence will carry Mongolian Cyrillic (ovog / patronymic / given name are
non-negotiable three fields). `path.read_text(encoding="utf-8")` — one argument, no semantic change
on today's corpus.

### F-T291-7 — LOW. The evidence is read TWICE, so the sha pin does not cover the graded bytes

`check_file` calls `sha256_of(path)` and then `load_json(path)` — two opens of the same path. The
acknowledgement pin (fail-closed direction 4: *"you cannot make the record agree by retro-editing
it"*) therefore proves a property of the bytes read by the **first** open, not of the document that
was **graded**. Demonstrated, because the two-ness is observable: with a FIFO as target the rule
**hangs indefinitely** (measured: no exit code in 20 s) — the first read drains the pipe and the
second blocks forever. A TOCTOU swap is **declared, not measured**; I could not drive it
deterministically. Repair: read the bytes once, hash the buffer, parse the buffer. Also tells T269
that a wired guard needs a timeout — a guard that never returns never reports.

### F-T291-8 — LOW, wiring precision. §8 amendment 2 is overstated; and the draft has two bare greps

Driven, not reasoned [`probe/wrapper-probe-t291.sh`, `out/wrapper-probe-t291.txt`]:

```
RULE ON DISK: blob 4f844ed
PY=python3                      -> SAY … T259-VPA: GREEN …          WRAPPER_RC=0
PY=python3-that-does-not-exist  -> WARN … NO probe line (exit 127)  WRAPPER_RC=1
```

**T268's draft already fails closed when the interpreter is absent**, via the probe-presence check.
T286's §8(2) reads as though the draft is unsafe there; it is not. The amendment is a better
message, not a hole-closer — and §8(1), *do not drop the probe-presence check*, is what makes it
true. Getting this the wrong way round is how a "redundant" line gets deleted.

Separately: the draft's two `grep` calls are **bare** and on this host `grep` is the bundled ugrep
(P-75). T259's fail-open lint flags both when the draft is put in front of it. Neither T268, T281
nor T286 mentions it. T269 should use `/usr/bin/grep` or `LC_ALL=C /usr/bin/grep` when it installs.

---

## 3. WHAT HOLDS — every T286 claim I could check, checked

**Every count reproduces, re-run first-hand, never reconciled by arithmetic (P-83):**

| claim | re-run result | transcript |
|---|---|---|
| three-arm battery 32 / 0 / **0 SKIPPED** | **32 passed, 0 failed, 0 SKIPPED**, exit 0 | `out/rerun-t286-battery.txt` |
| sweep 38 fixtures, 0 lost refusals | **38 fixtures, 0 lost refusals, 1 exit-code repair — PASS** | same |
| error matrix 37 cases, 0 violations, 4 exit-0 | **37 cases, 0 violations, 4 exit-0**, exit 0 | `out/rerun-error-matrix.txt` |
| gate self-test 15/15, T268's 12-field prefix intact | **PASS**, 16 fields, prefix unchanged field for field | `out/rerun-gate-selftest.txt` |
| T268's 23 legs, unmodified | **23 passed, 0 failed**, exit 0 | `out/rerun-t268-battery.txt` |
| T259's 14 legs, unmodified | **14 passed, 0 failed**, exit 0 | `out/rerun-t259-battery.txt` |
| T268's committed `red-green-legs.json` restored | `git hash-object` = `68287dc…` **= the committed blob** | — |
| `sha256(classify-t229.json)` | `f831736f07f1a6fecd4ee69b5a1de8dac0abcae89210f997e72526070f62821a` ✓ | — |
| blob pins `86f4285` / `0607ecd` / `4f844ed` / `a70051b` | all four resolve; PRE == `main:<rule>` | — |

**R1 and R1b are genuinely closed for the shapes named.** `N6` and `H1` both refuse on NEW;
`H1` greens on T268 **and on WIP**, so T286's third finding — that the in-flight root-phrased repair
is incomplete — is **CONFIRMED first-hand on all four arms**.

**R2 is closed.** 53 independent cases, **0 invariant violations**. `--help` and `-h` both exit **2**
with no probe line. The fourth fail-open is real and it is fixed.

**R3 is closed.** `Report.COUNTERS` drives both the gate and the probe line; the self-test drives
each of 15 counters and reads the exit code; `voidAcks` now refuses (`ack/block-file-mismatch` →
exit 1).

**`git grep` / P-81 — VERIFIED, and independently reproduced.** `run.sh` runs `git grep`, not the
bundled ugrep, captures the code into `GG`, and classifies it in a `case` block: `0` = a caller
exists, `1` = **NO MATCH** (and says so in prose), `*` = **ERROR, the question is UNANSWERED, RC=1**.
That is the correct handling and it is the only hatch in the file, carrying its reason. I ran the
same search: `GIT_GREP_RC=1`. **T286 classified it; it did not read it as clean.**

**NOTHING INVOKES THIS RULE — confirmed, and confirmed WIDER than T286 claimed.** `conformance.sh`:
0 hits. Repo-wide (`git grep -l -e check_verdict_predicate_agreement -e R-VPA`, excluding handoffs,
gates, patterns, tasks.json, reviews) the only hits are inside the rule's own capture directory —
its docstring, its own `run.sh`, `drive-red.sh`, `census_verdict_shape.py`, `rederive_counts_t259.py`
and three of its fixtures. **No caller anywhere.**

**The sweep's self-correction is real, and is not present in another form.** `sweep_no_lost_refusal`
defines `REFUSED` as `rc == 1 AND the probe line is present`; `CRASH-1 → ERROR-2` is counted
separately as an exit-code repair; the docstring records the wrong first draft rather than tidying
it. I read every branch of `outcome()` and drove it: an `rc == 0` with no probe would classify
`UNKNOWN-0` and count as a lost refusal — the fail-closed direction. **No residue of the
conflation.** Its only defect is corpus coverage (F-T291-1), which is the caveat T286 itself wrote.

**F-2 adjudication — all three legs check out.**

| leg | verdict | how |
|---|---|---|
| T268's *repair* is real (both `SystemExit("ERROR: …")` sites → `RuleError` → 2) | **TRUE** | PRE has exactly two such sites (`repo_root` line 79, `load_registers` line 144). Both drive to **2, probe ABSENT** on NEW: `register/no-autoPredicatePattern`, and the rule copied outside any git repo → `ERROR: no .git ancestor` **exit 2** |
| T268's *headline* "none returns 1" is FALSE as measured | **TRUE** | driven on T268's own blob: `--register <a JSON array>` → **exit 1**, `AttributeError: 'list' object has no attribute 'get'`, no probe line |
| **T281's own enumeration missed the exit-0 path** | **TRUE** | T281's REVIEW.md §4 tabulates six sites, every one "exit 2", including "argparse's own usage exit". `--help`'s `SystemExit(0)` appears nowhere in it. A reviewer enumerating only failure directions inherits the grep's blind spot — T286's phrasing, and it is correct about T281 |

**Scope and harness.** `.softhouse/conformance.sh` untouched (0 hits, confirmed by the driver and
by me). No Go changed; `go build ./...` clean and `go test ./...` **all `ok`** on the pinned
toolchain (ledger, ledger/conformance, loanschedule, loanschedule/conformance).

**THE BAR, on my branch: `VERDICT: PASS (exit 0)`** — 46 parity vectors, 7884 cells, oracle probe
**UP**, `frontier == pinned (all 11 rows, by path)`, all 9 census pins `== pinned`, 6/6 wrong ledger
implementations killed through the harness [`out/bar-t291.txt`]. **The probe line was PRINTED, once.**

**On `/tmp/t234_matrix2.txt`, said loudly as instructed: IT DID NOT MATTER.** I checked
first — `/tmp/t234_matrix2.txt` and `/tmp/t234_matrix.txt` are both **ABSENT** on this host — and
the bar passed anyway, with the frontier at 11/11 by path *and* by tier. T273's repair (the
instrument now owns a `mktemp -d` scratch it removes on EXIT) is holding. T286's own first BAR exit
2 was real when it happened; **that dependency is gone now.** No task after this one should have to
restore 24 bytes to /tmp.

**Guard #10's revertibility claim — VERIFIED BY EXECUTION.** I demoted `container_affirmations` from
`REFUSAL` to `CENSUS` and disabled the single `if` block, then re-ran the full battery
[`out/t286-battery-guard10-reverted.txt`]:

```
LEG G10-container-affirmation-over-refuted-record: FAIL
SWEEP: 38 fixtures, 0 lost refusals … PASS
T286 BATTERY: 31 passed, 1 failed, 0 SKIPPED
```

Exactly one leg. R1/R1b/R2/R3 untouched. The claim is true.

---

## 4. GUARD #10 — DECIDED, since the author flagged it honestly and asked

**IN SCOPE. KEEP IT. Do not revert it — but do not ship its current claim.**

*In scope*, because it is not an unrelated feature bolted on: it is the second half of the
container/record distinction this task introduced. Having split rows into containers and records
for the purpose of coverage, leaving a container's affirmative verdict ungraded and unreported is
an incomplete application of the task's own idea, not a new one. It is four lines, one counter,
measured inert on both real classify files (`containerRows=0`), and I verified it is revertible at
a cost of exactly one leg.

*But its claim must be narrowed.* As shipped it says it closes "the evasion of moving the
affirmative word out of the records and into a header". **F-T291-2 measures that false** — the
list-shaped header walks past it. A guard whose stated scope is wider than its measured scope is
the same species as a refusal printed in the body that the gate never reads. In the retry, guard
#10 must be re-derived **together with** the coverage predicate: both are phrased on the same
mapping-key-versus-list axis and both fail on the same bracket. Fixing one without the other just
moves which of the two lies.

---

## 5. WHAT T269 MUST BE TOLD

**FIRST: DO NOT WIRE THIS RULE YET.** Not because it is unwired-and-harmless, but because a wired
R-VPA that greens an empty corpus behind a list-shaped header is *"a wired rule that lies"*, which
this program has already decided is worse than no rule (T262). Wait for T286's retry, then wire the
repaired rule. If a driver overrules that and wires today, it must carry F-T291-1 and F-T291-2 in
the guard's own comment block, verbatim, so the next reader knows what the green does not cover.

**Confirmed: nothing invokes it today**, repo-wide, not merely in `conformance.sh`. Prose does not
fire on the next fire; §8 of T286's handoff is a recipe and a recipe is prose until someone runs it.

**T286's §8 recipe, adjudicated item by item — it is executable, with these corrections:**

1. **§8(1) — CORRECT AND LOAD-BEARING.** The probe-presence check must come first and must not be
   deleted as redundant. **It is also what closes §8(2)** — measured, exit 127 with no probe → the
   wrapper returns 1.
2. **§8(2) — TRUE BUT OVERSTATED (F-T291-8).** The draft is *already* fail-closed on a missing
   interpreter. Add `command -v python3` for a better message if you like; do not describe it as
   closing a hole, and above all do not let it become the reason someone thinks (1) is redundant.
3. **§8(3) — CORRECT, AND NOW MEASURED.** `rc -ne 0`, never `rc -eq 1`. Driven: SIGTERM **−15**,
   SIGKILL **−9**, SIGINT **−2**, a closed stdout **120**, a missing interpreter **127**. The
   draft's `rc -eq 2` / `rc -ne 0` shape is right; keep it exactly.
4. **§8(4) — targets from a committed `targets.json`. Endorsed.** And T286 is right that
   `classify-t219.json` must stay out until T271 resolves B-1.
5. **§8(5) — correct.** T268's 12 probe fields keep names, values and positions; the four T286
   fields are appended; the gate self-test asserts the prefix. A substring reader is unaffected.
6. **§8(6) — the P-84 hazard is real and must be repeated.** `run_guards` flattens any non-zero to
   `EXIT_UNUSABLE` = 2 *before* the oracle probe line prints, so an R-VPA **refusal** reaches the
   harness boundary as **exit 2 with no probe line**. Read whether `conformance: R-VPA` was printed
   at all: present ⇒ a HARD guard failed, nothing about the oracle is in question; absent ⇒ keep
   walking. Do not park vector work on the absence alone.

**Two additions of mine to the recipe:**

7. **Use `/usr/bin/grep`, not bare `grep`** — the draft has two bare calls; on this host `grep` is
   the bundled ugrep (P-75) and T259's own lint flags them (F-T291-8).
8. **Give the invocation a timeout.** The rule can hang indefinitely on a target it cannot read to
   EOF (F-T291-7, measured on a FIFO). A guard that never returns never reports, and a hung bar
   reads as neither pass nor fail.

**For the T286 retry, the acceptance criterion should be a MEASUREMENT, not a sentence:** *no
document shape that the pre-T268 rule (`86f4285`) refuses may exit 0 on the new rule*, swept over a
corpus that contains, at minimum, list-wrapped headers at depths 1, 2 and 4, a top-level JSON array
holding only a header, and `X5`'s affirmation-in-a-list over a refuted record. Those fixtures are
committed at `.softhouse/reviews/t291-review-t286/probe/fixtures/` — **add them to the corpus**
rather than reasoning about them, which is exactly what T286 told its next reviewer to do with the
error matrix, and it was right.

---

## 6. WHAT I DID NOT VERIFY

* **[UNVERIFIED] That my own enumeration is complete.** 53 cases is a corpus, not a proof — the same
  caveat T286 wrote about its 37, and it applies to me. The honest reading of this review is that
  the fifth fail-open was found because the brief said to assume one exists; **assume a sixth.**
  Add rows to `probe/enumerate-exit0-t291.py`; do not re-read the source and agree with it.
* **[UNVERIFIED] TOCTOU between `sha256_of` and `load_json`** (F-T291-7). The two-read structure is
  read from the source and the FIFO hang makes it observable, but I did not drive a swap.
* **[NOT MEASURED] `/dev/full`** — absent on macOS, so the ENOSPC-on-write path is not measured. Said
  rather than assumed.
* **I did not audit** `classify_t229.py`, `classify_t219.py`, `site3.py`, `census_verdict_shape.py`
  or `rederive_counts_t259.py`. This review is about the rule and T286's instruments.
* **I did not re-derive T268's twelve F-3 adversarial shapes from T262's originals.** I re-ran
  T268's battery as an unmodified regression control, as T281 and T286 both did, and inherited the
  reconstruction.
* **`probe/reproduce-in-t286s-own-sweep.sh` requires T286's branch state in the tree.** On my
  branch it correctly exits **2** saying `NOT MEASURED`. The committed transcript
  `out/t286-own-sweep-with-t291-fixtures.txt` was produced with T286's files checked out; T268's
  `red-green-legs.json` was restored afterwards and verified byte-identical (`68287dc…`).
* **My own first draft was wrong, and it is recorded rather than tidied.** `wrapper-probe-t291.sh`
  initially computed `REPO_ROOT` from the wrong depth and reported `WRAPPER_RC=1` on **both** arms —
  fail-closed, and measuring nothing. It was caught by *reading the output*, which is the entire
  subject of this lineage. The script now asserts its own `REPO_ROOT` and prints the blob sha of the
  rule it actually drove. T259's fail-open lint also caught my instruments on their first draft
  (4 findings: a `|| true` in a cleanup trap, two bare greps, a missing strict-mode preamble);
  repaired, with one reasoned hatch on the greps because they are T268's draft under test and
  repairing them would mean no longer driving the draft. **0 findings now** [`out/lint-failopen-t291.txt`].

---

## 7. FOLLOW-UPS

* **FU-T291-1 (BLOCKING, for the T286 retry).** F-T291-1 + F-T291-2. Re-derive the coverage
  predicate and guard #10 together; acceptance criterion in §5.
* **FU-T291-2 (MED, for the T286 retry).** F-T291-3 — `return 1 if (b.failed or b.skipped) else 0`
  in `drive_red_t286.py`. One line. A battery that hides nine dropped legs behind exit 0 is the
  defect this directory is about, inside the instrument that measures it.
* **FU-T291-3 (MED).** F-T291-4 — duplicate keys. `object_pairs_hook` that refuses a repeat.
* **FU-T291-4 (LOW).** F-T291-5 `parse_constant`, F-T291-6 `encoding="utf-8"`, F-T291-7 read-once-
  then-hash. Three one-line changes; none of them alters a single count on today's corpus.
* **FU-T291-5 (LOW, for T269).** F-T291-8: fix the two bare greps in the wrapper draft and add a
  timeout to the invocation.
* **FU-T286-2 is CONFIRMED and I hit it myself.** T268's driver overwrites its own committed
  `out/red-green-legs.json`. My reproduction script restores it and verifies the hash; the driver
  should still write to a run-derived path.
* **FU-T286-3 — I can close the /tmp half of it.** `/tmp/t234_matrix2.txt` is absent on this host
  and the bar passes with the frontier at 11/11 by path and tier. T273's repair holds. The general
  point — a guard a `/tmp` file can flip is measuring the host — stands as a pattern.

---

## 8. ONE SENTENCE FOR THE DRIVER

T286 found a third and a fourth fail-open, closed the ones it named, reproduced every number it
claimed, kept `conformance.sh` untouched and told the truth about its own defects — and then
staked the repair on a sentence that is defeated by two characters, which its own sweep confirms
the moment the fixture is put in front of it; **REJECTED, retry with the coverage predicate as the
subject, and assume there is a sixth.**
