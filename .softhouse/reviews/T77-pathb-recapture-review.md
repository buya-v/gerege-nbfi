# T77 — independent review of `softhouse/T76-pathb-gerege-recapture`

Reviewer: T77, independent. I did not plan T76 and did not read its conclusions back. Every
material claim below is marked `[VERIFIED: <source>]` or `[UNVERIFIED]`. Where I found nothing, I
say what I checked, so silence is distinguishable from not looking.

Branch reviewed: `softhouse/T76-pathb-gerege-recapture` (`dd06aee`, `3d70a86`, `9dbccf4`).
Handoff read from the branch, not disk. Diff read with three dots.
Pinned Fineract source: `/Users/buv/fineract` @ `426a23544` — **left clean**
[VERIFIED: `git status --porcelain` empty, `git rev-parse --short HEAD` = `426a23544`, after all my work].

---

## VERDICT: **REJECTED**

Scoped, and narrow. **No number in this branch is wrong. Nothing needs reverting.** The captures are
sound, the money re-derives exactly, the promotion refusal is correct and better argued than the
brief asked for, the new invariant is genuine, the scope guard held, and the author's refutation of
its own brief is **true in every particular** — the driver's brief was stale and `.softhouse/RESUME.md`
needs correcting.

The rejection is against **one deliverable**: §3, the precondition hardening, which the handoff
presents as *"TWO REAL HOLES … found and closed"* with four attack transcripts as the evidence.

1. **One of the two "closed" holes is still open.** I re-opened it live with a one-character change
   and drove the rig to `ALL PRECONDITIONS HOLD, exit 0` on a neutered canary — and made the
   strongest assertion in the script certify **HALF_UP on a HALF_EVEN JVM**. (P0-T77-1)
2. **The bigger hole was never attacked at all.** The place T22 P0-4's fail-the-run property
   actually lives is the *caller*, `t36/recapture.sh`, and its abort is **unreachable**. I ran a
   capture on the wrong tenant, past five breached preconditions, to `exit 0`. (P0-T77-2)
3. **The other closure's attack transcript does not run the attack it names**, and its documented
   breach count does not reproduce. (P1-T77-3)

The project's own standard is *"a precondition script is only worth what its negative run proves"*
and *"a precondition that can be talked out of failing is not a precondition"*. Two of the three
defects above are exactly that, in the artefact whose entire purpose is to stop a capture taken at
the wrong arithmetic from entering the vector store. Pattern **P-15** — *the guard's first draft was
a silent false green found only by testing it* — applies verbatim, twice. This is not a ≤10-line
mechanical micro-fix: the corrections must be **re-demonstrated by attack**, not asserted, and one
of them is a control-flow change in a different script.

Everything outside §3 I would have approved without reservation.

---

## 1. The driver-claim check — **the author is right on every point**

The brief asserted T22's P0-3/4/5/6 were still open and that `contract.go` was at REVISION 10. The
author refuted all of it. I checked each claim against the commits and the files myself.

| item | brief said | author said | I find | evidence |
|---|---|---|---|---|
| T22 P0-5 (capture-loop glob, `%{http_code}`) | open | closed by T30 `1b65b1c` | **CLOSED** | commit exists, 2026-08-18T13:09:37Z [VERIFIED: `git log -1 1b65b1c`]. `REPRODUCE.md:116` now writes `-o "out/$outname-raw.json" -w '%{http_code}'` with explicit names; the `-o out/B-$n-*-raw.json` glob is gone [VERIFIED: `REPRODUCE.md:100-130`] |
| T22 P0-3 (attestation sidecar) | open | closed by T36 `78c5bda` | **CLOSED** | commit exists, 2026-08-18T23:13:42+08:00. `t36/attest.py` (19,241 B) and `t36/out/recapture-gerege/attestation.json` are on **main** [VERIFIED: `ls`] |
| T22 P0-4 (fail-the-run preconditions) | open | closed by T36 `c3bbf26` | **CLOSED as to `preconditions.sh`** — but see P0-T77-2, the *caller* never enforced it | commit exists, 2026-08-18T23:08:52+08:00; `t36/preconditions.sh` (11,883 B) on main |
| T22 P0-6 (re-point at `gerege`) | open | closed by T36 `fab040a` + `60c08ad` | **CLOSED** | both commits exist (23:10:15, 23:14:33 +08:00); `t36/out/recapture-gerege/B-0{1..4}` on main |
| T22 P1-14 (B-03/B-04 never re-derived) | "largest remaining hole" | closed by T30, re-checked by T36 | **CLOSED** | `.softhouse/reviews/t30-probe/t30_rederive_b03_b04.py` (16,303 B) + `t30-rederive-output.txt` on main; `t36/t36_rederive_check.py` on main. **And now closed a second, fully independent way — see §2.** |
| `contract.go` revision | REVISION 10 | REVISION **11** | **REVISION 11** | highest marker is `contract.go:50` "REVISION 11"; `:97`, `:715`, `:775`, `:878` are REVISION 10 back-references [VERIFIED: `grep -n "REVISION [0-9]*"`] |
| `PIN.json` / `capabilities.json` | — | `dec1_revision` 12 | **12** | [VERIFIED: `PIN.json:7`, `capabilities.json:3`] |

**`.softhouse/RESUME.md:163-165` is FALSE and should be corrected.** It reads *"T25's parked P0s (T21
P0-2/3/4, P1-8/9/11; T22 P0-3/4/5/6) … They still block vector promotion."* T22's four have been
closed since fire `20260818-230002`, and the actual promotion blocker is now the ratified DEC-1 §4.7
refusal plus the frozen contract's missing component — a different and much smaller thing. The
author's follow-up **F-2 is correct and should be applied.** [VERIFIED: `.softhouse/RESUME.md:163-165`
read directly]

I also note the brief was generated *from* that sentence, which is how a stale line propagated into
a worker task. Pattern already in `patterns.md` ("a handoff is a claim, not a fact"); this is another
instance, and it is the driver's file this time.

### P-9 ordering — **REAL**

* `dd06aee` (`t76/PREDICTION.md`) author date **and** committer date `2026-08-20T17:09:44+08:00`
  = **09:09:44Z** [VERIFIED: `git log -1 --format="%aI %cI"`].
* First oracle contact recorded in the evidence: `attestation.json` `generated_at_utc` /
  `captured_at_utc` = **`2026-08-20T09:12:53Z`** [VERIFIED: `attestation.json`].
* Evidence commit `3d70a86` = 09:21:00Z; handoff `9dbccf4` = 09:23:01Z.

Ordering holds with ~3 minutes of margin, and `dd06aee` is a **parent** of the evidence commit, so
the prediction cannot have been inserted afterwards without rewriting the branch. The prediction
document is specific and falsifiable (digests named in advance, breach counts named in advance),
which is what makes the discipline worth anything here. `[UNVERIFIED]`: git timestamps are
self-reported by the committing process; there is no external notarisation. That caveat applies to
every P-9 registration in this program, not to this one specially.

**P3-T77-6 (trivial).** The handoff says *"First capture: **09:12:11Z** (`attestation.json`)"*. The
file says **09:12:53Z**. Mis-transcription of the author's own evidence; changes nothing.

---

## 2. Money re-derived from the pinned source — **CONFIRMED, exactly**

I did not read T76's conclusions back. I commissioned a **from-source model built without reference
to any existing re-derivation script** in this repo (`t30_rederive_b03_b04.py`, `t36_rederive_check.py`,
`t22_rederive.py`, `t22-probe/rederive.py` were all explicitly off-limits to it), at
`(19, HALF_UP)`, integer minor units, no float, no tolerance — the DAILY cross-year partial-period
arm T22 named.

### B-04 (`FEB_29_PERIOD_ONLY`) and B-03 (`FULL_LEAP_YEAR`) — **0 minor units of disagreement**

All 12 periods of both, on `interestOriginalDue`, `principalOriginalDue`, row total, closing balance
and `daysInPeriod`, plus every plan total. Integer equality, not approximate.

| | B-03 | B-04 | B-04 − B-03 |
|---|---|---|---|
| T22 / T76 claim | 14,465,921 | 14,501,143 | **+35,222** |
| Captured JSON (`totalInterestCharged`, and Σ`interestOriginalDue` independently) | 14,465,921 | 14,501,143 | **+35,222** |
| Independent from-source model | 14,465,921 | 14,501,143 | **+35,222** |

[VERIFIED: independent re-derivation against `ProgressiveEMICalculator.java:1330-1353`, `:1505-1507`,
`:1526-1531`, `:1550-1568`, `:1578-1584`, `:1202-1205,1210`, `:1962`, `:1975`;
`ProgressiveLoanInterestScheduleModel.java:280-296,439-442`; `Money.java:52`; `MoneyHelper.java:35,93`]

Mechanism, independently re-read: period 12 spans 2024-12-01 → 2025-01-01, so for B-03 the partial
arm fires and the rate factor is `0.216 × (30/366 + 1/365)`; for B-04 `FEB_29_PERIOD_ONLY` adds the
"period must contain 29 Feb" conjunct, the arm is suppressed, and period 12 takes the ordinary
`0.216 × 31/365`. The year boundary is **31 December**, not 1 January, because
`isInterestRecognitionOnDisbursementDate` is false [VERIFIED: `:1578-1584`] — worth 17 minor units on
B-03's total on its own. Per-period contribution to the +35,222 is
`[6015, 53, 5100, 4521, 4221, 3638, 3274, 2778, 2188, 1724, 1133, 577]`; period 2, the Feb-29 period,
contributes only **+53**, because both strategies use 366 there and the +53 is a second-order effect
of the opening balance carried in from period 1 — not a day-count difference. Anyone reading "the
Feb-29 strategy" as "the effect lands in the Feb-29 period" has it backwards.

**Discrimination probes** (the model is not accidentally right — each mutation moves it off the
captured value): days-in-year switch disabled → B-04 = 14,465,904 (≠); cross-year arm disabled →
B-03 = 14,465,904 (≠) while **B-04 is unchanged**, confirming B-04 never uses that arm;
`isInterestRecognitionOnDisbursementDate = true` → B-03 = 14,465,904 (≠); precision 8 → both off by
1–2 minor units.

**Two corpus facts that fall out of this and are NOT in T76's handoff — record them:** B-03 and B-04
are **blind** to HALF_UP vs HALF_EVEN, and **blind** to precision 12 vs 19 (they do catch precision 8)
[VERIFIED: model probes]. This is the *mechanistic* explanation of the byte-identity result in §3 —
the identity is not luck, and it is not evidence that these captures were taken at `(19, HALF_UP)`.
The canary is the only thing that carries that, which is why P0-T77-1 matters so much.

### B-01 → B-02 (`installmentAmountInMultiplesOf = 100`) — **CONFIRMED cell by cell, by me**

I recomputed the differential directly from the two captures in exact minor units.

| claim | my measurement | |
|---|---|---|
| 12 of 12 periods move | 12 of 12 | ✅ |
| level installment 11,208,237 → 11,210,000 (**+1,763** on periods 1–11) | exactly | ✅ |
| final installment 11,208,240 → 11,186,622 (**−21,618**) | exactly | ✅ |
| total repayment **−2,225** | 134,498,847 → 134,496,622 | ✅ |
| principal unchanged | 120,000,000 both sides | ✅ |

The whole −2,225 is interest; principal is untouched, so I1 is not disturbed.

**The rounding rule, re-derived from source, confirms T22's correction and refutes the old report
text.** `applyInstallmentAmountInMultiplesOf` → `safeRoundingForEMI` → `Money.roundToMultiplesOf`,
which is `existingVal.divide(inMultiplesOfValue, 0, mode).multiply(inMultiplesOfValue)` — **round to
the NEAREST multiple under the tenant rounding mode**, not "raise to the next multiple" — with the
zero-guard `if (roundedEMI.isZero() && unRoundedEMI.isGreaterThanZero()) return unRoundedEMI;`
[VERIFIED: `Money.java:150-157`, `:164-170`; `ProgressiveEMICalculator.java:1761-1776`].
112,082.37 / 100 = 1120.8237 → scale 0 HALF_UP → 1121 → ×100 = **112,100.00**, the observed B-02
value. Note this capture *alone* cannot separate nearest from round-up (both give 112,100); T22's
round-down probe is what does, and it is still needed.

### Two source findings for the record, neither of them T76's error

* **`ProgressiveEMICalculator.java:1771` calls the 2-argument `Money.roundToMultiplesOf(Money, Integer)`**,
  which delegates to `MoneyHelper.getMathContext()` — the **AMBIENT** context — *not* the threaded
  `mc` [VERIFIED: `Money.java:159-161` vs `:163-170`]. This is precisely the "two overloads of one
  helper are two specifications" hazard already in `patterns.md`, sitting on the exact field B-02
  exercises. It must be in the record **before** B-02 is ever promoted, because a Go port that
  threads one rounding mode everywhere will not reproduce it if the two contexts ever diverge.
* **`EmiAdjustment.shouldBeAdjusted()` compares `|emiDifference| × 100` against
  `originalEmi.copy(lowerHalfOfRelatedPeriods)`**, which via `Money.copy(double)` is the literal
  amount **6.00** — not `EMI × 6` [VERIFIED: `EmiAdjustment.java:31-36`, `Money.java:220-222`]. It
  reads like a percentage test and is not one. With `|diff| = 0.05` the loop breaks on iteration 1
  for both B-03 and B-04, which is why the re-adjust loop is a no-op here. A porting trap worth
  naming in DEC-1's commentary.

---

## 3. The third re-capture, and the tenant — **verified from evidence, not prose**

**Byte-identity: confirmed.** Twelve files, four distinct digests, three independently produced sets
(`out/` = the original HALF_EVEN run, `t36/out/recapture-gerege/`, `t76/out/recapture-gerege/`), all
identical [VERIFIED: `shasum -a 256` over all twelve — `713a3560…`, `9de8757d…`, `892dd6f5…`,
`c80f62b0…`]. **0 minor units moved.**

**Tenant `gerege`, established from the captured evidence:**

* `attest.py` sends `Fineract-Platform-TenantId: %s % TENANT` on **both** the canary (`:186-187`) and
  the four B-0x captures (`:236-237`), from one variable, and passes the same `TENANT` to
  `preconditions.sh` (`:93`) [VERIFIED: source read].
* `attest.py:96-100` writes `pre.stdout + pre.stderr` to the transcript **and aborts on
  `pre.returncode != 0`** — so the committed all-PASS transcript is a genuine gate, on the path T76
  actually used. (Contrast `recapture.sh`, P0-T77-2.)
* The committed transcript names the tenant and its properties: `tenant 'gerege' exists`,
  `timezone_id = Asia/Ulaanbaatar`, `c_configuration.rounding-mode = 4 (HALF_UP)`,
  `running JVM initialized tenant 'gerege' at HALF_UP`, **22 PASS, 0 FAIL**
  [VERIFIED: `t76/out/recapture-gerege/preconditions.txt`].
* The committed canary **response** carries `principalDisbursed 1162502.5` and period-1
  `interestOriginalDue = 20925.05` — the HALF_UP answer to an exact half-cent tie
  [VERIFIED: `t76/out/recapture-gerege/canary-halfcent-raw.json`, parsed].
* The two-set count check corroborates: T36's transcript has **21** PASS lines, T76's has **22** —
  the +1 is exactly T76's new content-pin assertion [VERIFIED: `grep -c "^  PASS"` on both].

So the invocation was `gerege` at HALF_UP. **What the four captures cannot themselves witness** is
the tenant — they are byte-identical across modes, and §2 shows *from source* that they are blind to
the mode. The whole tenant claim therefore rests on the canary, and the canary is what P0-T77-1
breaks. The author's own framing of this ("a property of the inputs, observed not argued") is honest
and I agree with it.

**Byte-identity provenance cross-check.** The author's argument that `out/` really is the HALF_EVEN
original holds: `4b64950` (first Path B captures) landed 2026-08-18T17:10:03+08:00 and `4ebb5ec`
(gerege tenant provisioned) at 17:59:18+08:00 — the originals predate the tenant's existence
[VERIFIED: `git log -1` on both]. `[UNVERIFIED]` by me, as by the author: nobody witnessed the
original run; this is inference from commit order plus T22's contemporaneous evidence.

---

## 4. The precondition attacks — **the rejection lives here**

I attacked the fixed script myself, against the live oracle, from a throwaway extract of the branch
(`git archive` into `/tmp`), never the committed tree.

### ✅ Hole 1 (`CANARY_EXPECT` env-overridable) — **genuinely closed**

Pre-hardening the line was `CANARY_EXPECT=${CANARY_EXPECT:-20925.05}`; it is now the constant
`CANARY_EXPECT=20925.05` [VERIFIED: `preconditions.sh:42`, and the `-`/`+` in the diff]. I ran the
real attack:

```
$ CANARY_EXPECT=20925.04 CANARY_REQ=…/calc-pmode2-gerege.json sh t36/preconditions.sh default
EXIT=1   FAIL x5
```

The override is ignored and the canary still fails. **The hole is closed.** The original hole was
real, and finding it was good work.

### ❌ P1-T77-3 — the attack-B transcript does not run the attack it names

The handoff table and `REPRODUCE.md:200` both say the attack was **`CANARY_EXPECT=20925.04`** →
*"exit 1, **6** breaches; … the override attempt is itself a named breach"*.

The committed transcript shows the breach line
`CANARY_EXPECT_OVERRIDE is set ('20925.04')` — a **different variable**, introduced by T76 itself at
`preconditions.sh:43` (`CANARY_EXPECT_ENV_ATTEMPT=${CANARY_EXPECT_OVERRIDE:-}`), which **did not
exist before the fix** and which nobody attacking the script would ever set. My run of the attack as
documented gives **5** breaches, not 6 [VERIFIED: `/tmp/t77b/attackB-real.txt`, exit 1, 5 FAIL].

The security conclusion is right — the constant is what closes it — but the tripwire watches a name
no attacker uses, and the documented result is **not reproducible as documented**. An attack
transcript whose command differs from its caption is weaker evidence than no transcript, because it
invites the next reader to stop checking. Either make the tripwire watch `CANARY_EXPECT` (it can:
capture the inherited value before the constant assignment) or delete it and correct the caption to
say the constant alone closes the hole.

### ❌❌ P0-T77-1 — hole 2 (tautology canary) is **NOT closed**. Demonstrated live.

`preconditions.sh:165-177` pins the canary "by content" with four `grep -qF` literals and then
**prints** `sha256 $creqsha` — it never **compares** the digest to anything. `grep -qF` is a
substring test, so `'"principal": 1162502.5'` matches `1162502.55`, `1162502.5x`, and so on. The
other three literals are prefix-matchable too (`21.6` ⊂ `21.65`; `12` ⊂ `120`).

I changed one character — principal `1162502.5` → `1162502.55`, which is **not** a half-minor-unit
tie (`× 0.018 = 20925.0459`, which rounds to `20925.05` under *either* mode):

```
$ CANARY_REQ=/tmp/tautology-req.json sh t36/preconditions.sh gerege
  PASS  canary request pinned by content (half-cent tie 1162502.50 x 0.018 = 20925.045), sha256 13ce2f4f…
  PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)
ALL PRECONDITIONS HOLD — tenant 'gerege' at MathContext(19, HALF_UP), PostgreSQL only.
EXIT=0
```

Note the script announces a sha256 of `13ce2f4f…` while the pinned canary is `2a6621be…`, and calls
it pinned.

And the decisive half — the same crafted request against tenant **`default`, which runs HALF_EVEN**:

```
  PASS  canary request pinned by content (half-cent tie 1162502.50 x 0.018 = 20925.045), sha256 9b56535a…
  PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)
```

**The strongest assertion in the rig now certifies HALF_UP on a HALF_EVEN JVM.** That is the exact
failure attack C claims to have closed, reachable by a one-character edit
[VERIFIED: both runs, this fire, against the live oracle].

The fix is small and the script already computes the value: compare `$creqsha` against the pinned
constant `2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154` and `bad` on mismatch.
The literal-grep loop can stay as a human-readable explanation, but it must not be the assertion.
**And the closure must be re-demonstrated by an attack transcript** — including this one — not
asserted, which is the standard T76 correctly set for itself.

### ❌❌ P0-T77-2 — the fail-the-run gate in `t36/recapture.sh` is **unreachable**. Demonstrated live.

This is the larger of the two, and T76 never attacked it: it attacked `preconditions.sh` in
isolation and never attacked the caller, which is where T22 P0-4's property actually has to hold.

`bad()` writes every FAIL to **stderr** [VERIFIED: `preconditions.sh:47`, `printf … >&2`].
`recapture.sh` pipes only **stdout** into `tee`, then greps the tee'd file:

```
27:  CANARY_REQ="…" sh "$D/preconditions.sh" "$TENANT" \
28:    | tee "$O/preconditions.txt"
30:  if [ "$(grep -c '^  FAIL' "$O/preconditions.txt")" != "0" ]; then
31:    echo "ABORT: preconditions breached — nothing captured." >&2
32:    exit 1
33:  fi
```

The FAIL lines never reach that file, so `grep -c` is **always 0** and the `ABORT` at `:31` can never
fire. The pipeline's exit status is discarded too (`set -e` is not in force until `:44`, and the
status of a pipeline is `tee`'s).

Measured, then executed against the live oracle:

```
$ … sh t36/preconditions.sh default >stdout 2>stderr ; echo $?
1
FAIL lines in stdout (what recapture.sh tees): 0
FAIL lines in stderr:                          5

$ TENANT=default sh t36/recapture.sh ; echo $?
  … PRECONDITIONS BREACHED: 5. DO NOT CAPTURE. …
  ### captures — explicit filenames, HTTP status checked, non-200 fails the run
  B-01  HTTP 200 …  B-02  HTTP 200 …  B-03  HTTP 200 …  B-04  HTTP 200 …
0
```

**Five breached preconditions — including a canary that returned HTTP 404, i.e. the mode in force
was never established at all — no ABORT, all four captures taken, exit 0.**
[VERIFIED: `/tmp/t77/recap-default.log`, this fire]

It is worse than a missing gate, for two compounding reasons:

* **`recapture.sh:17` hard-codes `O=$D/out/recapture-gerege` while `:18` makes `TENANT` a variable.**
  My `default` run wrote `default`-tenant output into a directory literally named
  `recapture-gerege`, and silently overwrote the committed evidence set in my working copy. (I hit
  this myself mid-review: a `cat` of what I thought was T36's transcript returned my own run's
  output. I re-extracted a clean copy and every count in this review is from the clean one.)
* **The output is byte-identical**, so no digest, no diff and no downstream check can tell the two
  runs apart. The *only* artefact that would have differed is `preconditions.txt` — and it differs
  by lines that are **silently absent** (17 PASS instead of 22, no FAIL lines at all), which is the
  hardest kind of difference for a reader to notice.

`attest.py` — the path T76 itself used — does it **correctly**: `fh.write(pre.stdout + pre.stderr)`
then `if pre.returncode != 0: … abort` [VERIFIED: `attest.py:96-100`]. So **T76's own run is sound**
and none of its evidence is in doubt. What is defective is the committed recipe that a future fire
will run. `recapture.sh` is not in `REPRODUCE.md`'s "whole recipe" block (which calls `attest.py`),
which reduces the blast radius — but it sits in the same directory, is named `recapture.sh`, and
carries a comment claiming *"Preconditions are FAIL-THE-RUN: no capture is attempted unless every
one holds"* (`recapture.sh:12-13`). That comment is false.

Fix: check the exit status of `preconditions.sh` rather than grepping a stdout-only transcript,
derive `O` from `$TENANT` (`:17`), and correct the false comment at `:12-13`. Prove the fix with a
negative run — `TENANT=default sh t36/recapture.sh` must exit non-zero and capture nothing.

### ✅ Attacks A and D — real, and correctly attributed to T36

Both were already covered pre-T76 (the tenant assertions and the `else bad "canary NOT run"` branch
are unchanged in the diff), and the handoff says so. Attack A's five breaches on `default`
reproduce exactly under my own run [VERIFIED: 5 FAIL, exit 1].

---

## 5. Invariant I7 — **claim upheld in full, reproduced independently**

**The gap was real.** `t22-audit/t22_invariants.py` contains **zero** occurrences of `Original`, and
reads exactly one `Outstanding` field — `principalLoanBalanceOutstanding` at `:94`
[VERIFIED: `grep -c Original` = 0; `grep -n Outstanding`]. The whole `*Original*` / per-period
`*Outstanding*` mirror family is unread by all ten.

**The mutant.** `t76/out/mutation/B-01-mut-totalOriginalDue.json` differs from the clean capture in
exactly one cell: period 12 `totalOriginalDueForPeriod` `112082.4` → `112082.41`, +1 minor unit
[VERIFIED: I diffed the two files field by field — one difference, nothing else].

**I ran both checkers on it myself:**

| | on the mutant | exit |
|---|---|---|
| T22's ten invariants | `RESULT: ALL PASS` / `OVERALL: PASS` | **0** |
| T76's I7 | `**FAIL** … period 12: total columns disagree: totalOriginalDueForPeriod=11208241, totalDueForPeriod=11208240, totalOutstandingForPeriod=11208240, totalInstallmentAmountForPeriod=11208240` | **1** |

And I7 on all four clean captures: `PASS` ×4, exit 0. **A green invariant that can go red — the
requirement is met.** [VERIFIED: both runs, this fire]

The finding is real and it matters for the reason the author gives: the ORIGINAL column is where a
rounded installment must also land, so this is the check B-02 would need if it were ever promoted.
Follow-up **F-3** (adopt I7 into the standard set) is well-founded; I would raise it to P1.

**P3-T77-7.** `t76/out/mutation/` commits `inv-principalDue.txt` and `inv-totalDue.txt` but **no
transcript of I7 failing on the mutant** — the one run a reader most needs. The mutant JSON is
committed, so the claim is checkable (I checked it), but the evidence bundle is incomplete against
its own prose *"FAIL on the mutant"*.

---

## 6. Promotion — **"promote nothing" is the honest answer, not an avoidance**

I checked all four refusals against the frozen contract and `capabilities.json`, and re-checked the
B-01 identity claim myself rather than reading the author's script back.

| refusal | verified? | evidence |
|---|---|---|
| B-02: `InstallmentRoundingMultipleMinor` refused for Run 1 per DEC-1 §4.7 | **YES** | *"InstallmentRoundingMultipleMinor stays in this contract and is refused for Run 1 (DEC-1 section 4.7)"* [VERIFIED: `contract.go:114-116`]; graded-domain predicate `InstallmentRoundingMultipleMinor == 0` [VERIFIED: `contract.go:1130`]; `installment.rounding.multiple.in_graded_domain: false` [VERIFIED: `capabilities.json:40`] |
| …and DEC-1 is ratified, so amendment is a gate | **YES** | *"DEC-1 revision 12 is RATIFIED"*, G-1 **CLOSED** [VERIFIED: `.softhouse/gates.md:231-236`] |
| B-03/B-04: the frozen `GenerateRequest` has no component and pins the input null | **YES** | `daysInYearCustomStrategy = null` is one of six pinned oracle inputs [VERIFIED: `contract.go:1183`], reasoned at `:1246-1265`, ending in the exact sentence the author quotes: *"it becomes a contract question the moment DayCountActualActual enters the graded domain, and not before"* |
| …plus ACT/ACT is itself ungraded | **YES** | `daycount.actual.actual.in_graded_domain: false` [VERIFIED: `capabilities.json:52`]; `REFUSE-01-actual-actual-ungraded.json` exists in the store |
| both capabilities are `exercised` on `path_b_server` (so the *seam* test passes) | **YES** | [VERIFIED: `capabilities.json:138-139`] |
| B-01's product is ACT/ACT, so a truthful transcription lands outside the graded domain | **YES** | `daysInYearType: 1`, `daysInMonthType: 1` [VERIFIED: `req/product-1-baseline.json`]; `ACTUAL(1, …)` [VERIFIED: `fineract-core/…/portfolio/common/domain/DaysInYearType.java:36`] |
| **B-01 ≡ `P-MNT-1M2` cell for cell in minor units** | **YES — I recomputed it** | see below |

**The B-01 identity, checked by me, cell by cell.** I compared the vector's `expect.periods` against
the B-01 capture in exact integer minor units — disbursement row (`principal`, `outstanding`), then
12 periods × (`principalDue`, `interestDue`, `principalLoanBalanceOutstanding`, `totalDueForPeriod`),
then total interest. **0 mismatches out of 51 money cells.** Total interest 14,498,847 both sides.
[VERIFIED: my own comparison script, this fire — not `t76_crosscheck.py`]

So **no promotable vector was discarded on the money side.** B-01 genuinely adds no grading power to
`P-MNT-1M2`, and the rest of the refusal reasoning holds. Promoting any of the four would have
asserted numbers where the ratified contract mandates `ErrNoDiscriminatingVector` — a rejection.
`capabilities.json` is default-deny and untouched; nothing was promoted; gate **G-7** is raised
rather than crossed. **This is the correct call, and it is better argued than the brief required** —
in particular the author found a *third* blocker (the pinned oracle inputs) the brief did not name.

**One datum the author discarded that I would keep.** B-01 runs the **2026** calendar; `P-MNT-1M2`
runs **2024**, a leap year. The money is identical anyway. That is a positive observation — day-count
is inert under `SAME_AS_REPAYMENT_PERIOD`, now witnessed across a leap/non-leap pair on two different
seams — and it is *stronger* than "it kills nothing new" implies. It still cannot be expressed in the
frozen shape (same ACT/ACT problem), so it does not change the verdict; but it belongs in
`PATHB-REPORT.md` as an observation rather than being dropped as a non-promotion. Not a defect;
a P3 opportunity.

The author's `[UNVERIFIED]` on `interestCalculationPeriodType = 1` vs the contract's "left unset" pin
is correctly marked and correctly not guessed at (F-4). I did not test it either.

---

## 7. P1-T77-4 — the attestation sidecar carries three **false** statements about program state

The sidecar T76 generated **this fire** still says:

* `_status`: *"… DEC-1 is at revision **6** and **UNRATIFIED** (gate G-1)."*
* `does_not_license[0]`: *"promotion to the parity vector store (**DEC-1 unratified, gate G-1**)"*
* `_closes`: `["T22 P0-3 …", "T22 P0-4 …", "T22 P0-6 …"]`

DEC-1 is at **revision 12** and is **RATIFIED**; **G-1 is CLOSED** [VERIFIED: `PIN.json:7`,
`capabilities.json:3`, `.softhouse/gates.md:231-236`] — all three are facts T76 asserts correctly
*elsewhere in the same commit*. And `_closes` claims this sidecar closes the very P0 items T76's own
headline finding says T36 closed two fires ago.

The promotion *conclusion* is unaffected (it is refused for other, correct reasons), but the stated
*reason* is wrong, in the one artefact of the set designed to be machine-read and quoted downstream.
T76 edited the **adjacent** `produced_by` block for exactly this class of defect — its own comment
reads *"provenance that names the wrong author is a false record, even when every number in it is
right"* — and left the neighbouring claims stale. This is `patterns.md`'s **corrections leak**:
*an author fixes the section the review named and leaves the sections that restate the same claim.*
Two more env overrides (or reading `PIN.json`) would close it.

---

## 8. Hygiene, scope and the oracle — **all clean**

* **Scope guard: clean.** Every changed path is under `.softhouse/capture/pathb/` or
  `.softhouse/handoff/`. Files outside those two: **0** [VERIFIED: `git diff --name-only main...`].
* **`contract.go` untouched.** Not in the diff. sha256 `0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139`
  on **both** `main` and the branch, and identical to `PIN.json:contract_sha256`
  [VERIFIED: `git show <ref>:… | shasum -a 256`, `PIN.json:9-10`]. `admit.go`'s
  `VerifyContractDigest` also passed inside the conformance run.
* **`gofmt -l nexus/` names exactly `nexus/internal/apps/loanschedule/contract/contract.go`** — the
  expected G-3 Option A state, nothing else unformatted
  [VERIFIED: repo-local toolchain `/Users/buv/gerege-nbfi/.softhouse/toolchain/go/bin/gofmt`;
  note `gofmt` is deliberately not on the default PATH, see `.softhouse/bin/go-env.sh`].
* **No DEC-1, `capabilities.json`, `PIN.json` or vector file altered** [VERIFIED: diff name filter].
* **No shared oracle state mutated.**
  - `fineract-fineract-1` `State.StartedAt` = `2026-08-18T09:51:53.088984338Z`, **identical** to
    `attestation.json:oracle.container_started_at` — no restart [VERIFIED: `docker inspect`].
  - `c_configuration.rounding-mode`: `4` in `fineract_gerege`, `6` in `fineract_default`, both
    enabled — unchanged from what T22/T36/T76 all recorded [VERIFIED: `psql`].
  - `select count(*) from m_loan` in `fineract_gerege` = **0** — nothing persisted [VERIFIED: `psql`].
  - No `INSERT`/`UPDATE`/`DELETE`/`ALTER`/restart/tenant-write appears anywhere in the added lines
    [VERIFIED: `git diff … | grep -inE` over `^\+` lines; every hit is a read-only assertion or a
    transcript string].
  - **My own footprint:** read-only queries, and `POST /loans?command=calculateLoanSchedule` requests
    while attacking the scripts. That endpoint is pure calculation; `m_loan` is still 0 afterwards.
    I wrote nothing to the oracle and restarted nothing.

---

## 9. P2-T77-5 — the `sh` / exit-2 collision is a latent trap, and deserves its own finding

Both of the author's claims reproduce exactly:

```
$ bash .softhouse/conformance.sh        → EXIT 0
    parity 36 PASS / 0 FAIL · refusal 4 PASS · self-test 1 PASS
    4034 graded cells · 0 invariant violations · 0 harness errors
    VERDICT: PASS (exit 0)

$ sh .softhouse/conformance.sh          → EXIT 2
    .softhouse/conformance.sh: line 104: syntax error near unexpected token `<'
```

[VERIFIED: both runs, this fire. `sh` here is GNU bash 3.2.57 in POSIX mode; line 104 is
`done < <(find "$STORE_ROOT" …)`.]

**I rate this worse than an operational note.** Exit 2 is the harness's documented *"the harness, the
corpus or the oracle is unusable"* code (`conformance.sh:13-16`), and `/softhouse-program`'s third
and only remaining stop condition is *"the oracle is unreachable for vector work"*. A CI job, a
wrapper script, or a future agent that invokes it as `sh` therefore emits a signal **indistinguishable
from a legitimate oracle-down park** — and the program driver's correct response to that signal is to
stop doing vector work. A shell-selection typo could quietly stall the migration while every log line
looks like a known, sanctioned condition. The fix is a few lines: re-exec under `bash` when
`$BASH_VERSION` is unset, or reserve a distinct code for "wrong interpreter". Filed against the
harness, **not** against T76 — the author found it and reported it honestly, which is to its credit.

---

## 10. Required changes

**P0 — blocks acceptance**

1. **P0-T77-1. Pin the canary request by digest, not by substring.** `preconditions.sh:165-177`
   computes `$creqsha` and never compares it. Compare it to
   `2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154` and `bad` on mismatch. Then
   **re-run attack C and add my `1162502.55` variant as a fifth transcript** — a closure asserted is
   not a closure, which is the standard this task itself set.
2. **P0-T77-2. Make `t36/recapture.sh` actually fail the run.** Its ABORT at `:30-33` is unreachable
   because `bad()` writes to stderr and `:28` tees only stdout. Test the exit status of
   `preconditions.sh`, not a grep of a stdout-only transcript. Also derive `O` from `$TENANT`
   (`:17` hard-codes `recapture-gerege`), and correct the false comment at `:12-13`. Prove it with a
   negative run — `TENANT=default sh t36/recapture.sh` must exit non-zero and capture nothing.

**P1**

3. **P1-T77-3.** Correct the attack-B caption in the handoff and `REPRODUCE.md:200`, or make the
   tripwire watch `CANARY_EXPECT` itself. As committed, the transcript's command is not the caption's
   command and the breach count (6) does not reproduce (5).
4. **P1-T77-4.** Fix the three stale claims in the T76 attestation sidecar: `_status` (revision 6 /
   UNRATIFIED / G-1), `does_not_license[0]`, and `_closes`. Read the revision from `PIN.json` rather
   than hard-coding it, so it cannot go stale again.
5. **P1-T77-8.** Record the two source findings from §2 in `PATHB-REPORT.md` before B-02 is ever
   promoted: `ProgressiveEMICalculator.java:1771` takes the **ambient** rounding context via the
   2-arg `Money.roundToMultiplesOf`, and `EmiAdjustment.shouldBeAdjusted` compares against the
   literal `6.00`, not `EMI × 6`. Both are live porting traps on the graded path.
6. **P1-T77-9.** Record §2's corpus limits: B-03/B-04 are **blind** to HALF_UP vs HALF_EVEN and to
   precision 12 vs 19. They are strong discriminators of the custom strategy and the cross-year arm
   and nothing else. *"Coverage is what a corpus can distinguish."*
7. Apply the author's **F-2** — correct `.softhouse/RESUME.md:163-165`. It is the sentence that
   produced this stale brief. (Driver task, not the author's.)
8. Raise the author's **F-3** (adopt I7 into the standard invariant set) from P2 to **P1**. A whole
   column family has been ungraded for the life of the program.
9. The author's **F-1** stands and I confirm it: `.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh`
   still carries the pre-hardening `CANARY_EXPECT` hole. Add: it will also carry the P0-T77-1
   substring weakness once fixed, so replace the copy with a call to the original rather than
   patching two files forever.

**P2 / P3**

10. **P2-T77-5.** Guard `conformance.sh` against being invoked with a non-bash shell (§9).
11. **P3-T77-6.** Handoff says first capture 09:12:11Z; `attestation.json` says 09:12:53Z.
12. **P3-T77-7.** Commit the I7-on-mutant transcript alongside the other two.
13. **P3.** Record the B-01 / `P-MNT-1M2` **calendar** difference (2026 vs 2024 leap) as a positive
    observation about day-count inertness under `SAME_AS_REPAYMENT_PERIOD`, rather than dropping it
    with the non-promotion.

---

## What I checked and found nothing wrong with

So that silence is distinguishable from not looking: the four capture digests across three sets;
the tenant/timezone/rounding-mode/precision/PostgreSQL-version attestation fields against the live
server; the absence of any Oracle Database, MySQL or MariaDB artefact in the changed files; the
absence of any float in the added Python (all three scripts use `parse_float=Decimal` with an
exact `×100` integrality assertion — I read them, and I re-ran two of them); `graded_against`,
`capabilities_required` and the default-deny posture of `capabilities.json`; the ten T22 invariants
on all four T76 captures; `contract.go` byte-identity three ways; and the pinned Fineract checkout,
which is clean at `426a23544` after everything I ran.

**The single most useful thing this branch did** was refuse its own brief and register the refusal
before touching the oracle. That is P-16 working, and it is why the driver now knows `RESUME.md` is
lying. **The single most important thing it missed** is that it attacked the guard and not the gate:
`preconditions.sh` was hardened while `recapture.sh`, which is where "fail the run" actually has to
happen, would have captured on the wrong tenant at the wrong rounding mode and exited 0 — and
produced bytes nobody downstream could distinguish.
