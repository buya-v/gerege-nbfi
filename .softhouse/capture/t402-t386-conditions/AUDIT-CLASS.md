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
| **K8** | **state loss in a subshell** — a state-mutating call (`sel`, `calibrate`, `_calib_refuse`, `engine_count`, or a `SWEEP_*=` assignment) inside a pipeline, `$( )`, `( )` or `&`. **Added by T424, `F-T408-2`.** | **17** | **29** |

**`K2` and part of `K3` were T381's two buckets. `K1`, `K5`, `K6` and `K7` had no row — and two
of those four were carrying live defects.**

**AND `K8` HAD NO ROW IN THIS TAXONOMY — the same lesson, one level up.** `K1..K7` all enumerate
ways an **exit status** is lost. `sel()`'s integrity also rests on **state written into globals**
(`SWEEP_REFUSED`, `SWEEP_RC`, `SWEEP_DIDNOTRUN`, `SWEEP_SELECTORS`) that the `SWEEP-RESULT` line
and `exit "$SWEEP_RC"` later read; a subshell discards those. T408 drove it — same selector, same
corpus, same commit:

```
sel "S16 ..." -n -E '\bstatus\b'          -> exit=3  refused=1  selectors=15   (correct)
sel "S16 ..." -n -E '\bstatus\b' | cat    -> exit=0  refused=0  selectors=15   (LOST)
```

The census **did** list that line — as a `K2` pipeline — but the verdict vocabulary below had no
verdict that fits, so an adjudicator working the list would have written DIAGNOSTIC and moved on.
So `T424` added both the kind **and** the verdict. **`K1..K8` counts re-measured by T424 on the
same two refs: `K1..K7` reproduce T402 exactly, cell for cell** (`out/T424-CENSUS-before-with-K8.txt`,
`out/T424-CENSUS-after-with-K8.txt` under `.softhouse/capture/t424/`).

---

## 1. Adjudication — every site that could lose a status

Verdicts are **FAIL-OPEN** (can print a number or an absence nobody measured), **FAIL-CLOSED**
(a lost status makes the run refuse), **PROVENANCE** (a lost status corrupts the record of what
was graded, not the grade), **READ** (the status is consulted), or — **added by T424,
`F-T408-2`** — **STATE-LOSS** (the construct runs in a subshell, so a global it writes is
discarded; the status may be read correctly and the *verdict* still evaporate). **STATE-LOSS is
not a flavour of FAIL-OPEN and must not be recorded as one:** the fail-open verdicts here are all
"a status was not consulted", and a `STATE-LOSS` site can consult every status it has and still
lose the answer. That distinction is the whole reason `F-T408-2` had no row to be written on.

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
| all sixteen `sel "S…" …` calls | K8 | **NOT state-loss.** All sixteen are bare at column 0. They appear in the wide `K8` list only because each carries a `\|` **inside its own quoted ERE**, exactly the over-inclusion `K2`/`K3` have by design. The de-noised `K8s` view lists **none** of them. |
| the eight `SWEEP_*=$((SWEEP_*+1))` counters | K8 | **NOT state-loss.** `$((` is arithmetic expansion, not a subshell; the wide `K8` matches them on the `$(` prefix. `K8s` excludes `$((` explicitly and lists none of them. |
| `SWEEP_ERRF=$(mktemp …)`, `SWEEP_CORPUS_N=$(… \| grep -c .)`, `SWEEP_UNTRACKED_N=$(…)`, `if ! SWEEP_COMMIT=$(…)`, `if ! SWEEP_DATE=$(…)`, `case "$SWEEP_UNTRACKED_N" …` | K8 | **NOT state-loss — the six `K8s` sites.** Each *runs* a command in a subshell but **assigns in the parent**; the global survives. Listed so the intersection is visibly non-empty: a `K8s` of zero and a `K8s` of six-benign must not look alike. |
| **live `STATE-LOSS` sites** | K8 | **ZERO, before and after** — measured, not assumed. The kind is latent. `t424-k8-discrimination.sh` shows `K8s` moving `6 → 7` the moment one selector is spelled `sel … \| cat`, so the row is not decorative. |

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
not fire. The corpus assertion would then have **passed the sweep through on a corpus nobody
counted** — and every `MEASURED ZERO` below it would have been denominated in a number that was
never taken.

> ### THE CAUSE THIS SECTION USED TO GIVE WAS WRONG — corrected by T424, `F-T408-5`
>
> It said: *"So had `git ls-files` failed, …"*. **A failing `git ls-files` ABORTS.** `grep -c .`
> prints `0` for an empty stream, so the substitution captures `"0"`, `[ "0" -lt 1 ]` is **true**,
> and the abort fires. T408 drove it; T424 re-derived it independently
> (`.softhouse/capture/t424/instruments/t424-f2-true-cause.sh`, `arms_failed=0`):
>
> | sabotage | captured | old block | new block |
> |---|---|---|---|
> | `git ls-files` exits 128 | `[0]` rc 1 | **ABORT** — stated cause does not reproduce | ABORT |
> | `grep` exits 2, no stdout | `[]` rc 2 | **FELL THROUGH** — the true cause | ABORT |
> | real `grep`, invalid regex | `[]` rc 2 | — | — |
> | healthy | `[9237]` rc 0 | passes | passes |
>
> **The fall-through needs `grep` ITSELF to fail** — invalid pattern, broken locale, missing
> binary, EMFILE. Mechanism right, exploit path right, **attribution wrong**, and the wrong
> attribution had been committed into `casualty-sweep.sh`'s own comment, where the next reader
> would have reasoned from it. Both sites are corrected.
>
> **Also do not infer that `pipefail` covers the `git ls-files` case** (T408 says it does; T424
> drove that false too): `pipefail` returns the **rightmost** non-zero status, which is
> `grep -c .`'s `1`, not git's `128`. The failing-`git` case is caught by the **value** test, as
> before. The status read adds the `grep`-failed case, which is the one that used to fall through.

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
**eight** kinds, and re-run `t402-status-class-census.sh` on BEFORE and AFTER. **If a kind's count
moves, every new site in it needs a row here.** That is a cheaper obligation than the audit that
missed `C-1`, and it is the one that would have caught it.

**T424 adds two clauses, both of which this file has now been bitten by:**

1. **Audit the diff for lost STATE as well as lost status.** `K8` exists because seven kinds of
   status loss did not describe a refusal evaporating in a subshell. When you add a kind, add the
   **verdict** that fits it too — `F-T408-2` had no row *and* no word.
2. **When you write down a CAUSE, drive the cause, not only the effect.** `F-2`'s repair was
   right and its explanation was wrong, and the explanation is what shipped in the source comment.
   An attribution nobody drove is a claim, and the next reader will fix the wrong thing with it.
