# A2-10 — independent review of A2-5 (capture-rig fixes for D-2 and D-3)

**Target:** branch `softhouse/A2-5-capture-rig-fixes`, commit `9aceec1`, diffed `main...` (merge-base `187e972`).
**Reviewer:** A2-10, branch `softhouse/A2-10-review-a2-5`. I did not plan this work.

## Verdict: **MICRO-FIX** — 3 lines in `manifest.py`, mechanical, plus a `manifest.py write` re-run.

One real defect, and it is the characteristic one: **the fix for D-3 opened a new laundering path in the very
guard it was fixing** (A2-10-D1, below). It is a three-line deletion/flag-flip to close, no design decision
involved, so it does not clear the REJECTED bar. Everything else in the task I attacked and could not break,
and **both of A2-5's contested judgment calls are correct** — one of them emphatically so.

Every claim below is marked. `[VERIFIED: …]` means I ran it in this worktree and read the output. The full
transcript is committed at `.softhouse/reviews/A2-10-probe/TRANSCRIPT.txt` (484 lines) and every number in
this review regenerates from the scripts beside it.

---

## Method — my own poison first

I wrote all nine attack scripts **before opening A2-5's `prove-*.py` or its `RED-GREEN-*.txt`**, and drove
every guard red myself against the real pre-fix bytes from `main`'s immutable blobs:

- `cap.sh` blob `55d5d63af96820ada43544913b2a344478f0393d`, sha256 `5820f363…62a`
- `manifest.py` blob `cbc888d4698cb8211a8ceec31494314dc64d1a67`, sha256 `65e54af9…8a8`

Both blob ids and both sha256s are the ones A2-5 pinned in its provers, and I computed them independently
rather than copying them [VERIFIED: `git rev-parse main:…`, `shasum -a 256`].

---

## (a) D-2 — can a stale body and a stale status survive under a fresh `captured-at-utc`? **No.**

I attacked this hardest, as instructed. Four separate assaults.

### 1. Interpreter/option matrix — 72 cases, wider than A2-5's 32

5 shells (`/bin/sh`, `bash`, `dash`, `zsh`, `ksh`) × 7 option sets (none, `-e`, `-u`, `-eu`,
`-e -o pipefail`, `-eu -o pipefail`, **`-E -e`** — the ERR-trap-enabling combination A2-5 did not test) ×
2 branches (body / no-body), plus shebang execution. Endpoint `127.0.0.1:1` (closed). Sandbox seeded with an
earlier fire's `.json` + `.status` + a `.http` reading `captured-at-utc: 2000-01-01T00:00:00Z`. A case counts
as LAUNDERED if the run exits 0, **or** the timestamp moves, **or** the body or status is mutated.

| | pre-fix (`main`) | post-fix (A2-5) |
|---|---|---|
| CAUGHT | 11 | **68** |
| **LAUNDERED** | **57** | **0** |
| skipped (dash refuses `-o pipefail`) | 4 | 4 |

[VERIFIED: TRANSCRIPT §1, §2.] Every pre-fix laundering was the exact D-2 artefact: `exit=7`, the earlier
fire's body byte-identical on disk, and `out/POISON.http` re-dated to today.

One honest addition to A2-5's own scoping note: it recorded that pre-fix `-u` on the **no-body** branch dies
early at `BODY=$4` and refused to round "12 of 16" up to "all shells". Correct for its matrix — and
`/bin/ksh -u` (not in its matrix) **does** launder on that branch, so its conservatism was warranted rather
than excessive [VERIFIED: TRANSCRIPT §1, `/bin/ksh -u nobody exit=7 FRESH-TIMESTAMP`].

### 2. Transport failures that are not "connection refused"

`set -e` is not the only way a handler goes unreachable, and connection-refused is not the only way curl fails.

- **Partial transfer.** A local server that sends `Content-Length: 4096`, writes 42 bytes and closes →
  curl exits 18 **after having written bytes to the output file**. Pre-fix: `out/POISON.json` **overwritten
  with the truncated response** *and* re-dated — that is worse than the stale-under-fresh case A2-4 found,
  because it destroys the earlier observation as well as mis-dating it. Post-fix: exit 1, body, status and
  timestamp all byte-identical [VERIFIED: TRANSCRIPT §3].
- **`curl` absent** (`PATH=/nonexistent`, command substitution returns 127). Both versions caught it; noted
  for completeness [VERIFIED: TRANSCRIPT §3].

### 3. Clean slate — does a failed fire write anything at all?

Pre-fix, with an empty `out/`: after the failure `out/` contains **`N.http` with today's `captured-at-utc`** —
a dated record of an exchange that never happened. Post-fix: `out/` is **empty**, exit 1
[VERIFIED: TRANSCRIPT §4 step 1].

### 4. The success path is not regressed

A fix that breaks capture is as bad as the defect, so I ran both versions against a real local HTTP server:

- 200 + JSON body: identical body, identical status, `.http` record **byte-identical modulo the timestamp**;
- **400 refusal: still exit 0 and still recorded** — in slice A2 a refusal *is* the observation, and the fix
  does not turn one into an error;
- 204 empty body (0 bytes) and a 100 KB body: identical lengths on both versions

[VERIFIED: TRANSCRIPT §4]. The one `<-- BAD` line in §4 step 4 is **my** off-by-one in the expected length
(`{"pad":"` + 100000 + `"}` = 100010, not 100011); both versions produced 100010, i.e. identical.

The strongest non-regression evidence is §12 below: **27 real exchanges against the live reference oracle
through the fixed `cap.sh`, 0 transport errors, 24 bodies byte-identical to the committed capture.**

### 5. The callers

All **15** `cap.sh` call sites in the five `run-*.sh` carry `|| exit 1`, and all 15 are the plain
statement-level form, where `exit 1` leaves the batch [VERIFIED: `grep -rn 'cap\.sh' run-*.sh`, 15 lines, 15
guards]. I confirmed the follow-on `printf '%s' "$(cat out/…json)"` in `run-020` / `run-060` is a separate
statement that cannot be reached after the guard fires.

**Residual, not a defect today:** `|| exit 1` is defeated if a future caller wraps the call in a **pipeline**
or a **subshell** — I drove both and the stale body reached stdout with exit 0 on the fixed `cap.sh` as well
[VERIFIED: TRANSCRIPT §3 section C]. No current call site has that shape. Worth a line in the rig's comment
block so the next author does not introduce one.

**(a) conclusion: the fix holds under every attack I could construct. No path leaves a fresh-timestamped
artefact under `out/`, because nothing under `out/` is written until `curl` has returned 0.**

---

## (b) D-3(i) — zero files inspected is now an ERROR

| attack | pre-fix | post-fix |
|---|---|---|
| empty `MANIFEST.sha256` | RED (by luck: the 5 real files become `UNTRACKED`) | RED, `INSPECTED NOTHING` |
| **empty manifest over an empty capture dir** | **`OK: 0 files match`, exit 0** | **exit 1** |
| manifest stripped to a single line | RED | RED |
| manifest written by the OLD tool, verified by the new | n/a | RED, `REFUSING … does not cover` |

[VERIFIED: TRANSCRIPT §7, §8.] The vacuous pass is closed, and the `REQUIRED` floor closes the narrower
version of it. Reproduced on the **real evidence**, not only in a sandbox: A2-5's tool against `main`'s tree
refuses with `REFUSING: MANIFEST.sha256 does not cover CAPTURE-PLAN.md, DEFECTS-FOUND-BY-REVIEW.md,
FLAGGED-NOT-REPRODUCIBLE.txt, cap.sh, env.sh, manifest.py` [VERIFIED: TRANSCRIPT §14].

---

## (c) D-3(ii) — a fabricated observation in `out/<subdir>/`

I dropped three of them. `out/sub/A2-999-FABRICATED.json`, `out/a/b/c/A2-998.json` (three levels deep), and a
top-level control. Pre-fix: the first two are **laundered green**. Post-fix: all three `UNTRACKED`, exit 1
[VERIFIED: TRANSCRIPT §7, §8].

**But see A2-10-D1 — the same attack delivered as a symlink is not caught, and it was caught before this fix.**

---

## (d) D-3(iii) — the plan, the rig, and `manifest.py` itself

Seven separate poisonings, each pre-fix green and post-fix red [VERIFIED: TRANSCRIPT §7, §8]:

| poison | pre-fix | post-fix |
|---|---|---|
| `"MNT rounds HALF_EVEN and money may be stored as a float."` appended to `CAPTURE-PLAN.md` | green | **RED** `CHANGED CAPTURE-PLAN.md` |
| `DEFECTS-FOUND-BY-REVIEW.md` rewritten to "All defects resolved." | green | **RED** |
| `cap.sh` repointed at `https://evil.example/api/v1` | green | **RED** |
| `env.sh` switched to the **wrong tenant** (`default`) | green | **RED** |
| `run-020-accounts.sh` recipe altered | green | **RED** |
| `manifest.py` appends to **itself** | green | **RED** `CHANGED manifest.py` |
| `FLAGGED-NOT-REPRODUCIBLE.txt` deleted | green | **RED** |

Plus, driven red on the fixed tool: flagged evidence deleted, flagged evidence uncovered, a malformed manifest
line, a duplicate manifest line carrying a false hash, and — my own — the flag file **gutted to zero flagged
paths** (caught, because the flag file is itself hashed). The **control on an untampered sandbox is GREEN**,
so none of these REDs is the artefact of a tool that always fails [VERIFIED: TRANSCRIPT §8].

**Stated blind spot, not a defect:** a `manifest.py` that rewrites its own `verify()` to `sys.exit(0)` passes.
No self-hashing tool can catch its own subversion; git is the defence. A2-5's docstring says "this script
included", which is true of the *hash*, and I would add one sentence saying the tool cannot vouch for a
mutated copy of itself [VERIFIED: TRANSCRIPT §8, `(d) manifest.py NEUTERS its own verify()` → green].

---

## DEFECT — A2-10-D1: the fix opened a symlink laundering path that `main` had closed (P-22 class)

`manifest.py::entries()` gained `and not os.path.islink(p)` in **both** of its loops (branch lines 88 and 94).
Consequence:

> A fabricated observation dropped into `out/` **as a symlink**, whose target lies outside the capture
> directory, is invisible to `verify`. The run exits **0**. A consumer that opens
> `out/A2-996-FABRICATED.json` reads the fabricated bytes.

| attack (payload outside the capture dir) | pre-fix (`main`) | **post-fix (A2-5)** | proposed micro-fix |
|---|---|---|---|
| fabricated **file** symlinked into `out/` | **RED** (exit 1, `UNTRACKED`) | **green — LAUNDERED** | RED |
| fabricated **directory** symlinked as `out/sub` | green — laundered | green — laundered | RED |
| tracked observation replaced by a symlink to a fake | RED | RED | RED |
| fabricated file **hardlinked** into `out/` (control) | RED | RED | RED |

[VERIFIED: TRANSCRIPT §10.] Pre-fix `os.path.isfile(p)` **follows** symlinks, so the symlinked file was
hashed, found absent from the manifest, and reported `UNTRACKED`. A2-5's added `not os.path.islink(p)` skips
it entirely, so it is neither hashed nor untracked — it simply does not exist as far as the guard is
concerned. **This is requirement (c)'s exact attack wearing a symlink, and this task introduced it.**

The directory-symlink row is **not** a regression — `os.walk(..., followlinks=False)` never descended, pre-fix
or post — but it is the same laundering effect and should be closed in the same edit.

### The micro-fix (3 lines, mechanical, no design decision)

In `.softhouse/capture/tierA-a2/manifest.py`:

```
line 84:  for root, dirnames, filenames in os.walk(base):
      ->  for root, dirnames, filenames in os.walk(base, followlinks=True):
line 88:  if os.path.isfile(p) and not os.path.islink(p):
      ->  if os.path.isfile(p):
line 94:  if os.path.isfile(p) and not os.path.islink(p):
      ->  if os.path.isfile(p):
```

Validated, not reasoned: with this applied, **both** symlink rows go RED, and my full 25-attack suite still
behaves as expected on 23 of 25 — the two exceptions being the self-neutering case (inherent) and a fabricated
file in a **new top-level directory** (`out2/`), which is outside the manifest's declared scope
[VERIFIED: TRANSCRIPT §9, §10].

**Two consequences whoever applies it must not skip:**

1. `manifest.py` covers itself, so the edit turns `verify` RED (`CHANGED manifest.py`) until
   `python3 manifest.py write` is re-run and `MANIFEST.sha256` re-committed. I confirmed this on the real
   tree [VERIFIED: micro-fix candidate on the real tree → exit 1, `CHANGED manifest.py`].
2. It makes the second zero-input refusal genuinely unreachable — see adjudication 2.

---

## THREE SELF-REPORTED DEVIATIONS, ADJUDICATED INDEPENDENTLY

### 1. Refusing to restore `rm -f "$OUT"` — **A2-5 is right, and more right than it argued. Do not ding it.**

I did not take A2-5's word. I **built the brief's prescription** and ran it against the same seeded sandbox.

**Variant A — the naive form** (add `|| rc=$?`, keep the pre-fix trailing `rc=$?`, keep `rm -f`):

```
POISON                                       HTTP 000
  exit=0
  out/POISON.http captured-at-utc: 2026-08-21T07:03:05Z      <- FRESH
  out/POISON.json: {"stale":"BODY FROM AN EARLIER FIRE …"}   <- STALE, presented as new
  out/POISON.status: 000                                     <- FABRICATED status code
```

The trailing `rc=$?` reads the exit status of the **`if` compound**, which the `|| rc=$?` list made **0**. The
handler is still unreachable, the script exits **0** so every caller's `|| exit 1` is silent, and it now
writes a **fabricated `000` status** over the earlier fire's. That is a *worse* P-22 defect than the one being
fixed [VERIFIED: TRANSCRIPT §5].

**Variant B — the correct form** (reachable handler done properly, `rm -f` retained):

```
TRANSPORT FAILURE (curl rc=7) for POISON — NO OBSERVATION WAS MADE.
  exit=1
  out/POISON.http captured-at-utc: 2026-08-21T07:03:40Z   <- STILL FRESH
  out/POISON.status: 200                                  <- STILL THE EARLIER FIRE'S
  out/POISON.json: DELETED by rm -f
```

So with `rm -f` restored exactly as the brief named it: **the stale-under-fresh artefact still lands** (a
today-dated `.http` beside an untouched `200` from an earlier fire), *and* a manifest-covered observation is
destroyed, breaking `MANIFEST.sha256` on every failed retry [VERIFIED: TRANSCRIPT §6].

A2-5's diagnosis is exactly correct: the root cause was the **ordering** — `out/NAME.http` stamped before the
request — and `rm -f` was treating one third of a symptom. **A worker that refused a prescribed fix for a
better reason and proved the reason. This is the good outcome, and it should be recorded as one.**

### 2. The guard "that could not be driven red" — **label is safe; the guard is FUNCTIONAL, and I drove it red**

A2-5 shipped `REFUSING: found 0 files under out/, req/, sql/ or this directory — INSPECTED NOTHING` labelled
belt-and-braces, saying it is unreachable because `manifest.py` now covers itself. It **never counted it as
coverage**, which is the thing P-22 actually forbids, and the prover and transcript both carry the disclaimer
verbatim [VERIFIED: TRANSCRIPT of `prove-manifest-blind-red.py`, "NOT DRIVEN RED, stated rather than claimed"].

The premise is nonetheless **over-conservative**: because `entries()` skips symlinks, invoking `manifest.py`
**through a symlink**, in a directory holding nothing but that link and a non-empty manifest, empties the
scanned set. One command:

```
dir contents: ['MANIFEST.sha256', 'manifest.py']   (manifest.py is a symlink)
exit: 1
REFUSING: found 0 files under out/, req/, sql/ or this directory — INSPECTED NOTHING.
```

[VERIFIED: TRANSCRIPT §11.] **The guard fires, prints the right refusal and exits 1 — it is inert-in-practice,
not broken.** Upgrade its `[UNVERIFIED]` to VERIFIED-REACHABLE.

Note the interaction with the micro-fix: once `not os.path.islink(p)` is removed, a symlinked `manifest.py`
*is* counted and the guard becomes genuinely unreachable. Keep it (it is 3 lines and costs nothing) and change
the label to "unreachable by construction", which will then be true.

### 3. `run-120-delete-update.sh`'s "22 lines" — **not scope creep; the premise is a `--stat` artefact**

`git diff --stat` reports `22 +-` because **11 modified lines** count as 11 deletions plus 11 insertions. The
hunk is 11 call sites, each receiving the identical `|| exit 1` and nothing else — no path, no method, no
body-file, no ordering changed [VERIFIED: full hunk read, `git diff main...` on that file].

`run-120` has 11 straight-line call sites; the other four scripts have one call site each, inside a `for`
loop. 11 + 4 = the 15 guards. **The one-line change was applied uniformly. There is no extra change to
justify.**

---

## (e) EVIDENCE INTEGRITY — clean

- `git diff main...` restricted to `out/`, `req/`, `sql/`: **empty** [VERIFIED: exit 0, no output].
- `out/`: **327 files on main, 327 on the branch.** `req/`: **76 / 76** [VERIFIED: `git ls-tree -r`].
- `attempt1-*`: **30 on main, 30 on the branch.** None deleted [VERIFIED].
- `MANIFEST.sha256`: 406 → 430 lines. `diff` of main's manifest against `head -406` of the branch's is
  **empty, exit 0** — the pre-existing lines are byte-identical **and in the same order**; all 24 additions
  are top-level rig/doc files [VERIFIED]. The `cap.sh` line carries `67640ea3…`, which is the sha256 I
  computed from the branch blob myself.
- Real-tree `verify` with the shipped tool: **exit 0**, `OK: 430 files match … (406 under out/ req/ sql/, 24
  rig + docs, this script included)`, `FLAGGED, covered, NOT citable: 30 attempt1-* files`
  [VERIFIED: TRANSCRIPT §13].
- Files touched outside `.softhouse/capture/tierA-a2/`: **one**, its own handoff [VERIFIED].
- Non-negotiables sweep of added lines: no `ojdbc`/`oracle.jdbc`/`1521`/MySQL/MariaDB, no US rails/vendors, no
  `first_name`/`last_name`, no "insured/guaranteed". Every `float` / `HALF_EVEN` hit is the **poison string**
  used as a test payload, correctly quoted inside a prover [VERIFIED].
- `CAPTURE-PLAN.md` is an **appended, marked** correction block on the final paragraph; no finding, number or
  table altered [VERIFIED: full diff read].

**Both `RED-GREEN-*.txt` transcripts are genuine.** I re-ran both provers from a clean extraction of the
branch and diffed: the output is **byte-identical except for wall-clock timestamps and temp paths**, and both
exit 0 [VERIFIED: `D2 PROVER EXIT=0`, `D3 PROVER EXIT=0`, diffs contain only the committed prose preamble and
`captured-at-utc` lines].

---

## (f) A2-4's corpus property — **still holds, same counts, one day later**

A2-4: *"All 27 non-`attempt1` POST refusals … byte-identical = 24, differs = 3."* A2-5 explicitly did **not**
re-issue and said so. I did, because the property is what makes the corpus citable.

Method: selected every non-`attempt1` `.http` whose method is POST and whose recorded `.status` is 4xx —
**27 recipes**, the same set — and re-issued them against the live reference oracle
(`https://localhost:8443`, health `{"status":"UP"}`) **through the branch's fixed `cap.sh`**, into a
**temp sandbox `out/`**, so not one committed byte was written.

```
selected 27 non-attempt1 POST recipes with a recorded 4xx
byte-identical = 24   differs = 3   transport-error = 0
```

The three that differ are **the same three A2-4 named**, for the reasons it recorded:

- `A2-bad-045-no-usage` — differs only in the burned PostgreSQL identity value (MF-11);
- `A2-prod-066-bad-paymenttype` — recorded **404**, now **403**, because A2-3's own `A2-111` retype reordered
  validation (MF-10);
- `A2-086-disburse-loan3-dupchannel` — now differs following A2-4's own disclosed control disbursement.

[VERIFIED: TRANSCRIPT §12.] Afterwards, `manifest.py verify` on the committed capture directory is still
**exit 0 / 430 files** — the re-issue touched nothing [VERIFIED: TRANSCRIPT §12 tail].

This doubles as the end-to-end proof that the fixed `cap.sh` still captures correctly against the **real**
oracle: 27 exchanges, 0 transport errors, 4xx recorded as data and exit 0, 24 bodies reproducing the committed
bytes exactly.

---

## Guards I could NOT drive red (reported as defects, per the brief)

**None.** Every guard A2-5 shipped fired for me:

- both zero-input refusals (the second one via the symlink invocation — see adjudication 2);
- the `REQUIRED` floor, on the real tree as well as in sandbox;
- recursion into `out/<subdir>/` and three levels deeper;
- coverage of `CAPTURE-PLAN.md`, `DEFECTS-FOUND-BY-REVIEW.md`, `cap.sh`, `env.sh`, `run-*.sh`, `manifest.py`;
- the flag file's deletion, gutting, and both `FLAGGED-BUT-ABSENT` / `FLAGGED-BUT-UNCOVERED` cases;
- the malformed-line refusal;
- the `cap.sh` transport handler, in 68 of 68 runnable interpreter/option/branch combinations.

The defect is the opposite shape: an attack the guard **should** catch and does not (A2-10-D1).

## Known blind spots, to be documented rather than silently carried

1. **A2-10-D1** — symlinked file (regression) and symlinked directory (pre-existing) under `out/`. Micro-fix above.
2. A `manifest.py` that neuters its own `verify()` passes. Inherent; git is the defence.
3. A fabricated file in a **new top-level directory** (`out2/`) is outside the manifest's declared scope.
4. `|| exit 1` is defeated by a **pipeline** or **subshell** caller. No current call site has that shape.
5. `manifest.py` writes `MANIFEST.sha256` from disk, so anyone who re-runs `write` after tampering gets green.
   The manifest detects **silent mutation**, not a **deliberate re-write** — that is what the git history is for.

## What I checked and found nothing wrong with, so silence is distinguishable from not looking

`cap.sh` `mktemp -d` failure path (exits under `set -e`, writes nothing); the `EXIT/HUP/INT/TERM` trap;
`${1-}`…`${4-}` under `-u` on the 3-argument form; `env.sh` sourcing under `set -eu`; the `.http` record's
field order and redaction; `.status` written last; `FLAGGED-NOT-REPRODUCIBLE.txt`'s 30 paths against the 30
`attempt1-*` files on disk; the manifest's dir-first ordering claim; the pinned pre-fix blob ids and sha256s;
the diff's scope; the prohibited-engine and no-float sweeps.

Not run and not claimed: `go build` / `go test` (this diff contains **zero** Go files) and
`.softhouse/conformance.sh` (this diff touches no vector, no contract and no Go module).

## Recommended follow-ups (backlog, outside this branch)

A2-5's four follow-ups stand. Add:

6. **Sweep every other capture directory's `manifest.py` for the symlink clause too** if the hardened copy is
   replicated rather than promoted — copying A2-5's version as-is would propagate A2-10-D1.
7. **The `|| exit 1` caller shape is fragile.** One comment line in `cap.sh` naming pipelines and subshells
   as the two ways to defeat it would cost nothing.
