# T107 — independent review of T91 (`softhouse/T91-preconditions-copy`)

> ## PROVENANCE — READ THIS BEFORE CITING ANY NUMBER BELOW
>
> **This document was written by a worker that was KILLED before it signalled done.** T107 was the
> paired independent reviewer of T91 on local fire `20260820-230001`; the harness terminated it
> mid-flight. No handoff was written, and at the moment the file was rescued onto
> `softhouse/T107-review-t91` (commit `35655fb`, "RESCUED: WIP from a worker that never signalled
> done") **not one of its numbers had been re-run by anybody.** A review whose figures nobody has
> reproduced is the same defect class this run keeps finding, one layer out.
>
> **T107b (fire `20260821-080001`) re-established it.** Every falsifiable headline claim was
> re-derived from `main`'s bytes and from source, against the live reference oracle, with real
> command output — not by reading T91's write-up back. Result: **all six headline claims reproduce**,
> **seven factual corrections** (C-1…C-7) are boxed inline where the claim is made, **one claim moves
> to `[UNVERIFIED]`** (the `ugrep` limb, C-7), the three micro-fixes in §10 are confirmed correctly
> specified and MF-1/MF-2 were driven red **and** green, and **MF-4** was added. The full ledger is
> **§14**. The verdict — **MICRO-FIX** — is unchanged and is now attested.
>
> Correction boxes are marked `[T107b CORRECTION C-n]`. Nothing T107 wrote has been deleted; where
> it is wrong it is struck and corrected in place, so a reader who finds the original sentence also
> finds the correction (P-12: corrections must land where the claim is *restated*, not only where it
> was scored).

Reviewer spawned fresh, no shared context with T91. Everything below was re-run by me on this host
against the live reference oracle (Fineract) unless explicitly marked `[UNVERIFIED]`. Destructive
work ran against `git archive` exports in `/tmp`; my worktree is clean and `main` was never touched.

**VERDICT: MICRO-FIX.** T91's substance is correct and I reproduced every headline number from
main's actual bytes. Three defects remain, all in the *evidence tooling* T91 ships, all in the
vacuous-pass class this run keeps finding (P-22), and all closable in 9 mechanical lines. None is a
money defect, none changes a conclusion, none touches a vector. The exact edits are in §10.

---

## 0. TL;DR of the rulings the brief asked for

| # | question | ruling |
|---|---|---|
| 1 | Does any promoted parity vector's provenance depend on the unhardened gate? | **NO — zero of 42.** Per-vector determination in §1. The promoted corpus is unaffected, and the reason is structural, not incidental. |
| 2 | True invoker count | **20 distinct files, 23 executable call sites.** T91 said 17 + `attest.py`; the driver's grep said 6. **T91 missed `leapboundary/bin/t55-negative-tests.sh:52`.** §2. |
| 3 | Is the call-through behaviour-preserving? | **Yes**, measured on five real callers × {`sh`,`bash`} × {pre,post}. Additive only on the happy path; one reworded FAIL line on the negatives; breach counts unchanged. §3. |
| 4 | Attack suite re-run | **Reproduced: pre-fix 6 of 13 ADMIT, post-fix 0 of 13**, both interpreters, 13/13 `sh`/`bash` identical. A2c reproduced verbatim. Four new attacks of my own; **three admit**. §4. |
| 5 | Was the expectation table back-fitted? | **No.** I derived all 13 rows independently from the hardened rig's stated contract before comparing; my table matches T91's row for row. §5. |
| 6 | Is the zero-file hardening real? | **Partly.** Both declared zero-file paths driven red by me (exit 3). But `verdict.sh` **passes vacuously on content-free transcripts** — demonstrated. §6. |
| 7 | T80's BSD-grep claim | **T91 is right, T80 is not — on this host.** BSD grep matched in 18/18 combinations (re-measured independently by T107b). The `ugrep -I` silent miss is **`[UNVERIFIED]` — T107b could not reproduce it and no ugrep exists on this host; see correction C-7.** The `LC_ALL=C grep -a` hardening is correct anyway, and does not depend on the ugrep limb. §7. |
| 8 | Invariants | All hold. Conformance **PASS, exit 0, 42 parity, 5,576 cells, 0 invariant violations**, re-run by me. §8. |
| 9 | `go build` / `go test` / `gofmt` | **Run by me, all green.** T91's `[UNVERIFIED]` was avoidable — the toolchain is repo-local and `conformance.sh` itself loads it. §9. |

---

## 1. THE BLAST RADIUS — the most important question, answered per vector

**Ruling: NO promoted parity vector's provenance depends, directly or transitively, on
`charges/bin/preconditions.sh` or on `audit-t44/charges/bin/preconditions-COPY.sh`. Zero of 42.
The promoted corpus is trustworthy on this axis.**

I did not assert this; I enumerated it.

### 1.1 What the 42 actually are

`.softhouse/vectors/loanschedule/` holds **46** files: **42 `parity`** and 4 `contract-refusal`. I
read every one's `provenance` and `oracle` block mechanically.

> **[T107b CORRECTION C-1]** This paragraph originally read "47 files: 42 parity, 4
> contract-refusal, 1 `selftest`". The directory holds 46; the single self-test fixture lives in the
> **sibling** directory `.softhouse/vectors/_selftest/SELFTEST-01-two-period-zero-rate.json`, not in
> `loanschedule/`. The 42 is unaffected.
> [VERIFIED T107b: `ls .softhouse/vectors/loanschedule/ | wc -l` = 46;
> `find .softhouse/vectors -type f`; class census over the 46 = `{'parity': 42, 'contract-refusal': 4}`.]

All 42 parity vectors carry `oracle.seam = "path_a_embeddable"`, and
`threaded_mathcontext = ambient_mathcontext = (19, HALF_UP)`. Their `capture_ref` values collapse
to **seven** files, all under `.softhouse/capture/out/`:

| capture_ref | vectors | declared `capture_sha256` == bytes on disk? |
|---|---|---|
| `capture-prod3b-raw.json` | 11 (`P-00`…`P-04t`, four `P-MNT-*`) | **yes** `8d23c48f…c945c79` |
| `capture-prod3c-raw.json` | 2 (`P-EMI-*`) | **yes** `cae566d3…e8c92dec` |
| `capture-prod3d-raw.json` | 2 (`P-RND-S1`, `P-RND-S2`) | **yes** `e9772dc5…dae1dcae` |
| `capture-prod3e-raw.json` | 14 (8 `P-DRIFT-*`, 4 `P-ME-*`, 2 `P-LAT-*`) | **yes** `8822699c…05104fc0` |
| `capture-prod3f-raw.json` | 3 (`T61-HE-A/B/C`) | **yes** `48b5377a…07479034` |
| `capture-prod3g-raw.json` | 4 (`T64-ZP-A/B/C/D`) | **yes** `6e0c3701…41827d91` |
| `capture-prod3i-raw.json` | 6 (`T74-E-P*`) | **yes** `e0ea0bcf…9acde430` |

11+2+2+14+3+4+6 = **42**. Every vector carries a `capture_sha256`; every declared digest equals the
sha256 of the file on disk today (I recomputed all seven).
[VERIFIED: my own recomputation over `.softhouse/vectors/loanschedule/*.json`.]

### 1.2 What produced those seven files

`.softhouse/capture/src/run-pass3{b,c,d,e,f,g,i}.sh` + `Capture3{b,c,d,e,f,g,i}.java`.

`grep -rn "preconditions" .softhouse/capture/src/` returns **eleven hits and not one is an
invocation**: **eight** `printf 'preconditions OK …'` lines (`run-pass3{b,c,d,e,f,g,h,i}.sh`), one
comment in `Capture3h.java`, one in
`Capture3i.java`, plus a JSON string literal in `run-rc6-rounddown-attestation.sh`. There is no
`preconditions.sh`, no `run-preconditions.sh`, no `preconditions-COPY.sh`, no `source`, no `.`, no
`subprocess` anywhere in the Path A rig.
[VERIFIED: grep over `.softhouse/capture/src/`, full output re-read line by line.]

> **[T107b CORRECTION C-2]** The breakdown originally said "**nine** `printf`" lines; there are
> **eight** (8 printf + 2 Java comments + 1 JSON literal = the 11 hits). The total and the ruling —
> not one hit is an invocation — reproduce exactly.
> [VERIFIED T107b: `grep -rn "preconditions" .softhouse/capture/src/` = 11 lines, enumerated.]
>
> **[T107b ADDITION]** A stronger, structural form of the same ruling, which I ran because the
> absence of the *word* does not by itself prove the absence of the *dependency*:
> `grep -rn "curl\|psql\|localhost:8443\|5432"` over all seven recipes that produced the 42
> vectors' capture files returns **zero hits**. The Path A chain contacts no server and no
> database, so no Path B tenant-assertion gate can ever have stood in front of it.
> [VERIFIED T107b: that grep, exit 1 / no output, over
> `run-pass3{b,c,d,e,f,g,i}.sh`.]

The Path A rigs carry their own **inline** fail-the-run preconditions, and they are pinned by
literal, not by comparison against a caller-supplied operand: `EXPECTED_IMAGE_ID` (image digest),
`EXPECTED_FINERACT_COMMIT` + clean-tree check, `EXPECTED_SEAM_SHA` **on both copies of the seam
source**, and `EXPECTED_REF3{B,C,E,G}_SHA` — literal digests of the very capture files the existing
vectors were transcribed from.
[VERIFIED: `.softhouse/capture/src/run-pass3i.sh` — **corrected line range, T107b**: the pins are
*assigned* at `:108-143` (`EXPECTED_IMAGE_ID`, `EXPECTED_FINERACT_COMMIT`, `EXPECTED_SEAM_SHA`,
`EXPECTED_REF3{B,C,E,G}_SHA`) and *compared* at `:165-216`. The original citation `:97-207` stops
four comparisons short of the end of the block. **[T107b CORRECTION C-3]**]

### 1.3 Why this is structural, not lucky

Path A runs the embeddable seam **in-process inside a `docker run` of the pinned image**. It starts
no Fineract server and opens no database connection — `run-pass3b.sh:10-13` says so and the recipe
contains no `curl` against the server and no `psql`. Every assertion the weak Path B script makes is
*about a running server and its tenant*: the tenant row (P8), `timezone_id` (P9),
`c_configuration.rounding-mode` (P10), `schema_connection_parameters` (P11), the server port (P12),
the JVM's `MoneyHelper` log line (P13), the HTTP half-cent canary (P14), MNT seeding (P15).

**Path A has no tenant.** The weak gate is not merely absent from the Path A chain; it is
inapplicable to it. There is no configuration under which a Path A capture could have been gated by
it, which is why the answer is safe rather than merely observed.

### 1.4 Secondary blast radius — what IS gated by the weak twin, and how far the harm reaches

Real, and worth naming precisely, because it is not nothing:

* **Every committed Path B capture under `charges/` (T40, T44, T46, T48, T51), `leapboundary/`
  (T55, 33 captures) and `actualactual/pathb/`** was gated by the unhardened bytes. 25 committed
  precondition transcripts live in those subtrees.
* Downstream **claims**, not vectors: DEC-1 §4.5.1's charge decisions (C-1, C-2, membership rules
  M4/M5); `capabilities.json`'s `charges` rows; and — the one with a pending gate attached — the
  **corrected ACT/ACT promotion condition** (finding T55-N1, "LB-DEC31 has a zero first segment and
  still grades the arm by 6,015 minor units"), which is the operative text behind proposed
  **gate G-4** (amending DEC-1's stale wording).
  [VERIFIED: `.softhouse/vectors/capabilities.json:53`.]
* The attestations `charges/out/attested/attestation.json:11` and `attestation-exact.json:11` say
  `"preconditions_script": "bin/preconditions.sh (copied verbatim from pathb/t36/preconditions.sh)"`
  — an attestation naming the *hardened* rig as its authority over a run that executed the
  *unhardened* bytes. This is P-21 (an attestation vouching in another task's name). T91 raised it
  as F-2 and understated it as "wording that implies a copy"; it is a provenance claim, not a
  wording nit.

**None of that is a promoted parity vector and none of it contributes a cell to the 5,576.**

**How far does the harm actually reach?** The weak script has exactly two defeats and both require
the *runner* to misbehave — supply a `CANARY_REQ` that is not the pinned tie, or set
`CANARY_EXPECT`. Three independently checkable facts bound it:

1. Every committed invoker hard-codes the pinned file and sets no `CANARY_EXPECT`
   (`charges/bin/run-preconditions.sh:8`, `attest.py:89-90`, `attest-t40.py:90-91`).
2. `pathb/t22-audit/req/calc-pmode2-gerege.json` has **not been touched since commit `4ebb5ec`**
   (the T22 audit, before T40's charge captures) and hashes to the pin
   `2a6621be…93352154` today. [VERIFIED: `git log --follow`, `shasum -a 256`.]
3. **24 of 24** positive-run transcripts in those subtrees record `21 PASS / 0 FAIL` and the line
   `PASS effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)`; the 25th is a
   deliberate `default` control at `16 PASS / 5 FAIL`. [VERIFIED: my own scan of all 25;
   re-scanned independently by T107b — 25 files, 24 at exactly `21 PASS / 0 FAIL` carrying the
   canary line, 1 at `16 PASS / 5 FAIL`.]

   > **[T107b CORRECTION C-4 — attribution]** The 25th transcript is **T51's**, not T44's: it is
   > `charges/out/t51/negative/n1-preconditions-default.txt`, written by
   > `charges/bin/t51-negative.sh:21`. **T44's own committed control is a 26th transcript**,
   > `audit-t44/charges/out/PRECOND-default.txt`, also `16 PASS / 5 FAIL` — and it lives in
   > `audit-t44/`, a **fourth** subtree this section's list does not name. Both non-conforming
   > transcripts are deliberate negatives, so the bounding argument is unchanged and marginally
   > strengthened: 24 of 26, with both exceptions intended.
   > [VERIFIED T107b: `find charges leapboundary actualactual audit-t44 -name '*precondition*'`
   > plus a per-file `grep -ac '^  PASS  '` / `'^  FAIL  '` census.]

So on the committed evidence **no capture was actually taken through a defeated gate**. State that
honestly: it is an *inference* from three facts, not a proof. The pre-T91 transcripts carry no
digest line, so they cannot testify to which bytes were POSTed — that is precisely the guarantee
T80's P14b adds and the reason it was needed.

**What would re-establish it, if anyone wants proof rather than inference:** re-run
`bin/run-preconditions.sh` through the hardened call-through, which now prints the digest. I did
exactly that against the live oracle: **22 PASS / 0 FAIL / exit 0**, the added line being the digest
comparison (§3). That is a present-tense observation about today's environment, not a retroactive
one about the historical runs. **No re-capture is warranted and I recommend none.**

---

## 2. The true invoker count

T91 said "17 capture scripts and `attest.py`". The driver's narrower grep found 6. Neither is right.

**Measured: 20 distinct files, 23 executable call sites.**

**Direct invocations of `charges/bin/preconditions.sh` — 5 files, 5 sites**

| file:line | form |
|---|---|
| `charges/bin/run-preconditions.sh:9` | `sh "$W/.../charges/bin/preconditions.sh" gerege` (the T40 wrapper) |
| `charges/bin/attest.py:90` | `subprocess.run('CANARY_REQ=%s sh %s %s' …)`, `HERE` = `charges/bin` |
| `charges/bin/attest-t40.py:91` | same shape |
| `charges/bin/t51-negative.sh:21` | `sh "$CH/bin/preconditions.sh" default` |
| **`leapboundary/bin/t55-negative-tests.sh:52`** | `sh "$W/.softhouse/capture/charges/bin/preconditions.sh" t55-no-such-tenant` — **T91 MISSED THIS ONE** |

**Via the wrapper — 15 files, 18 sites**

`charges/bin/`: `capture.sh:10`, `control.sh:18`, `create-charges.sh:11`, `create-charges2.sh:8`,
`t46-capture.sh:18`, `t48-capture.sh:28`, `t48-determinism.sh:14`, `t51-capture.sh:29` **and** `:195`,
`t51-capture2.sh:28` **and** `:234`, `t51-capture3.sh:20`, `t51-capture4.sh:22`, `t51-capture5.sh:21`
**and** `:120`, `t51-capture6.sh:20`; plus `leapboundary/bin/t55-capture.sh:56` and
`actualactual/src/pathb-capture.sh:37`.

**Not an invoker:** `charges/bin/selfcheck.sh:15` names the file in a `grep -v` *exclusion* — that is
T91's F-4 and it is correctly characterised.

**Consequence of the miss.** `t55-negative-tests.sh` leg N2 asserts the transcript contains
`has no row in fineract_tenants.tenants`. T91 changed the script that leg tests without knowing the
leg exists. **I checked it and it survives**: pre and post, tenant `t55-no-such-tenant` gives
`12 PASS / 9 FAIL / exit 1` and the required string is present in both (§3, caller C3). The omission
cost nothing *this time*; the census was still not established, and a census is the input to the
blast-radius question the driver asked. Finding **F-3 (P2)**.

`preconditions-COPY.sh` is invoked by nothing — I re-ran the sweep and confirm T91's finding: every
hit is prose. [VERIFIED: repo-wide grep, `--exclude-dir=.git`.]

---

## 3. Is the call-through behaviour-preserving?

**Yes.** Five real callers, two interpreters, two trees, all against the live oracle.

| caller | pre-fix | post-fix | delta |
|---|---|---|---|
| **C1** `run-preconditions.sh` (the T40 wrapper), tenant `gerege` | 21 PASS / 0 FAIL / exit 0 | **22 PASS / 0 FAIL / exit 0** | exactly one **added** `PASS canary request pinned by DIGEST COMPARISON …` line |
| **C2** `t51-negative.sh`'s form — direct, tenant `default`, no `CANARY_REQ` | 16 PASS / **5 FAIL** / exit 1 | 16 PASS / **5 FAIL** / exit 1 | one FAIL line reworded, breach count unchanged |
| **C3** `t55-negative-tests.sh` N2 — tenant `t55-no-such-tenant` | 12 PASS / 9 FAIL / exit 1 | 12 PASS / 9 FAIL / exit 1 | one FAIL line reworded; the asserted string survives |
| **C4** T44's control through `preconditions-COPY.sh`, tenant `default`, pinned canary | 16 PASS / 5 FAIL / exit 1 | 17 PASS / **5 FAIL** / exit 1 | one added PASS; **same 5 breaches** — T44's finding survives |
| **C5** the same call from a foreign CWD (`/tmp`), absolute path | 21 / 0 / exit 0 | 22 / 0 / exit 0 | identical to C1 — resolution is CWD-independent |

`sh` and `bash` legs are identical in every cell for all five callers.

**Mechanism checks, done rather than assumed:**

* **`$0` / `$BASH_SOURCE` / relative paths inside the rig:** none.
  `grep -n '\$0\|BASH_SOURCE\|dirname\|\.\./' pathb/t36/preconditions.sh` returns **zero** hits. The
  rig resolves nothing relative to itself and takes `CANARY_REQ` from the environment. Dot-sourcing
  it from a different CWD therefore cannot change what it reads. C5 confirms behaviourally.
* **Positional arguments:** `. "$RIG"` with no extra words inherits `"$@"`; the rig reads
  `TENANT=${1:-gerege}` and both C2 (`default`) and C3 (`t55-no-such-tenant`) arrive correctly.
* **Exit status:** the rig terminates with an explicit `exit 0` / `exit 1`, which in a sourced
  script exits the shim's own shell. Propagation confirmed on every row above and through the
  wrapper (`PRECONDITIONS_EXIT=…`).
* **`set -u` / `set -e`:** the shim sets `-u`, the rig sets `-u`; neither sets `-e`, and no caller
  sources the shim, so no caller's options are inherited into or out of it.
* **Missing-rig branch is fail-closed:** if the `cd` in the command substitution fails the result is
  empty, `$RIG` becomes `/pathb/t36/preconditions.sh`, `[ ! -f ]` fires, exit 2.
* **`exec` vs dot-source:** T91's reasoning is right and I confirmed the consequence rather than the
  argument — `sh`/`bash` transcripts are byte-identical after normalisation, 13/13, both labels
  (§4).

**Side note, verified because T91 asserted it and T85/T80 before it:** the unbraced
`'$PIN_PG_MAJOR_MINOR…'` in main's twin **does** kill the script under `set -u`. On this host both
`/bin/sh` and `/bin/bash` report `PIN_PG_MAJOR_MINOR\xe2: unbound variable` and exit 1 — bash treats
the leading byte of U+2026 as an identifier character. So T91's "hole 4" is real.
[VERIFIED: my own minimal repro, `/tmp/t107-brace.sh`.]

---

## 4. Attack suite, re-run from main's actual bytes

I restored main's bytes myself (`git archive main` → `/tmp/t107-pre`, sha256
`9256b881…a416a46b54` on **both** twins, confirming the driver's blob identity behaviourally) and
T91's branch (`/tmp/t107-post`, shim sha256 `7f53f33b…c55cc038`). I ran T91's parameterised runner
under my own labels; I did not reuse a single committed transcript.

**Pre-fix, from main's bytes: 6 of 13 ADMIT, scorer exit 1.** Reproduced exactly.
`A2a`, `A2c`, `A4c`, `A5`, `A7`, `A8` — every one exit 0 printing the HALF_UP certification with **no
digest pin**.

**A2c reproduced verbatim**, and it is as bad as T91 says. On tenant `gerege`, with a request I
crafted (principal `1162502.4`) and an expectation I supplied (`CANARY_EXPECT=20925.04`), main's
live twin printed:

```
  PASS  effective rounding mode canary: period-1 interest 20925.04 (= HALF_UP)

ALL PRECONDITIONS HOLD — tenant 'gerege' at MathContext(19, HALF_UP), PostgreSQL only.
EXIT=0
```

`20925.04` is the value the script's own comment (`# …must answer 20925.05 under HALF_UP and
20925.04 under HALF_EVEN`) says means HALF_EVEN. **Both operands attacker-supplied.** Same defect
class as the canary this run already found (T77→T80). [VERIFIED: my own run,
`/tmp/t107-pre/.softhouse/capture/t91/out/t107-prefix-sh/A2c-*.txt`.]

**Post-fix: 0 of 13 admit, scorer exit 0.** The three genuine admissions close (`A2a`, `A2c`, `A5`
→ exit 1); `A4c`, `A7`, `A8` still exit 0 **but now with a passing digest pin on `gerege`**, which is
the correct invariance result, not a residual hole.

**`sh` vs `bash`: 13/13 identical after normalisation, both labels, exit 0.** Re-run by me.

### 4.1 Four attacks T91 did not try — three admit

| # | attack | result |
|---|---|---|
| **N8a** | rig file present but **EMPTY** | **ADMITS.** Shim exits **0** printing nothing. Through the real wrapper: `PRECONDITIONS_EXIT=0`, exit 0, **zero-byte transcript**. `attest.py:95` gates only on `pre.returncode != 0`, so it would proceed and stamp `'preconditions_result': 'ALL PASS (transcript: …)'` at `:269` over a transcript containing nothing. (**[T107b CORRECTION C-5]** — the review said `:96` and `:270`; the gate is at **95** and the stamp at **269**. Both re-read.) |
| **N8b** | rig file present with a **syntax error** | refuses — exit 1. Fail-closed. |
| **N9** | rig replaced at its path by **main's pre-hardening bytes** | **ADMITS.** A2c reproduces exactly through the post-fix shim: `PASS effective rounding mode canary: period-1 interest 20925.04 (= HALF_UP)`, `ALL PRECONDITIONS HOLD`, exit 0. |
| **N10** | shim reached through a **symlink** placed in a foreign tree | **ADMITS.** `$0`-relative resolution picks up the attacker's `pathb/t36/preconditions.sh`; my stub printed `ALL PRECONDITIONS HOLD` and exited 0. |

**Reading these honestly.** N8a's *mechanism* ("an empty script file exits 0") is not introduced by
T91 — main's twin would do the same if emptied. What **is** new is the indirection: the shim's
effective gate is now selected by a path relative to `$0`, with **no identity check and no record of
which rig ran**. The rig pins its canary by digest precisely because "a check whose operands the
caller controls is not a check" — and the shim's own operand, *which rig*, is pinned by nothing. The
realistic trigger is not sabotage: it is a `git archive` of an older commit, a stale worktree, or a
tree where `pathb/` was reverted (this program backed out a `pathb/`-touching merge two fires ago).
Finding **F-2 (P2)**; remedy in §10.

---

## 5. Was the expectation table back-fitted? (auditing T91's disclosure (h))

T91 disclosed that its scorer's first rule was wrong and that the corrected table was written
**after** the first post-fix run. That is the exact ordering in which a rig gets tuned, so I
reconstructed the table independently, from what each attack **should** do given the hardened rig's
stated contract (`t36/preconditions.sh:170-175`: "the sentence … must be unreachable except on the
exact pinned half-cent tie"; P14a: an inherited `CANARY_EXPECT` is itself a breach).

| attack | my derived expectation | T91's | agree? |
|---|---|---|---|
| A2a | BREACH / sentence NEVER — digest mismatch, canary not sent | BREACH/NEVER | ✓ |
| A2b | BREACH / NEVER | BREACH/NEVER | ✓ |
| A2c | BREACH / NEVER — P14a *and* P14b both fire | BREACH/NEVER | ✓ |
| A3a | BREACH / NEVER — valid file, wrong digest | BREACH/NEVER | ✓ |
| A3b | BREACH / NEVER — not a readable file | BREACH/NEVER | ✓ |
| A3c | BREACH / NEVER — `CANARY_REQ` unset | BREACH/NEVER | ✓ |
| A4a | BREACH / NEVER — P14a fires; pin holds so the canary is sent to `default`, where it cannot equal the constant | BREACH/NEVER | ✓ |
| A4b | BREACH / **PINNED** — P14a fires, pin holds, canary legitimately graded against the CONSTANT and agrees | BREACH/PINNED | ✓ |
| A4c | **CLEAN** / PINNED — the decoy name is unread by the hardened rig, so setting it must change nothing | CLEAN/PINNED | ✓ |
| A5 | BREACH / PINNED — the tripwire captures *any* inherited value, agreement is irrelevant | BREACH/PINNED | ✓ |
| A6 | BREACH / NEVER — `[ -f ]` false for a directory | BREACH/NEVER | ✓ |
| A7 | **CLEAN** / PINNED — a digest grades bytes; `-f` and `shasum` follow symlinks | CLEAN/PINNED | ✓ |
| A8 | **CLEAN** / PINNED — the rig resolves no relative path | CLEAN/PINNED | ✓ |

**13 of 13 agree. No row shows any sign of having been set to match an observation.** Each is
derivable from the rig's text without running anything, and I checked the two that would be easiest
to fudge: `A4c`'s CLEAN rests on `CANARY_EXPECT_OVERRIDE` appearing in the hardened rig **only in a
comment** (line 49, `grep -c` = 1), and `A5`'s BREACH rests on `CANARY_EXPECT_ENV_ATTEMPT` capturing
the inherited value one line before the constant overwrites it (`:53-54`). Both hold.

I also independently re-derived T91's rule change and agree with it: on the hardened rig `A4b`/`A5`
exit 1 *and then* legitimately print the sentence, so "exit 0 **or** sentence present" would score a
**fired guard** as an admission. T91's replacement — the sentence is a violation only without a
passing digest pin on `gerege` — is T80's own `forbidden-sentence.sh` rule and is correct.

**One qualification the table does not state.** The three `CLEAN` rows are clean only *conditional on
all 21 other preconditions holding against a healthy oracle*. The table is environment-coupled: on a
degraded oracle the scorer would report `REGRESSION` for A4c/A7/A8. That is the right direction to
fail, but it means "13/13 met their expectation" is partly a statement about the oracle's health.

---

## 6. Is the zero-file / vacuous-pass hardening real?

**Partly — and the gap is my sharpest finding.**

**What is real, driven red by me:**

* `verdict.sh` over an empty directory → **exit 3**, `"a scan over an empty file set proves
  NOTHING"`. A named attack with no transcript is `MISSING TRANSCRIPT`, not a skip.
* `shell-invariance.sh` over two empty label directories → **exit 3**, `"compared ZERO transcript
  pairs — proves nothing"`.
* `verdict.sh` against my own pre-fix transcripts → **6 admissions, exit 1**. It discriminates.
* `prove-guards.sh` G-1 red leg, run by me from a real repo: rig deleted → shim exit **2** with
  `PRECONDITIONS NOT RUN. DO NOT CAPTURE — nothing was asserted about the oracle.`, and
  `run-preconditions.sh` propagates `PRECONDITIONS_EXIT=2`. The message is true when it prints —
  the check is the first executable statement after `set -u`, before any output, `curl` or
  `docker exec`.

**F-1 (P1) — `verdict.sh` guards zero FILES but not zero CONTENT, and passes vacuously.**

I replaced ten of the thirteen transcripts with a single line reading
`truncated, nothing was ever run` — no attack output, no exit status, no PASS/FAIL line — and the
scorer printed:

```
ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION.
TRUNC_EXIT=0
```

Cause: `st=$(LC_ALL=C tail -1 "$f" | sed 's/EXIT=//')` never checks that the last line **is** an
`EXIT=` line. Ten of thirteen rows are `BREACH`, tested as `[ "$st" != 0 ]`, and *any* garbage
string satisfies that. So the scorer reports a clean sweep over evidence that does not exist.

This is P-22 one layer in, inside the file whose own honesty note is about P-22 — the same shape as
T80's F-1 that T85 caught ("the abort message was FALSE at the moment it printed"), and the same
shape as the green control with no discriminating power that T98 found. **The conclusion T91 draws
is nevertheless correct** — I reproduced the real transcripts and the real counts — but the guard
that certifies it would have certified nothing just as loudly. Remedy in §10.

**F-6 (P3) — `prove-guards.sh` reports rather than asserts.**

Three sub-defects, all demonstrated:

1. It never checks that `git archive` produced anything. I ran it once from a non-git export:
   `git archive` printed `fatal: not a git repository`, the export was empty, **all three G-1 legs**
   died with `No such file or directory`, the G-1 green leg printed **`exit=0`** next to that
   failure, and the script still **exited 0** with a full-looking transcript.

   > **[T107b CORRECTION C-6]** The original sentence said "**every** leg printed `No such file or
   > directory`". Only the three **G-1** legs did. G-2 and G-3 ran correctly and returned **exit 3**
   > even from the non-git export, because they build their own fixtures in `$S` and never read the
   > export. G-4 took its `|| { … skipping G-4; exit 0; }` branch, which is *how* the run reached
   > exit 0. The defect is unchanged and reproduces exactly: an unchecked `git archive`, a `$?`
   > taken after a pipeline, and a script that exits 0 over a transcript of nothing.
   > [VERIFIED T107b: `sh /tmp/.../nogit/.softhouse/capture/t91/prove-guards.sh`; exit 0; transcript
   > shows `exit=0` beside `No such file or directory` in the G-1 GREEN leg and `exit=127` in the
   > RED leg.]
2. `echo "   exit=$?"` follows a pipeline (`… | tail -1`) in the G-1 GREEN leg, so `$?` is `tail`'s
   status — that leg **cannot** report a failure. (The RED leg uses no pipeline and is correct.)
3. The script prints `(expect 3)` beside the observed value instead of comparing, and exits 0
   unconditionally.

When run from a real repository the guards themselves fire correctly — I verified that by
`git init`-ing the export and re-running. So this is a defect of the *proof*, not of the guards.
The committed `GUARDS-RED.txt` is genuine.

---

## 7. Ruling on the T80 contradiction (g)

I tested it myself rather than deferring.

**Experiment.** Three files, each containing the exact certification sentence:
`clean.txt`; `badutf8.txt` (sentence + `\xff\xfe` + `\xc3\x28`, an invalid UTF-8 sequence);
`withnul.txt` (sentence + `\x00`). Three locales (`en_US.UTF-8`, `C.UTF-8`, `C`) × with and without
`-a`, on `/usr/bin/grep` = **BSD grep 2.6.0-FreeBSD**.

**Result: rc = 0 (match) in all 18 combinations.** T80's stated behaviour — "BSD grep in a UTF-8
locale matches nothing and returns 0" — **did not reproduce on this host, in any form.** I land on
**T91's side**, and I say so from my own experiment, not from T91's report.
[VERIFIED: `/tmp/t107-grep/probe.sh`. **INDEPENDENTLY REPRODUCED T107b**: same three file shapes ×
three locales × ±`-a` on `/usr/bin/grep` = BSD grep 2.6.0-FreeBSD → **rc = 0 in 18 of 18**.
Probe: `/tmp/t107b/grepprobe.sh`.]

**~~What DOES reproduce is T91's ugrep finding, exactly.~~** *(struck by T107b — see the correction
box below.)* The claim as written was: the `grep` on this environment's
interactive PATH is a shim onto **ugrep 7.5.0** with `-I` (ignore binary); on `badutf8.txt` it
returns **1 — "absent" — for a file that plainly contains the sentence**; with `-a` it returns 0;
`withnul.txt` likewise returns 1; `/usr/bin/grep` returns 0 on both.
~~[VERIFIED: my own runs.]~~ → **`[UNVERIFIED]`**.

> **[T107b CORRECTION C-7 — the one claim in this review that did not reproduce]**
> **I could not reproduce the ugrep limb, and it must not stand as `[VERIFIED]`.** In my session
> there is **no `ugrep` on this host at all**: `command -v ugrep` is empty; nothing named `ugrep`
> exists under `/opt/homebrew`, `/usr/local`, `~/.local` or `/Users/buv/bin`; and
> `/pkg/env/global/bin`, which *is* on `PATH`, **does not exist as a directory**. `command -v grep`
> resolves to `/usr/bin/grep`, and `grep --version` reports `grep (BSD grep, GNU compatible)
> 2.6.0-FreeBSD` — the same binary as the `/usr/bin/grep` leg, which matched 18/18.
> **T91's own committed proof takes the same fallback branch**: `t91/prove-guards.sh:87-95` runs
> the ugrep legs only `if command -v ugrep`, and the committed `out/GUARDS-RED.txt` records the
> `else` text — *"ugrep is not on PATH here; the ugrep limb was measured interactively and is
> reported in the handoff."*
> So the ugrep observation rests on **two agents' unrecorded interactive measurements** and on
> **zero committed evidence**. It is exactly the defect class this run grades for, one layer out:
> a number nobody can re-run. It moves to the `[UNVERIFIED]` register in §12 and is handed to
> **T108**, whose brief is precisely to settle which tool T80 actually observed.
> **What is unaffected:** the BSD half (18/18 match; T80's stated BSD behaviour does not reproduce)
> is now measured by two independent workers, and the conclusion below — that `LC_ALL=C grep -a` is
> correct, fail-closed and cheap — does not depend on the ugrep limb.
> [VERIFIED T107b: `command -v ugrep` (empty), `find /opt/homebrew /usr/local ~/.local ~/bin -name
> ugrep` (empty), `ls -d /pkg` (No such file or directory), `grep --version`,
> `/tmp/t107b/grepprobe.sh`; and `sed -n '87,95p' t91/prove-guards.sh` + `GUARDS-RED.txt:47-48`.]

**Hypothesis, marked as such and offered to T108:** T80 may have hit this same ugrep shim and
attributed it to BSD grep. I did not test T80's original file, so this is `[UNVERIFIED]`.

**Is the hardening right even though T80's reason is wrong?** Yes, and for two separable reasons,
which is worth stating because nobody has yet:

* **`-a` is what fixes the failure that actually reproduces** — it defeats the binary-content
  heuristic that made ugrep skip the file.
* **`LC_ALL=C` fixes a different failure that I could not test here** — GNU grep on Linux, in a
  UTF-8 locale, genuinely can fail to match across an invalid multibyte sequence. This program's
  scripts are run on macOS today but nothing pins that. `[UNVERIFIED on Linux — no Linux host
  available to me.]`

So `LC_ALL=C grep -a` is correct, fail-closed, and cheap. T91 applied it while reporting that it
could not reproduce the stated reason — which is the honesty rule working, and is the right call.

---

## 8. Invariants

| check | result |
|---|---|
| `git diff main...T91 -- .softhouse/vectors/ nexus/ .softhouse/capture/pathb/` | **EMPTY** (0 lines). Driver's measurement confirmed. |
| Files modified by the diff | **exactly two**, both scripts: `charges/bin/preconditions.sh`, `audit-t44/charges/bin/preconditions-COPY.sh`. 133 additions, all under `.softhouse/capture/t91/` plus the T91 handoff. |
| `PIN.json` | blob `b51595bb…` on main **and** on the branch — untouched |
| `capabilities.json` | blob `882e97bc…` on main **and** on the branch — untouched |
| `contract.go` | blob `4bcbafad…` on main **and** on the branch — **byte-identical** |
| `gofmt -l nexus/` | names **exactly** `internal/apps/loanschedule/contract/contract.go` — gate **G-3, expected state**. No `gofmt -w` was run by T91 or by me. |
| Any committed capture's bytes edited | **NO** — no capture output file appears in the diff at all |
| `bash .softhouse/conformance.sh` (bash, never `sh`) | **VERDICT PASS, exit 0** — 42 parity PASS / 0 FAIL, 4 contract-refusal PASS, 1 self-test, 0 refused, 0 inadmissible, 0 harness errors, **5,576 cells graded**, 84 ungraded, **0 invariant violations, 0 invariant assertions not run**. Re-run by me on the branch export. |
| Oracle discipline | read-only throughout: `POST /loans?command=calculateLoanSchedule` (pure calculation) and read-only `docker inspect` / `docker exec … psql -c 'select …'`. No restart, no rebuild, no re-seed, no `compose down`, no DB write. Containers still `Up 2 days (healthy)` / `Up 3 days (healthy)`. |
| Prohibited engines | no `ojdbc` / `oracle.jdbc` / `:1521` / MySQL / MariaDB token introduced anywhere in the diff. "Oracle" throughout means the Fineract reference implementation. |
| Money | no money code, no float, no vector, no contract surface touched by this diff. |

---

## 9. `go build` / `go test` / `gofmt` — T91's `[UNVERIFIED]`, closed

T91 reported no Go toolchain and declined to claim these. Correct behaviour on the honesty rule, but
**the gap was avoidable**: the toolchain is repo-local and gitignored at
`/Users/buv/gerege-nbfi/.softhouse/toolchain`, put on `PATH` by `.softhouse/bin/go-env.sh` — which
`conformance.sh:159` sources, and T91 ran `conformance.sh` successfully. Finding **F-5 (P3)**: a
worker that runs a harness which loads a toolchain has evidence that the toolchain exists.

Run by me on the branch export, toolchain loaded the same way:

* `go version` → `go1.26.6 darwin/arm64`
* `go build ./...` → **exit 0**, no output
* `go test ./...` → **exit 0**; `loanschedule` ok 7.406 s, `loanschedule/conformance` ok 8.108 s,
  two packages with no test files
* `gofmt -l .` → **exactly** `internal/apps/loanschedule/contract/contract.go` (G-3 expected)

---

## 10. Findings and the required micro-fix

| id | sev | finding |
|---|---|---|
| **F-1** | **P1** | `verdict.sh` reports `ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION` and exits 0 over ten transcripts containing no attack output. It guards zero *files* but not zero *content*: `st=$(tail -1 … \| sed 's/EXIT=//')` is never validated, and ten of thirteen rows accept any non-`0` string. Demonstrated. |
| **F-2** | **P2** | The call-through selects its rig by a `$0`-relative path and never establishes its identity, nor records it in the transcript. Demonstrated three ways: empty rig → exit 0 having asserted nothing (`attest.py` would stamp `ALL PASS` over a zero-byte transcript); rig replaced by main's pre-hardening bytes → **A2c reproduces exactly**; shim reached via symlink → rig taken from the attacker's tree. |
| **F-3** | **P2** | The invoker census is wrong. True figure **20 files / 23 call sites**; T91 omits `leapboundary/bin/t55-negative-tests.sh:52`, a *direct* invoker in the negative-test suite. I verified its asserted string survives the change; the census was still not established. |
| **F-4** | **P3** | The shipped shim's header states `bin/t51-negative.sh` "now reports one further breach". **Measured 5 FAIL before and 5 FAIL after**, both interpreters — the hardened rig *replaces* the "canary NOT run" breach. This is PR-10's error, which T91 scored as **wrong** in its prediction table and then left standing in a shipped file. P-12/P-21 exactly: the correction landed where the claim was scored, not where it was restated. |
| **F-5** | **P3** | `[UNVERIFIED] go build/gofmt` was avoidable (§9). Closed by me; no action needed beyond noting it for the next worker brief. |
| **F-6** | **P3** | `prove-guards.sh` prints rather than asserts: no check that `git archive` succeeded, `$?` after a pipeline in the G-1 green leg, and an unconditional exit 0. Demonstrated by running it outside a git repo, where it produced a full-looking transcript of nothing and exited 0. The guards themselves are sound; the proof is not. |

### The micro-fix — 9 lines, mechanical, no number, no money logic

**MF-1 — `.softhouse/capture/t91/verdict.sh`** (closes F-1). Immediately after the `st=` assignment,
reject a transcript whose last line is not an `EXIT=<digits>` line:

```sh
  case "$st" in
    ''|*[!0-9]*) printf '%-46s %-6s %-9s %-10s %s\n' "$name" "-" "-" "-" 'ERROR (no EXIT= line — the transcript has no attack body)'
                 echo "$name NO EXIT LINE" >> "$D/.score-fail"; continue ;;
  esac
```

**MF-2 — both shims** (`charges/bin/preconditions.sh`, `audit-t44/charges/bin/preconditions-COPY.sh`),
closes F-2's first limb. After `. "$RIG"`:

```sh
echo "PRECONDITIONS NOT RUN: the rig at '$RIG' returned without exiting — nothing was asserted." >&2
exit 2
```

(The rig always terminates with `exit 0` or `exit 1`; reaching the next line means it was empty,
truncated or neutered.)

**MF-3 — `charges/bin/preconditions.sh` header** (closes F-4). Delete or correct the sentence
"`bin/t51-negative.sh` passes none, so it now reports one further breach" — the measured breach count
is unchanged at 5.

**MF-4 — `charges/bin/preconditions.sh:8` header** (**added by T107b**; closes the same defect class
as MF-3, in the same file, 41 lines above it). The shipped shim says
"this file — which **17 capture scripts and `attest.py`** actually invoke". The measured census is
**20 distinct files, 23 executable call sites** (§2, re-derived by T107b). This is a false sentence
in a shipped file that a future reader will cite, it is one line, and MF-3 exists for exactly this
reason — so it is a micro-fix, not a follow-up. FU-2 remains as written for the *other* restatements
(`tasks.json`, handoffs), which are outside T91's diff.
`audit-t44/charges/bin/preconditions-COPY.sh` carries **no** census sentence
[VERIFIED T107b: `grep -n "17 \|invoke\|call site"` over both shims → the only census hit is
`charges/bin/preconditions.sh:8`], so MF-3 and MF-4 are correctly scoped to the one file.

**Each of MF-1 and MF-2 must be driven RED before merge** (P-22). Reproductions are ready:
MF-1 against a truncated transcript set; MF-2 against an emptied rig — both procedures are in §4.1
and §6 and take under a minute.

> **[T107b ATTESTATION OF §10 — the three specifications were applied and driven, not read]**
> I applied MF-1 and MF-2 **exactly as written above** to a `/tmp` copy of T91's branch
> (`/tmp/t107b/apply-mf.sh`; the repo was not touched, per the brief) and drove each red and green.
>
> * **Anchors are correct.** MF-1's anchor — the `st=$(LC_ALL=C tail -1 "$f" | sed 's/EXIT=//')`
>   line — occurs **exactly once** in `verdict.sh`. MF-2's anchor — `. "$RIG"` — is the **last line
>   of both shims**, so "after `. "$RIG"`" is unambiguous. Both assertions were made programmatically
>   and both held.
> * **MF-1 RED:** against the ten content-free transcripts of §6 → **exit 1**, ten rows
>   `ERROR (no EXIT= line …)`, `EXPECTATIONS NOT MET (10)`. Before MF-1 the identical input scored
>   `ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION`, exit 0.
> * **MF-1 GREEN, and still discriminating:** on my real post-fix transcripts → exit 0,
>   `ALL 13 …`; on my real pre-fix transcripts → **exit 1, the same 6 admissions**. It does not
>   blunt the scorer.
> * **MF-2 RED:** rig emptied → shim **exit 2**, `PRECONDITIONS NOT RUN: the rig at '…' returned
>   without exiting — nothing was asserted.`; through `bin/run-preconditions.sh` → `PRECONDITIONS_EXIT=2`,
>   exit 2, and the transcript is **no longer zero bytes**. That closes N8a.
> * **MF-2 GREEN, no regression:** all five callers of §3 re-measured with MF-2 applied — C1
>   22/0/exit 0, C2 16/5/exit 1, C3 12/9/exit 1 (asserted string present), C4 17/5/exit 1, C5
>   22/0/exit 0 — **identical to the post-fix column, cell for cell**.
> * **MF-2's premise is sound:** the hardened rig contains exactly two `exit` statements, both
>   terminal (`t36/preconditions.sh:234` `exit 1`, `:237` `exit 0`), so reaching the line after
>   `. "$RIG"` really does mean the rig never ran to completion.
> * **MF-2 does NOT close N9, as §10 implies and as it should not.** With the rig replaced by main's
>   unhardened bytes, the MF-2 shim still exits **0** and still prints
>   `PASS effective rounding mode canary: period-1 interest 20925.04 (= HALF_UP)`. Only FU-1 (an
>   identity check on the rig) closes N9/N10. Verified so that nobody merges MF-2 believing F-2 is
>   discharged.
> * **MF-3 is correctly specified.** Measured breach count for the `t51-negative.sh` form is **5
>   before and 5 after**, both interpreters (§3 row C2, re-measured). The sentence is false.
>
> **One residual, stated so the next worker can decide.** MF-1 as specified validates the *value*
> `$st` (`''|*[!0-9]*`), not the *shape of the last line*. A transcript whose final line is a bare
> numeral — e.g. `5` — would still be accepted as a status. A strictly tighter form is
> `LC_ALL=C tail -1 "$f" | LC_ALL=C grep -aq '^EXIT=[0-9][0-9]*$' || { … }`. MF-1 as written closes
> the demonstrated F-1 defect completely and I do not block on this; I record it rather than let a
> later reader assume the check is exhaustive.

### Follow-ups — NOT micro-fixes, for T108 or a successor

* **FU-1 (P2).** Give the shim an identity check on the rig it sources — either a digest pin or, at
  minimum, `shasum -a 256 "$RIG"` echoed into the transcript so every future attestation records
  *which* rig ran. This changes transcript bytes and so needs its own task and its own additive-only
  measurement. It is the only thing that closes F-2's N9/N10 limbs.
* **FU-2 (P2).** Correct the census wherever it is restated — the shim headers say "17 capture
  scripts", `tasks.json` repeats it, and this review says 20/23. Sweep for the *restatements*, per
  P-21, not for the numeral.
* **FU-3 (P2).** T91's own F-1: `AUDIT-CHARGES.md:190`'s "all three sha256 `9256b881…`" is now false
  for all three. Endorsed. Add T91's F-2 with the stronger characterisation from §1.4: the
  attestations at `charges/out/attested/attestation*.json:11` name `t36/preconditions.sh` as the
  authority for runs executed by the *unhardened* bytes — a provenance claim, not a wording nit.
* **FU-4 (P3).** Make `prove-guards.sh` assert (F-6): fail if the export is empty, drop the pipeline
  before `$?`, and compare observed to expected instead of printing "(expect 3)".
* **FU-5 (P3).** T91's F-5 — nothing in CI asserts that exactly one executable rig exists. Endorsed,
  and it would have caught this whole class. T91's F-3 (`pathb/t80/forbidden-sentence.sh` passes
  vacuously on an empty glob) and F-4 (dead `selfcheck.sh` exclusion) are also endorsed as written.

---

## 11. What I checked and found nothing wrong with

So that silence is distinguishable from not looking:

* Every one of the 42 promoted parity vectors: class, seam, threaded and ambient `MathContext`,
  `capture_ref` resolution, `capture_case_id`, and `capture_sha256` recomputed against the bytes on
  disk. All 42 clean.
* All seven Path A capture files and all nine `run-pass3*.sh` recipes, read for any external gate
  dependency. None.
* The full `git diff --name-status main...T91`: 133 A, 2 M, 0 D. No capture bytes edited.
* `PIN.json`, `capabilities.json`, `contract.go` — blob ids equal on both sides.
* The hardened rig `pathb/t36/preconditions.sh` read end to end for `$0`, `BASH_SOURCE`, `dirname`,
  relative paths, and env-overridable pins. Only `CANARY_REQ` is env-driven, which is the intended
  input; `PIN_IMAGE`, `PIN_COMMIT`, `PIN_CANARY_SHA256`, `WANT_*`, `FIN`, `DB`, `BASE`, `AUTH` are
  all unconditional assignments.
* T91's refutation of the driver's brief: main's twin contains exactly **one** sha256
  (`PIN_IMAGE`) and it **is** compared at P1; the two holes the driver named are not in it. T91 was
  right to refuse the framing, and I confirmed it from main's bytes, not from T91's report.
* T91's prediction scoring: PR-9 (21→22) and PR-10 (breach count unchanged at 5) are both scored
  **wrong**, correctly. My C1 and C2 measurements confirm both corrections independently.
* Oracle state before and after my work: containers healthy, uptimes unchanged, no restart.

---

## 12. Honesty register

Marked, as required.

* `[UNVERIFIED]` — **that the pre-fix rig would print the HALF_UP certification on a genuinely
  HALF_EVEN JVM.** I did not attempt it. The pinned canary's `productId 11` does not exist on tenant
  `default`, so the POST returns HTTP 404 and the canary limb is never graded there; establishing it
  needs an oracle **write**, which the brief forbids and which other workers are sharing. T80 and
  T91 hit the same wall and said so; I confirm the wall, not the claim. A2c demonstrates the same
  *harm* on `gerege` without it.
* `[UNVERIFIED]` — **that GNU grep on Linux exhibits the multibyte failure `LC_ALL=C` guards
  against.** No Linux host available. I argue the hardening is right on the ugrep evidence, which I
  did reproduce, plus general caution.
* `[UNVERIFIED — moved here by T107b, correction C-7]` — **that a `ugrep 7.5.0 -I` shim on the
  interactive PATH returns 1 ("absent") on a poisoned transcript that contains the certification
  sentence.** T107 recorded this as `[VERIFIED: my own runs]` in §7. T107b re-ran §7 and found **no
  `ugrep` binary on this host at all** and `grep` = `/usr/bin/grep` = BSD grep 2.6.0-FreeBSD;
  T91's own `prove-guards.sh` likewise falls to its "ugrep is not on PATH here" branch in the
  committed `GUARDS-RED.txt`. The claim has no committed evidence behind it and belongs to T108.
* `[UNVERIFIED]` — **that T80 was actually hitting the ugrep shim.** A hypothesis, offered to T108,
  not a finding.
* `[UNVERIFIED]` — **that no fourth executable copy of the rig exists anywhere.** I re-ran T91's
  content and basename sweeps and agree with its result, and I inherit its stated limits: a
  behavioural re-implementation sharing no token, a copy outside the repo, a copy in a binary or in
  a ref not on `main`.
* `[UNVERIFIED]` — **that any published number under `charges/`, `leapboundary/` or `actualactual/`
  is wrong.** Nothing I ran suggests one is, and §1.4 bounds the doubt; but I re-verified no captured
  value and this review makes no claim about them.
* `[UNVERIFIED]` — **that the 15 wrapper-calling capture drivers still run green end to end.** Like
  T91, I proved the *gate* through `bin/run-preconditions.sh` and through four direct call forms; I
  did not run `capture.sh`, `t46/t48/t51-capture*.sh`, `t55-capture.sh` or `pathb-capture.sh` to
  completion, because they POST loans and would write to the shared oracle.
* The conjunction in §1.4 ("no capture was actually taken through a defeated gate") is an
  **inference** from three verified facts, and I label it as one. The pre-T91 transcripts carry no
  digest line and cannot testify to which bytes were sent.

---

## 13. Verdict

**MICRO-FIX** — apply MF-1, MF-2, MF-3 **and MF-4** (§10, ~10 lines total, mechanical, no number, no
money logic), drive MF-1 and MF-2 red before merge, then merge.
**T107b concurs, on its own measurements.** MF-4 is T107b's addition.

The core of T91 is sound and I re-established it independently rather than reading it back: the
driver's brief was wrong twice, T91 was right to refuse it, the live twin really did certify HALF_UP
over `20925.04` with both operands attacker-supplied, the call-through really is behaviour-preserving
across five real callers and two interpreters, and **no promoted parity vector is touched by any of
it**. The remaining defects are in the tooling that certifies the fix, not in the fix — but they are
the run's own dominant defect class, in the file whose header discusses that class, so they are worth
nine lines and a red run before this lands.

---

## 14. T107b — re-establishment and attestation

*Written by T107b, fire `20260821-080001`. T107's document above was authored by a worker the
harness killed before it signalled done (see the provenance box at the top). Everything in this
section is my own measurement, taken from `main`'s bytes, from source, and from the live reference
oracle (Fineract). I did not confirm a single figure by reading T91's handoff back.*

### 14.1 Method

Two `git archive` exports under `/tmp`, never the repo:

| export | ref | the two twins' sha256 |
|---|---|---|
| `/tmp/t107b/pre` | `main` (`8faee44`) | both `9256b881153d3deab2013cb9d95fae95258b68b398cdf22e5da9a8a416a46b54` |
| `/tmp/t107b/post` | `softhouse/T91-preconditions-copy` | `charges/bin/preconditions.sh` = `7f53f33b…c55cc038`; `preconditions-COPY.sh` = `41548c1b…260ee557` |

`main` still carries blob `e6c1795a172168105d788321a71ee4ca62b73e36` at **both** twin paths today,
so "main's bytes" is the same object T91 forked from (`ab2de89`) — the pre-fix side of every
measurement below is current, not stale.
[VERIFIED T107b: `git rev-parse main:… ab2de89:… softhouse/T91-preconditions-copy:…`; `shasum -a 256`.]

Oracle: **UP** before and after (`{"status":"UP"}`), containers `fineract-fineract-1 Up 2 days
(healthy)` / `fineract-db-1 Up 3 days (healthy)` — same uptimes at start and finish, nothing
restarted, rebuilt or re-seeded. All oracle traffic was the rig's own
`POST /loans?command=calculateLoanSchedule` (pure calculation) plus read-only
`docker exec … psql -c 'select …'`.

### 14.2 The reproduction ledger — six headline claims, all six reproduced

| # | claim | verdict | the command that settled it |
|---|---|---|---|
| **1** | **zero of 42** promoted parity vectors depend on the unhardened gate | **REPRODUCED, and re-derived per vector** | `python3 /tmp/t107b/derive2.py` — 42 `class:parity` in `loanschedule/`, `oracle.seam = path_a_embeddable` on **42/42**, threaded = ambient = `(19, HALF_UP)` on **42/42**, `capture_ref` collapses to the same **7** files with counts **11/2/2/14/3/4/6 = 42**, and all **7** declared `capture_sha256` equal the sha256 of the bytes on disk. Then `grep -rn "preconditions" .softhouse/capture/src/` = 11 hits, **none an invocation**, and `grep -rn "curl\|psql\|localhost:8443\|5432"` over the seven producing recipes = **zero hits**. The Path A chain has no server and no tenant, so the Path B gate is inapplicable, not merely absent. |
| **2** | **20 distinct files, 23 executable call sites** | **REPRODUCED EXACTLY** | `grep -rn 'bin/preconditions\.sh'` + `'run-preconditions\.sh'` over `.softhouse/capture`, hand-partitioned: **5 direct files / 5 sites** (`run-preconditions.sh:9`, `attest.py:90`, `attest-t40.py:91`, `t51-negative.sh:21`, **`leapboundary/bin/t55-negative-tests.sh:52`**) + **15 wrapper files / 18 sites** = 20 / 23. `attest-t40.py:305` is a JSON literal, not a call. `selfcheck.sh:15` is a `grep -v` exclusion. `preconditions-COPY.sh` is invoked by nothing — every hit repo-wide is prose. **T91's omission of `t55-negative-tests.sh:52` is confirmed**, and so is T107's finding that leg N2 survives (§3 row C3). |
| **3** | attack suite **pre-fix 6/13 ADMIT, post-fix 0/13**, both interpreters, 13/13 `sh`/`bash` identical | **REPRODUCED EXACTLY** | `RECIPE=… LABEL=t107b-prefix SH={sh,bash} sh t91/run-attacks.sh` then `sh t91/verdict.sh`. Pre-fix: exit 0 on **A2a, A2c, A4c, A5, A7, A8** under both interpreters, scorer **exit 1**, `EXPECTATIONS NOT MET (6)`. Post-fix: scorer **exit 0**, `ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION`, both interpreters. `sh shell-invariance.sh` → **13 pairs compared, 0 differing**, exit 0, for pre-fix *and* post-fix. **A2c reproduced verbatim**: `PASS  effective rounding mode canary: period-1 interest 20925.04 (= HALF_UP)` / `ALL PRECONDITIONS HOLD — tenant 'gerege' at MathContext(19, HALF_UP), PostgreSQL only.` / `EXIT=0`. |
| **4** | T107's four new attacks — **three admit** | **REPRODUCED, 3 of 4** | **N8a** rig emptied → shim **exit 0**, **zero-byte** output; through `run-preconditions.sh` → `PRECONDITIONS_EXIT=0`, exit 0, zero-byte transcript. **N8b** rig with a syntax error → **exit 1**, fail-closed. **N9** rig replaced by main's unhardened bytes → **exit 0**, A2c reproduces exactly through the post-fix shim. **N10** shim reached via a symlink in a foreign tree → **exit 0**, the attacker's stub rig ran. |
| **5** | conformance **PASS, exit 0, 42 parity, 5,576 cells, 0 invariant violations** | **REPRODUCED, and on two trees** | `bash .softhouse/conformance.sh` on the **T91 branch export** → `VERDICT: PASS (exit 0)`, 42 parity PASS / 0 FAIL, 4 contract-refusal, 1 self-test, 0 refused, 0 inadmissible, 0 harness errors, **5576 cells graded**, 84 ungraded, **0 invariant violations, 0 assertions NOT RUN**; `oracle probe UP`. Same run on the **current-`main` export** → identical figures, exit 0. T91 moves nothing. |
| **6** | `verdict.sh` **passes vacuously on content-free transcripts** | **REPRODUCED EXACTLY** | Ten of the thirteen real post-fix transcripts replaced by the single line `truncated, nothing was ever run` → `sh verdict.sh` prints **`ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION.`** and **exits 0**, with `truncated, nothing was ever run` printed *in the EXIT column* of ten rows. Cause confirmed by reading: `st=$(LC_ALL=C tail -1 "$f" | sed 's/EXIT=//')` is never validated and the ten `BREACH` rows test only `[ "$st" != 0 ]`. |

### 14.3 Everything else I re-ran, and what it showed

* **§3 behaviour-preservation, all five callers, pre and post** (`/tmp/t107b/callers.sh`) —
  **every cell of T107's table reproduced**: C1 21/0/exit 0 → **22**/0/exit 0 (one *added* digest
  PASS line, confirmed by `diff`); C2 16/**5**/exit 1 → 16/**5**/exit 1 (one FAIL line reworded, count
  unchanged); C3 12/9/exit 1 → 12/9/exit 1 with `has no row in fineract_tenants.tenants` present in
  both; C4 16/5/exit 1 → **17**/5/exit 1 (same five breaches — T44's finding survives); C5 identical
  to C1 from `/tmp`.
* **F-4 confirmed by measurement, not by reading.** The shim header's "`bin/t51-negative.sh` … now
  reports one further breach" is **false**: 5 FAIL before, 5 FAIL after. The hardened rig *replaces*
  the "canary NOT run" breach; `diff` shows exactly one reworded line.
* **The zero-file guards are real.** `verdict.sh` over an empty directory → **exit 3**;
  `shell-invariance.sh` over two empty label directories → **exit 3**; rig deleted → shim **exit 2**
  with `PRECONDITIONS NOT RUN. DO NOT CAPTURE — nothing was asserted about the oracle.`, and
  `run-preconditions.sh` propagates `PRECONDITIONS_EXIT=2`.
* **F-6 reproduced** (with correction C-6): `prove-guards.sh` from a non-git export → `git archive`
  fails unchecked, the G-1 GREEN leg prints `exit=0` beside `No such file or directory` because `$?`
  follows a `| tail -1`, and the script **exits 0**. The committed `GUARDS-RED.txt` is genuine — it
  records `exit=2`, `PRECONDITIONS_EXIT=2` and real guard output.
* **§5, the back-fitting audit.** The *ordering* claim ("the table was not set to match an
  observation") is not checkable from artefacts and I do not claim to have checked it. What **is**
  checkable, and what I checked, is that every row is **derivable from the rig's text without
  running anything**, and it is: `CANARY_EXPECT_OVERRIDE` occurs in the hardened rig **only in a
  comment** (line 49) so A4c must be inert; `CANARY_EXPECT_ENV_ATTEMPT` captures the inherited value
  at `:53` one line before the constant overwrites it at `:54`, so A5 must breach even when it
  agrees; `[ ! -f ]` and `shasum -a 256` both follow symlinks, so A7 must be CLEAN; the rig resolves
  no relative path, so A8 must be CLEAN. My own 13 post-fix results met all 13 declared expectations
  under both interpreters — which is an independent check of the table's *content*.
* **§3 mechanism checks.** `grep -n '\$0\|BASH_SOURCE\|dirname\|\.\./' pathb/t36/preconditions.sh` →
  **zero hits** (rc 1). `TENANT=${1:-gerege}` at `:18`. The rig's only two `exit` statements are
  terminal, at `:234` and `:237`. T91's "hole 4" reproduces: `/tmp/t107b/brace.sh` dies under both
  `sh` and `bash` with `PIN_PG_MAJOR_MINOR\xe2: unbound variable`, exit 1.
* **§7 BSD half reproduced 18/18**; **ugrep half not reproducible — see C-7.**
* **§8 invariants.** `git diff <merge-base>..T91 -- .softhouse/vectors/ nexus/ .softhouse/capture/pathb/`
  → **0 lines**. `git diff --name-status` → **133 A, 2 M, 0 D**; the only files outside
  `.softhouse/capture/t91/` are the two twins (M) and the T91 handoff (A) — **no committed capture's
  bytes edited**. Blob ids equal on `main` and the branch for `PIN.json` (`b51595bb…`),
  `capabilities.json` (`882e97bc…`) and `contract.go` (`4bcbafad…`).
* **§9 Go, re-run.** `go version` = `go1.26.6 darwin/arm64`; `go build ./...` **exit 0**;
  `go test ./...` **exit 0** (`loanschedule` ok 8.566s, `loanschedule/conformance` ok 9.158s, two
  packages with no test files); `gofmt -l .` names **exactly**
  `internal/apps/loanschedule/contract/contract.go` — gate **G-3, expected**. No `gofmt -w` was run.
* **§1.4 secondary blast radius, re-checked.** `calc-pmode2-gerege.json` has not been touched since
  `4ebb5ec` (`git log --follow`) and measures `2a6621be…93352154` today, equal to the rig's
  `PIN_CANARY_SHA256`. `charges/out/attested/attestation.json:11` and `attestation-exact.json:11`
  both read `"preconditions_script": "bin/preconditions.sh (copied verbatim from
  pathb/t36/preconditions.sh)"` — the P-21 provenance claim, confirmed verbatim.
  `capabilities.json:53` carries the corrected ACT/ACT promotion condition citing T55-N1 and gate
  G-4, as stated. `AUDIT-CHARGES.md`'s "all three sha256 `9256b881…`" sentence is present and is now
  false for all three — T91's F-1 / T107's FU-3 endorsed. Transcript census corrected at C-4.

### 14.4 What T107b could NOT check

* **The ugrep limb (C-7).** No `ugrep` exists on this host in my environment. Moved to
  `[UNVERIFIED]`; it is T108's question.
* **T107's authoring order** — whether §5's expectation table, or any other passage, was written
  before or after the run it describes. Unknowable from artefacts. I checked derivability instead.
* **Whether the pre-fix rig would print the HALF_UP certification on a genuinely HALF_EVEN JVM.**
  I did not attempt it, for T80's, T91's and T107's reason: `productId 11` does not exist on tenant
  `default`, so the POST is HTTP 404 and the canary limb is never graded there. Establishing it
  needs an oracle **write**, which the brief forbids and which sibling workers share. A2c
  demonstrates the same *harm* on `gerege` without it.
* **GNU grep on Linux.** No Linux host. T107's `[UNVERIFIED]` stands.
* **The 15 wrapper-calling capture drivers end to end.** They POST loans and would write to the
  shared oracle. Like T91 and T107, I proved the *gate* through `bin/run-preconditions.sh` and four
  direct call forms, not the drivers.
* **That no fourth executable copy of the rig exists** anywhere outside the repo, in a binary, or on
  a ref not on `main`. I re-ran the basename and content sweeps and inherit T91's stated limits.
* **Any published number under `charges/`, `leapboundary/` or `actualactual/`.** I re-verified no
  captured money value; §1.4 bounds the doubt and this review makes no claim about them.

### 14.5 T107b's own honesty note

T107's §1.4 inference — "no capture was actually taken through a defeated gate" — remains an
**inference**, and I strengthened its evidence rather than converting it to a proof: the pinned
canary is unchanged since `4ebb5ec`, every committed invoker hard-codes it and sets no
`CANARY_EXPECT`, and 24 of 24 positive transcripts record `21 PASS / 0 FAIL` with the HALF_UP canary
line. The pre-T91 transcripts still carry no digest line and still cannot testify to which bytes were
POSTed. That gap is exactly what T80's P14b closes going forward, and it is why the honest label is
"inference", not "proof". **I recommend no re-capture.**

No money code, no float, no vector, no `PIN.json`, no `capabilities.json` and no contract surface was
touched by T91's diff or by mine. PostgreSQL only; no Oracle Database / MySQL / MariaDB token
anywhere. "Oracle" throughout means the Fineract reference implementation.

**T107b verdict: MICRO-FIX, attested.** Apply MF-1, MF-2, MF-3, MF-4; drive MF-1 and MF-2 red;
merge.
