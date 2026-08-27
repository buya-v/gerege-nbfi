# T127 — independent review of T109 (`softhouse/T109-fork-point-digest-compare`, 5 commits)

**Verdict: MICRO-FIX.**

The fix is **correct and mergeable**. Every behavioural claim T109 makes about the rig reproduced on my
own runs, in my own throwaway clone, with my own drivers: the 12 refusals, the zero-stdout-byte ordering,
the three digests, the two new pins, and the P-24 scratch merge with a byte-identical transcript. I found
no defect in the shipped guard.

What fails is the **write-up**, and it fails in the way P-23 says to grade hardest — in the artefacts a
decision-maker reads. Six claims are false or unreproducible, and **one of them has already been acted on**:
the driver put T109's class-sweep headline into `main`'s commit message and dispatched **T125** on it. I
measured that headline and it is **refuted**. That is the finding of this review.

Reviewed at: `main` = `0a78286` (moved four times during this review: `9027f00` → `79a67d1` → `e35ea7b` →
`0a78286`); branch head `fb2048d`. Everything below was re-derived by me; nothing is read back from T109.

---

## 0. The gap T109 left — CLOSED. There *is* a Go toolchain.

T109 marked `go build` / `go test` / `gofmt -l` **[UNVERIFIED]** on the stated premise *"there is no Go
toolchain on this host (`which go` / `which gofmt` both fail; no `/usr/local/go`)"*. The premise is **false**,
and the disproof is a **committed file in the tree T109 was working in**:

`.softhouse/bin/go-env.sh` (tracked since `781c19e`, present on T109's own branch) reads, verbatim:

```
# Usage from any checkout OR worktree:
#     . /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
GEREGE_TOOLCHAIN=/Users/buv/gerege-nbfi/.softhouse/toolchain
```

`which go` failing is the **documented, expected** state — `.softhouse/conformance.sh:155-169` (`load_toolchain`)
says so in a comment and sources that very script. T109 read a designed condition as an absent capability.
(Now recorded as **P-30** on `main`; this is the second worker this fire.)

**I ran all four, in `nexus/`, at `go1.26.6 darwin/arm64`:**

| check | result |
|---|---|
| `go build ./...` | **exit 0**, no output |
| `go vet ./...` | **exit 0**, no output |
| `go test -count=1 ./...` | **ok** `internal/apps/loanschedule` 9.629s · **ok** `…/conformance` 9.312s · 2 pkgs no test files |
| `gofmt -l .` | names **exactly** `internal/apps/loanschedule/contract/contract.go` — and nothing else. **G-3 satisfied.** |

`gofmt -w` was **not** run (G-3). `git status --porcelain` clean before and after.

**Baseline conformance**, `bash .softhouse/conformance.sh`, on my worktree:

```
conformance: reference oracle (https://localhost:8443/…/actuator/health) probe = up
    parity vectors  PASS 42   FAIL 0
    cells compared  5576 graded, 84 ungraded
    invariant violations 0
    invariant assertions 0 NOT RUN
VERDICT: PASS (exit 0)
```

Every baseline figure in the brief matched.

---

## 1. The pre-fix green — reproduced, and it **refutes T109's account of it**

### 1.1 What I found

The brief asked me to pin `main`'s tip against the pre-fix rig and reproduce T103's green 25/25. With
**today's** `main` that is impossible, and the reason is the finding.

```
LEG 1a: PRE-FIX rig (clone main = T102 bytes), pin = TODAY'S main tip 79a67d1
  exit=1  stdout_bytes=31428  proof_row_artefacts=2
  T82 guard proofs: 18 as expected, 7 not as expected
```

Not a green. To reproduce T103's case 5i I had to use the `main` tip **T103 actually had**, `2755999b`
(`T103-review-of-T102.md:136` records it). Then:

```
A. PRE-FIX rig, pin = 2755999b (T103 case 5i, verbatim)
   exit=0  stdout_bytes=41954  proof_artefacts=4
   BASE run-pass3i.sh sha256 d84ec7bf9888baa1b1fa3f75be679af982ae7435c4aa2e1edbb06f999084e0d3
   T82 guard proofs: 25 as expected, 0 not as expected      <- T103's green, reproduced

B. FIXED rig (T109), the SAME commit + the real pinned digests
   exit=0  stdout_bytes=42604  proof_artefacts=4
   BASE run-pass3i.sh sha256 d84ec7bf…  [MATCHES PIN]
   T82 guard proofs: 25 as expected, 0 not as expected      <- the FIX ACCEPTS IT TOO
```

The extracted `BASE run-pass3i.sh` digest at `2755999b` is `d84ec7bf…` — **the fork point's own digest.**
Measured across every relevant tip:

| commit | `run-pass3i.sh` | `T74-promote-vectors.py` | `build-counterfactuals.py` |
|---|---|---|---|
| `8da4b83` (fork point) | `d84ec7bf…` | `27bb20b4…` | `e7aee917…` |
| `2755999` (main @ T103) | `d84ec7bf…` | `27bb20b4…` | `e7aee917…` |
| `ab2de89` (main @ T102) | `d84ec7bf…` | `27bb20b4…` | `e7aee917…` |
| `61e7102` (T102's merge, which landed T82) | `3ca0d3f6…` | `efcfcfa5…` | `b1e9f608…` |
| `f7e3d59` / `79a67d1` (main @ T109 / today) | `3ca0d3f6…` | `efcfcfa5…` | `b1e9f608…` |

### 1.2 F-1 (P2) — "a green 25/25 against a baseline that already contains the fix" is FALSE

`T109.md:31`, `FORK-POINT-SHA:25`, `prove-guards-go-red.sh:79`, and — worst — the **operator-facing FATAL
text** at `prove-guards-go-red.sh:209`:

> `prove-guards-go-red.sh:209`: `"       main's tip scored a green 25/25 before this check existed."`
> `T109.md:31`: *"the rig scores a green **25/25** against a baseline that already contains the fix, i.e.
> every counterproof compares the fixed code against itself and prints a green row for a comparison that
> never happened."*

At T103's `main` tip the three baseline files were **byte-identical to the fork point's**. T82 was not yet
merged (`git merge-base --is-ancestor 55409cfd ab2de893` → false). The baseline did **not** contain the fix,
the counterproofs ran against genuine pre-T82 bytes, and the green 25/25 was the **arithmetically correct
verdict on the bytes that ran**. Nothing "compared the fixed code against itself".

**T103 did not say this.** `T103-review-of-T102.md:211` says only: *"5i | current `main` tip — a valid commit,
not the fork point | accepted, green 25/25"*. That is accurate and modest. **T109 escalated it into a causal
story that its own §2 already contradicts** — §2 says correctly *"A different commit carrying byte-identical
files is not a defect — the counterproofs would be running against exactly the right code."* The document
holds both, ten paragraphs apart. This is P-26's shape exactly, in the task written to fix P-26's shape.

**Does this weaken the fix?** No. The property the pin now checks — *these bytes are the pre-T82 bytes* — is
the right property, and it is why the fixed rig accepts `2755999b` and refuses `79a67d1`. But the sentence is
now shipped as a diagnostic message an operator reads at the moment of failure, and it tells them something
that did not happen.

**Micro-fix:** four sentences, no predicate change. Say what is true: *a wrong-but-valid pin was accepted
with nothing checking the bytes; the danger it exposes is a baseline that contains the fix, which is what
today's `main` tip is.*

### 1.3 F-2 (P3) — the re-derivation recipe in the file was **already stale when T109 wrote it**

`FORK-POINT-SHA:46` and the FATAL recovery block at `prove-guards-go-red.sh:212` both instruct:

```
git merge-base main softhouse/T82-pass3i-defects
```

Run today, and at every `main` tip T109 saw (`41132e5`, `6d2a1e9`, `f7e3d59` — I checked all of them):

```
$ git merge-base main softhouse/T82-pass3i-defects
55409cfda225518d014a0d203dc4b36191a045a8      <- T82's HEAD, not the fork point
$ git show 55409cfd:.softhouse/capture/src/run-pass3i.sh | shasum -a 256
3ca0d3f6…                                     <- the POST-fix bytes
```

T82 has been an ancestor of `main` since `61e7102`, so the merge-base collapses onto T82's own head. The
recipe worked for T102 (`main` = `ab2de89`) and for T103 (`main` = `2755999b`); it has been wrong ever since.

The consequence is an **infinite loop in the recovery path**: the rig refuses, prints "Re-derive the pin; do
not adjust the digests to match it", the operator follows the printed command, gets `55409cfd`, and is
refused again. This is precisely T103's **F-2 class — a documented recovery command that does not work** —
which T109 spent a section fixing at three other sites. It fails safe, so P3, not P2.

**Micro-fix:** the correct re-derivation is `git rev-parse softhouse/T82-pass3i-defects~4` or, better,
`git log --format=%H -1 <T82's first commit>^`. Simplest honest form: state that the commit is a **literal
locator** and that the *digests* are authoritative — which T109 already argues in §2.

---

## 2. The 12 red cases — all reproduce, and the ordering holds three ways

My own driver, my own clone, `find scratch/ -name 'att-*' -o -name 'cf-*'` as the proof-row metric
(it returns **4** on a green run, so it discriminates):

```
CASE       EXIT   STDOUT_BYTES  PROOF_ROWS   note
GREEN      0      42604         4            25 as expected, 0 not
R1         2      0             0            FATAL: THE PINNED BASELINE IS NOT THE FORK POINT
R1b        1      32078         2            18 as expected, 7 not as expected
R2         2      0             0            unknown directive '<bare sha>' … T102-era format REFUSED
R3         2      0             0            digest moved (promote-vectors, one nibble)
R3b        2      0             0            digest moved (build-counterfactuals — the third file)
R4         2      0             0            no `commit` directive found
R5         2      0             0            more than one `commit` directive  (T103 F-6)
R6         2      0             0            could not extract … from the pinned baseline (root commit, F-4)
T102-1     2      0             0            FORK-POINT-SHA is missing
T102-2     2      0             0            `commit` value is not lowercase 40-hex
T102-3     2      0             0            `commit` must be a FULL 40-hex sha
T102-4     2      0             0            deadbeef… is not a commit in this repository
GREEN2     0      42604         4            25 as expected, 0 not      (pin restored, byte-identical)
```

**11 of 12 give exit 2 with 0 stdout bytes and 0 proof-row artefacts.** R1b behaves exactly as documented.
(My R1b byte count is 32,078 vs T109's 33,843 — the difference is repo-root path length in the transcript,
not content.)

**The ordering claim is load-bearing and I verified it three independent ways:**

1. **Zero stdout bytes** — the header is the first thing the rig prints; it had not run.
2. **Zero `att-*`/`cf-*` artefacts** in `scratch/` — no `expect` row wrote anything.
3. **Directly, from source line numbers** — which is the check T109 did not state:

```
prove-guards-go-red.sh:217   check_base_digest "$BASE_PATH_1" "$PIN_1" "$GOT_1"
prove-guards-go-red.sh:224   FATAL: THE CAPTURE UNDER TEST IS NOT THE PINNED ARTEFACT
prove-guards-go-red.sh:261   echo "T82 guard proofs"                    <- the header
prove-guards-go-red.sh:283   expect 0 "CONTROL — …"                     <- proof row 1
```

Both refusals precede both. There is no `||` swallow, no `set -e` dependence, and `exit 2` is unconditional.

### 2.1 The two NEW pins, driven red by me

| pin | mutation (clone only) | result |
|---|---|---|
| capture under test | one newline appended to the clone's `capture-prod3i-raw.json` | **exit 2, 0 bytes, 0 rows**, `FATAL: THE CAPTURE UNDER TEST IS NOT THE PINNED ARTEFACT` |
| sliced precondition block | one **comment line** inserted inside the `<<'PY'` heredoc of the clone's `run-pass3i.sh` — behaviour unchanged, bytes moved | `FATAL: THE SLICED PRECONDITION BLOCK IS NOT THE PINNED BLOCK`, **exit 1, 23 as expected, 2 not** |
| both restored | `git checkout` | **25/25, exit 0** |

Matches T109 exactly. Both guards are real; neither is decoration.

---

## 3. The three digests — a fourth independent measurement

```
$ git show 8da4b831b96a146c2b46ad34d85ed098395de160:.softhouse/capture/src/run-pass3i.sh | shasum -a 256
d84ec7bf9888baa1b1fa3f75be679af982ae7435c4aa2e1edbb06f999084e0d3
$ git show 8da4b831…:.softhouse/handoff/T74-promote-vectors.py | shasum -a 256
27bb20b4161bb5359ff3eaae5cea963e8a26585a8f2ede4b8ab12507cf87c3d1
$ git show 8da4b831…:.softhouse/capture/t74-multiplesof/build-counterfactuals.py | shasum -a 256
e7aee91733596e12e48b8abf0070c0c3e2f9574cdf70189a273c491dfaceac3f
```

**All three agree with T102, T103 and T109.** Four independent parties.

I also confirmed `8da4b83` **is** the fork point, structurally rather than by merge-base:
`git log --oneline 8da4b83..55409cfd` = exactly T82's four commits (`402a1da`, `0101fbb`, `849d618`,
`55409cf`) and nothing else. The pin names the last commit before T82 touched anything.

---

## 4. The ten invocation forms — **and here T109's discrimination claim breaks**

T109 ran **leg A (wrong pin) on all ten forms** and **leg B (correct pin) on three**, while its committed
transcript header reads `LEG B — CORRECT PIN, SAME FORMS`. Three of ten is not "same forms", and the seven
it skipped are exactly the ones where a shell or `$0` problem could manufacture a false refusal.

**I ran both legs on all ten:**

```
LEG A — WRONG-BUT-VALID PIN (main tip 79a67d1)
  bash <abs>, cwd=repo root            exit=2 bytes=0     rows=0
  bash <rel>, cwd=repo root            exit=2 bytes=0     rows=0
  bash <bare>, cwd=rig dir             exit=2 bytes=0     rows=0
  bash ./<name>, cwd=rig dir           exit=2 bytes=0     rows=0
  bash <abs>, cwd=/tmp                 exit=2 bytes=0     rows=0
  bash <abs>, cwd=$HOME                exit=2 bytes=0     rows=0
  direct exec (shebang)                exit=2 bytes=0     rows=0
  sh <abs>                             exit=2 bytes=0     rows=0
  zsh <abs>                            exit=2 bytes=0     rows=0
  piped: bash < script                 exit=2 bytes=0     rows=0

LEG B — CORRECT PIN, ALL TEN FORMS
  bash <abs>, cwd=repo root            exit=0 bytes=42604 rows=4   25/0
  bash <rel>, cwd=repo root            exit=0 bytes=42604 rows=4   25/0
  bash <bare>, cwd=rig dir             exit=0 bytes=42604 rows=4   25/0
  bash ./<name>, cwd=rig dir           exit=0 bytes=42604 rows=4   25/0
  bash <abs>, cwd=/tmp                 exit=0 bytes=42604 rows=4   25/0
  bash <abs>, cwd=$HOME                exit=0 bytes=42604 rows=4   25/0
  direct exec (shebang)                exit=0 bytes=42604 rows=4   25/0
  sh <abs>                             exit=0 bytes=42604 rows=4   25/0
  zsh <abs>                            exit=2 bytes=0     rows=0   *** REFUSES THE CORRECT PIN ***
  piped: bash < script                 exit=0 bytes=42604 rows=4   25/0
```

### F-3 (P2) — the `zsh` row has **zero discriminating power**, and T109 could not have known

```
$ zsh ./prove-guards-go-red.sh          # with the COMMITTED, CORRECT pin
FATAL: …/FORK-POINT-SHA — unknown directive 'commit 8da4b831b96a146c2b46ad34d85ed098395de160'.
       A BARE SHA on its own line is the T102-era format and is REFUSED deliberately…
EXIT=2
```

**Diagnosis:** `prove-guards-go-red.sh:127` does `set -- $fork_line`. zsh does not word-split unquoted
parameter expansions, so `$1` becomes the entire line and every directive is "unknown". Under zsh the fixed
rig **refuses everything**, correct pin or not.

Two consequences:

1. The zsh row in `every-invocation.txt` LEG A proves nothing. It is P-22's own shape — *a refusal that
   cannot go green is not a refusal, it is a rig that cannot run* — inside the evidence for a P-22 fix. It is
   also this program's own conformance-guard story (a wrong-interpreter `exit 2` misread as a genuine
   refusal), which `.softhouse/conformance.sh:37-64` has a 30-line comment about.
2. It is a **regression T109 introduced**. The pre-fix parser used `grep -v '^#' | tail -1` and is
   shell-agnostic:

```
$ git checkout main && zsh ./prove-guards-go-red.sh
T82 guard proofs: 25 as expected, 0 not as expected
```

**Severity P2, not P1:** the script is `#!/bin/bash`, its only documented usage is
`bash prove-guards-go-red.sh`, its only repo caller is `T82.md:557` (a human instruction in bash form), and
it **fails safe**. The defect is the *claim*, not the guard.

**Micro-fix:** drop the zsh row from the discrimination table (or mark it "refuses unconditionally — not a
discrimination datum, see F-3"), and relabel the transcript's `SAME FORMS` header to `3 OF THE 10 FORMS`.
Optionally one line of portability (`read -r k v p <<< "$fork_line"` or `setopt shwordsplit`); not required.

**9 of 10 forms discriminate cleanly.** The core claim survives; the count does not.

---

## 5. P-24 — the scratch clone, reproduced in the state that killed T98

`git clone --local --no-hardlinks` of the live repo, `git merge` T109's branch into the **clone's own `main`**:

```
clone main BEFORE merge : e35ea7b  (softhouse: T99 done — …)
clone main AFTER merge  : 1e7fdd65f09a38c7c8b311e08df63411ee73002b
HEAD                    : 1e7fdd65f09a38c7c8b311e08df63411ee73002b
main == HEAD ?          : YES
merge-base main HEAD    : 1e7fdd65f09a38c7c8b311e08df63411ee73002b   <- the merge commit itself
current branch          : main
```

That is exactly T98's fatal state, on a `main` tip **two commits newer than any T109 saw**.

| leg | result |
|---|---|
| **A** — rig on the merge, committed pin | **25 as expected, 0 not — exit 0**; BASE `8da4b83…`, all three `[MATCHES PIN]`, capture `[MATCHES PIN]` |
| **B** — pin the clone's own `main` (= the merge commit) | **exit 2, 0 stdout bytes, 0 proof rows**; expected `d84ec7bf…`, observed `3ca0d3f6…` from commit `1e7fdd65…` |
| **F** — post-merge transcript vs the branch's committed `TRANSCRIPT.txt`, root-normalised | **BYTE-IDENTICAL** (`diff` exit 0) |
| **G** — clone hygiene | `git status --porcelain` **empty**; the real repo was never written |

Leg F is the strong result and it holds: **the transcript does not depend on merge state.** T109's P-24
handling is correct, and its refusal to accept a worktree for this (`git worktree add` leaves `main` at the
pre-merge tip) is right — I confirmed the mechanism independently.

I also verified the `TRANSCRIPT.txt` diff on the branch contains **no moved number**: the 148 changed lines
outside the new `[MATCHES PIN]` / `[provenance …]` labels are worktree-path substitutions
(`agent-a97675ac…` → `agent-a7aa8927…`) and nothing else.

---

## 6. F-2 / F-1 / F-6 — verified, one site missed

**F-2 (the `cat FORK-POINT-SHA` recovery command).** Breakage reproduced against the real pre-fix bytes:

```
$ git show $(cat …/FORK-POINT-SHA):.softhouse/handoff/T74-promote-vectors.py
fatal: failed to stat '# T102 / T109 — THE COUNTERPROOF BASELINE: A LITERAL IMMUTABLE COMMIT SHA, …
```

The literal form works. All three named sites replaced: `mutate.py:13`, `prove-promote-guards.py:11`,
`prove-promote-guards.py:206` (the operator-facing `SystemExit`).

### F-4 (P3) — the F-2 sweep missed a fourth site, in a file T109 was editing

`.softhouse/handoff/…/T82.md:124`, **byte-identical on `main` and on T109's branch**:

> `| **counterproof** | the **same** mutated capture, through **`git show $(cat T82-guard-proofs/FORK-POINT-SHA):…/run-pass3i.sh`** — the fork point's REAL pre-T82 bytes …`

This is not a description of the defect — it is the never-working command presented as **the command that
produced the counterproof evidence**. T109 edited `T82.md` (at `:397+`, for F-1) in the same commit and did
not sweep it. P-26, again: the correction landed where the defect was *named*, not where it is *restated*.

**F-1 (the `sweep-census.py` stamp).** Verified stronger than claimed. `SWEEP.txt` is regenerated and
stamped `aeedf9b9b11fa43352b627a7e1da130781e660d6 (clean tree)`, and **re-running the committed script at
that commit reproduces the whole file byte-identically** (`diff` exit 0 ignoring the stamp line):

```
prose files (TIER 1, bare-numeral net): 194
other files (TIER 2, structural nets):  1943
lines over 4000 chars skipped by TIER 2 only: 333
```

Driven red and back by me:

```
$ printf '\n# probe\n' >> mutate.py && python3 sweep-census.py .
generated at commit: fb2048de… + 1 UNCOMMITTED path(s) — THESE COUNTS BELONG TO NO COMMIT; re-run on a clean tree before citing them
$ git checkout -- mutate.py && python3 sweep-census.py .
generated at commit: fb2048de… (clean tree)
```

And the exclusion is **exactly** the script's own two outputs — dirtying `SWEEP.txt` or `TRANSCRIPT.txt`
still reports `(clean tree)`; dirtying anything else does not. As designed and as documented.

**F-6 (duplicate directive)** — closed. Case R5: exit 2, 0 bytes, 0 rows,
`more than one \`commit\` directive (T103's F-6…)`.

**F-5 (uppercase hex still refused)** — unchanged, deliberate, fails safe. Agreed.

**File modes.** `git diff --raw main...HEAD` shows only `:100644 100644` and `:000000 100644`. **No mode
change remains.** The accidental `100755` was genuinely reverted. (I chmod'd the script in my *clone* for
the direct-exec form and restored it; the real repo was never touched.)

---

## 7. The class sweep — re-censused independently

### 7.1 F-5 (P3) — the denominator is not reproducible

T109: *"I censused **every** `*.sh` / `*.py` under `.softhouse/` (**356 files**) plus `conformance.sh`."*

On T109's **own branch head** `fb2048d`, clean tree, every counting method agrees on **348**:

| method | count |
|---|---|
| `find .softhouse -type f -name '*.sh'` + `-name '*.py'` | 108 + 240 = **348** |
| `git ls-files -- .softhouse \| grep -E '\.(sh\|py)$'` | **348** |
| `find` without `-type f` (dirs too) | **348** |
| repo-wide on-disk, excluding `.git` | **348** |
| same census at `main` (`79a67d1`) | **345** — i.e. 345 + T109's own 3 new scripts = 348 |

`conformance.sh` is one of the 348 (it lives at `.softhouse/conformance.sh`), so "356 plus conformance.sh"
overcounts by **8 or 9** and I could not reproduce it by any variant, including the classic
`-name … -o -name …` precedence trap. A census's denominator is the one number a reader cannot check
cheaply; it should be the one number that is right. **P-29 was ratified on `main` for exactly this shape
while T109 was in flight.**

### 7.2 My own structural census, for comparison

| measure | count |
|---|---|
| `.sh`/`.py` under `.softhouse/` | **348** |
| of those, files computing a digest (`shasum\|sha256sum\|md5\|cksum\|hashlib\|sha256(`) | **82** |
| …with a detectable digest **comparison** | **26** |
| …with **no** detectable comparison | **56** |

56 candidate files is consistent with T109's "~90 sites" (sites > files). The *shape* of the finding is
sound and I agree it is systemic. The blind spots T109 declared, **quantified**:

| T109's declared limit | measured size |
|---|---|
| digests in Java — not censused | **44** `*.java` under `.softhouse/` |
| digests in Go — spot-checked for one symbol | **21** `*.go` under `nexus/` |
| rigs outside `.softhouse/` and `nexus/` | **0** `.sh`/`.py` — this limit is empty, and saying so would have strengthened the sweep |
| non-`.sh`/`.py` executables under `.softhouse/` | **0** `.sql`/`.jq`/`Makefile`/`.yml` — also empty |

The two empty limits are worth stating: T109 hedged where there was nothing to hedge about, and the 44 Java
files are the one that is real.

### 7.3 Spot-verification of the backlog rows

| T109's row | my measurement | verdict |
|---|---|---|
| `capturesCanonicalSha256` in **8** rigs, read by no code | **8** files (`run-pass3b/c/d/e/f/g/h/i.sh`); the only `.go`/`.py` hit is a **comment** at `emi.go:448`; no comparison anywhere | **ACCURATE** |
| `CP_DIGEST` in **11** rigs with no `EXPECTED_*` | **6** files, 12 lines; `CP_COUNT` the same 6; `EXPECTED_CP*` occurrences: **0** | substance **ACCURATE**, count **WRONG (6, not 11)** |
| `run-t50-tier1/2.sh:90` class digests, only `grep -q MISSING` asserted | confirmed at `:100-103` — presence only, digests never compared | **ACCURATE** |
| `t45-probe/gen-cumulative-vs-progressive.sh:14-15` two `md5`s never compared; `:43` conclusion a hard-coded literal | confirmed, including the mitigating whole-method `diff` | **ACCURATE** |
| §8.3(3) the 3b–3h seam check may be a tautology | confirmed: `run-pass3b.sh:79` computes `SEAM_SHA` and passes it to the emitter; only `run-pass3i.sh:120,188,191` has `EXPECTED_SEAM_SHA` and a real comparison | **ACCURATE — and the best unactioned item in the sweep** |

---

## 8. THE RULING THE DRIVER NEEDS — T109's headline finding is REFUTED

### 8.1 F-6 (P1) — "a HALF_EVEN JVM writes a complete attestation and exits 0" is FALSE

T109 §8.2 item 1, called *"the highest-value item this task found"*, reproduced by the driver into `main`'s
commit message `79a67d1` and dispatched as **T125**:

> *"`attest.py`'s only two `sys.exit(1)` calls are at `:98` (preconditions) and `:240` (HTTP≠200); neither is
> the canary. **A `HALF_EVEN` JVM writes a complete attestation and exits 0.** This is P-22's founding defect,
> verbatim, in three files."*

**The mechanics are accurate. The consequence is false.** The same canary **is** gated — one level up, in the
script `attest.py` itself runs at `:90`:

```
charges/bin/preconditions.sh:36    CANARY_EXPECT=${CANARY_EXPECT:-20925.05}
charges/bin/preconditions.sh:159   [ "$p1" = "$CANARY_EXPECT" ] && ok "…" \
charges/bin/preconditions.sh:160     || bad "effective rounding-mode canary returned period-1 interest '$p1',
                                          expected '$CANARY_EXPECT'; 20925.04 would mean the process is
                                          running HALF_EVEN"
charges/bin/preconditions.sh:39    bad()  { printf '  FAIL  %s\n' "$1" >&2; fails=$((fails+1)); }
charges/bin/preconditions.sh:177-180  if [ "$fails" -ne 0 ]; then … exit 1; fi

charges/bin/attest.py:90   pre = subprocess.run('CANARY_REQ=%s sh %s %s' % (canary, …'preconditions.sh', TENANT), …)
charges/bin/attest.py:95   if pre.returncode != 0:
charges/bin/attest.py:97       sys.stderr.write('\nABORT: preconditions breached — no capture attempted, no attestation written.\n')
charges/bin/attest.py:98       sys.exit(1)
```

On a `HALF_EVEN` JVM the canary returns `20925.04`, `bad` fires, `preconditions.sh` exits 1, and `attest.py`
exits 1 at `:98` printing **"no capture attempted, no attestation written."** It does not write a
green-looking attestation. It writes **nothing**.

The `verdict` string at `:337` / `:377` / `:437` is a **redundant copy** of a check that *is* enforced — not
the unenforced original. It is still decoration and still worth deleting or wiring, but it is P3 hygiene, not
P-22's founding defect.

**`pathb/t36/attest.py`** has four `sys.exit(1)` sites (`:57`, `:66`, `:174`, `:325`), not two; `:325` is an
HTTP≠200 capture abort. T109's "only two `sys.exit(1)` calls" is true of `charges/bin/attest.py` and stated
as if it covered all three.

### 8.2 …AND THE REAL DEFECT IS NEXT DOOR, UNREPORTED — P1

There **is** a live hole in that family, and it is worse than the one T109 named:

```
                                                    sha256                              CANARY_EXPECT
pathb/t36/preconditions.sh            237 lines   7c68f2dc…   HARDENED  (:54 constant, :181 env tripwire)
charges/bin/preconditions.sh          183 lines   9256b881…   NOT HARDENED (:36 ${CANARY_EXPECT:-20925.05})
audit-t44/charges/bin/preconditions-COPY.sh 183   9256b881…   NOT HARDENED (identical copy)
```

`t36/preconditions.sh:45-53` records that T80 closed exactly this — *"`CANARY_EXPECT` used to be
env-overridable … the tripwire now watches `CANARY_EXPECT` ITSELF"* — and `:181-182` makes an environment
attempt its own `bad`. **That hardening was never back-ported to the charges copy.** The two files now differ
in 66 lines.

So for `attest.py` and `attest-t40.py`, which run the **charges** copy via `subprocess.run(…, shell=True)`
and therefore inherit the environment:

> **`CANARY_EXPECT=20925.04 python3 attest.py` passes the gate on a HALF_EVEN JVM and writes a complete
> attestation.**

That is T80's ATTACK 4a (`pathb/t80/run-attacks.sh:88-94`), still open in the charges rigs.

**And the attestations misattribute which script gated them:**

- `charges/bin/attest.py:269` writes `'preconditions_script': 't36/preconditions.sh'` — it runs
  `charges/bin/preconditions.sh`.
- `charges/bin/attest-t40.py:305-306` writes `'preconditions_script': 'bin/preconditions.sh (copied verbatim
  from pathb/t36/preconditions.sh)'` — **not verbatim; 66 lines and the hardening apart.**

An attestation naming a hardened script while running an unhardened one is P-27 with the drift built in, and
it is a false provenance claim in an artefact whose whole purpose is provenance.

### 8.3 My ruling on the scope call

**The scope call was RIGHT: T109 was correct not to touch those files.** They are another worker's territory
and a fix there is a predicate change requiring its own red/green run.

**The escalation was WRONG**, and it cost real work. T109 promoted a redundant copy of an enforced check into
"P-22's founding defect, verbatim, in three files, P1", the driver believed it, wrote it into `main`'s commit
log, and dispatched T125 against it. Meanwhile the genuine hole — an env-overridable gate and two false
provenance strings — went unreported, and is in the *same three files*.

**Action for the driver, before T125 lands anything:**

1. **Re-scope T125.** Its stated premise is refuted. Deleting or wiring the `:337`/`:377`/`:437` verdict field
   is fine hygiene, but it is not the P1.
2. **Give T125 the real target:** back-port T80's `CANARY_EXPECT_ENV_ATTEMPT` tripwire into
   `charges/bin/preconditions.sh` and `audit-t44/charges/bin/preconditions-COPY.sh` (drive it red with
   `CANARY_EXPECT=20925.04`), and correct the two `preconditions_script` provenance strings.
3. **Correct `main`'s ledger.** The commit message of `79a67d1` states the refuted claim as driver-verified
   fact (*"Driver verified the shape"* — the shape, yes; the consequence, no).

---

## 9. `admit.go` — assessed, and my ruling

`nexus/internal/apps/loanschedule/conformance/admit.go:574-597`:

```go
if v.Provenance.CaptureRef == "" {
    bad("a parity vector must cite provenance.capture_ref: …")
} else {
    abs := filepath.Join(repoRoot, v.Provenance.CaptureRef)
    info, err := os.Stat(abs)
    switch {
    case err != nil:      bad("provenance.capture_ref %q does not resolve to a file …")
    case info.IsDir():    bad("provenance.capture_ref %q is a directory …")
    case v.Provenance.CaptureSHA256 != "":                       // <- the skip
        …
        if got := hex.EncodeToString(sum[:]); got != v.Provenance.CaptureSHA256 {
            bad("provenance.capture_sha256 %s does not match the referenced capture (%s)", …)   // :594
        }
    }
}
```

**Can an empty capture digest reach it on a promoted vector? Today: no.** I measured the whole corpus:

| | |
|---|---|
| vector files inspected | **47** |
| `class: parity` | **42** |
| parity vectors with a non-empty `capture_sha256` | **42 of 42** |
| `capture_sha256` empty or absent | **5** — exactly the 4 contract-refusal + 1 self-test, which have no capture and legitimately carry none |
| parity vectors with no usable digest | **0** |

**But the guard cannot fail, and the corpus is the only thing holding it up.** Nothing requires it:

- `vector.go:183` documents the field as **"optional. When present the harness verifies it"** — the skip is
  deliberate design, not a bug.
- `PIN.json` imposes no requirement.
- `admit.go` requires `capture_ref` (must exist) and `capture_case_id` (must be non-empty) for parity — but
  **not** `capture_sha256`. The harness insists the capture file exists and does not insist it is the same
  bytes the numbers were transcribed from. That asymmetry is the defect.
- **`structural_test.go:750-847` (`TestNewSchemaFieldsDecode`) constructs a `"class": "parity"` vector with
  `"capture_sha256": ""` and admits it.** The skip is not merely reachable — it is **enshrined in a passing
  test in the graded module.**
- The promoters are inconsistent: `T74`, `T64`, `T61`, `T58`, `T57`, `T8` all write it, and `T57`/`T61`
  transcription audits *do* compare it (`T61-transcription-audit.py:99-100` `sys.exit`s on a mismatch). So
  writing it is the convention and enforcing it is not.

**What the skip permits, if a digest ever goes missing:** a parity vector whose expected values were
transcribed from a capture that has since changed on disk would be admitted and graded, with the harness
reporting PASS against numbers whose provenance it never checked. That is a silent poisoning of the parity
claim — the exact class this program has rejected five times.

### Ruling: **yes, it deserves its own task — but a small P3 one, not a P2.**

Not a defect today (42/42 covered, and I verified it rather than assuming it). It is a **guard that cannot
fail**, which P-22 says is worse than none because it is believed. The task is one `if` and one fixture:

```go
if v.Class == ClassParity && v.Provenance.CaptureSHA256 == "" {
    bad("a parity vector must cite provenance.capture_sha256: capture_ref proves a file EXISTS, "+
        "not that it holds the bytes these numbers were transcribed from")
}
```

plus a fixture driving it red, plus flipping `structural_test.go`'s fixture (or scoping it to a non-parity
class). `vector.go:183`'s "optional" comment must change with it, or the next reader will re-open the hole.
`nexus/` is another worker's this fire — **do not fold this into T125.**

T109's placement of this at "P2, worker-owned, reported" was **right in kind, one notch high in severity**,
and its line citation is `:594` where the comparison is `:593` and the skip is `:586`.

---

## 10. Standing constraints

| constraint | result |
|---|---|
| `git diff main...HEAD -- .softhouse/vectors/` | **EMPTY** |
| `git diff main...HEAD -- nexus/` | **EMPTY** |
| `PIN.json`, `capabilities.json` | **absent from the diff** |
| `.softhouse/conformance.sh` | **absent from the diff**; executed read-only |
| other workers' territory (`pathb/t99`, `t91`, `charges`, `t83-nonamortizing`, `t108-grep`, `gates.md`, `emi.go`, `conformance/`) | **absent from the diff**; I read `charges/` and `nexus/` **only from a throwaway clone**, never from the live tree, and wrote to neither |
| file modes | only `:100644 100644` and `:000000 100644` — **no mode change remains** |
| money non-negotiables (`float`, `first_name`/`last_name`, `insured`/`guaranteed`, `ojdbc`/`oracle.jdbc`, `mysql`/`mariadb`/`:1521`, Stripe/Plaid, `FixedZone`/`+08:00`) over added lines | **no hits** |
| **P-25** (no float in analysis scripts) | **clean.** The decimal literals in added lines are all inside regenerated `SWEEP.txt` / `TRANSCRIPT.txt` **quoted rig output** that already existed on `main`; T109's own additions compute only git object ids, sha256 hex and integer counts. `sweep-census.py`'s stamp code is `subprocess` + string handling, no arithmetic on an amount. |
| `gofmt -w` on `contract.go` (G-3) | **never run.** `gofmt -l` only. |
| oracle | contacted **once**, read-only, by `conformance.sh`'s health probe (`probe = up`). No container restarted, rebuilt or re-seeded; no DB write; no vector promoted. |
| Oracle Database / MySQL / MariaDB | not present anywhere in this work. PostgreSQL only. |

---

## Explicitly UNVERIFIED

- **[UNVERIFIED]** that 25/25 is the *correct* score rather than the *expected* one. Like T102, T103 and
  T109, I inherited T82/T87's guard predicates and expected exit codes and did not re-derive whether each
  guard tests what its label claims. That was T87's job; it remains the largest unaudited assumption under
  this whole chain, now carried by a fourth task.
- **[UNVERIFIED]** the behaviour of every §8.2 backlog site. I executed **none** of them. My verification of
  items 1, 5, 6, 7 and §8.3(3) is **static reading plus grep**, exactly like T109's. The one exception is the
  `HALF_UP` canary path, where I read the full call chain `attest.py:90 → preconditions.sh:36,159-160,177-180
  → attest.py:95-98` — still a reading, not a run. **I did not run `attest.py` against a HALF_EVEN JVM**, and
  I could not: it needs docker, the pinned image and a tenant. §8.1's refutation is a source re-derivation of
  a control flow, and it should be *observed* before T125 is re-scoped on it alone.
- **[UNVERIFIED]** whether `charges/bin/preconditions.sh`'s env-override is *exploitable in practice* — I did
  not run `CANARY_EXPECT=20925.04 python3 attest.py`. The unconditional-vs-defaulted assignment and the
  `shell=True` env inheritance are both read from source.
- **[UNVERIFIED]** the origin of T109's "356". I reproduced 348 by five methods and could not construct 356;
  I cannot say what T109 counted, only that no counting of the committed tree gives its number.
- **[UNVERIFIED]** that no **eleventh** invocation form exists. I tested the same ten, both legs. A `Makefile`
  target, a CI step, or a wrapper that `source`s rather than executes is not covered — and sourcing would be
  worse under T109's rig than T102's, because `exit 2` would kill the caller's shell.
- **[UNVERIFIED]** my own P-26 sweep's completeness, with the same five limits T109 published (§5) plus one
  it did not state: I swept `.softhouse/**` for the concept, and a restatement in `docs/`, in a commit
  message, or in `.claude/` skill definitions would not be found. `tasks.json` carries **2** occurrences of
  *"nothing can"*; T109 read them and left them as the driver's artefact, which I agree with.
- **[UNVERIFIED]** that `8da4b83` is the fork point of the branch anyone merges **next**. It is the fork
  point of `softhouse/T82-pass3i-defects` as it stands, verified structurally. A rebase invalidates it — and
  the digest comparison now makes that **loud**, which is the fix working.
- **[UNVERIFIED]** whether any human already acted on T109's refuted §8.2(1) beyond T125's dispatch and
  `79a67d1`'s commit message. I checked `tasks.json` and `main`'s log; a decision taken and not written down
  is not in any file.

---

## Micro-fix list (prose and evidence only — no predicate, no number, no vector)

| # | site | change |
|---|---|---|
| M-1 | `T109.md:31`, `FORK-POINT-SHA:25`, `prove-guards-go-red.sh:79`, `prove-guards-go-red.sh:209` | Retract "a green 25/25 against a baseline that already contains the fix". At T103's `main` tip the bytes were the fork point's. Say what the hole is: nothing checked the bytes. §1.2. |
| M-2 | `FORK-POINT-SHA:46`, `prove-guards-go-red.sh:212` | The `git merge-base main softhouse/T82-pass3i-defects` recovery command returns `55409cfd` and has since `61e7102`. Replace it or state that the digests are authoritative. §1.3. |
| M-3 | `T109.md:§6`, `every-invocation.txt` LEG B header | The zsh row does not discriminate — the rig refuses the correct pin under zsh too. Drop it or annotate it; relabel `SAME FORMS` → `3 OF THE 10 FORMS`. §4. |
| M-4 | `T82.md:124` | The `git show $(cat …FORK-POINT-SHA):…` restatement the F-2 sweep missed. §6/F-4. |
| M-5 | `T109.md:§8` | `356` → **348** (measured five ways at `fb2048d`); `CP_DIGEST` "11 rigs" → **6 files**; add the two blind spots that measured **zero**. §7.1, §7.3. |
| M-6 | `T109.md:§8.2(1)`, and the driver's ledger | The consequence is refuted: the canary is gated at `preconditions.sh:160` via `attest.py:90/98`. Replace with the real finding — the charges copy is missing T80's hardening and the two attestations name the wrong precondition script. §8. |
| M-7 | `T109.md:§8.2(11)` | `admit.go:594` → the skip is `:586`, the comparison `:593`. Note that `structural_test.go:766` enshrines the empty case in a passing test. §9. |

**None of these touches the guard.** The guard is correct, refuses twelve ways with zero stdout bytes before
the header and before row 1, discriminates on nine of ten invocation forms, survives the merge state that
killed T98 with a byte-identical transcript, and its two new pins both go red on a one-byte mutation. Merge
it once M-1 through M-7 land, and re-scope T125 before it does.
