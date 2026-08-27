# T101 — independent review of T100 (`softhouse/T100-g8-two-families`)

Reviewer: T101, spawned fresh with no planning context, in worktree
`/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0aed3828d5f8f61a` (forked from `main`),
branch `softhouse/T101-review-t100`.

Artefact under review: the G-8 section of `.softhouse/gates.md` on
`softhouse/T100-g8-two-families` (gates.md lines **894–1311**), plus the handoff
`.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T100.md` and the evidence under
`.softhouse/capture/t100-g8-rescope/`.

Reference oracle (Fineract) pinned checkout `/Users/buv/fineract` at `426a23544` (clean tree,
verified). I read the oracle source and re-graded through the in-JVM/in-process seams only.
**I started nothing, restarted nothing, rebuilt nothing, and wrote nothing to any container or to
the oracle database.** Every re-measurement below ran either against committed capture bytes or
against the Go port in a throw-away `/tmp` tree.

---

## VERDICT: **REJECTED**

Narrowly. **Three sentences**, all in the write-up, none in the measurement. The measurement itself
is sound: I re-derived every load-bearing number independently and, in two places, over a **wider**
set of cells than T100 measured, and it held. But the brief's standard is mechanical — *any claim
that silently generalises from one family to both, or from the swept grid to the graded domain, is
a rejection* — and one sentence asserts family A at a rate where family A does not exist,
contradicting the document's own discriminator table nine lines earlier. That is P-23 recurring
inside the artefact written to cure P-23, and it is caused by exactly the leak `patterns.md`
already names: *the table was corrected and the prose restatement of the same claim was not.*

The other two are a wrong multiplier in the bound section (the section the product owner reads to
size the risk) and a caveat that mis-describes its own exit codes. All three corrections are
numbers, so none is eligible for MICRO-FIX under this brief's rule ("never a number").

**Separately and more urgently: there is a merge hazard on `main` that this branch cannot see and
must not be merged without fixing** — see M-1. `main`'s current G-8 UPDATE block misattributes the
family-**B** exemption result to family **A**, i.e. it states the single most decision-relevant
sentence in the gate backwards, and T100's branch (forked earlier) neither supersedes nor deletes
it.

---

## 1. Mechanical checks (item 8) — ALL PASS

| check | result |
|---|---|
| `git diff main...softhouse/T100-g8-two-families -- .softhouse/vectors/ nexus/` | **EMPTY** [VERIFIED] |
| branch's `.softhouse/vectors` tree vs merge-base's | **identical** (`ae990ff3402187c65ce975f9e750752256852ca2`) — nothing promoted [VERIFIED] |
| branch's `nexus` tree vs merge-base's | **identical** (`06466e75fc964ace7a363556f963f423b17a4532`) — no port change [VERIFIED] |
| `PIN.json`, `capabilities.json` | untouched (inside the identical vectors tree) [VERIFIED] |
| `contract.go` byte-identity | blob `4bcbafaddd6014650375a315d346dbba284d5bb5` on **both** `main` and the branch [VERIFIED] |
| `gofmt -l ./nexus` | names **exactly** `nexus/internal/apps/loanschedule/contract/contract.go` — the expected G-3 state, contract.go never gofmt'd [VERIFIED] |
| files changed outside `.softhouse/{capture,reviews,handoff}/` | **only** `.softhouse/gates.md` [VERIFIED] |
| `bash .softhouse/conformance.sh` (bash, never `sh`) | **VERDICT PASS, exit 0, 42 parity vectors PASS / 0 FAIL, 5576 graded cells, 0 invariant violations** — unmoved [VERIFIED: my own run, `/tmp/t101-conf.log:132,138,141,144`] |
| float in T100's added sources | two uses, both disclosed in comments, both display-only (`float(gap)` for an order-of-magnitude print; `float()` to sort rate *labels*). No money value converted. My own re-derivations used exact `Fraction`/integer minor units throughout and reproduced T100's numbers, which independently confirms no float contaminated a conclusion. [VERIFIED] |

Note: `git diff main...branch` is a **merge-base** diff. `main` has independently advanced
`nexus/internal/apps/loanschedule/emi.go` (+678 lines) and added `.softhouse/vectors/README.md`
since the fork. **My re-grades below therefore ran against `main`'s CURRENT port, not T100's base
port, and reproduced T100's cell counts and diffs exactly** — so the finding survives the newer
port. That is a stronger result than T100 claimed.

---

## 2. Provenance and prediction discipline (item 10) — PASS

- **`34e973f` ("T100 PREDICTION, registered before the probe is built") is a STRICT ancestor of the
  evidence commit `6b0c1da`.** `git merge-base --is-ancestor 34e973f 6b0c1da` → true; the two SHAs
  differ. [VERIFIED]
- `PREDICTION.md` and `prediction.json` appear **once** in the branch history — in `34e973f` — and
  were never amended afterwards. [VERIFIED: `git log <branch> -- <paths>`]
- The probe itself (`src/CaptureT100.java`, `src/build_harness.py`, `src/run-t100.sh`,
  `out/capture-t100-raw.json`) appears **only** in the later commit `6b0c1da`. The only source file
  present in both is `closed_form_check.py`, and its only change in `6b0c1da` is a **+5-line comment**
  explaining the single display `float`. No logic changed. [VERIFIED: `git show 6b0c1da -- <file>`]
- **All 15 registered predictions held, and the capture contains exactly those 15 non-calibration
  cases — no unregistered case slipped in.** I re-evaluated every prediction (fail/clean *and*
  family) against the capture myself: 15/15 held, 0 refuted, 0 unpredicted cases. [VERIFIED: my
  `/tmp/t101/checkpred.py` over `prediction.json` × `out/capture-t100-raw.json`]
- **Rig calibration is real.** `P-CAL-ZPA` / `P-CAL-ZPB` in T100's capture reproduce the committed
  promoted vectors `T64-ZP-A` / `T64-ZP-B` **cell for cell** — every principal, interest, balance
  and due date across 57 and 56 rows, plus total interest. I checked the same for T83's and T84's
  captures: 8 of 8 calibration cells identical. [VERIFIED: my `/tmp/t101/calib.py`]
- **Capture attestation checks out**: canonical sha256 over the captures array =
  `314c4d551c1a406bbac85d3ba2db519d24ec808ed27d0a86a35d4f879c92bfba`, exactly as claimed; Fineract
  git commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`; `moneyHelperPrecision 19`, effective
  MathContext `(19, HALF_UP)` ordinal 4; Path A in-process, "No Fineract server is started and no
  database connection is opened"; every unvaried input field constant and inside the graded domain
  (MNT, dp 2, MONTHS/1, DECLINING_BALANCE, DAYS_30/DAYS_360, both multiples-of null, no down
  payment). Tenant ids are per-case and disjoint from T83's `cap_t83_*` and T84's `t84*_`; case
  order is genuinely scrambled (not sorted by n, rate or family). [VERIFIED: my `/tmp/t101/attest.py`]
- **`CaptureT100.java` really is `CaptureT84B.java` with only the header and the case list changed.**
  I applied the rename myself and diffed: the *only* differing lines are the `WHY THIS PASS EXISTS`
  paragraph and the `cases.add(prodDates(...))` block. Every line that produces a number — the seam
  call, the emitted columns, the attestation block, the `(19, HALF_UP)` setting — is byte-identical.
  [VERIFIED: `diff <(sed s/CaptureT84B/CaptureT100/g CaptureT84B.java) CaptureT100.java`]
- T83's capture canonical sha256 = `01b41d9ca79e2625a3eb67041c247b5f05815fab72529c4fa7b4710c64e3101b`
  over 332 cases — matches the `01b41d9c…3101b` cited in `gates.md`. (That T84 *re-ran* and got the
  same bytes is T84's claim, attributed as such; I did not re-run T84's capture.) [VERIFIED for the
  digest; T84's re-run UNVERIFIED by me, as T100 also states.]
- T84's committed `.gz` captures are the full runs: canonical sha256 `3900a204…dbf17` (251 cases)
  and `47611b04…23313` (95 cases), both matching the digests recorded in the trimmed JSON beside
  them. 251 + 95 − 4 calibrations = **342**. [VERIFIED]

---

## 3. THE SCOPE TABLE — every conclusion sentence in G-8, with its family and its domain

This is the check the brief exists for. Enumerated, not summarised. "Family" = which of A / B / both
/ neither the sentence is about; "Domain" = the measured set it is entitled to. Line numbers are
`gates.md` on `softhouse/T100-g8-two-families`.

| # | line(s) | conclusion sentence (abridged) | names FAMILY? | names DOMAIN? | verdict |
|---|---|---|---|---|---|
| 1 | 897 | "the *remedy* is a DEC-n amendment, which is a hard `user` gate" | both | n/a (procedural) | OK |
| 2 | 902 | "**state: OPEN** — blocks nothing today" | both | n/a | OK — verified, still OPEN |
| 3 | 908–912 | "Everything below is scoped to the family it was measured on … the domain is graded **by sampling** … unbounded" | both | graded domain, cited to `contract.go:1163-1170` | OK — the scoping instruction itself; citation verified |
| 4 | 916–925 | the 10-row discriminator table (per column: A vs B) | **both, per cell** | "measured at" row names rates/n/cell-count per family | **OK — I re-verified every one of the 10 rows on all 341 cells; see §4** |
| 5 | 927–931 | "312 family-A … 29 family-B … Every row of that table holds on **every** cell of its family **in those captures** — no exceptions, no mixed cases. The two families are disjoint and each is internally uniform **on what was swept**." | both | "in those captures", "on what was swept" | OK — domain explicitly bounded twice; independently reproduced |
| 6 | 933–939 | "T75 … Result: MNT 0.01 / 6 × 21.6 % … balance column never reaches zero … That shape is **family A**" | A | T75's single shape | **F-5** — true, but the `[VERIFIED]` tag cites `T100-FAMA-R21p6-N6-B2` (MNT **0.02**), a neighbouring cell, not the shape in the sentence |
| 7 | 941–945 | "On family A this is a live port-vs-oracle divergence on an **admitted** shape" | **A, named** | admitted (graded) domain | OK |
| 8 | 947–950 | "On family B … there is no port-vs-oracle divergence to arbitrate, because the port agrees with the oracle — both emit a schedule that never repays the loan" | **B, named** | family B as measured | OK — I verified over all 29, see §4 |
| 9 | 952–954 | "conformance.sh reports PASS … **only because no vector covers either family**" | both | the 42-vector corpus | OK — **I checked all 42 parity vectors: 0 land in either family** |
| 10 | 962–968 | family-A discriminator, 3 tests, "checked on every cell claimed below" | **A** | every family-A cell | OK — re-verified on 312/312 |
| 11 | 970–973 | "Test 3 is the decisive one … the discriminator the driver's re-derivation named in advance" | A vs B | n/a | OK |
| 12 | 977–984 | "T83's sweep — 330 cells, all family A … 198 fail / 132 clean / 0 family B"; domain enumerated | **A** | 4 rates × 8 terms, principals 1..27, all fixed fields listed | OK — I get 198/132/0 and principals 1..27, n 2..56 |
| 13 | 986–987 | "T84's extension — 111 further family-A cells" at 11 named rates, "terms up to n = 600, principals 1..100 000 minor" | **A** | rates + n + principal range named | OK — I get 111; T84 principals 1..100000, n 1..600 |
| 14 | 989–993 | "T100's confirmation — 3 family-A cells … all three fail, all three sum, all three predicted in advance" | **A** | the three shapes named | OK — reproduced |
| 15 | 997–1000 | "**This table describes 4 rates × 8 terms and nothing else**" | A | explicit | OK — model sentence |
| 16 | 1004–1035 | the boundary table (32 rows) | A | per-row "principals swept" column | OK — every LARGEST FAILING / SMALLEST CLEAN cell reproduced from the raw capture |
| 17 | 1037–1038 | "T75's report is CONFIRMED and is a strict subset … 0.03/6 **and above** are clean at 21.6 % / n = 6" | A | shape named; principal domain **not** | **F-7** — measured over principals 3..6 minor only; "and above" is a half-line beyond the sweep |
| 18 | 1040–1042 | "**21.6 % is not load-bearing for family A** — family A exists at **all 12 rates swept**, from 0.12 % to 300.0 %" | A | claims *all 12* swept rates | **F-1 — REJECTION.** Family A exists at **11** of the 12; there is **no** family-A cell at 600.0 %. Contradicts row 4 of its own table (line 925: "**11** of the 12 … all but 600.0 %") |
| 19 | 1041–1042 | "the rate moves *where* the boundary sits and moves it DOWN as the rate rises; the region is **empty at n = 2** at all four rates T83 tested" | A | "Across T83's grid", "four rates T83 tested" | OK — verified monotone at n = 56 (23/19/17/13) and empty at n = 2 on all four |
| 20 | 1046–1052 | "On family A the divergence … is **the FINAL row's outstanding principal and nothing else**: 198 divergent cells over T83's 198 failing cases … plus 111 further divergent cases in T84's sweep … T100 re-measured one: 2525 cells, exactly one diff" | **A, named twice** | the three measured sets | OK — **I re-graded all 312 and got exactly 1 diff each, always `outstanding_principal_minor` on the final row** |
| 21 | 1056–1058 | "**Attribution: the `:400` / `:1180` / `:1210` chain is T75's** … It is not the driver's finding and this record previously failed to say so" | A | n/a | OK — attribution correction present and explicit (item 6) |
| 22 | 1062–1074 | the five source bullets (`:398`, `:400`, `:278`/`:283`, `:1160`, `:1180`, `:1210`, readers `:617`/`:1180`/`:1629`) | A | pinned commit named | OK — **every line re-verified by me at `426a23544`; see §5** |
| 23 | 1076–1078 | "**The driver's candidate site is REFUTED** … `:413-426` reads `getPrevious()`'s balance and therefore can never populate the LAST period's memo" | A | pinned commit | OK — re-verified; `:413` is the method opening and `:426` the return, exactly |
| 24 | 1085–1090 | order-dependence: T83 5/5 + 4/4; T84 reproduced; T100 re-ran T84's probe, `1.09 → 0.00`, 3 clean controls unmoved, path identity 7/7 | **A** | the probe's own shapes | OK — I read `out/orderdep-t84probe-rerun-by-t100.json`: 7 cases, path identity true on all 7, `paidPrincipal` restored on all 7 |
| 25 | 1092–1095 | "So **family A is precisely: the oracle's outstanding-balance column is stale … while its principal column and its own totals are right.** That sentence is true **of family A** — … in that unscoped form it is **false**; see family B." | **A, and the unscoping is called out** | family A | OK — the model of what this rewrite was asked to do. (Nit: "its own totals are right" leans on `totalOutstandingAmount = 0`, which is a hard-coded zero carrying no information — the same table calls it a non-discriminator two pages earlier.) |
| 26 | 1103–1109 | family-B discriminator: principal column does not sum; sums to 0.00 vs 0.01; `totalPrincipalAmount` 0.00; no non-zero principal row; last row `interest 0.01`; forced recompute does not move the balance | **B** | "every family-B cell measured so far" | OK — **all six limbs verified on 29/29; see §4** |
| 27 | 1115–1118 | "annual rate **600.0 % — and no other rate has ever produced a family-B cell** … the 300 % failures are **family A** … 6 family-A cells at 300.0 %, 0 family-B" | **B** | rates swept named | OK — I get exactly 6 failing 300 % cells, all family A, 0 family B |
| 28 | 1119 | "principal **MNT 0.01** — no other principal has produced a family-B cell" | **B** | principals swept | OK — every family-B cell has disbursement = 1 minor |
| 29 | 1120–1123 | "n ∈ {104…122} ∪ {150, 200, 250} … T100 added n = 122 and n = 250, **which are above the top of n T84 swept** … At n = 103 the same shape is **clean**" | **B** | n set enumerated exactly | **F-4** — the n-set and the n = 103 bracket are exactly right; but n = 122 is **not** above T84's top (T84 swept 150 and 200, as the same bullet says two lines earlier, and as T100's own `prediction.json` records with basis "T84 measured"). Only n = 250 is |
| 30 | 1125–1127 | "**The Go port reproduces family B cell for cell — 0 divergent cells** … On family B there is **no oracle/port divergence at all**" | **B, named** | T84's 22 + T100's 1 through the grader | OK — **I re-graded all 29 through the real port: 25 751 graded cells, 0 cell diffs.** Strengthened, not weakened |
| 31 | 1129–1131 | "**Family B is NOT order-dependent** … So the family-A mechanism above does **not** explain family B, and no claim is made that it does" | **B** | 3 + 3 probe cells named | OK — verified from the probe output |
| 32 | 1135–1140 | four `[UNVERIFIED]` items: cause; other rates/principals/n < 104; termination in n; `MinorUnitDigits ≠ 2` and Path B/REST | **B** | explicit | OK — correctly marked, correctly scoped |
| 33 | 1146–1151 | "`invariant_exemptions` has power over invariant statuses and none over cell diffs (`CheckInvariants` runs first at `grade.go:488` … `:489-493` short-circuits the **outcome**, not the computation)" | both | source cited | OK — **re-verified at those exact lines** |
| 34 | 1153–1157 | "Both halves … measured with the REAL `conformance.Run` and the REAL Go port … Nothing was written to `.softhouse/vectors`; the corpus count did not change" | both | one run, two cells | OK — reproduced end-to-end; vectors tree provably unchanged |
| 35 | 1159–1165 | the option-(a) table: 761 / 2525 cells; 0 / 1 cell diffs; FAIL+2 violations / FAIL on cell diff with all six invariants HOLD; PASS+parityPass 1+0 violations+zero port change / FAIL unchanged; both admissible | **both, column-per-family** | the two named cells | OK — **every cell of this table reproduced exactly by me; see §6** |
| 36 | 1169–1172 | "**On family B, option (a) is reachable TODAY** — existing mechanism, **no port change**, no DEC-n amendment" | **B, named** | family B | OK — reproduced |
| 37 | 1173–1176 | "**On family A, option (a) still requires a port change** … That is a port change no agent has made or proposes to make unilaterally" | **A, named** | family A | OK — reproduced; both halves present and each attached to its family (item 3 satisfied) |
| 38 | 1178–1179 | "T83's sentence … is therefore **true of family A and false of family B**, and it was recorded here unscoped" | both, split | — | OK |
| 39 | 1181–1185 | "**each** variant's process exit code is non-zero for a reason that has **nothing to do with G-8**" | both | the four demo runs | **F-3 — REJECTION.** False for three of the four variants: `ExitCode()` returns **1** from `ParityFail>0 \|\| InvariantViolations>0` *before* it inspects `FatalReasons`, so their non-zero exit **is** the G-8 finding |
| 40 | 1187–1190 | "Prepared and **NOT promoted**, for both families" + paths | both | — | OK — paths resolve on the branch; nothing in `.softhouse/vectors` |
| 41 | 1196–1198 | "That was true of **T83's grid** and false as a statement about the graded domain" | A | explicit | OK |
| 42 | 1200–1201 | "**Over T83's grid** … the largest failing principal is **MNT 0.23**, at 7.0 % / n = 56" | A | grid named | OK — reproduced exactly (`T83-SW-R7p0-N56-B23`). Nit **F-8**: "n ∈ {2…56}" reads as contiguous; the eight discrete terms are listed correctly in the table above |
| 43 | 1202–1205 | "**Over the union of every cell T83, T84 and T100 have swept** (687 cells; 12 rates …; n from 1 to 600): the largest failing principal is **MNT 2.91**, at 0.12 % / n = 600 — **11.6× the old bound**" | A | union named precisely | 687 / 2.91 / 0.12 % / n = 600 / clean at 2.92 **all reproduced**. But **F-2 — REJECTION**: "11.6×" has no antecedent in this section; against the only bound stated here (MNT 0.23) the ratio is **12.65×** |
| 44 | 1206–1209 | "**MNT 1.09 fails at 3.6 % p.a. over n = 360 — an ordinary 30-year monthly term at an ordinary rate** … This is not sub-MNT dust and must not be described as such" | A | shape named, clean bracket at 1.10 | **OK — present, prominent, its own bullet, explicitly protected from being called dust. Item 4 satisfied.** Reproduced: 109 fails, 110 clean |
| 45 | 1210–1214 | "The region **grows as the term lengthens and as the rate falls**: 59, 118, 176, 234, 291 minor at n = 120…600 — ≈ n/2 … every one bracketed by a measured clean cell one minor unit above" | A | 0.12 % series named | OK — all five values and all five brackets reproduced exactly |
| 46 | 1216–1225 | what was NOT swept: dp, currency, day count, frequency, disbursement, charges, multiples-of, MathContext; the 12 rates and the gaps between them; "**No term above n = 600 has ever been asked**"; "**the measurement establishes no upper bound on the failing principal over the graded domain as a whole** — only over the grid swept"; the practical reading "holds **over that grid**, and is not a proof about the domain" | A (bound) | exhaustive | **OK — the strongest passage in the document. Every negative claim verified: max n swept = 600; the 12 rates are exactly those listed; the gaps are real; no charges, dp 2, MNT only. Item 4 satisfied.** |
| 47 | 1229–1233 | "T83 … **labelled it a HYPOTHESIS CONSISTENT WITH the measurement rather than a measured fact**. **That call was right** … held on all 32 shapes, 106 of 106" | A | T83's grid | OK |
| 48 | 1235–1243 | "**It is false outside that grid** … over T83's own 330 cells it holds **330 of 330**; over all 342 non-calibration cells of T84's two captures, **320 held, 22 refuted, 0 exact ties**. **Every one of the 22 refutations is a family-B cell** … gap `+2.429e-19` at n = 104 … `+3.025e-36` at n = 200 … offered as an explanation, not as a verified mechanism `[UNVERIFIED]`" | **B (refutations), A (fit)** | both sets named | **OK — I reproduced 330/330 and 320/22/0 in exact rational arithmetic, and both gap values to four figures. See §7 for the adjudication.** |
| 49 | 1245–1249 | "**A count correction:** T84 records **18**; T100 finds **22**. The four extra are `T84-TIE-R600p0-N{108,120,150,200}-B1`, which `prediction.json` registers as `predictedFails: false` and which measured FAIL" | B | the 342 cells | **OK — T100 is RIGHT. Adjudicated independently; see §7** |
| 50 | 1251–1253 | "the closed form is a good description of family A on the grid where it was fitted, and it is **not a law**. It does not predict family B at all. No claim is made for any un-sampled rate, term or day-count" | both, split | explicit | OK |
| 51 | 1257–1259 | "**(a)** … **Reachable today on family B with zero port change; requires a port change on family A.** Scope any decision to one family; a vector for one says nothing about the other" | **both, split** | — | OK |
| 52 | 1260–1263 | "**(b)** … Cheap in code for family A over the grid swept — but the region is **not** fully bounded … and it is a **graded-domain amendment**" | A named; caveat covers B | "over the grid swept" | OK — **describes, does not decide** |
| 53 | 1264–1267 | "**(c)** … That is what the port does *today, ungraded, on family A only* — **on family B … (c) does not describe family B at all**" | **both, split** | — | OK — **describes, does not decide** |
| 54 | 1269–1271 | "**(b) and (c) both amend the graded domain … a hard `user` gate no agent may cross.** Buyan decides. T83, T84 and T100 each analysed them and **decided none and recommend none**; T100 attaches only the measurement and the scoping" | both | — | **OK — item 7 satisfied; see §8** |
| 55 | 1273–1278 | "**What it leaves uncovered**: on T84's accounting, **331** measured divergent-or-invalid cells … 309 family-A (198 T83 + 111 T84) plus **22** family-B … The last 22 are the worse half" | both, split | "on T84's accounting" | **F-6** — correctly attributed and internally consistent, but it is the one number taken over a *narrower* set than the section's own union; over T83+T84+T100 it is **341** (312 + 29). I measured 312 family-A divergent cells through the real grader |
| 56 | 1280–1282 | "**Conformance is unmoved by this rewrite**: PASS, exit 0, 42 parity vectors, 5576 graded cells, 0 invariant violations. Nothing was promoted" | both | — | OK — reproduced exactly |

**Sentences that name neither family nor domain: none.** Every conclusion in the section carries at
least one, and the great majority carry both explicitly. On that structural test the rework does
what it was asked to do. It fails on three sentences whose *content* is wrong, not on their form.

---

## 4. Item 1 & item 2 — the discriminators, re-derived from scratch

I wrote my own classifier (no code shared with T83's, T84's or T100's), parsed every money value as
**integer minor units** via exact `Decimal` scaling with an integrality assertion, and ran it over
the four committed raw captures — including T84's **full** `.gz` runs, not the trimmed JSON.

Cell counts, independently derived:

| capture | cases | calibration | sweep | family A | family B | clean |
|---|---|---|---|---|---|---|
| T83 | 332 | 2 | **330** | **198** | **0** | **132** |
| T84 (both) | 346 | 4 | **342** | **111** | **22** | **209** |
| T100 | 17 | 2 | **15** | **3** | **7** | **5** |
| **union** | | | **687** | **312** | **29** | **346** |

Every number T100 published matches. 687 swept cells, 312 family A, 29 family B — confirmed.

**Family A signature — ALL HOLD on 312/312, no exceptions:** `totalPrincipalAmount` = the
disbursement; **exactly one** non-zero principal row; that row **is the last**; it carries the
**whole** disbursement; last row interest = `0.00`; balance column **constant** at the disbursed
amount; `totalOutstandingAmount` = `"0"`.

**Family B signature — ALL HOLD on 29/29, no exceptions:** principal column sums to **0.00**;
disbursement is **1 minor unit** on every cell; `totalPrincipalAmount` = `0.00`; **no** non-zero
principal row; last row interest = `0.01`; balance column constant at the disbursed amount;
`totalOutstandingAmount` = `"0"`.

Family B rates: **{600.0} only**. Family B n: **{104…122} ∪ {150, 200, 250}** — exactly the set
`gates.md` states. Family A rates: **{0.12, 1.2, 3.6, 7.0, 12.0, 16.8, 21.6, 36.0, 48.0, 96.0,
300.0}** — **eleven**, and **600.0 is absent**. Family A n: 3…600.

**The last limb of item 1 — "the Go port reproduces family B cell for cell, so there is NO
divergence in family B at all" — is the one that decides whether the two-family framing is right, so
I did not accept it on one graded cell.** I built a vector for **every** family-B cell in every
committed capture and graded all 29 in one run against the **real `conformance.Run` and the real Go
port** (main's current `emi.go`), over a throw-away `/tmp` store:

```
built 29 family-B vectors
exit 1  parityPass 0  parityFail 29  invariantViolations 58  inadmissible 0  refused 0
cases: 29   with CELL DIFFS: 0   invariant-only FAIL: 29   clean PASS: 0   total graded cells: 25751
TOTAL divergent cells: 0
```

**Zero cell diffs across 25 751 graded cells. Confirmed, over a set larger than either T84's 22 or
T100's 1.** Every one of the 29 failures is invariant-only (58 = two per case). The two-family
framing survives.

I did the same for family A — all 312 cells in one run:

```
built 312 family-A vectors
exit 1  parityPass 0  parityFail 312  invariantViolations 0  inadmissible 0  refused 0
cases: 312  with CELL DIFFS: 312  per-case diff distribution {1: 312}  total graded cells: 182727
TOTAL divergent cells: 312   (every one: final row outstanding_principal_minor, oracle = B, port = 0)
```

**Exactly one cell per case, always the same cell, and zero invariant violations.** T100's "ONE CELL
PER CASE" is confirmed and extended from 309 cited cells to 312 measured ones.

Cross-check against T84's own committed `port-vs-oracle.json` (344 entries): family A 111 cases /
111 divergent cells, all `outstanding_principal_minor`; family B 22 cases / **0** divergent cells.
Agrees with mine.

**Item 2 — `totalOutstandingAmount`.** T100 is **RIGHT and T83/the driver's brief are wrong.** It
reads `"0"` on **all 312 family-A cells and all 29 family-B cells** — 341 of 341 — so it separates
nothing. This corroborates the standing pattern that the field is a hard-coded `BigDecimal.ZERO`
passed straight through. I then checked the rewritten section does not lean on it anywhere: it
appears **once**, in the table at line 921, explicitly labelled "**so this field does not
discriminate**", and it is **absent** from both discriminator definitions (lines 962–968 and
1103–1109). Clean. [VERIFIED]

Two further limbs of item 1 verified: forced memo recompute **does not** move the family-B balance
(3/3 at n = 104, 108, 120; `A_balanceAsEmitted` = `B_balanceAfterForcedRecompute` = `0.01`), while
the family-A control in the same run moves `1.09 → 0.00`; path identity true on all 7 cases;
`paidPrincipal` restored on all 7. [VERIFIED: `out/orderdep-t84probe-rerun-by-t100.json`]

And the corpus-blindness claim (line 952): **I parsed all 42 committed parity vectors and none of
them lands in either family** — every one amortizes to zero. So the green bar really is silent
about both. [VERIFIED]

---

## 5. Item 6 — attribution and source, re-verified at `426a23544`

`/Users/buv/fineract` at `426a23544e8426a38ae43ae404670a0a7e85b9eb`, clean tree.

`fineract-progressive-loan/.../calc/data/RepaymentPeriod.java`:

- **`:398`** is `.minus(getDuePrincipal(), getMc()); //` inside the `outstandingBalanceCalculation`
  memo body. ✔
- **`:400`** is `}, () -> new Object[] { paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount });`
  — **`emi` is absent**. ✔
- The sibling: **`:272`** opens `getDueInterest()`, **`:278`** opens its `Memo.of(`, and **`:283`**
  is `fixedInterest, reAged, emi, interestPaymentGrace });` — **`emi` is literally on line 283**.
  T100's citation `(:278 opening, :283)` is exact, and the driver's `:272-286` is the method span. ✔
- **`:371-372`** `isFullyPaid()` is
  `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().isEqualTo(getTotalPaidAmount())` — the
  `0 == 0` step T75 contributed. ✔
- **`:413-426`** is `getInitialBalanceForEmiRecalculation()` exactly, and **`:416`** is
  `initialBalance = getPrevious().get().getOutstandingLoanBalance();`. It reads the **previous**
  period's memo, so it can never populate the **last** period's. **The driver's candidate site is
  REFUTED — confirmed by me.** ✔
- `emi` is a Lombok **`@Setter`** at `:57-58` — a plain field setter that invalidates nothing, as
  claimed. ✔

`fineract-progressive-loan/.../calc/ProgressiveEMICalculator.java`:

- **`:1160`** opens `private void calculateLastUnpaidRepaymentPeriodEMI(...)`. ✔
- **`:1176-1180`** is the fallback, and **`:1180`** ends
  `.filter(rp -> rp.getOutstandingLoanBalance().isGreaterThanZero());` applied to the **last**
  period (`reduce((first, second) -> second)`) — so it does populate the memo on the target period. ✔
- **`:1210`** is `repaymentPeriod.setEmi(adjustedEmi);`, in the **same method**. ✔
- Readers of `getOutstandingLoanBalance()` in that class: **`:617`, `:1180`, `:1629`** — exactly
  three (`:604` is the differently-named `getOutstandingLoanBalanceOfPeriod`). ✔

`nexus/.../conformance/grade.go`:

- **`:488`** is `r.Invariants = CheckInvariants(v, got, placeholders)` and **`:489-493`** is the
  `if len(diffs) > 0 { … return r }` early return. T100's correction of T83's `:487-497` is right. ✔

**Attribution.** The G-8 section credits the `:400`/`:1180`/`:1210` chain to **T75** at line 1056,
states plainly that "It is not the driver's finding and this record previously failed to say so",
and records the driver's candidate site as **REFUTED** at line 1076. Both required corrections are
present and correctly worded. **Item 6: PASS.**

---

## 6. Item 3 & item 9 — I reproduced the exemption demo end to end

I did not accept the disclosed caveat; I re-ran the measurement. I rebuilt T100's
`exemption_demo_t100.py` against a scratch root containing **my** worktree's `nexus` (i.e. `main`'s
current port, newer than T100's), `main`'s `PIN.json`/`capabilities.json` read-only, and T100's
committed capture. Real `conformance.Run`, real port, throw-away `/tmp` store, nothing written to
`.softhouse/vectors`.

| variant | exit | parityPass / parityFail | invariantViolations | graded cells | outcome |
|---|---|---|---|---|---|
| FAMILY-B-NO-EXEMPTION | 1 | 0 / 1 | **2** | **761** | FAIL — `principal_portions_sum_to_disbursed` and `principal_amortizes_to_zero` VIOLATED, **no cell diff** |
| FAMILY-B-WITH-EXEMPTION | 2 | **1** / 0 | **0** | **761** | **PASS** — three invariants EXEMPT, zero port change |
| FAMILY-A-NO-EXEMPTION | 1 | 0 / 1 | 0 | **2525** | FAIL — `row 360 outstanding_principal_minor: expected 109 minor units, got 0 (delta -109)`; **all six invariants HOLD** |
| FAMILY-A-WITH-EXEMPTION | 1 | 0 / 1 | 0 | **2525** | **FAIL, unchanged** — two invariants register EXEMPT and the cell diff still decides |

**Every cell of `gates.md`'s option-(a) table is reproduced byte-for-byte, on a newer port.** Item 3
is satisfied: the section states **both** halves, attaches each to its family by name (lines
1169–1176), and explicitly retires T83's unscoped "option (a) is NOT reachable" at line 1178.

**Item 9 — the caveat, tested rather than accepted.** The non-zero exits hide nothing, but the
caveat mis-describes them:

- The **only** non-G-8 fatal is the corpus-coverage fatal on `monthend.reanchor`, and it is a pure
  artefact of a one-vector scratch store: in the full corpus that capability **is** killed, by
  `MONTHEND-CONTINUE-FROM-CLAMPED-DAY` and `MONTHEND-REANCHOR-GUARD-STRICTLY-GREATER-THAN-28`
  [VERIFIED: my conformance run, `/tmp/t101-conf.log:71`]. The second fatal, "NO PARITY VECTOR WAS
  GRADED", is a downstream consequence of the only vector failing, which `gates.md` itself says.
- **But** `Summary.ExitCode()` (`grade.go:154-160`) returns **1** on
  `ParityFail+ContractFail+SelfTestFail > 0 || InvariantViolations > 0` **before it ever inspects
  `FatalReasons`**. Three of the four variants exit 1. For those three the non-zero exit **is** the
  G-8 finding, not an unrelated fatal. Only FAMILY-B-WITH-EXEMPTION's exit **2** comes from the
  coverage fatal. So the caveat's "each variant … for a reason that has nothing to do with G-8" is
  false three times out of four. It errs *safely* — it under-claims the harness rather than hiding a
  failure — but it invites the reader to discount an exit code that is honest. **F-3.**

---

## 7. Item 5 — the closed form, and I RULE on the 18-vs-22 dispute

I evaluated `B_minor × a(r,n) < 0.5`, with `a(r,n) = r/(1−(1+r)^−n)` and `r = annual/100/12`, in
**exact rational arithmetic** (`fractions.Fraction`, no `Decimal`, no float anywhere in the
comparison), independently of T83's, T84's and T100's code:

| set | cells | held | refuted | exact ties |
|---|---|---|---|---|
| T83's capture | **330** | **330** | **0** | 0 |
| T84's two captures | **342** | **320** | **22** | **0** |
| T100's capture | 15 | 8 | 7 | 0 |

**RULING: T100's 22 is right; T84's 18 is wrong.** All 22 refutations are family-B cells
(600.0 % / B = 1 / n ≥ 104), and the four T84 omitted are precisely
`T84-TIE-R600p0-N{108,120,150,200}-B1`, exactly as `gates.md` says. The measured gaps match to four
significant figures: `+2.429e-19` at n = 104, `+3.025e-36` at n = 200.

**And I can say *why* T84 undercounted, which neither party recorded.** T84's
`.softhouse/reviews/T84-evidence/prediction.json` stores `BtimesA` for those four cells as the
**float** `0.5` — e.g. `{"B": 1, "BtimesA": 0.5, "n": 108, "predictedFails": false}`. In exact
rational arithmetic `B·a − ½` is strictly **positive** there (`+4.799e-20` at n = 108), so the
closed form predicts CLEAN and the measured FAIL refutes it. T84 classified them as *exact ties*
and excluded them, because double-precision arithmetic could not resolve a residual of order
1e-20. **The 18-vs-22 dispute is a float-precision artefact in T84's evaluation** — a small,
concrete illustration of this project's own rule that no monetary decision may be made in floating
point, even in an analysis script. T100's exact-rational re-evaluation is the correct method and
the correct count. `gates.md` line 1245 is accurate; it just does not say why, and could usefully.

The section labels the closed form a **FALSIFIED hypothesis**, names the precision-19-floor
refutations, and marks the sub-ulp explanation `[UNVERIFIED]`. **Item 5: PASS on substance,** with
the count adjudicated in T100's favour.

---

## 8. Item 7 — gate discipline

- **`state: OPEN`** at line 902 [VERIFIED].
- Option **(b)** (line 1260) and option **(c)** (line 1264) are each stated **descriptively**: what
  they would cost, what they would and would not cover, and — for (c) — that it "does not describe
  family B at all". Neither is chosen.
- Line 1269: "**(b) and (c) both amend the graded domain, which is a change to a ratified DEC-n — a
  hard `user` gate no agent may cross.** Buyan decides. T83, T84 and T100 each analysed them and
  **decided none and recommend none**; T100 attaches only the measurement and the scoping."
- **Nothing pre-implemented**: `.softhouse/vectors` tree is bit-identical to the merge base; no
  contract-refusal vector was added; `contract.go` untouched; `capabilities.json` untouched. A
  refusal vector or a graded-domain edit would have shown in the tree hash and did not.
- The proposed vectors for **both** families exist but are explicitly labelled "Prepared and **NOT
  promoted**" (line 1187), and the handoff says promoting one "is still a scope decision for a task
  with a promotion mandate, not for a write-up task". Correct restraint.
- Option (a) is presented as **reachable**, not as **taken**. That is a statement of fact about the
  existing mechanism, not an amendment, and it is the kind of recommendation the brief permits.

**No fait accompli. Item 7: PASS.**

---

## 9. FINDINGS

### M-1 — P1, MERGE HAZARD ON `main` (not a defect in this branch, but this branch must not be merged without it)

`main` and this branch have merge base `8da4b831`. Since that fork, **`main` gained a 66-line block
`## G-8 — UPDATE from local fire 20260820-200002` at `main:.softhouse/gates.md:936-998`**, written by
the `/softhouse-program` driver. T100 forked before it and its `git diff main...HEAD` (a merge-base
diff) cannot show it. A merge will therefore leave `gates.md` carrying **both** write-ups, and the
older one contradicts the newer on the most decision-relevant sentence in the gate:

> `main:.softhouse/gates.md` — "**1. Option (a) is reachable today on Family A, with no port change and
> no amendment.** Graded with the real `conformance.Run` and the real port: **without** the exemption,
> 761 cells, **0 cell diffs**, FAIL with two invariants violated; **with** the exemption, **PASS**."

**That is the family-B measurement attributed to family A.** 761 graded cells, 0 cell diffs, two
invariants violated, PASS under exemption — I reproduced all four numbers myself, and they belong to
`600.0 % / MNT 0.01 / n = 108`, which is **family B**. On family A the same demo gives 2525 cells,
**one** cell diff, and FAIL **unchanged** under exemption. `main`'s block also carries the
**18**-refutation count I have now ruled wrong, and describes family A's mechanism while calling the
family-B result family A's.

T100's rewrite gets all of this right. **Remedy: whoever merges this branch must delete
`main:.softhouse/gates.md:936-998` in the same commit**, since T100's section supersedes it in full.
Merging without that ships a product-owner-facing document that says option (a) is free on the
family where it is not.

### F-1 — P1, REJECTION (`gates.md:1040`)

> "**21.6 % is not load-bearing for family A** — family A exists at **all 12 rates swept**, from
> 0.12 % to 300.0 %."

**False.** Family A exists at **11** of the 12 swept rates. There is **no** family-A cell at
600.0 % — every failing cell at that rate is family B. The sentence asserts family A at precisely
the rate that defines family B, in a document whose thesis is that the two families are disjoint,
and it **contradicts its own discriminator table nine lines earlier** (line 925: "**11** of the 12
annual rates swept (all but 600.0 %)").

[VERIFIED: my independent reclassification of all 687 swept cells across the four committed raw
captures — family-A rates = {0.12, 1.2, 3.6, 7.0, 12.0, 16.8, 21.6, 36.0, 48.0, 96.0, 300.0}; family
A at 600.0 % = **∅**.]

This is P-23 recurring, by the exact leak `patterns.md` already documents: *"an author fixes the
section the review named and leaves the sections that restate the same claim"*. The table was
scoped; the prose restatement was not. **Remedy:** "family A exists at **11 of the 12** rates swept
— every rate from 0.12 % to 300.0 %, and **not** at 600.0 %, where every failing cell is family B."

### F-2 — P2, REJECTION (`gates.md:1204`)

> "the largest failing principal is **MNT 2.91**, at 0.12 % / n = 600 — **11.6× the old bound**"

"11.6×" is T84's figure, computed against T83's *handoff* phrasing "every principal in the region is
below MNT 0.25" (2.91 / 0.25 = 11.64). **T100's rewrite deleted every occurrence of "MNT 0.25"** —
`grep` finds none in the section — so the multiplier now has no antecedent. Against the only bound
this section states, **MNT 0.23** (quoted at line 1196 and measured at line 1201), the ratio is
**12.65×**. [VERIFIED: 291/23 = 12.652; 2.91/0.25 = 11.64.]

**Remedy:** either "**12.7×** the MNT 0.23 measured over T83's grid", or restore the antecedent:
"11.6× the 'below MNT 0.25' bound this file previously asserted".

### F-3 — P2, REJECTION (`gates.md:1181-1185`)

> "**each** variant's process exit code is non-zero for a reason that has **nothing to do with G-8**"

False for three of the four variants. `Summary.ExitCode()` returns **1** from
`ParityFail+ContractFail+SelfTestFail > 0 || InvariantViolations > 0` **before** it inspects
`FatalReasons` [VERIFIED: `nexus/internal/apps/loanschedule/conformance/grade.go:154-160`], and
FAMILY-B-NO-EXEMPTION, FAMILY-A-NO-EXEMPTION and FAMILY-A-WITH-EXEMPTION all exit **1** — i.e.
because of the G-8 failure itself. Only FAMILY-B-WITH-EXEMPTION exits **2**, and only that one is
the unrelated `monthend.reanchor` coverage fatal.

I reproduced all four runs; **the caveat hides nothing** — the case outcomes and invariant statuses
are exactly as tabulated, and the coverage fatal really is a one-vector-store artefact. The defect
is that the sentence is not true as written and teaches the reader to discount an honest signal.

**Remedy:** "Only the **PASS** variant's exit code is unrelated to G-8: a one-vector scratch store
trips the corpus-level coverage fatal on `monthend.reanchor`, so it exits 2 rather than 0. The three
FAILing variants exit 1 **because of the G-8 failure itself**. In every case the case outcome and
the invariant statuses in the table are the measurement."

### F-4 — P3 (`gates.md:1122`, and `CaptureT100.java` header, and `src/build_harness.py`)

> "T100 added n = 122 and n = 250, **which are above the top of n T84 swept**"

n = 250 is; **n = 122 is not**. T84 swept n = 150 and n = 200 at the same rate and principal — as
the *same bullet* says two lines earlier, and as T100's own `prediction.json` records with basis
"T84 measured". n = 122 is one above T84's top **contiguous** n (121). **Remedy:** "n = 122, one
above T84's contiguous top of 121, and n = 250, above the top of n T84 swept."

### F-5 — P3 (`gates.md:933-939`)

The sentence describes T75's shape as **MNT 0.01 / 6 × 21.6 %** and tags it
`[VERIFIED by T100: T100-FAMA-R21p6-N6-B2 …]`. `B2` is **MNT 0.02** — a neighbouring cell, not the
one in the sentence. The claim itself is true and verifiable: `T83-SW-R21p6-N6-B1` is family A
[VERIFIED by my reclassification]. Citation defect only. **Remedy:** cite `T83-SW-R21p6-N6-B1`, or
say "the neighbouring cell at MNT 0.02".

### F-6 — P3 (`gates.md:1275-1278`)

"on T84's accounting, **331** measured divergent-or-invalid cells" is correctly attributed and
internally consistent (198 + 111 + 22), but it is the one figure in the rewrite taken over a
*narrower* set than the section's own union. Over T83 + T84 + T100 it is **341** (312 family-A
divergent cells, which I measured through the real grader, plus 29 family-B). **Remedy:** add
"— 341 over the union including T100's own cells".

### F-7 — P3 (`gates.md:1038`)

"0.03/6 **and above** are clean at 21.6 % / n = 6" — T83 swept principals **1..6 minor** at that
shape, so "and above" extends past the sweep. The boundary table's own "principals swept" column
makes this visible, but the sentence should say "3..6 minor, the range swept".

### F-8 — P3 (`gates.md:1200`)

"n ∈ {2…56}" for T83's grid reads as a contiguous range; the eight discrete terms are
{2, 3, 4, 6, 12, 24, 36, 56}, as the table above correctly lists.

---

## 10. What I checked and found NOTHING wrong with, so silence is distinguishable from not looking

- Every cell of the 10-row discriminator table, on all 341 classified cells — **no exceptions, no
  mixed cases**. The families really are disjoint and internally uniform on what was swept.
- All 32 rows of T83's boundary table (LARGEST FAILING and SMALLEST CLEAN), re-derived from the raw
  capture.
- The 0.12 % series 59 / 118 / 176 / 234 / 291 at n = 120 / 240 / 360 / 480 / 600, and all five
  clean brackets one minor unit above.
- MNT 0.23 at 7.0 % / n = 56 over T83's grid; MNT 2.91 at 0.12 % / n = 600 over the union with MNT
  2.92 clean beside it; MNT 1.09 at 3.6 % / n = 360 with MNT 1.10 clean beside it.
- Every negative claim in the "what was NOT swept" paragraph: max n swept = 600; exactly twelve
  rates; the named gaps between them are real; principals 1..27 (T83), 1..100 000 (T84); no charges;
  dp 2; MNT only; `(19, HALF_UP)` only.
- The 300.0 % result: 53 cells, 6 failing, **all family A, 0 family B**.
- n = 103 clean at 600.0 % / MNT 0.01, in both T84's and T100's captures.
- All 42 committed parity vectors: **none** lands in either family.
- Every Fineract source line cited (`RepaymentPeriod.java:398, :400, :272/:278/:283, :371-372,
  :413-426, :57-58`; `ProgressiveEMICalculator.java:1160, :1176-1180, :1210, :617, :1629`) and
  `grade.go:488, :489-493, :154-160`.
- Prediction-before-probe ancestry, prediction immutability, 15/15 predictions held, no unregistered
  case.
- Rig calibration cell-for-cell against two already-promoted vectors, on all four captures.
- T84's `.gz` capture digests, and T83's capture digest against the `01b41d9c…3101b` cited.
- `CaptureT100.java`'s mechanical derivation from `CaptureT84B.java`.
- Float discipline in every file T100 added.
- Conformance: PASS, exit 0, 42 / 5576 / 0, run with **bash**.

**What I did NOT verify** (stated plainly rather than filled in):

- That T84 re-ran T83's capture and got byte-identical output. That is T84's measurement; I verified
  only that the digest cited matches the committed T83 capture. `[UNVERIFIED by T101]`
- The *cause* of family B. Not located by T84, T100 or me. The sub-ulp explanation is consistent
  with my exact-rational gaps but I did not trace it in source. `[UNVERIFIED]`
- Whether family B exists at any rate other than 600.0 %, any principal other than MNT 0.01, below
  n = 104, or above n = 250. Nothing outside those bounds has been asked by anyone. `[UNVERIFIED]`
- `MinorUnitDigits ≠ 2`, currencies other than MNT, day counts other than DAYS_30/DAYS_360, and
  Path B / REST. Not measured by T83, T84, T100 or me. `[UNVERIFIED]`
- T83's `measured-boundary.json` and `port-vs-oracle.json` internals — I re-derived the same numbers
  from the raw capture rather than auditing those files, as T100 also did.

---

## 11. What a re-run must do

1. Fix **F-1**, **F-2**, **F-3** in `gates.md` (each is one sentence).
2. Fix **F-4**…**F-8** while in the file, and — per `patterns.md`'s "corrections leak" rule — **grep
   the whole section for restatements** of each corrected claim before committing. F-4 in particular
   is restated in `CaptureT100.java`'s header and `src/build_harness.py`.
3. Optionally record in the closed-form section **why** T84 counted 18: its `prediction.json`
   evaluated `BtimesA` in double precision and read four strictly-positive 1e-20-scale residuals as
   exact ties. That is a useful, transferable finding, and it makes the count correction
   self-evidently right rather than merely asserted.
4. Whoever merges must also delete `main:.softhouse/gates.md:936-998` (**M-1**) in the same commit.

Nothing in the measurement needs redoing. I re-derived all of it and, on family A (312 cells) and
family B (29 cells), measured **more** than T100 did and got the same answer.
