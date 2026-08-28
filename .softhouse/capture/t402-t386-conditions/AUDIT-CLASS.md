# T402 — RE-AUDIT OF `casualty-sweep.sh` BY **CLASS**, NOT BY SYNTAX

Subject: `.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh`.
BEFORE = `964b532e`, sha256 `1fa6acfe6a24588c…` (byte-identical to the artefact T386 reviewed at
`9eedfe4d` and on the merge result — I hashed it, I did not carry the claim forward).
AFTER = the T402 repair, sha256 `fdfe8d06087ec51c…`.

Census instrument: `instruments/t402-status-class-census.sh`.
Transcripts: `out/T402-CENSUS-before.txt`, `out/T402-CENSUS-after.txt`.

---

## 0. Why the taxonomy is the finding

T381's `AUDIT.md` promised to classify **"every `2>/dev/null` and every pipeline in the file"**.
It delivered exactly that, and T386 independently re-derived its counts as internally correct.
But the defect class is **every construct from which an exit status can be lost**, and
`err=$(cat "$SWEEP_ERRF")` is neither a `2>/dev/null` nor a pipeline. It had no row — and it was
the one carrying the defect.

> **A taxonomy narrower than the defect class does not find the defect. It certifies the part of
> the file the taxonomy could see.**

So this audit enumerates **seven** kinds chosen to cover the class, and the census
**over-includes on purpose** — `K2` and `K3` match `|` and `>` inside the selectors' own quoted
ERE patterns, which are not shell operators at all. Narrowing a census to fit the last defect is
precisely how the last defect was missed. A de-noised sub-view (`K2s`/`K3s`, quoted spans blanked)
is printed beside the wide list and is explicitly **not** the census.

| kind | what it is | BEFORE | AFTER |
|---|---|---|---|
| **K1** | command substitution `$(…)` | 22 | 26 |
| **K2** | pipeline `a \| b` | 31 (9 operator-position) | 32 (16) |
| **K3** | output redirection `>` `>>` `2>` — **opened by the shell BEFORE the command runs** | 40 (36) | 54 (48) |
| **K4** | command-as-condition `if`/`while`/`until <cmd>` | 0 | 7 |
| **K5** | assignment-masked status `local x=$(…)` | 0 | 0 |
| **K6** | substitution in an ARGUMENT — `printf "$(…)"`, structurally unreadable | **3** | **0** |
| **K7** | arithmetic / numeric test on unvalidated input | 28 | 44 |

**`K2` and part of `K3` were T381's two buckets. `K1`, `K5`, `K6` and `K7` had no row — and two
of those four were carrying live defects.**

---

## 1. Adjudication — every site that could lose a status

Verdicts are **FAIL-OPEN** (can print a number or an absence nobody measured), **FAIL-CLOSED**
(a lost status makes the run refuse), **PROVENANCE** (a lost status corrupts the record of what
was graded, not the grade), or **READ** (the status is consulted).

Sites are named by **content**, not by line number. T386 measured **14 of 16** of T381's audited
line numbers as having moved within one fire; `f3bf5563` ratified the rule.

### 1.1 The defects — repaired

| site (by name) | kind | BEFORE verdict | repair |
|---|---|---|---|
| `ENGINE_ERR=$(cat "$SWEEP_ERRF")` in `engine_count()` | K1 | **FAIL-OPEN, MAJOR** — `cat`'s status discarded | `_errf_read`, return 4 |
| `err=$(cat "$SWEEP_ERRF")` in `sel()` | K1 | **FAIL-OPEN, MAJOR** | `_errf_read`, refuse |
| `2>"$SWEEP_ERRF"` on `engine_count()`'s `git grep` | K3 | **FAIL-OPEN, MAJOR** — an unopenable redirect returns **1** without running the command, and 1 is a MEASURED ZERO here | `_errf_prime` + witness |
| `2>"$SWEEP_ERRF"` on `sel()`'s `git grep` | K3 | **FAIL-OPEN, MAJOR** | `_errf_prime` + witness |
| `$(git ls-files .softhouse \| grep -c .)` — the `MEASURED ZERO` **denominator** inside `sel()` | K1+K6 | **FAIL-OPEN, MINOR** (`FU-T381-1`) | hoisted to `$SWEEP_CORPUS_N`, status + shape read. **The site no longer exists.** |
| `if [ "$(git ls-files .softhouse \| grep -c .)" -lt 1 ]` — the **corpus assertion** | K1+K7 | **FAIL-OPEN, MINOR — F-2, NEW** | see §2 |
| `$(printf '%s' "$all" \| grep -c .)` ×2 and `$(printf '%s' "$live" \| grep -c .)` — the `hits total` / `LIVE` cardinals | K1+K6 | **FAIL-OPEN, MINOR** — inside `printf` arguments, where no `$?` can ever be consulted; an errored `grep -c` prints an **empty field**, which reads as a zero | `n_all` / `n_live`, statuses **and numeric shape** read, refuse otherwise |
| `$(git rev-parse --short HEAD)` ×2 and `$(date -u +%Y…)` — header and `SWEEP-RESULT` provenance | K1+K6 | **PROVENANCE** — `commit=` printing empty is the one cardinal telling a reader **which tree** the transcript grades, and `T399` is about to gate on that line | `$SWEEP_COMMIT` / `$SWEEP_DATE`, printing the word `UNMEASURED` rather than a blank |
| `$(git ls-files … \| wc -l \| tr -d ' ')` ×2 — the population lines | K1+K2+K6 | **PROVENANCE** | `$SWEEP_CORPUS_N` / `$SWEEP_UNTRACKED_N` |

### 1.2 Classified and left alone, with the reasoning

| site (by name) | kind | verdict |
|---|---|---|
| `SWEEP_ERRF=$(mktemp …) \|\| { … exit 2; }` | K1 | **READ.** Fatal. |
| `_top=$(git rev-parse --show-toplevel 2>/dev/null) \|\| _top=""` | K1+K3 | **FAIL-CLOSED.** Status read by the `\|\|`; the next line refuses at exit 2 on an empty `_top` or a failed `cd`. T386 drove it with a shim: `exit=2`, `SWEEP ABORT … no corpus to sweep`. Confirmed, not inherited. |
| `$(date -u +%s)` inside `CALIB_NEG_STR` and `CALIB_NEG_ERE` | K1 | **FAIL-CLOSED, and this is the one T386 listed without adjudicating.** If `date` fails the sentinel loses one component and stays unique via `$$` and `$RANDOM`. Both are **ANTI**-calibration arms: their refusal condition is `n > 0`. A degraded sentinel can only ever make the arm *more* likely to abort at exit 3, never less. **Left as-is deliberately** — changing it would be churn on a construct that cannot fail open. |
| `n=$(printf … \| awk …); arc=$?` | K1+K2 | **READ**, and the tally's numeric **shape** is validated too (`case … *[!0-9]*`). T386 drove `engine_count()` with fourteen hostile engines: `cases_guarded=14 cases_defective=0`, including `1e+17`, `-5` and `"   12  "`. |
| `printf '%s' "$a" \| grep -q '…'; esc_rc=$?` | K2 | **READ**, three outcomes separated. T386 drove the inverse defect (EPIPE at the front of a 400 kB argument): `rc=0`, no misfire. |
| `live=$(… \| grep -v -E "$ARCHIVE"); live_rc=$?` and its `arch` twin | K1+K2 | **READ**, `>=2` refuses. |
| `printf '%s' "$err" \| grep . \| cut \| sed` ×4 — the diagnostic echo pipelines | K2 | **DIAGNOSTIC, fail-neutral.** These print explanatory text *after* a verdict has already been decided by a status that was read. Losing them loses detail, never a verdict. The one carrying real weight is the LIVE-list print, and its **count is printed separately from `$n_live`**, so a silently truncated list is visible as a count with no lines under it. **Recorded, not repaired** — repairing it would add checks with no failure mode to catch. |
| `SWEEP_*=$((SWEEP_*+1))` ×8 | K1+K7 | **READ-NOT-APPLICABLE.** Arithmetic on integers this file initialises and owns. |
| every `[ "$rc" -ge 2 ]`, `[ "$ec" -eq 0 ]`, `[ "$ENGINE_N" -lt 1 ]` … | K7 | **READ.** Each operand is a `$?` captured on the preceding line, or `ENGINE_N`, which `engine_count()` only sets after validating its shape. **The one K7 operand that was NOT validated was the corpus assertion — F-2.** |
| the 7 new `if ! <cmd>` sites | K4 | **READ.** Five call `_errf_prime`/`_errf_read`, which return only 0 or 1 by explicit `return`. Two are `if ! VAR=$(cmd)`, where the assignment's status **is** the substitution's; both fall back to `UNMEASURED`. |
| `K5` | K5 | **0 sites, before and after.** `local x=$(…)` — where the builtin's status masks the substitution's — does not occur. Checked rather than assumed. |

---

## 2. `F-2` — THE BOUND WAS ITSELF FAIL-OPEN

T386 records `FU-T381-1`'s residual as *"bounded by the corpus assertion"* — the block that
refuses at exit 2 if `git ls-files` yields fewer than one file, before any selector runs.

**The bound was fail-open.** Driven, not reasoned:

```
$ bash -c 'x=""; if [ "$x" -lt 1 ]; then echo ABORTED; else echo "FELL THROUGH"; fi'
bash: [: : integer expression expected
FELL THROUGH
$ bash -c 'x=""; [ "$x" -lt 1 ]; echo "[ ] returned $?"'
[ ] returned 2
```

`[` returns **2** on a malformed comparison; `if` reads any non-zero as **false**; the abort does
not fire. So had `git ls-files` failed, the corpus assertion would have **passed the sweep
through on a corpus nobody counted** — and every `MEASURED ZERO` below it would have been
denominated in a number that was never taken.

It is `K1` inside `K7`: a command substitution in a numeric test. Neither of T381's two buckets
contains it, and neither did T386's list of six unaudited `$(…)` sites. **It was found by
auditing the class.**

Repaired: the corpus is counted once, its pipeline status read (`rc >= 2` ⇒ the count did not
run ⇒ exit 2), its numeric shape validated, and every consumer reads `$SWEEP_CORPUS_N`.

---

## 3. The rule this file should be maintained under

Six of the seven previously-known instances of the shape in this file were **introduced by
somebody repairing the previous one**. `C-1` was created by the repair for `R4`; `D-R5` was
created by the repair for `R3`. That is not a property of `casualty-sweep.sh` — **it is a
property of the repairs.**

The next task to touch this file should audit its **own diff** for discarded statuses across all
seven kinds, and re-run `t402-status-class-census.sh` on BEFORE and AFTER. **If a kind's count
moves, every new site in it needs a row here.** That is a cheaper obligation than the audit that
missed `C-1`, and it is the one that would have caught it.
