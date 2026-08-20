# T87 — independent review of T82 (`softhouse/T82-pass3i-defects`, commits `402a1da`, `0101fbb`)

**Reviewer:** T87, run `2026-08-17-run1-harness-schedule-poc`, branch `softhouse/T87-review-t82`.
**Target:** T82's fixes for the seven follow-up defects raised by
`.softhouse/reviews/T75-pathA-multiplesof-review.md`.
**Needed no oracle for the guard work.** No container was started, restarted, rebuilt or re-seeded;
no database connection; no tenant write. `.softhouse/conformance.sh` was run once and its only
outbound call is a read-only 10-second health probe. `.softhouse/capture/pathb/` and
`.softhouse/capture/t83-nonamortizing/` were never opened.

> "The oracle" here is the **Fineract reference implementation**. **Oracle Database** is prohibited
> in this program and appears nowhere in this work. PostgreSQL remains the only permitted engine.

**Method.** I extracted the T82 branch to a scratch tree (`git archive` → `/tmp/t82tree`), extracted
`main`'s bytes of the three edited scripts separately, and built **my own** mutations with my own
scripts rather than re-using `T82-guard-proofs/mutate.py`. Where T82 reconstructed the pre-T82 code
from a string literal, I drove the **actual `main` bytes** instead. Every guard below was made red by
me, with an input I chose, on cases T82 did not use.

---

## VERDICT: **REJECTED**

Four numbered findings, all independently checkable. **None of them is a defect in the shipped guard
logic** — I confirmed every guard T82 rewrote is live, and I additionally confirmed live two guards
T82 never exercised. The rejection is on **evidence integrity**:

* T82's one substantive green control for D-2 **has zero discriminating power**, and the harness it
  committed **prints a false conclusion** which the handoff then repeats as established (F-1);
* the single D-2 guard that actually cures the `or 0` defect is **never exercised** by the rig (F-2);
* the assigned defect **A-1 survives uncorrected in a fourth location**, inside a file T82 edited
  twice, while the handoff claims its grep sweep is the reason this is not a P-12 (F-3).

F-3 and F-4 both turn on a number, so **MICRO-FIX is not available** for them under this task's own
rule ("never a number"). All four are cheap to fix; the code needs no change.

---

## PART 1 — everything I confirmed (the bulk of T82 is sound)

### Guards I drove RED myself

| # | guard | my constructed input | result |
|---|---|---|---|
| 1 | precondition 17, unregistered id | added `T87-REVIEWER-FORGOT-THE-TABLE` to `EXPECTED_IDS` **and** to the capture (clone of `T74-C4-DP0-CUR7`, a different donor from T82's), left `CASE_PRECISION` alone | **exit 1** — `no expected MathContext precision registered for ['T87-REVIEWER-FORGOT-THE-TABLE']` |
| 1c | **counterproof, on `main`'s REAL bytes** | the *same* mutated capture through `git show main:.../run-pass3i.sh` (not T82's `restore-old-table` reconstruction) | **exit 0** — `validation OK — 37 captures`, all nine calibrations green |
| 2 | precondition 17, stale entry | inserted `'T87-GHOST-CASE': 19` into `CASE_PRECISION` | **exit 1** — `CASE_PRECISION registers ['T87-GHOST-CASE'], which this run does not capture` |
| 3 | precondition 17, per-case | `T74-D2-DP0-SMALL-INST1000` made to report precision 12 (T82 used `T74-E-P4`) | **exit 1** — `must run at precision 19, got 12` |
| 4 | precondition 18, direction (a) | registered `T74-C5-DP0-CUR1000` at 12 and ran it at 12 (T82 used `T74-A0-DP0-NONE`) | **exit 1** — named/observed probe sets disagree |
| 5 | precondition 18, **direction (b), which T82 never tried** | registered `T74-E-P59-p12` at 19 and ran it at 19 — a `-p12` id that does *not* run below 19 | **exit 1** — same guard, opposite direction |
| 6 | `build-counterfactuals.py` rounding mode | **all six pairs**, both arms → `HALF_EVEN` (ordinal 6); repeated at `HALF_DOWN` | **exit 1** — `... is not the ratified HALF_UP rounding mode` |
| 7 | `T74-promote-vectors.py` D-2, **payable row with absent `periodNumber`** — the case the old `or 0` silently wrote a 0 for, and the case T82's rig never runs | deleted `periodNumber` from payable row 1 of all six group-E cases | **exit 1** — `period[1] is a payable REPAYMENT row with NO periodNumber` |
| 7c | counterproof for 7 | same capture through `main`'s promotion script | **exit 0** — 6 vectors promoted, no complaint |
| 8 | D-2, non-payable row that *carries* a `periodNumber` — also never run by the rig | set `periodNumber: 0` on every `DISBURSEMENT` row | **exit 1** — `period[0] is a DISBURSEMENT row but carries periodNumber 0` |
| 9 | (not T82's guard; confirms T92) applied the T92 correction to `Capture3i.java` in a scratch root | | **exit 1** — `harness sha mismatch host 2a7bfb37… vs container 772f9226…` |

All [VERIFIED: my runs, this session].

### E-1 — the hand-written table is correct, and correct in both directions

Parsed `EXPECTED_IDS` and the `CASE_PRECISION` literal out of the shipped script and cross-checked
against the capture:

```
EXPECTED_IDS count: 36
CASE_PRECISION literal lines: 36   unique keys: 36
missing from table: []      stale in table: []
capture case count: 36      capture id order == EXPECTED_IDS order: True
table vs observed mismatches: {}
ids ending -p12:      [P340-p12, P4-p12, P426-p12, P59-p12, P6940-p12, P72-p12]
table entries at 12:  P-CAL + those six
observed below 19:    P-CAL + those six
```

**A hand-written table is a new place to be wrong, and this one is not wrong.** No duplicate key, no
missing id, no stale id, and every registered precision equals the precision that case actually ran
at in `capture-prod3i-raw.json`. [VERIFIED: `/tmp/t87-check-table.py`, my script]

### E-3 — "dead in both directions" is correct, and I checked it against `main`, not against prose

* **Both arms sharing a non-ratified mode → old code passes.** `main`'s
  `build-counterfactuals.py` on my all-six-pairs `HALF_EVEN` capture: **exit 0**, and it printed a
  complete, confident counterfactual report. The guard was blind. [VERIFIED]
* **Arms differing → the mode guard is never reached.** `main`'s code on my one-arm `HALF_EVEN`
  capture: **exit 1**, but with `T74-E-P426 vs T74-E-P426-p12 differ in more than the precision:
  ['mathContextRoundingMode', 'mathContextRoundingModeOrdinal']` — the `varying` check at
  `build-counterfactuals.py:72-75`, two checks earlier, exactly as T82 says. [VERIFIED]
* **The legitimate capture is unaffected, and by more than T82 claimed.** The new code exits 0 with
  the six divergent-cell counts unchanged (23, 27, 2, 25, 39, 18 of 146) — and the regenerated report
  is **byte-identical to the committed
  `.softhouse/capture/t74-multiplesof/out/t74-counterfactuals-pass3i.json`**, and byte-identical to
  what `main`'s code produces from the same input. [VERIFIED: `cmp` clean, both ways]

### E-2 — removed halves genuinely dead, kept half genuinely live

`parity_ids` is defined one line above as `... and c['id'] not in probe_ids`, so
`set(probe_ids) & set(parity_ids)` is empty for **every** `caps`. Beyond the structural argument I
hammered the two verbatim comprehensions with **360,435 synthetic capture lists** (randomised plus an
exhaustive sweep over all lists of length ≤ 3 drawn from a pathological id/precision alphabet
including duplicate ids and calibration ids): **0** inputs made either removed check fire.
[VERIFIED: `/tmp/t87-e2-dead.py`] The kept half I drove red in **both** directions (rows 4 and 5
above). `parity_ids` is still consumed by the sidecar (`parityCandidateCaptureIds`), so the deletion
left no dead variable.

### The guard-proof rig — slicing is faithful

* `run-pass3i.sh` contains **exactly one** `<<'PY'` (line 266) and **exactly one** `^PY$` (line 708),
  so the anchors are unambiguous.
* I reproduced the slice independently with `sed -n '267,707p'`: sha256
  `ada3a43988d544dc620c18b9e1b8aa4e2b04e2170f2f8dad3fd32d4255d57269`, **identical to the sha the
  driver printed** on its own extraction. It really is the shipping bytes, and the heredoc is
  single-quoted so no shell expansion intervenes. [VERIFIED]
* The 21 argv the driver passes match the shipping invocation
  (`run-pass3i.sh:264-266`) position for position against the unpack at `:269-271`
  (`sys.argv[1:22]`). [VERIFIED]
* I re-ran `prove-guards-go-red.sh` end to end: **16 as expected, 0 not as expected, exit 0**, and my
  transcript is identical to the committed `TRANSCRIPT.txt` modulo absolute paths and `mktemp`
  suffixes. [VERIFIED]
* **Honest limitation, not a finding:** the driver feeds the *pinned* `EXPECTED_IMAGE_ID` /
  `EXPECTED_FINERACT_COMMIT` / `EXPECTED_REF*_SHA` where the real script feeds the *measured* actuals,
  so the checks at `:312-320` compare a literal against the capture rather than against a live
  measurement. The harness-sha check at `:321` is **not** affected — it is measured with `shasum` off
  the tree, which is how I was able to drive row 9 red.

### D-1 / D-2 — no float, and the refusals are real

`git diff main...softhouse/T82-pass3i-defects | grep '^+' | grep -E 'float\('` returns **3** hits and
**all three are prose saying "never by `float()`"** (`T82.md:1380`, `T82.md:1544`,
`T74-promote-vectors.py`'s comment). No float call, no float literal, no `double`, no division by a
float anywhere in the added code. [VERIFIED]

I exercised `down_payment_percentage()` and `day_count()` directly:

```
enabled=False pct='0' / '0.00' / '-0.0' / '+0' / 0   -> {'numerator': 0, 'denominator': 1}
enabled=False pct='0.001' / '25' / '' / None / '0e0' -> REFUSED
enabled=True  pct='0'                                -> REFUSED
enabled=None  pct='0'   enabled=0 pct='0'            -> REFUSED
(DAYS_30,DAYS_360) -> FIXED_30_360   (ACTUAL,ACTUAL) -> ACTUAL_ACTUAL
(ACTUAL,DAYS_365) / custom strategy set / missing key -> REFUSED
```

Zero is decided by exact string inspection; every ambiguous input refuses. The
`contract.go:359-360` mapping is transcribed correctly [VERIFIED: I read `contract.go:350-366`], and
`contract.go:1509-1510` does state a disbursement row's `InstallmentNumber` is 0 because it is not
payable [VERIFIED: read].

A legitimate `0` survives un-withdrawn: payable row 1 `installment_number = 0` with
`unrecorded_fields = []`, while the `DISBURSEMENT` row carries `installment_number = 0` with
`unrecorded_fields = ['installment_number', 'interest_minor']`. [VERIFIED — but see **F-1**: this is
*also* true of the pre-T82 code, so it does not prove what T82 says it proves.]

### C-4 — 21, counted a fourth way

T82 counted three ways (enumeration, `PIN.json` today, `git show d4bfff1`). My fourth route is
structural and uses neither:

* `EXPECTED_IDS` = 36 = **9** calibrations (`P-CAL*`) + **27** `T74-*` cases;
* of those 27, exactly **6** are the capture case ids named in the provenance of a promoted vector
  (`T74-E-P4, P59, P72, P340, P426, P6940`);
* **27 − 6 = 21** never-promotable, and `PIN.json`'s `never_promotable_capture_case_ids` carries
  **exactly 21** `T74-` entries, all of which are in `EXPECTED_IDS`, and the only `T74-` ids not on
  the list are those same six.

[VERIFIED: `/tmp/t87-c4.py`]

### A-1 — the corrected census is right

Recounted mechanically over all 46 files by resolving `provenance.capture_ref` myself:

```
capture-prod3b 11 | 3c 2 | 3d 2 | 3e 14 | 3f 3 | 3g 4 | 3i 6 | (no capture_ref) 4
total 46 = 42 parity + 4 contract-refusal
```

Exactly T82's corrected table. [VERIFIED: `/tmp/t87-census.py`]

### Invariants

| check | result |
|---|---|
| `git diff --stat main...softhouse/T82-pass3i-defects -- .softhouse/vectors/` | **empty** [VERIFIED] |
| same for `nexus/` | **empty** [VERIFIED] |
| same for `.softhouse/capture/pathb/` and `.softhouse/capture/t83-nonamortizing/` | **empty** [VERIFIED] |
| re-run **modified** `T74-promote-vectors.py` against the real store | all **46** vector files byte-identical (sha256 list unchanged) [VERIFIED] |
| re-run **`main`'s** promotion script | also byte-identical — the D-1/D-2 derivations agree with the literals they replaced [VERIFIED] |
| `bash .softhouse/conformance.sh` | **exit 0**, `parity vectors PASS 42 FAIL 0`, `5576 graded`, 0 invariant violations, 0 assertions NOT RUN, oracle probe UP [VERIFIED: my run] |
| `gofmt -l` | names **exactly** `nexus/internal/apps/loanschedule/contract/contract.go` and nothing else [VERIFIED: via `.softhouse/bin/go-env.sh`'s toolchain] |
| `sh -n run-pass3i.sh`, `bash -n` both proof scripts, `py_compile` all four Python files | clean [VERIFIED] |

### T92 / T93 — correctly characterised

* **T93** (`.softhouse/vectors/README.md:580`, "all **36** promoted parity vectors withdraw exactly
  those two cells"). Only the number is stale: **42 of 42** parity vectors withdraw exactly
  `{installment_number, interest_minor}` on every `DISBURSEMENT` row, and the 4 refusal vectors carry
  no `expect.periods`. [VERIFIED: `/tmp/t87-readme580.py`]
* **T92** (`Capture3i.java:442`). The "an EXHAUSTIVE per-id table rather than a defaulted lookup"
  string **is** baked into `capture-prod3i-raw.json` [VERIFIED: grepped the capture]. T82 was right
  not to edit it, and I proved *why* rather than accepting the reasoning: I applied the T92 wording
  fix to `Capture3i.java` in a scratch root and the precondition block went **red** on the committed
  capture — `RUN FAILED: harness sha mismatch host 2a7bfb37… vs container 772f9226…`. A capture whose
  text no longer matches what the oracle emitted is no longer a capture, and the harness enforces
  that mechanically. [VERIFIED]

---

## PART 2 — findings

### F-1 (P1) — the D-2 "legitimate zero" GREEN CONTROL has zero discriminating power, and the committed harness PRINTS A FALSE CONCLUSION

`prove-guards-go-red.sh:174` runs `prove-promote-guards.py … period-number-zero` and expects exit 0.
On success `prove-promote-guards.py:134` prints, and `TRANSCRIPT.txt:205` records:

> `-> a legitimate 0 and an absent value are DISTINGUISHED. `p.get("periodNumber") or 0` could not do this.`

and `T82.md:247-255` states it as established:

> **`p.get("periodNumber") or 0` cannot distinguish those two.**

**That is false.** In `main`'s promotion script the *value* and the *withdrawal* were decided by two
different expressions:

```python
# .softhouse/handoff/T74-promote-vectors.py @ main
255:    "installment_number": p.get("periodNumber") or 0,
260:    if p.get("periodNumber") is None:
261:        unrecorded.append("installment_number")
```

The `or` collapsed the value, but line 260 tested `is None` **separately**, so a recorded `0` was
already transcribed as `0` and already **not** withdrawn. The emitted vector distinguished the two
cases before T82 touched it.

**Demonstrated, not argued.** I ran the identical `period-number-zero` mutation through both the T82
script and `main`'s script and compared the generated vectors' `expect.periods`:

```
mutation period-number-zero   expect.periods identical between T82 and pre-T82 code: 6, differing: 0
```

and the control's own assertion block passes verbatim against `main`'s script:

```
$ cd <root with main's promote script>
$ python3 …/prove-promote-guards.py <root> period-number-zero
  payable row 1 installment_number = 0   unrecorded_fields = []
  DISBURSEMENT  installment_number = 0   unrecorded_fields = ['installment_number', 'interest_minor']
  -> a legitimate 0 and an absent value are DISTINGUISHED. `p.get("periodNumber") or 0` could not do this.
EXIT=0
```

So this is not a control. It is a case that passes on both codebases, wearing a control's badge and
emitting an untrue sentence about the code it is supposed to discriminate against. That is the
"replacement that is true but insufficient" shape the brief names, and it is the honesty-rule class of
defect: a `[VERIFIED]` claim that the evidence does not support.

**Reproduce:** `/tmp/t87-zero-control.py` (committed reasoning above; the mutation is three lines).
**Fix:** either delete the false sentence from `prove-promote-guards.py:80,134`, `TRANSCRIPT.txt` and
`T82.md:247-255` and re-label the case a *regression control* (what it actually is), or replace it
with F-2's mutation, which is a real control. Prose only.

### F-2 (P1) — the one D-2 guard that actually cures the `or 0` defect is never exercised

`prove-promote-guards.py`'s `MODES` are `day-count, down-payment, down-payment-enabled,
repayment-every-absent, repayment-every-conflict, period-number-zero, period-number-bad`. **None**
removes `periodNumber` from a *payable* row — and that is precisely the case T82's own handoff calls
out: *"payable row, absent → error (this is the case the old `or 0` wrote a silent `0` for)"*. The
headline D-2 guard therefore ships undemonstrated. Nor is the non-payable-row-carries-a-number
direction exercised.

Both are live; I proved it (rows 7, 7c and 8 above), including the counterproof that `main`'s script
accepts the same capture at **exit 0** and promotes six vectors from it. But T82 did not, and by this
task's own standard — *a guard you cannot make go red is still dead* — a guard nobody tried is a guard
nobody has evidence for. The rig makes this cheap: two more `MODES` entries.

### F-3 (P1) — a FOURTH copy of the census, uncorrected, in a file T82 edited twice

`.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T74.md:225-238` restates the census in full:

> I resolved `provenance.capture_ref` for every file in `.softhouse/vectors/loanschedule/`:
> | `capture-prod3b-raw.json` | 11 | … | `capture-prod3g-raw.json` | 4 | *(none — contract-refusal)* | 4 |
> **36 parity + 4 refusal.**

`capture-prod3i-raw.json` (6) is missing, exactly as it was missing from the two reports and the
banner. This is **present tense about the current store**, not a historical transcript — and the same
file says *"Store: 36 → 42 parity vectors"* **21 lines earlier**, at `T74.md:217`, so the document
contradicts itself. T82 edited this file twice (line 45 for C-4, and a correction block at line
353-365) and passed over the table both times.

**Why the sweep missed it, which is the transferable lesson.** Both of T82's regexes were tuned to the
*banner's* phrasing:

* sweep 1 required `36 … (parity|promoted|golden) … vector`; T74.md says `36 parity + 4 refusal.`
  with no following "vector" — **no match**;
* sweep 3 searched for the parenthesised form `` `capture-prod3b-raw.json` (11) ``; T74.md renders the
  same census as a **markdown table row** `| `capture-prod3b-raw.json` | 11 |` — **no match**.

Same claim, different rendering, invisible to a sweep written against one rendering. That is P-12
recurring inside the very task assigned to close P-12, and the handoff's claim that *"the sweep is why
this handoff is not that"* does not hold.

**My own sweep**, run over `.softhouse/capture`, `.softhouse/handoff`, `.softhouse/reviews`,
`.softhouse/vectors`, `docs`, `CLAUDE.md` for `36 parity|36 promoted|all 36 |the 36 |36 vectors|36/36`,
returned 63 hits. Every other hit is a genuine historical transcript of an earlier fire (T13, T64,
T68, T71, the driver re-derivations, `program.json`/`tasks.json`/`gates.md`/`patterns.md` records), a
loan *shape* (`36 × 16.8 %`), or a count of something else (36 builder fields, 36 periods).
`T74.md:238` is the **only** remaining present-tense restatement besides the already-registered T93.
[VERIFIED: `/tmp/t87s/sweep36.txt`]

**Fix:** either correct the table and the "36 parity + 4 refusal" sentence, or add a correction block
under it as T82 did at `T74.md:353`. It changes a number, so it is not a micro-fix.

### F-4 (P2) — "Five of the sixteen are deliberate green controls" — there are four

`T82.md:380`. `prove-guards-go-red.sh` has **16** `expect` calls: **4** `expect 0` (lines 63, 86, 141,
174) and **12** `expect 1`. My transcript confirms `expecting exit 0` occurs 4 times and
`expecting exit 1` 12 times. The handoff's own parenthetical enumerates only four items ("the
unmutated capture, the legitimate counterfactual, the legitimate-zero promotion, and the old-table
counterproof"). A miscount in the handoff of a task whose C-4 defect was a miscount. [VERIFIED]

(The related claim at `T82.md:28,300` — "five new falsification rows added to `README-pass3i.md`" — is
**correct**; the added table has 5 rows.)

### N-1 (P2, note only) — one absence not distinguished from a value

`day_count()` reads `i.get("daysInYearCustomStrategy")`, so an **absent key** and an explicit `null`
are indistinguishable — the same "absence is not a value" doctrine D-2 enforces two functions below.
It does not bite today: the key is present with an explicit `null` in **36/36** cases. Worth a line if
the file is opened again. [VERIFIED]

### Observation, not a finding — `repaymentEvery` is absent from every case

`repaymentEvery` is present in **0/36** cases and `repaymentFrequency` in **36/36** (value `1`). So
`main`'s `i.get("repaymentEvery", i.get("repaymentFrequency"))` was taking the *fallback* branch on
every single case — the fallback was load-bearing, not decorative. The new `repayment_every()` reads
both keys and returns the same `1`, which is why the vectors are byte-identical. T82's description is
accurate; the fact is worth recording because it means the "two silent fallbacks" were the only thing
producing the value. [VERIFIED]

---

## What would have made this an APPROVAL

Deleting the false sentence at `prove-promote-guards.py:134`, adding a `payable-absent` mode to
`MODES`, and correcting or annotating `T74.md:238`. All three are minutes of work; none touches a
guard predicate and none touches a vector.

## What I did NOT verify

* **That the corrected `run-pass3i.sh` produces an identical capture end to end.** I ran the
  precondition block, byte-for-byte extracted, against committed artefacts. I did not run docker, by
  design. `[UNVERIFIED]`
* **That preconditions 1–16 of `run-pass3i.sh` are falsifiable.** T82's F-4 already registers this and
  I did not attempt it. `[UNVERIFIED]`
* **That `NON_PAYABLE_ROW_TYPES = {"DISBURSEMENT"}` is complete for row kinds no capture in this store
  carries.** Same limit T82 records; the failure direction is a loud refusal, which is the right one.
  `[UNVERIFIED]`
