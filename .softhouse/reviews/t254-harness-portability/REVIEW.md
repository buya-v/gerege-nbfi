# T254 — independent review of T253 harness portability (Mac arm)

**Reviewer:** T254, isolated worktree, opus. Did not write either implementation.
**Measured at:** my HEAD `607252a8660101cab01ac0dc68d1ecc61b14c43d` unless a line says otherwise.
**Host:** Darwin 25.5.0 arm64, bash 3.2.57, `/usr/bin/grep` = BSD grep 2.6.0-FreeBSD.
**Reference oracle (Fineract):** REACHABLE, `https://localhost:8443/...` → HTTP 200.
**Vector store digest, read live at open AND at close (P-69):**
`13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` — **UNCHANGED, matches the required value.**

**Candidates:**

| arm | ref | conformance.sh | go-env.sh |
|---|---|---|---|
| CLOUD | `origin/softhouse/T253-harness-portability` @ `d7a7ea3` | **+62 / −10, net +52** | rewritten |
| MAC | `softhouse/T253b-harness-portability-mac` @ `0208477` | **+10 / −10, net 0** | rewritten |

Refs re-measured at close: `origin/main` = `1b8c1f8`, cloud = `d7a7ea3`, mac = `0208477`,
`softhouse/T255-dec2-rev8` = `b334786` (it moved from `ed686d7` mid-review; the citation
count was **re-measured at the new tip** and is unchanged — see F-2).

---

## VERDICTS

| artefact | verdict | why, in one line |
|---|---|---|
| **`conformance.sh` — MAC** | **MERGE** | net-zero, all 10 sites fixed, PASSes on main, rots no citation |
| **`conformance.sh` — CLOUD** | **REJECT (as the merge candidate)** | functionally equivalent, but its +52 shift rots **100%** of DEC-2 rev-8's harness citations on the merge |
| **`go-env.sh` — MAC** | **MICRO-FIX** | correct on the defect that actually fires; must gain the cloud's `GEREGE_GO_STRICT` |
| **`go-env.sh` — CLOUD** | **MICRO-FIX** | has the better config knob, but **re-creates the D2 symptom** it was written to remove |

**Neither arm is a superset. The merge is a graft, and the graft is well-defined.**

---

## THE MERGE RECOMMENDATION — executable

1. **Take `conformance.sh` from MAC** (`softhouse/T253b-harness-portability-mac`). Do **not**
   take the cloud's. This is the decisive call and F-2 is the reason.
2. **Take `go-env.sh` from MAC as the base**, then **graft one block from CLOUD**: the
   `GEREGE_GO_STRICT` arm (cloud `go-env.sh:159-167`). Graft it *after* the Mac's
   stale-`GOROOT` drop (mac `go-env.sh:153-156`), which must be kept — it is the thing the
   cloud gets wrong (F-3).
3. **Also graft from CLOUD**: the richer `GEREGE_GO_SOURCE` *value*. Cloud exports
   `substituted:/abs/path/to/go`; Mac exports the bare token `fallback-path`. The path is
   what a parity claim has to name, so the cloud's value is strictly more useful.
   (Keep the Mac's `pinned` / `absent` tokens or the cloud's `pinned:$PATH` — either is fine,
   but pick one and make all three consistent.)
4. **Take the cloud's `conf_tmpdir` trailing-slash strip only if you also take its helper.**
   You are not taking its helper, so instead apply F-7 as a one-line micro-fix to the Mac's
   ten call sites, or accept F-7 as LOW and leave it. **My recommendation: leave it** — it is
   cosmetic, and changing ten lines to fix a doubled slash re-opens the diff you just chose
   for being minimal.
5. **Keep both branches' evidence directories.** They do not collide
   (`capture/t253-portability/src|transcripts` vs `.../instruments|evidence`) and the two
   independent BSD/GNU proofs are worth more together than either alone.
6. **Do NOT let F-1 block this merge.** It is pre-existing on `main` — **measured**, see F-1.
   File it; do not gate the portability fix on it.

Both branches merge into `origin/main` **cleanly** — `git merge-tree --write-tree` returns a
tree with no conflict report for each:
cloud → `7f25bee96fc3c2bfa40e989d7299da81d9eb64fd`, mac → `64f191e50f2ba06237cadfdc0b19c4011b7b2e90`.

---

## THE TWO BAR RESULTS — probe-line PRESENCE stated before its value (P-83)

Invoked exactly as `bash .softhouse/conformance.sh`. Baseline to beat (driver, `c0e88c6`,
live oracle): PASS, 46 parity / 7884 cells, frontier 11 == pinned 11, 9 exemption-census
pins matched, 6/6 wrong ledger implementations killed.

### Run 1 — MAC candidate `0208477`, in its own worktree
- **PROBE LINE PRESENT? — YES** (1 matching line)
- probe value: `probe = up`
- **BAR_EXIT = 0**, `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.`
- fail-open: **frontier 11, pinned at 11**; `frontier == pinned (all 11 rows, by path)`; census inspected 924 tracked `.sh`/`.py`
- stderr: **0 lines**
- evidence: `evidence/40-BAR-mac-0208477.{stdout,stderr,meta}.txt`, `evidence/42-bar-facts-mac.txt`

### Run 2 — CLOUD candidate `d7a7ea3`, in its own worktree
- **PROBE LINE PRESENT? — YES** (1 matching line)
- probe value: `probe = up`
- **BAR_EXIT = 0**, same `VERDICT: PASS`, same 46 / 7884
- fail-open: **frontier 10, pinned at 10**; census inspected 904 files
- evidence: `evidence/41-BAR-cloud-d7a7ea3.{stdout,stderr,meta}.txt`, `evidence/42-bar-facts-cloud.txt`

**The 10-vs-11 difference is NOT a weakened guard and I will not let it be read as one.**
The cloud branched from `a6bec72`, which predates T248 (the commit that widened the frontier
to 11 and introduced TIER1B). Its 10/10 is self-consistent *at its own base*. What it does
mean is that **the cloud's BAR was measured against a tree that no longer exists on main** —
the same rot class as T266, and the reason I re-ran both on main below.

### Runs 3 and 4 — the honest apples-to-apples: each candidate's MERGED files on main's tree
Varying only `conformance.sh` + `go-env.sh` on an `origin/main` checkout.

| | probe present? | probe | exit | frontier | verdict |
|---|---|---|---|---|---|
| cloud-merged on main | **YES** | `up` | **0** | **11 == 11** | PASS, 46 / 7884 |
| mac-merged on main | **YES** | `up` | **0** | **11 == 11** | PASS, 46 / 7884 |

**Both candidates leave every baseline invariant unchanged on main.** No guard weakened, no
pin moved, 46/7884 identical, frontier 11==11 in both. Evidence:
`evidence/60-BAR-cloudMERGED-on-main.*`, `evidence/61-BAR-macMERGED-on-main.*`.

---

## FINDINGS

### F-1 — HIGH — the `t234` residue: the CLOUD is right, the MAC is wrong, and the defect is PRE-EXISTING

The disagreement the driver asked me to settle by running it. I ran it
(`instruments/70-t234-residue-adjudicate.sh`, backs up and restores `/tmp` state).

Same tree, twice, changing only whether `/tmp/t234_matrix2.txt` exists:

| | residue PRESENT | residue ABSENT |
|---|---|---|
| BAR_EXIT | **0** | **2** |
| **PROBE LINE PRESENT?** | **YES** (`probe = up`) | **NO — NOT PRINTED** |
| frontier count | 11, pinned at 11 | **11, pinned at 11** |
| `frontier == pinned` line | present | **ABSENT** |
| result | PASS | **HARD guard failed** |

The harness's own diff, from stderr:

```
THE FAIL-OPEN FRONTIER IS NOT THE PINNED FRONTIER (- pinned, + measured):
+TIER1 .softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh
-TIER2 .softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh
```

**The Mac author's decisive claim is FALSE.** It argued the count and path-set are identical
in both arms and the harness "pins by path", so this "fails no BAR" — a classification
defect, not a frontier defect. The count *is* identical (11==11) and the path set *is*
identical. **The BAR still fails, exit 2, with no probe line.** The pinned rows carry the
**TIER token**, and the comparison is over the whole row, so a TIER2→TIER1 flip fails it.
I believe the Mac was misled by the harness's own sentence *"All are pinned by PATH, not by
count"* — that sentence rules out a bare count, it does not say the tier is ignored.

**The cloud's account is correct and its refusal is vindicated.** It reported the tier
depends on leftover `/tmp` state and **refused to move the pin or weaken the guard to make
its own bar green.** That refusal was the right call and survives review.

**But the blame does not land on either candidate.** I ran **unmodified `main`**, both files
pristine, residue absent: **BAR_EXIT = 2, probe line NOT printed**
(`evidence/72-BAR-MAIN-UNMODIFIED-residue-ABSENT.*`). It is fix-independent — the cloud's
merged files reproduce it too (`evidence/71-BAR-cloudMERGED-residue-ABSENT.*`, exit 2, probe
absent).

> **This Mac's BAR passes only because `/tmp/t234_matrix2.txt` happens to exist on it.**
> The next reboot, `/tmp` sweep, or fresh host turns main's own BAR red. That is a live,
> pre-existing, latent HARD-guard failure on `main` and it should be filed as its own task.
> **It must not gate T253** — gating a portability fix on a defect it did not cause would
> leave the harness broken on Linux for no gain.

*Methodology note, and it caught me:* a naive `grep -c probe` on the failing run returns
**1** — an unrelated `"tie probes"` line. The probe-line selector `probe[[:space:]]*=`
returns **0, rc=1**. Reporting presence from the loose selector would have inverted this
finding. This is exactly the P-83 trap.

### F-2 — HIGH — the cloud diff rots **100%** of DEC-2 revision 8's harness citations, on the merge

The count the driver asked for. Measured with `instruments/20-…` and cross-checked with a
deliberately wider selector (`instruments/21-…`) because my first selector was too narrow.

At `softhouse/T255-dec2-rev8` (re-measured at the final tip `b334786`):

| term | value |
|---|---|
| `conformance.sh` line-citations in DEC-2 rev 8 | **10** (9 forward-form + 1 prose-form at DEC-2:428) |
| distinct cited line **ranges** | **5** (`718`, `1115-1116`, `1152-1187`, `1189-1213`, `1254`) |
| **live** harness line numbers carried | **17** |
| **numbers that rot under the cloud diff** | **17 — 100%** |
| un-numbered prose mentions (P-40, nothing to rot) | 51 |

Every cited line is ≥ **718**; the cloud inserts **+52 lines at line 570**, so *every one*
shifts. Worked examples: `718 → 770`, `1115-1116 → 1167-1168`, `1152-1187 → 1204-1239`,
`1189-1213 → 1241-1265`, `1254 → 1306`.

I confirmed the citations are **live and correct against `main` today** before calling the
shift damage — a stale number cannot be "rotted" by a merge
(`evidence/22-verify-rev8-citations.txt`). They resolve exactly:
`conformance.sh:718` → `# guard_no_float_in_harness: no floating-point identifier ANYWHERE in the Go`;
`:1115` → `# P-57: every stage here consumes all of its input …`.

**Confirmed on the MERGE RESULT, not merely on the branch** — I read the merged blobs out of
`git merge-tree`'s written trees:

| conformance.sh | lines | `mktemp` | `mktemp -t` |
|---|---|---|---|
| main | 2617 | 10 | 10 |
| **merged-cloud** | **2669** (+52) | 23 | 2 (**both in comments**) |
| **merged-mac** | **2617** (+0) | 10 | **0** |

**The Mac's net-zero property survives the merge; the cloud's +52 shift also survives it.**
T255 and T253 are landing in the same fire. Merging the cloud diff would rot revision 8's
citations *at the moment of merge* — re-enacting G-14 inside the fix for G-14, which is
precisely what got revision 7 rejected. That is the whole recommendation in one sentence.

### F-3 — HIGH — the cloud's `go-env.sh` re-creates the D2 symptom: it announces a fallback to a `go` that cannot run

The Mac author's claim about its peer. **I reproduced it; it is TRUE**
(`instruments/30-goroot-stale-repro.sh`). Both scripts staged outside any git repo with no
toolchain, a real `go` on PATH, and a bogus `GOROOT=/nonexistent/t254/goroot` exported first:

| | GOROOT after source | `go version` rc | output |
|---|---|---|---|
| **cloud** | `/nonexistent/t254/goroot` (**survives**) | **2** | `go: cannot find GOROOT directory: …` |
| **mac** | **`<unset>`** (dropped, and says so) | **0** | `go version go1.26.6 darwin/arm64` |

It is worse than the Mac stated. The cloud's banner interpolates `$("$_ge_path_go" version 2>&1)`,
so **the error is printed inside its own "SUBSTITUTING" banner** —

```
gerege go-env: SUBSTITUTING the go already on PATH:   /…/toolchain/go/bin/go
gerege go-env:   go: cannot find GOROOT directory: /nonexistent/t254/goroot
```

— and it then asserts `this go uses its own built-in GOROOT`, which is **false in that
state**, and carries on. Its header says the defect it replaces was turning "toolchain not
installed" into "a HARD money guard did not compile"; on this path it does exactly that
again. Mac `go-env.sh:153-156` is the fix and must be kept:

```sh
if [ -n "${GOROOT:-}" ] && [ ! -d "${GOROOT:-}" ]; then
    printf '%s\n' "go-env.sh: dropping inherited GOROOT=$GOROOT — that directory does not exist." >&2
    unset GOROOT
fi
```

The condition is precisely right: it drops only a **nonexistent** `GOROOT`, so a legitimate
one (e.g. `golang:1.x` images set `GOROOT=/usr/local/go`) is left alone.

**This is not a misrepresentation by the Mac author.** The peer criticism is accurate and
understated.

### F-4 — MED — the `mktemp -t` population is **34**, not 10. Both authors fixed the right 10 and neither stated the denominator

P-67, two terms, enumerated myself at `607252a` with `/usr/bin/grep` over
`git ls-files` (`instruments/10-mktemp-census.sh`):

| term | value |
|---|---|
| tracked files in repo | **5216** |
| tracked files mentioning `mktemp` | **97** |
| lines mentioning `mktemp` (**wide** selector S1) | **155** |
| **`mktemp -t` call sites (narrow selector S2)** | **34, across 19 files** |

Selector check, per the P-76 addendum — "every `mktemp` call" is **not** the same set as
"every `mktemp -t` call", and `conformance.sh` is **not** the whole population:

- `.softhouse/conformance.sh` — **10** ← the only BAR-executed ones; both authors fixed all 10
- `t248-failopen-widen/instruments/30-additivity.sh` — 5
- `t252-tier3/instruments/10-verify-third-site.sh` — 2
- 14 further capture instruments — 1 each
- `tasks.json` ×2 and a handoff `.md` ×1 — **prose, not code**

So: **10 BAR-executed, 21 in non-BAR executable instruments, 3 prose.**

**Why "ten" is nevertheless the correct scope, and I checked rather than assumed:** the
harness *lints* the pinned instruments statically (`50-failopen-lint.py`) — it does not
execute them. The only scripts it *runs* are `.softhouse/capture/lib/*`, and I measured that
directory: **no `mktemp` at all** (grep exit 1, a real measured negative). So the BAR path is
exactly the 10.

The residual 21 are still latent-on-Linux: anyone re-running an archival instrument on a GNU
host to re-verify a past claim gets `too few X's in template` — the same failure that took
the BAR down. **Worth filing; not a blocker for this merge.**

### F-5 — MED — the cloud's own committed instruments are the weaker of the two

`instruments/80-instrument-audit.sh`, over each branch's added `.sh`/`.py`, blobs read from
each branch:

| | cloud `d7a7ea3` | mac `0208477` |
|---|---|---|
| `.sh`/`.py` touched | 5 (4 sh, 1 py) | 8 (6 sh, 2 py) |
| bare `grep` (ugrep-wrapper hazard) | **0** | **0** |
| `rg` | **0** | **0** |
| `git grep -E` with `\b` | **0** | **0** |
| `.sh` missing `set -euo pipefail` | **3** | **1** |
| `\|\| true` / `\|\| echo` rc-conflation | **5** | **2** |

**Both clear the three hard P-75 bars.** The difference is in rigour: the cloud's
`10-mktemp-red.sh`, `20-goenv-red.sh` and `30-proposed-linter-fix.py` carry the
`set -euo pipefail` and rc-conflation gaps; the Mac's own instruments carry none — its single
`no-set-euo` hit is `conformance.sh` itself and its two rc-conflation hits are
`conformance.sh` and `go-env.sh`, both **pre-existing and deliberate** (`go-env.sh` is sourced,
so it must not mutate the caller's shell options, and both files document this).

I did **not** hand-adjudicate whether each of the cloud's 5 `|| true` sites is a legitimate
expected-failure capture (P-40: **5 sites skipped**). Some plausibly are. The count is a
flag, not a conviction.

### F-6 — MED — `GEREGE_GO_STRICT` is the cloud's genuine win, it is safe, and it should be grafted

Only the cloud has it. The Mac author concedes the point and I agree: it keeps the rejected
hard-refusal arm **reachable as configuration rather than as a patch**, which is the right
shape for a decision recorded as "rejected as the default, not removed".

**And it is safe to graft, which I verified rather than assumed.** The cloud's strict arm ends
`return 2 2>/dev/null || exit 2`. A non-zero return from a sourced file would abort a caller
running under `set -e`. **Neither consumer uses `set -e`** — `conformance.sh:396` and
`check-ledger-invariants.sh:39` both read exactly `set -u -o pipefail`. So the strict return
cannot abort the harness, and both consumers reach their own compiler-absent refusal.

### F-7 — LOW — the Mac's inline `${TMPDIR:-/tmp}` does not strip a trailing slash

macOS always sets `TMPDIR` **with** a trailing slash, so every Mac scratch path becomes
`/var/folders/…/T//conformance-….XXXXXXXXXX`. Harmless — POSIX collapses interior duplicate
slashes, and the Mac's own matrix evidence records the doubled slash and confirms a real file
results. The cloud's `conf_tmpdir()` strips it and is tidier.

One genuine (if remote) edge: with `TMPDIR=/`, the Mac form yields a **leading** `//…`, and a
path beginning with exactly two slashes is **implementation-defined** in POSIX. The cloud
handles this explicitly (`[ -n "$d" ] || d=/`). Not worth a diff; recorded so it is not
rediscovered.

### F-8 — LOW — the Mac's sub-decision is right, but one premise it rests on is factually wrong

Mac `go-env.sh:55-63` justifies "this file always returns 0" partly because "a caller running
under `set -e` would abort at the `. go-env.sh` line". As measured in F-6, **neither actual
consumer sets `-e`**. The reasoning is defensible as defence-in-depth for future callers, but
it is stated as a fact about the current ones and it is not one. **The conclusion is harmless
and I am not asking for a change** — returning 0 from a sourced env file is fine. Recorded
because the premise is cited as decisive.

The Mac's *other*, genuinely decisive premise — that a hard refusal "would not prevent the
substitution, only the announcement of it" — **is TRUE and I verified it by reading both
consumers**, which the brief asked me to do rather than take on trust:
`conformance.sh:601-605` sources the file then runs its own `command -v go`;
`check-ledger-invariants.sh:55-60` does the same. With nothing exported, both would find and
use the PATH `go` anyway, unannounced. **Refusing there buys silence, not safety.** Both
authors reached the right decision on a sound premise.

*Silent success:* I found no path in either file that produces a silent substitution. Every
non-pinned arm prints to stderr before returning. But see **T267** — all of it is on stderr
and none on stdout, so the *verdict block* still never names the Go that compiled the money
guard. Neither candidate fixes that; it is correctly filed as its own task.

### F-9 — MED — T266 applies equally to both and changes neither's ranking

Confirmed at my own commit: `50-failopen-lint.py` on `main` is **722 lines**, with tier
decided by `os.path.exists` at **:366** and **:447**, unfixed. **Neither candidate touches
the linter** — it appears in neither diff. So the cloud's "5/5" is indeed a result about a
476-line file that no longer exists, but the Mac has no competing claim about the linter at
all. **T266 is orthogonal to the merge choice.** It is, however, the *upstream cause* of F-1:
`os.path.exists` on a `/tmp` path is exactly how leftover state decides a tier.

### F-10 — CREDIT — the cloud refused to go green, and it was right

The cloud found the tier flip, declined to move the pin or weaken the guard, and shipped
without a green bar. **My run confirms the refusal was correct** (F-1): moving that pin would
have pinned a TIER1 fail-open as though it were TIER2, on the strength of a `/tmp` file. This
is the behaviour the program wants and it should be said plainly, in a review that otherwise
recommends against merging its `conformance.sh`.

### F-11 — CREDIT — the GNU arm was executed, not asserted

The brief asked me to verify this rather than accept it. The Mac's
`evidence/10-mktemp-matrix.txt` records `image: postgres:16 -> mktemp (GNU coreutils) 9.7`
with per-case rc values and GNU's **own** error text including its typographic quotes —
`mktemp: too few X's in template ‘conformance-failopen’`. That is an execution transcript,
not a reasoned prediction. The BSD arm was executed natively here. Both arms are evidence.
(The cloud review's compiled-Apple-`mktemp.c` proof, 12 OK / 0 FAIL, closes the BSD side
independently and by a better route; I treated it as settled per the driver and did not redo it.)

### F-12 — the Mac's self-criticism is real

Verified: the handoff records at `:113` that two of its own instruments were wrong first, and
at `:194` that its toolchain census asserted "go-env.sh is NO LONGER among them" while its
own selector contradicted it — **left visible and corrected in place rather than edited out.**
That is what it claimed to have done and it is what it did.

---

## WHAT I COULD NOT VERIFY

1. **A repaired Linux BAR.** Unchanged from the Mac author's own admission, and honestly
   stated by it. The oracle is bound to this host; I cannot observe a green Linux run. What I
   *can* say is stronger than before: on this Mac, **with the residue cleared, the BAR fails
   identically for main, for the cloud and for the Mac arm** (F-1) — so the first thing a
   repaired Linux host will hit is F-1, not D1.
2. **Nine of the ten `mktemp` sites remain latent-by-mechanism.** The first site kills the
   run, so sites 2-10 were never individually observed to fire on GNU. Both authors state
   this. The GNU matrix in F-11 exercises the *form* on both arms, which is the property that
   matters; the per-site claim is by mechanism, correctly labelled as such. I did not
   construct a per-site GNU drive (**P-40: 9 sites not individually driven**).
3. **Whether each of the cloud's 5 rc-conflation sites is a legitimate expected-failure
   capture** (F-5). **5 sites skipped.**
4. **The 21 non-BAR `mktemp -t` sites** were enumerated but **not executed** on GNU (F-4).
   Their breakage is by mechanism, identical to the 10.
5. **`GEREGE_GO_STRICT` grafted onto the Mac's `go-env.sh`** — I judged it safe from the
   consumers' `set -u -o pipefail` (F-6) but **did not build and run the grafted file**,
   because I may not edit either artefact. The graft should be re-BARed after it lands.

---

## Instruments and evidence

All under `.softhouse/reviews/t254-harness-portability/`. P-75/P-80 throughout: `grep` on
this host is a **ugrep 7.5.0 shell-function wrapper** with `--ignore-files` and six
`--exclude-dir` silently prepended, so every measurement here calls **`/usr/bin/grep` by
absolute path**; no `rg` (also a wrapper, no binary); no `git grep -E` with `\b`; grep exit
**1 = a real measured negative**, exit **>1 aborts** and never prints an absence.

| instrument | produces |
|---|---|
| `10-mktemp-census.sh` | F-4 population, both terms, S1-vs-S2 selector split |
| `20-dec2-citation-damage.py` | F-2 citation counts |
| `21-dec2-selector-widen.py` | self-check that caught my own too-narrow selector (found DEC-2:428) |
| `22-verify-rev8-citations.py` | proves the citations are live before calling the shift damage |
| `30-goroot-stale-repro.sh` | F-3 reproduction, both arms |
| `40-run-bar.sh` | BAR runner, exit code captured not swallowed |
| `42-bar-extract.py` | probe **presence before value**, baseline invariants |
| `50-merged-residual.sh` | residual `mktemp` on the **merge results** |
| `70-t234-residue-adjudicate.sh` | F-1 adjudication; backs up and **restores** `/tmp` state |
| `80-instrument-audit.sh` | F-5 P-75/P-80 audit of both branches |

**Host state restored:** `/tmp/t234_matrix2.txt` was parked and **put back**; verified present
at close. The scratch worktrees `t254-bar-mac`, `t254-bar-cloud`, `t254-merge` are detached
and disposable — `git worktree remove` them. I edited no file either implementation touched.

---

## MY OWN INSTRUMENTS, CHECKED AGAINST THE RULE I APPLIED TO OTHERS (P-80)

The fail-open linter's corpus is `git ls-files`, so my ten instruments enter it the moment
they are tracked — the trap that caught three workers last fire, one of them inside the
fail-open detector itself. So I ran the BAR **on my own committed review branch**
(`softhouse/T254-review-portability-mac` @ the commit carrying this review):

- **PROBE LINE PRESENT? — YES**; value `probe = up`
- **BAR_EXIT = 0**, `VERDICT: PASS`, 46 parity / 7884 cells
- census inspected **928** tracked `.sh`/`.py` — up from 918 on main, i.e. my 10 instruments
  are in the corpus and were linted
- **frontier 11, pinned at 11**; `frontier == pinned (all 11 rows, by path)`
- **none of my files is on the frontier**

Evidence: `evidence/90-BAR-SELFCHECK-my-own-branch.*`.

My instruments use `mktemp "${TMPDIR:-/tmp}/….XXXXXXXXXX"` — the portable form this review
recommends, not the `mktemp -t` form it condemns. `set -euo pipefail` in every standalone
`.sh`; `set -e` is lifted only around the BAR invocation itself, where a non-zero exit **is
the measurement**, and restored immediately.

**Three defects in my own work, recorded rather than edited out** (P-76 addendum — the
mis-selector is the interesting part):

1. `70-t234-residue-adjudicate.sh` first died with `label: unbound variable`, because
   **bash 3.2 on this host does not make an earlier name on the same `local` statement
   visible to a later one**. Fixed by splitting the declarations; the note is left in the file.
2. The same instrument then aborted at ARM 2 because `set -e` killed it on the BAR's non-zero
   exit — **which was itself the finding**. Fixed by lifting `set -e` around that one call.
   Had I not noticed, F-1 would have been reported as "could not run".
3. My first citation selector (`instrument 20`) matched only the *forward* form
   `conformance.sh:NNNN` and **missed DEC-2:428**, a prose-form citation carrying a live line
   number. `instrument 21` was written specifically to widen the selector and catch my own
   miss. This is why F-2 reports **10** citations and **17** numbers rather than 9 and 16.
